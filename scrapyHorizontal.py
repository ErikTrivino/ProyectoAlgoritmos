import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from unidecode import unidecode
import re

def clean_text(text):
    """Limpia el texto eliminando espacios y normalizando caracteres"""
    return unidecode(text.strip()) if text else ''

def extract_publisher(metadata_text):
    """Extrae el publisher del texto de metadatos"""
    # Patrón para: Autor - Publisher, Año - Fuente
    match = re.search(r'^.?-\s(.?),\s(19|20)\d{2}\s*-', metadata_text)
    if match:
        return match.group(1).strip()
    
    # Patrón alternativo para: Autor - Año - Publisher
    match = re.search(r'^.?-\s(19|20)\d{2}\s*-\s*(.?)(?:\s-|$)', metadata_text)
    if match:
        return match.group(2).strip()
    
    return None

class PaperItem(scrapy.Item):
    title = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(' ')
    )
    authors = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    year = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    source = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    publisher = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    summary = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(' ')
    )
    citations = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    abstract = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    versions = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )

class BibliometricSpider(scrapy.Spider):
    name = 'bibliometric'
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 5,
        'ROBOTSTXT_OBEY': False,
        'HTTPCACHE_ENABLED': True,
        'CONCURRENT_REQUESTS': 1  # Reducir concurrencia para evitar bloqueos
    }

    def start_requests(self):
        url = 'https://scholar.google.es/scholar?hl=es&as_sdt=0%2C5&q=computational+thinking'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Extraer artículos de la página actual
        for paper in response.xpath('//div[contains(@class, "gs_ri")]'):
            loader = ItemLoader(PaperItem(), selector=paper)
            
            # Título
            title_parts = paper.xpath('.//h3[contains(@class, "gs_rt")]//text()').getall()
            loader.add_value('title', ' '.join([t.strip() for t in title_parts if t.strip()]))
            
            # Metadatos (autores, año, fuente, publisher)
            metadata_text = ' '.join(paper.xpath('.//div[contains(@class, "gs_a")]//text()').getall()).strip()
            
            if metadata_text:
                # Autores (todo antes del primer guión)
                authors = metadata_text.split(' - ')[0].strip()
                loader.add_value('authors', authors)
                
                # Año
                year_match = re.search(r'\b(19|20)\d{2}\b', metadata_text)
                if year_match:
                    loader.add_value('year', year_match.group())
                
                # Publisher
                publisher = extract_publisher(metadata_text)
                if publisher:
                    loader.add_value('publisher', publisher)
                
                # Fuente (todo después del último guión)
                source = metadata_text.split(' - ')[-1].strip()
                loader.add_value('source', source)
            
            # Resumen
            summary = paper.xpath('.//div[contains(@class, "gs_rs")]//text()').getall()
            clean_summary = ' '.join([text.strip() for text in summary if text.strip()])
            clean_summary = ' '.join(clean_summary.split())  # Eliminar espacios múltiples
            loader.add_value('summary', clean_summary)
            
            # Citaciones (ej: "Citado por 351")
            citations = paper.xpath('.//div[contains(text(), "Citado por")]/text()').re_first(r'(\d+)')
            loader.add_value('citations', citations)
            
            # Versiones (ej: "Las 3 versiones")
            versions = paper.xpath('.//a[contains(text(), "versiones") or contains(text(), "versión")]/text()').re_first(r'(\d+)')
            loader.add_value('versions', versions)
            
            yield loader.load_item()
        
        # Navegación horizontal (paginación)
        next_page = response.xpath('//td[@align="left"]/a/@href').get()
        if next_page:
            next_url = response.urljoin(next_page)
            yield scrapy.Request(next_url, callback=self.parse)
        else:
            # Alternativa para botón "Siguiente"
            next_button = response.xpath('//button[contains(@aria-label, "Siguiente")]/@onclick').get()
            if next_button:
                # Extraer URL del JavaScript
                next_url = re.search(r"window\.location='([^']+)'", next_button)
                if next_url:
                    yield scrapy.Request(response.urljoin(next_url.group(1)), callback=self.parse)