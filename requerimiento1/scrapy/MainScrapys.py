import subprocess
import os
from datetime import datetime
from rispy import load  # Para leer archivos RIS existentes

def ejecutar_spiders():
    """Ejecuta todos los spiders de Scrapy"""
    spiders = [
        'bibliotecaCraiScrapy.py',
        'googleAcademyScrapy.py',
        'iiExploreScrapy.py'
    ]
    
    print("\n=== EJECUTANDO SPIDERS ===")
    for spider in spiders:
        print(f"\nEjecutando {spider}...")
        try:
            subprocess.run(['python', '-m', 'scrapy', 'runspider', spider], check=True)
            print(f" {spider} completado con éxito")
        except subprocess.CalledProcessError as e:
            print(f" Error en {spider}: {e}")
    print("\n Todos los spiders completados")

def cargar_resultados() -> list:
    """Carga y combina todos los archivos RIS generados"""
    archivos_ris = [
        'resultadosBibliotecaCrai.ris',
        'resultadosGoogleAcademy.ris',
        'resultadosleeexplore.ris'
    ]
    
    resultados = []
    
    print("\n=== CARGANDO RESULTADOS ===")
    for archivo in archivos_ris:
        if not os.path.exists(archivo):
            print(f" Archivo no encontrado: {archivo}")
            continue
            
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos = load(f)
                for item in datos:
                    # Añadir metadata de origen
                    item['fuente'] = os.path.splitext(archivo)[0]
                resultados.extend(datos)
                print(f" {archivo}: {len(datos)} registros cargados")
        except Exception as e:
            print(f" Error al leer {archivo}: {str(e)[:100]}...")
    
    return resultados

def limpiar_datos(item: dict) -> dict:
    """Normaliza y limpia los datos del registro"""
    cleaned = {
        'title': item.get('title', '').strip(),
        'authors': item.get('authors', ''),
        'year': str(item.get('year', '')).strip(),
        'source': item.get('journal') or item.get('source', ''),
        'publisher': item.get('publisher', ''),
        'abstract': item.get('abstract') or item.get('summary', ''),
        'url': item.get('url', ''),
        'doi': item.get('doi', ''),
        'keywords': item.get('keywords', ''),
        'volume': item.get('volume', ''),
        'issue': item.get('issue', ''),
        'pages': item.get('pages', ''),
        'language': item.get('language', ''),
        'fuente': item.get('fuente', '')
    }
    
    # Limpieza adicional de autores
    if isinstance(cleaned['authors'], list):
        cleaned['authors'] = '; '.join(cleaned['authors'])
    
    return cleaned

def identificar_duplicados(resultados: list) -> tuple:
    """Identifica registros duplicados basados en título, autores y año"""
    registros_unicos = []
    registros_duplicados = []
    claves_vistas = set()
    
    for registro in resultados:
        registro_limpio = limpiar_datos(registro)
        
        # Crear clave única normalizada
        clave = (
            registro_limpio['title'].lower(),
            registro_limpio['authors'].lower(),
            registro_limpio['year']
        )
        
        if clave not in claves_vistas:
            claves_vistas.add(clave)
            registros_unicos.append(registro_limpio)
        else:
            registros_duplicados.append(registro_limpio)
    
    return registros_unicos, registros_duplicados

def generar_registro_ris(item: dict) -> str:
    """Genera un registro RIS completo con todos los campos disponibles"""
    ris = "TY  - JOUR\n"
    ris += f"TI  - {item['title']}\n"
    
    # Manejo de autores (puede ser string o lista)
    authors = item['authors']
    if isinstance(authors, list):
        authors = '; '.join(authors)
    ris += f"AU  - {authors}\n"
    
    ris += f"PY  - {item['year']}\n"
    
    # Campos opcionales
    if item.get('source'): ris += f"JF  - {item['source']}\n"
    if item.get('publisher'): ris += f"PB  - {item['publisher']}\n"
    if item.get('abstract'): ris += f"AB  - {item['abstract']}\n"
    if item.get('url'): ris += f"UR  - {item['url']}\n"
    if item.get('doi'): ris += f"DO  - {item['doi']}\n"
    if item.get('keywords'): ris += f"KW  - {item['keywords']}\n"
    if item.get('volume'): ris += f"VL  - {item['volume']}\n"
    if item.get('issue'): ris += f"IS  - {item['issue']}\n"
    if item.get('pages'): ris += f"SP  - {item['pages']}\n"
    if item.get('language'): ris += f"LA  - {item['language']}\n"
    if item.get('fuente'): ris += f"N1  - Fuente: {item['fuente']}\n"
    
    ris += "ER  -\n\n"
    return ris

def guardar_resultados(registros: list, prefijo: str):
    """Guarda los registros en archivos RIS"""
    if not registros:
        print(f" No hay registros para guardar en {prefijo}")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"{prefijo}_{timestamp}.ris"
    
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        for registro in registros:
            f.write(generar_registro_ris(registro))
    
    print(f" Archivo guardado: {nombre_archivo} ({len(registros)} registros)")

def main():
    print(" INICIO DEL PROCESO DE RECOLECCIÓN Y UNIFICACIÓN ")
    
    # Paso 1: Ejecutar todos los spiders
    ejecutar_spiders()
    
    # Paso 2: Cargar y combinar resultados
    resultados = cargar_resultados()
    if not resultados:
        print(" No se encontraron resultados para procesar")
        return
    
    # Paso 3: Identificar duplicados
    unicos, duplicados = identificar_duplicados(resultados)
    print(f"\n Resumen final:")
    print(f"- Registros únicos: {len(unicos)}")
    print(f"- Registros duplicados: {len(duplicados)}")
    
    # Paso 4: Guardar resultados
    guardar_resultados(unicos, 'resultados_unificados')
    guardar_resultados(duplicados, 'registros_duplicados')
    
    print("\n PROCESO COMPLETADO CON ÉXITO ")

if __name__ == '__main__':
    main()