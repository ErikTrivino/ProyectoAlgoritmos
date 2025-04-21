import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from unidecode import unidecode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import re
import time
import random

def clean_text(text):
    return unidecode(text.strip()) if text else ''

class PaperItem(scrapy.Item):
    title = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=Join(' '))
    authors = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    year = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    source = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    publisher = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    abstract = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())

class IEEEXploreSpider(scrapy.Spider):
    name = 'ieee_xplore_full'
    export_format = None
    items = []
    max_horizontal_pages = 2  # Límite de 2 paginaciones horizontales
    current_horizontal_page = 1
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': random.uniform(3, 7),
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 3,
        'HTTPCACHE_ENABLED': False
    }

    def __init__(self, *args, **kwargs):
        super(IEEEXploreSpider, self).__init__(*args, **kwargs)
        
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        while True:
            choice = input("Selecciona formato de exportación (RIS/BibTeX): ").strip().lower()
            if choice in ['ris', 'bibtex']:
                self.export_format = choice
                break
            else:
                print("Formato no válido. Escribe 'RIS' o 'BibTeX'.")

    def start_requests(self):
        url = 'https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=computational%20thinking'
        yield scrapy.Request(url, callback=self.parse_search_results)

    def parse_search_results(self, response):
        print(f"\nProcesando página horizontal {self.current_horizontal_page} de {self.max_horizontal_pages}")
        
        self.driver.get(response.url)
        time.sleep(random.uniform(3, 5))
        
        # Scroll para cargar más resultados
        for _ in range(2):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))
        
        selector = scrapy.Selector(text=self.driver.page_source)
        
        # Extraer todos los artículos para scraping vertical ilimitado
        article_links = selector.xpath('//xpl-results-item/div[1]/div[1]/div[2]/h3/a/@href').getall()
        
        print(f"Encontrados {len(article_links)} artículos para scraping vertical")
        
        for link in article_links:
            article_url = response.urljoin(link)
            yield scrapy.Request(
                article_url, 
                callback=self.parse_article,
                meta={'original_url': article_url}
            )
        
        # Paginación horizontal (máximo 2 páginas)
        if self.current_horizontal_page < self.max_horizontal_pages:
            self.current_horizontal_page += 1
            yield from self.go_to_next_page(response)

    def parse_article(self, response):
        print(f"\nIniciando scraping vertical en: {response.url}")
        
        self.driver.get(response.url)
        time.sleep(random.uniform(4, 6))
        
        # Scroll para asegurar carga completa
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        selector = scrapy.Selector(text=self.driver.page_source)
        
        # 1. Extraer abstract con XPath proporcionado
        abstract = selector.xpath('//*[@id="xplMainContentLandmark"]/div/xpl-document-details/div/div[1]/div/div[2]/section/div[2]/div/xpl-document-abstract/section/div[2]/div[1]/div/div/div//text()').getall()
        abstract_text = ' '.join([text.strip() for text in abstract if text.strip()])
        
        # 2. Extraer metadatos de la página del artículo
        title = selector.xpath('//h1[contains(@class, "document-title")]//text()').getall()
        title_text = ' '.join([t.strip() for t in title if t.strip()])
        
        # Extracción de autores desde el contenedor con clase 'authors-info-container'
        authors = []

        # XPath para encontrar todos los <a> (enlaces a autores) dentro del contenedor correspondiente
        author_elements = selector.xpath(
            '//div[contains(@class, "authors-info-container")]//a[contains(@href, "/author/")]'
        )

        # Recorremos cada enlace que contiene un nombre de autor
        for author in author_elements:
            # Extraemos el texto del enlace (nombre del autor)
            author_name = author.xpath('.//text()').get()
            if author_name and author_name.strip():
                authors.append(author_name.strip())

        # Unimos todos los nombres de autores encontrados separados por comas
        all_authors = ', '.join(authors) if authors else ''

        # Agregamos los autores al item loader
        #loader.add_value('authors', all_authors)


        # Extraemos el texto desde el XPath completo proporcionado
        year_text = selector.xpath(
            '/html/body/div[5]/div/div/div[4]/div/xpl-root/main/div/xpl-document-details/div/div[1]/div/div[2]/section/div[2]/div/xpl-document-abstract/section/div[2]/div[3]/div[1]/div[1]/text()'
        ).get()

        # Extraemos el año (formato 19xx o 20xx) con regex
        year_match = re.search(r'\b(19|20)\d{2}\b', year_text or '')

        

        
        source = selector.xpath('//div[contains(@class, "doc-abstract-conference")]//text()').get()
        
        # 4. Crear ítem con todos los datos
        loader = ItemLoader(PaperItem())
        loader.add_value('title', title_text)
        #loader.add_value('authors', authors_text)
        loader.add_value('authors', all_authors)
        #loader.add_value('year', year_match.group() if year_match else '')
        # Si encontramos un año válido, lo agregamos al item loader
        if year_match:
            loader.add_value('year', year_match.group())
        loader.add_value('source', source.strip() if source else '')
        loader.add_value('publisher', 'IEEE')
        loader.add_value('abstract', abstract_text)
        loader.add_value('url', response.meta['original_url'])
        
        item = loader.load_item()
        self.items.append(item)
        yield item

    def go_to_next_page(self, response):
        try:
            print("\nNavegando a página horizontal siguiente...")
            
            next_button = self.driver.find_element(
                By.XPATH, 
                '//*[@id="xplMainContent"]/div[2]/div[2]/xpl-paginator/div[2]/ul/li[12]/button'
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
            time.sleep(random.uniform(1, 2))
            
            ActionChains(self.driver).move_to_element(next_button).pause(0.5).click().perform()
            time.sleep(random.uniform(4, 6))
            
            yield from self.parse_search_results(response)
                
        except Exception as e:
            print(f"Error en paginación horizontal: {str(e)}")
            yield from self.alternative_pagination(response)

    def alternative_pagination(self, response):
        selector = scrapy.Selector(text=self.driver.page_source)
        next_page = selector.xpath('//a[@aria-label="Next Page"]/@href').get()
        
        if next_page:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(next_page_url, callback=self.parse_search_results)

    def closed(self, reason):
        self.driver.quit()
        filename = f"resultados_completos.{self.export_format}"
        with open(filename, "w", encoding="utf-8") as f:
            for item in self.items:
                if self.export_format == 'ris':
                    f.write(self.to_ris(item))
                elif self.export_format == 'bibtex':
                    f.write(self.to_bibtex(item))
        print(f"\nExportación completada: {filename}")
        print(f"Total de artículos procesados: {len(self.items)}")

    def to_ris(self, item):
        return (
            "TY  - JOUR\n"
            f"TI  - {item.get('title', '')}\n"
            f"AU  - {item.get('authors', '')}\n"
            f"PY  - {item.get('year', '')}\n"
            f"JF  - {item.get('source', '')}\n"
            f"PB  - {item.get('publisher', '')}\n"
            f"AB  - {item.get('abstract', '')}\n"
            f"UR  - {item.get('url', '')}\n"
            "ER  -\n\n"
        )

    def to_bibtex(self, item):
        return (
            "@article{{\n"
            f"  title = {{{item.get('title', '')}}},\n"
            f"  author = {{{item.get('authors', '')}}},\n"
            f"  year = {{{item.get('year', '')}}},\n"
            f"  journal = {{{item.get('source', '')}}},\n"
            f"  publisher = {{{item.get('publisher', '')}}},\n"
            f"  abstract = {{{item.get('abstract', '')}}},\n"
            f"  url = {{{item.get('url', '')}}}\n"
            "}\n\n"
        )