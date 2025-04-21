import scrapy
import time
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from unidecode import unidecode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def clean_text(text):
    """Clean text by removing whitespace and normalizing characters"""
    return unidecode(text.strip()) if text else ''


class PaperItem(scrapy.Item):
    """Scrapy Item class for storing paper metadata"""
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
    url = scrapy.Field(
        output_processor=TakeFirst()
    )


class GoogleLoginBibliometricSpider(scrapy.Spider):
    name = 'google_login_bibliometric_vertical'
    start_urls = ['https://login.intelproxy.com/v2/inicio?cuenta=7Ah6RNpGWF22jjyq&url=ezp.2aHR0cHM6Ly9yZXNlYXJjaC5lYnNjby5jb20vYy9xNDZycGUvc2VhcmNoL3Jlc3VsdHM.bGltaXRlcnM9JnE9Y29tcHV0YXRpb25hbCt0aGlua2luZw--']
    export_format = None
    items = []
    max_articles = 5  # Límite de artículos a scrapear
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 5,
        'ROBOTSTXT_OBEY': False,
        'HTTPCACHE_ENABLED': True,
        'CONCURRENT_REQUESTS': 1
    }

    def __init__(self, *args, **kwargs):
        super(GoogleLoginBibliometricSpider, self).__init__(*args, **kwargs)
        
        # Configure Selenium
        chrome_options = webdriver.ChromeOptions()
        #chrome_options.add_argument('--headless=new')  # Ejecuta sin ventana, NO SIRVE
        #chrome_options.add_argument('--disable-gpu') solo estaba esto 
        # 🕵️‍♂️ Evasión de detección
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 📺 Invisibilidad sin headless (mueve la ventana fuera de la pantalla)
        chrome_options.add_argument('--window-position=-10000,0')  # Fuera del área visible
        chrome_options.add_argument('--start-maximized')           # Maximiza (aunque no se vea)
        chrome_options.add_argument('--disable-gpu')               # Evita errores gráficos
        self.driver = webdriver.Chrome(options=chrome_options)
        # Ejecuta este script JS para ocultar `navigator.webdriver`
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
        # Credentials
        self.correo = "erikp.trivinog@uqvirtual.edu.co"
        self.password = "Erikpablot18"
        
        # Ask for export format
        while True:
            #choice = input("Selecciona formato de exportación (RIS/BibTeX): ").strip().lower()
            choice = 'ris'
            if choice in ['ris', 'bibtex']:
                self.export_format = choice
                break
            print("Formato no válido. Escribe 'RIS' o 'BibTeX'.")

    def parse(self, response):
        """Handle the login process with Selenium"""
        self.driver.get(response.url)
        
        try:
            # Step 1: Click on "Login with Google"
            time.sleep(5)
            google_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Iniciar sesión con Google') or contains(., 'Google')]"))
            )
            google_button.click()
            
            # Step 2: Enter email
            self.ingresar_correo()
            
            # Step 3: Enter password
            time.sleep(4)
            self.ingresar_password()
            
            # Step 4: Redirect to search page and wait
            time.sleep(10)
            search_url = "https://research-ebsco-com.crai.referencistas.com/c/q46rpe/search/results?limiters=&q=computational+thinking"
            self.driver.get(search_url)
            
            # Wait for results to load
            time.sleep(8)
            
            # Get article links (up to max_articles)
            article_links = self.get_article_links()
            
            # Visit each article page
            for i, link in enumerate(article_links[:self.max_articles]):
                self.driver.get(link)
                time.sleep(5)  # Wait for article page to load
                
                # Parse the article page
                body = self.driver.page_source
                selector = scrapy.Selector(text=body)
                yield from self.parse_article_page(selector, link)
                
        except Exception as e:
            self.logger.error(f"Error en el proceso: {str(e)}")
            self.driver.save_screenshot('error.png')
            raise

    def get_article_links(self):
        """Extract links to individual articles from search results"""
        links = []
        try:
            # Find all article links in search results
            articles = WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/details/')]"))
            )
            
            # Get href attributes
            links = [article.get_attribute('href') for article in articles if article.get_attribute('href')]
            
            # Make sure links are complete (sometimes they're relative)
            base_url = "https://research-ebsco-com.crai.referencistas.com"
            links = [link if link.startswith('http') else base_url + link for link in links]
            
        except Exception as e:
            self.logger.error(f"Error al obtener enlaces: {str(e)}")
        
        return links

    def parse_article_page(self, selector, url):
        """Parse an individual article page"""
        loader = ItemLoader(PaperItem(), selector=selector)
        loader.add_value('url', url)

        # Extract title
        title = selector.xpath('//h1[contains(@class, "title")]/text()').get()
        loader.add_value('title', title.strip() if title else '')

        # Autores - Extrae todos los textos dentro de los li
        authors = selector.xpath(
            '//*[@id="details-page"]/div[2]/div/div/div/div/section/div/div/div/div/div/div[2]/article/ul[2]/li//text()'
        ).getall()
        loader.add_value('authors', [clean_text(a) for a in authors if clean_text(a)])
        # Source
        source = selector.xpath(
            '//*[@id="details-page"]/div[2]/div/div/div/div/section/div/div/div/div/div/div[2]/article/ul[3]/li/i/text()'
        ).get()
        loader.add_value('source', clean_text(source))

        # Publisher
        publisher = selector.xpath(
            '//*[@id="details-page"]/div[2]/div/div/div/div/section/div/div/div/div/div/div[2]/article/ul[4]/li//text()'
        ).get()
        loader.add_value('publisher', clean_text(publisher))

        # Year
        year = selector.xpath(
            '//*[@id="details-page"]/div[2]/div/div/div/div/section/div/div/div/div/div/div[2]/article/ul[5]/li//text()'
        ).re_first(r'\d{4}')
        loader.add_value('year', clean_text(year))

        # Abstract
        abstract = selector.xpath(
            '//*[@id="details-page"]/div[2]/div/div/div/div/section/div/div/div/div/div/div[2]/article/ul[7]/li//text()'
        ).getall()
        loader.add_value('abstract', [clean_text(a) for a in abstract])

        loader.add_value('summary', [clean_text(a) for a in abstract])

        # Citations
        citations = selector.xpath(
            '//*[@id="details-page"]/div[2]/div/div/div/div/section/div/div/div/div/div/div[2]/article/ul[10]/li//text()'
        ).getall()
        loader.add_value('citations', ' '.join([clean_text(c) for c in citations]))

        item = loader.load_item()
        self.items.append(item)
        yield item

    def ingresar_correo(self):
        """Enter email in Google login form"""
        try:
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'][name='identifier']"))
            )
            email_field.clear()
            email_field.send_keys(self.correo)
            email_field.send_keys(Keys.RETURN)
            
        except Exception as e:
            self.logger.error(f"Error al ingresar correo: {str(e)}")
            raise

    def ingresar_password(self):
        """Enter password in Google login form"""
        try:
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'][name='Passwd']"))
            )
            password_field.clear()
            password_field.send_keys(self.password)
            password_field.send_keys(Keys.RETURN)
            time.sleep(5)
            
        except Exception as e:
            self.logger.error(f"Error al ingresar contraseña: {str(e)}")
            raise

    def closed(self, reason):
        """Export collected items when spider closes"""
        if not self.items:
            print("No items were collected.")
            return

        filename = f"resultadosBibliotecaCrai.{self.export_format}"
        with open(filename, "w", encoding="utf-8") as f:
            for item in self.items:
                if self.export_format == 'ris':
                    f.write(self.to_ris(item))
                elif self.export_format == 'bibtex':
                    f.write(self.to_bibtex(item))
        
        print(f"\nExportación completada: {filename}")
        self.driver.quit()

    def to_ris(self, item):
        """Convert item to RIS format"""
        ris = (
            "TY  - JOUR\n"
            f"TI  - {item.get('title', '')}\n"
            f"AU  - {item.get('authors', '')}\n"
            f"PY  - {item.get('year', '')}\n"
            f"JF  - {item.get('source', '')}\n"
            f"PB  - {item.get('publisher', '')}\n"
            f"N2  - {item.get('summary', '')}\n"
            f"AB  - {item.get('abstract', '')}\n"
            f"UR  - {item.get('url', '')}\n"
            "ER  -\n\n"
        )
        return ris

    def to_bibtex(self, item):
        """Convert item to BibTeX format"""
        bib = (
            "@article{{\n"
            f"  title={{ {item.get('title', '')} }},\n"
            f"  author={{ {item.get('authors', '')} }},\n"
            f"  year={{ {item.get('year', '')} }},\n"
            f"  journal={{ {item.get('source', '')} }},\n"
            f"  publisher={{ {item.get('publisher', '')} }},\n"
            f"  abstract={{ {item.get('abstract', '')} }},\n"
            f"  url={{ {item.get('url', '')} }}\n"
            "}}\n\n"
        )
        return bib