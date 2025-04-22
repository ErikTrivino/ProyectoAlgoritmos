import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from unidecode import unidecode
import json
import difflib
from typing import List, Dict

class PaperItem(scrapy.Item):
    # Definición de la estructura de datos para cada publicación
    title = scrapy.Field()
    authors = scrapy.Field()
    year = scrapy.Field()
    abstract = scrapy.Field()
    doi = scrapy.Field()
    source = scrapy.Field()
    type = scrapy.Field()
    journal = scrapy.Field()
    publisher = scrapy.Field()

class BibliometricSpider(scrapy.Spider):
    name = 'bibliometric'
    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 2,
        'FEED_FORMAT': 'json',
        'FEED_EXPORT_ENCODING': 'utf-8',
    }

    def __init__(self, query='computational thinking', *args, **kwargs):
        super(BibliometricSpider, self).__init__(*args, **kwargs)
        self.query = query
        self.start_urls = self.prepare_start_urls()
        self.unique_entries = []
        self.duplicate_entries = []
        self.similarity_threshold = 0.85

    def prepare_start_urls(self) -> List[str]:
        """Prepara las URLs iniciales para cada base de datos"""
        return [
            f'https://www.semanticscholar.org/search?q={self.query}',
            f'https://scholar.google.com/scholar?q={self.query}',
            f'https://pubmed.ncbi.nlm.nih.gov/?term={self.query}'
            # Agregar más URLs según sea necesario
        ]

    def parse(self, response):
        """Método principal para parsear cada respuesta"""
        if 'semanticscholar.org' in response.url:
            yield from self.parse_semantic_scholar(response)
        elif 'scholar.google.com' in response.url:
            yield from self.parse_google_scholar(response)
        elif 'pubmed.ncbi.nlm.nih.gov' in response.url:
            yield from self.parse_pubmed(response)

    def parse_semantic_scholar(self, response):
        """Parser específico para Semantic Scholar"""
        for paper in response.css('[data-test-id="paper-row"]'):
            item = PaperItem()
            item['title'] = paper.css('[data-test-id="title-link"]::text').get()
            item['authors'] = '; '.join(paper.css('[data-test-id="authors-list"] a::text').getall())
            item['year'] = paper.css('[data-test-id="year"]::text').get()
            item['abstract'] = paper.css('[data-test-id="abstract-text"]::text').get()
            item['doi'] = paper.css('[data-test-id="doi-link"]::text').get()
            item['source'] = 'Semantic Scholar'
            item['type'] = 'article'
            yield item

    def parse_google_scholar(self, response):
        """Parser específico para Google Scholar"""
        for paper in response.css('.gs_r.gs_or.gs_scl'):
            item = PaperItem()
            item['title'] = paper.css('.gs_rt::text').get()
            item['authors'] = paper.css('.gs_a::text').get()
            
            # Extraer año de la línea de autores
            if item['authors']:
                year_match = re.search(r'\b(19|20)\d{2}\b', item['authors'])
                item['year'] = year_match.group() if year_match else ''
            
            item['abstract'] = paper.css('.gs_rs::text').get()
            item['source'] = 'Google Scholar'
            item['type'] = 'article'
            yield item

    def parse_pubmed(self, response):
        """Parser específico para PubMed"""
        for paper in response.css('.article-overview'):
            item = PaperItem()
            item['title'] = paper.css('.docsum-title::text').get()
            item['authors'] = paper.css('.docsum-authors::text').get()
            item['journal'] = paper.css('.docsum-journal-citation::text').get()
            
            # Extraer año de la información del journal
            if item['journal']:
                year_match = re.search(r'\b(19|20)\d{2}\b', item['journal'])
                item['year'] = year_match.group() if year_match else ''
            
            item['abstract'] = paper.css('.full-view-snippet::text').get()
            item['doi'] = paper.css('.id-link::text').get()
            item['source'] = 'PubMed'
            item['type'] = 'article'
            yield item

    def normalize_text(self, text: str) -> str:
        """Normaliza texto para comparación"""
        if not text:
            return ""
        text = unidecode(text.lower().strip())
        return ' '.join([word for word in re.sub(r'[^\w\s]', '', text).split() if len(word) > 2])

    def is_duplicate(self, new_item: Dict, existing_item: Dict) -> bool:
        """Determina si un ítem es duplicado"""
        title_sim = difflib.SequenceMatcher(
            None, 
            self.normalize_text(new_item['title']), 
            self.normalize_text(existing_item['title'])
        ).ratio()
        
        return (title_sim > self.similarity_threshold and 
                new_item['year'] == existing_item['year'])

class DuplicatesPipeline:
    """Pipeline para manejar duplicados"""
    def __init__(self):
        self.unique_items = []
        self.duplicate_items = []

    def process_item(self, item, spider):
        for existing in self.unique_items:
            if spider.is_duplicate(item, existing):
                self.duplicate_items.append(item)
                return None  # Descarta el duplicado
        
        self.unique_items.append(item)
        return item

    def close_spider(self, spider):
        """Al finalizar el spider, exporta los resultados"""
        with open('unified_results.json', 'w') as f:
            json.dump(self.unique_items, f, indent=2)
        
        with open('duplicate_entries.json', 'w') as f:
            json.dump(self.duplicate_items, f, indent=2)

# Configuración y ejecución
def run_spider(query):
    settings = get_project_settings()
    settings.update({
        'ITEM_PIPELINES': {'__main__.DuplicatesPipeline': 300},
        'FEED_EXPORT_FIELDS': ['title', 'authors', 'year', 'abstract', 'doi', 'source', 'type'],
    })
    
    process = CrawlerProcess(settings)
    process.crawl(BibliometricSpider, query=query)
    process.start()

if __name__ == "__main__":
    run_spider("computational thinking")