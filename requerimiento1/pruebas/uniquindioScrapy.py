import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from unidecode import unidecode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def clean_text(text):
    return unidecode(text.strip()) if text else ''

class PaperItem(scrapy.Item):
    title = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=Join(' '))
    authors = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    year = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    source = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    publisher = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    summary = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=Join(' '))
    citations = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    abstract = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    versions = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())

class BibliometricSpider(scrapy.Spider):
    name = 'bibliometric'
    start_urls = ['https://research-ebsco-com.crai.referencistas.com/c/q46rpe/search/results?q=computational%20thinking']

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 3,
        'ROBOTSTXT_OBEY': False,
        'HTTPCACHE_ENABLED': True,
        'CONCURRENT_REQUESTS': 1,
        'COOKIES_DEBUG': True
    }

    def __init__(self, *args, **kwargs):
        super(BibliometricSpider, self).__init__(*args, **kwargs)
        
        # Configuración de credenciales (REEMPLAZA CON TUS DATOS REALES)
        self.credentials = {
            'google_email': 'erikp.trivinog@uqvirtual.edu.co',
            'google_password': 'Erikpablot18'
        }
        
        # Selección de formato de exportación
        while True:
            choice = input("Selecciona formato de exportación (RIS/BibTeX): ").strip().lower()
            if choice in ['ris', 'bibtex']:
                self.export_format = choice
                break
            print("Formato no válido. Escribe 'RIS' o 'BibTeX'.")

        # Configuración de Selenium (modo visible para debug inicial)
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Descomentar cuando funcione
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.items = []

    def start_requests(self):
        if self.login():
            for url in self.start_urls:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_with_selenium
                )
        else:
            self.logger.error("No se pudo completar el login - revisar login_error.png")

    def login(self):
        """Maneja el proceso completo de autenticación"""
        try:
            # Paso 1: Cargar página de login del proxy
            login_url = "https://login.intelproxy.com/v2/inicio?cuenta=7Ah6RNpGWF22jjyq"
            self.driver.get(login_url)
            
            # Esperar a que la página cargue completamente
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Universidad del Quindío")]'))
            )
            
            # Paso 2: Esperar y hacer clic en el botón de Google
            # Primero esperamos a que el botón esté presente
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "btn-google"))
            )
            
            # Luego esperamos a que esté habilitado (sin atributo disabled)
            WebDriverWait(self.driver, 60).until(
                lambda driver: driver.find_element(By.ID, "btn-google").get_attribute("disabled") is None
            )
            
            # Hacer clic en el botón
            self.driver.find_element(By.ID, "btn-google").click()
            
            # Paso 3: Manejar la ventana de login de Google
            time.sleep(2)  # Esperar a que se abra la nueva pestaña
            
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[1])
                
                # Esperar y completar email
                email_field = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.ID, "identifierId"))
                )
                email_field.send_keys(self.credentials['google_email'])
                email_field.send_keys(Keys.RETURN)
                
                # Esperar y completar contraseña (con mayor tolerancia)
                try:
                    password_field = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.NAME, "Passwd"))
                    )
                    password_field.send_keys(self.credentials['google_password'])
                    password_field.send_keys(Keys.RETURN)
                except TimeoutException:
                    # Intentar alternativa si no encuentra el campo de contraseña
                    self.driver.save_screenshot("password_error.png")
                    raise Exception("No se encontró el campo de contraseña")
                
                # Volver a la ventana principal
                self.driver.switch_to.window(self.driver.window_handles[0])
                
                # Esperar redirección a EBSCO (con mayor tiempo de espera)
                WebDriverWait(self.driver, 40).until(
                    lambda driver: "ebsco" in driver.current_url.lower()
                )
                return True
            else:
                raise Exception("No se abrió la ventana de login de Google")
                
        except Exception as e:
            self.logger.error(f"Error en login: {str(e)}")
            self.driver.save_screenshot("login_error.png")
            return False

    def parse_with_selenium(self, response):
        """Procesa los resultados de búsqueda con Selenium"""
        try:
            # Verificar sesión activa
            if "login" in self.driver.current_url.lower():
                self.logger.info("Sesión expirada, reintentando login...")
                if not self.login():
                    self.logger.error("No se pudo reautenticar")
                    return
            
            # Navegar a la URL de búsqueda si no estamos ya allí
            if "ebsco" not in self.driver.current_url.lower():
                self.driver.get(response.url)
                time.sleep(3)
            
            while True:
                self.logger.info("Procesando página de resultados...")
                
                # Obtener HTML procesado por Selenium
                html = self.driver.page_source
                selector = scrapy.Selector(text=html)
                
                # Extraer datos de cada paper
                papers = selector.xpath('//div[contains(@class, "record-metadata_record-metadata")]')
                if not papers:
                    self.logger.warning("No se encontraron papers en la página")
                    break
                
                for paper in papers:
                    loader = ItemLoader(PaperItem(), selector=paper)
                    
                    # Extraer título
                    title = paper.xpath('.//div[contains(text(), "Título")]/following-sibling::div[1]/text()').get()
                    loader.add_value('title', title)
                    
                    # Extraer autores
                    authors = paper.xpath('.//div[contains(text(), "Autores")]/following-sibling::div[1]/text()').get()
                    loader.add_value('authors', authors)
                    
                    # Extraer fuente
                    source = paper.xpath('.//div[contains(text(), "Fuente")]/following-sibling::div[1]/text()').get()
                    loader.add_value('source', source)
                    
                    # Extraer publisher y año
                    publisher = selector.xpath('//span[contains(@class, "delimited-list__item")][1]/text()').get()
                    year = selector.xpath('//span[contains(@class, "delimited-list__item")][2]/text()').re_first(r'\d{4}')
                    loader.add_value('publisher', publisher)
                    loader.add_value('year', year)
                    
                    # Extraer abstract
                    abstract = paper.xpath('.//div[contains(text(), "Resumen")]/following-sibling::div[1]//text()').getall()
                    clean_abstract = ' '.join([s.strip() for s in abstract if s.strip()])
                    loader.add_value('abstract', clean_abstract)
                    loader.add_value('summary', clean_abstract)
                    
                    item = loader.load_item()
                    self.items.append(item)
                    yield item
                
                # Paginación - intentar cargar más resultados
                try:
                    show_more = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@data-auto="show-more-button"]'))
                    )
                    show_more.click()
                    time.sleep(3)  # Esperar a que carguen nuevos resultados
                except Exception as e:
                    self.logger.info("No hay más resultados disponibles")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error durante el scraping: {str(e)}")
            self.driver.save_screenshot("scraping_error.png")

    def closed(self, reason):
        """Método ejecutado al finalizar el spider"""
        # Cerrar el navegador
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
        
        # Exportar resultados
        if hasattr(self, 'items') and self.items:
            filename = f"resultados.{self.export_format}"
            with open(filename, "w", encoding="utf-8") as f:
                for item in self.items:
                    if self.export_format == 'ris':
                        f.write(self.to_ris(item))
                    else:
                        f.write(self.to_bibtex(item))
            self.logger.info(f"\nExportación completada: {filename}")

    def to_ris(self, item):
        """Formatea un item en formato RIS"""
        return (
            "TY  - JOUR\n"
            f"TI  - {item.get('title', '')}\n"
            f"AU  - {item.get('authors', '')}\n"
            f"PY  - {item.get('year', '')}\n"
            f"JF  - {item.get('source', '')}\n"
            f"PB  - {item.get('publisher', '')}\n"
            f"N2  - {item.get('summary', '')}\n"
            f"AB  - {item.get('abstract', '')}\n"
            "ER  -\n\n"
        )

    def to_bibtex(self, item):
        """Formatea un item en formato BibTeX"""
        return (
            "@article{{\n"
            f"  title={{ {item.get('title', '')} }},\n"
            f"  author={{ {item.get('authors', '')} }},\n"
            f"  year={{ {item.get('year', '')} }},\n"
            f"  journal={{ {item.get('source', '')} }},\n"
            f"  publisher={{ {item.get('publisher', '')} }},\n"
            f"  abstract={{ {item.get('abstract', '')} }}\n"
            "}}\n\n"
        )