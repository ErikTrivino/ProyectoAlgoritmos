import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Configurar Selenium para evitar detección
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ejecutar en segundo plano
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Inicializar el navegador
driver = webdriver.Chrome(options=chrome_options)

# URL de búsqueda en Google Scholar
query = "computational thinking"
url = f"https://scholar.google.com/scholar?q={query}"

# Acceder a la página
driver.get(url)
time.sleep(3)  # Esperar a que cargue

# Obtener HTML procesado por JavaScript
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Extraer datos de los artículos
articles = []
for article in soup.select(".gs_ri"):
    title = article.select_one(".gs_rt").text
    title = title.replace("[PDF]", "").replace("[HTML]", "").strip()
    
    authors_info = article.select_one(".gs_a").text
    # Separar autores, año y revista
    authors = authors_info.split(" - ")[0]
    year = "".join([c for c in authors_info if c.isdigit()][-4:])  # Extraer año
    
    link = article.select_one(".gs_rt a")["href"] if article.select_one(".gs_rt a") else "N/A"
    
    articles.append({
        "title": title,
        "authors": authors,
        "year": year,
        "link": link
    })

# Cerrar el navegador
driver.quit()

# Guardar en un DataFrame y exportar a CSV
df = pd.DataFrame(articles)
df.to_csv("google_scholar_results.csv", index=False)
print("✅ Datos guardados en 'google_scholar_results.csv'")
print(df.head())  # Mostrar primeras filas