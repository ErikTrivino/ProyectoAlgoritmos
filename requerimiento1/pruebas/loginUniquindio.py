import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class GoogleLoginSpider(scrapy.Spider):
    name = 'google_login_full'
    start_urls = ['https://login.intelproxy.com/v2/inicio?cuenta=7Ah6RNpGWF22jjyq&url=ezp.2aHR0cHM6Ly9yZXNlYXJjaC5lYnNjby5jb20vYy9xNDZycGUvc2VhcmNoL3Jlc3VsdHM.bGltaXRlcnM9JnE9Y29tcHV0YXRpb25hbCt0aGlua2luZw--']  # URL de inicio
    
    def __init__(self):
        # Configurar Selenium
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--disable-gpu')  # Para evitar el error de GPU
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Credenciales (cámbialas por las tuyas)
        self.correo = "erikp.trivinog@uqvirtual.edu.co"
        self.password = "Erikpablot18"  # Reemplaza con tu contraseña real
    
    def parse(self, response):
        self.driver.get(response.url)
        
        try:
            # Paso 1: Hacer clic en "Iniciar sesión con Google"
            time.sleep(5)
            google_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Iniciar sesión con Google') or contains(., 'Google')]"))
            )
            google_button.click()
            
            # Paso 2: Ingresar correo electrónico
            self.ingresar_correo()
            
            # Paso 3: Esperar y luego ingresar contraseña
            time.sleep(4)  # Espera adicional solicitada
            self.ingresar_password()
            
        except Exception as e:
            self.logger.error(f"Error en el proceso: {str(e)}")
            self.driver.save_screenshot('error.png')  # Guardar captura en caso de error
    
    def ingresar_correo(self):
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
        try:
            # Esperar a que el campo de contraseña esté disponible
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'][name='Passwd']"))
            )
            
            # Ingresar contraseña
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Presionar Enter para enviar
            password_field.send_keys(Keys.RETURN)
            
            # Opcional: Esperar a que el login se complete
            time.sleep(5)

            # Esperar 10 segundos y redirigir a la nueva página
            time.sleep(10)
            self.driver.get("https://research-ebsco-com.crai.referencistas.com/c/q46rpe/search/results?limiters=&q=computational+thinking")
            
            
        except Exception as e:
            self.logger.error(f"Error al ingresar contraseña: {str(e)}")
            raise
    
    def closed(self, reason):
        # Mantener el navegador abierto para inspección (opcional)
        # Si quieres que se cierre automáticamente, usa:
        # self.driver.quit()
        pass