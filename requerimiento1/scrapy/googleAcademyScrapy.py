import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from unidecode import unidecode
import re
import os


def clean_text(text):
    """Limpia el texto eliminando espacios y normalizando caracteres"""
    return unidecode(text.strip()) if text else ''

def extract_publisher(metadata_text):
    """Extrae el publisher del texto de metadatos"""
    match = re.search(r'^.*?-\s*(.*?),\s*(19|20)\d{2}\s*-', metadata_text)
    if match:
        return match.group(1).strip()
    
    match = re.search(r'^.*?-\s*(19|20)\d{2}\s*-\s*(.*?)(?:\s*-|$)', metadata_text)
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
    export_format = None
    items = []
    page_count = 0                # Contador de páginas procesadas
    max_pages = 5 

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 5,
        'ROBOTSTXT_OBEY': False,
        'HTTPCACHE_ENABLED': True,
        'CONCURRENT_REQUESTS': 1
    }

    def __init__(self, *args, **kwargs):
        super(BibliometricSpider, self).__init__(*args, **kwargs)
        while True:
            #choice = input("Selecciona formato de exportación (RIS/BibTeX): ").strip().lower()
            choice = 'ris'
            if choice in ['ris', 'bibtex']:
                self.export_format = choice
                break
            else:
                print("Formato no válido. Escribe 'RIS' o 'BibTeX'.")

    def start_requests(self):
        url = 'https://scholar.google.es/scholar?hl=es&as_sdt=0%2C5&q=computational+thinking'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        self.page_count += 1
        print(f"\n📝 Procesando página {self.page_count}: {response.url}")

        if self.page_count > self.max_pages:
            print(f"🚫 Límite de {self.max_pages} páginas alcanzado.")
            return
        for paper in response.xpath('//div[contains(@class, "gs_ri")]'):
            loader = ItemLoader(PaperItem(), selector=paper)

            title_parts = paper.xpath('.//h3[contains(@class, "gs_rt")]//text()').getall()
            loader.add_value('title', ' '.join([t.strip() for t in title_parts if t.strip()]))

            metadata_text = ' '.join(paper.xpath('.//div[contains(@class, "gs_a")]//text()').getall()).strip()
            if metadata_text:
                """authors_match = re.match(r'^([^,-]+)', metadata_text)
                if authors_match:
                    loader.add_value('authors', authors_match.group(1).strip())"""
                
                # Extraer la parte de autores antes del primer guion " - "
                author_block_match = re.match(r'^(.*?)\s+-', metadata_text)
                author_block = author_block_match.group(1).strip() if author_block_match else metadata_text.strip()

                # Dividir por comas y limpiar
                authors_list = [a.strip() for a in author_block.split(',') if a.strip()]

                # Tomar los primeros dos autores
                first_two_authors = ', '.join(authors_list[:2])

                loader.add_value('authors', first_two_authors)

                #loader.add_value('authors', authors)

                year_match = re.search(r'\b(19|20)\d{2}\b', metadata_text)
                if year_match:
                    loader.add_value('year', year_match.group())

                publisher = extract_publisher(metadata_text)
                if publisher:
                    loader.add_value('publisher', publisher)

                source = metadata_text.split(' - ')[-1].strip()
                loader.add_value('source', source)

            summary = paper.xpath('.//div[contains(@class, "gs_rs")]//text()').getall()
            clean_summary = ' '.join([text.strip() for text in summary if text.strip()])
            clean_summary = ' '.join(clean_summary.split())
            loader.add_value('summary', clean_summary)

            citations = paper.xpath('.//div[contains(text(), "Citado por")]/text()').re_first(r'(\d+)')
            loader.add_value('citations', citations)

            versions = paper.xpath('.//a[contains(text(), "versiones") or contains(text(), "versión")]/text()').re_first(r'(\d+)')
            loader.add_value('versions', versions)

            item = loader.load_item()
            self.items.append(item)
            yield item

        next_page = response.xpath('//td[@align="left"]/a/@href').get()
        if next_page:
            next_url = response.urljoin(next_page)
            yield scrapy.Request(next_url, callback=self.parse)
        else:
            next_button = response.xpath('//button[contains(@aria-label, "Siguiente")]/@onclick').get()
            if next_button:
                next_url = re.search(r"window\.location='([^']+)'", next_button)
                if next_url:
                    yield scrapy.Request(response.urljoin(next_url.group(1)), callback=self.parse)

    def closed(self, reason):
        """Export collected items when spider closes"""
        if not self.items:
            print("No items were collected.")
            return

        # Ruta completa donde quieres guardar el resultado:
        output_dir = r"C:/Users/erikp/Escritorio/ProyectoAlgoritmos/requerimiento1/scrapy"
        filename = os.path.join(output_dir, f"resultadosGoogleAcademy.{self.export_format}")

        # Asegúrate de que el directorio exista:
        os.makedirs(output_dir, exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            for item in self.items:
                if self.export_format == 'ris':
                    f.write(self.to_ris(item))
                elif self.export_format == 'bibtex':
                    f.write(self.to_bibtex(item))

        print(f"\nExportación completada: {filename}")

    def to_ris(self, item):
        ris = (
            "TY  - JOUR\n"
            f"TI  - {item.get('title', '')}\n"
            f"AU  - {item.get('authors', '')}\n"
            f"PY  - {item.get('year', '')}\n"
            f"JF  - {item.get('source', '')}\n"
            f"PB  - {item.get('publisher', '')}\n"
            f"N2  - {item.get('summary', '')}\n"
            f"AB  - {item.get('abstract', '')}\n"
            f"ER  -\n\n"
        )
        return ris

    def to_bibtex(self, item):
        bib = (
            "@article{{\n"
            f"  title={{ {item.get('title', '')} }},\n"
            f"  author={{ {item.get('authors', '')} }},\n"
            f"  year={{ {item.get('year', '')} }},\n"
            f"  journal={{ {item.get('source', '')} }},\n"
            f"  publisher={{ {item.get('publisher', '')} }},\n"
            f"  summary={{ {item.get('summary', '')} }},\n"
            f"  abstract={{ {item.get('abstract', '')} }}\n"
            "}\n\n"
        )
        return bib