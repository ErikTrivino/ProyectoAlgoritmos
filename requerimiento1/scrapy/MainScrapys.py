import subprocess
import os
from datetime import datetime

def ejecutar_spiders():
    """Ejecuta todos los spiders de Scrapy"""
    spiders = [
        'bibliotecaCraiScrapy.py',
        'googleAcademyScrapy.py',
        'ieeeXploreScrapy.py'
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

def parsear_ris(contenido: str) -> list:
    """Parsea manualmente el contenido RIS con manejo robusto"""
    registros = []
    registro_actual = {}
    
    for linea in contenido.split('\n'):
        linea = linea.strip()
        if not linea:
            continue
        
        # Fin de registro
        if linea.startswith('ER  -'):
            if registro_actual:
                registros.append(registro_actual)
                registro_actual = {}
            continue
        
        # Líneas de datos (formato: "XX  - valor")
        if len(linea) >= 6 and linea[2:6] == '  - ':
            campo = linea[:2].strip()
            valor = linea[6:].strip()
            
            # Mapeo completo de campos
            if campo == 'TY':
                registro_actual['type'] = valor
            elif campo == 'TI':
                registro_actual['title'] = valor
            elif campo == 'AU':
                registro_actual.setdefault('authors', []).append(valor)
            elif campo == 'PY':
                registro_actual['year'] = valor
            elif campo in ['JF', 'JO', 'T2']:
                registro_actual['journal'] = valor
            elif campo == 'PB':
                registro_actual['publisher'] = valor
            elif campo in ['AB', 'N2']:
                registro_actual['abstract'] = valor
            elif campo == 'UR':
                registro_actual['url'] = valor
            elif campo == 'DO':
                registro_actual['doi'] = valor
            elif campo == 'KW':
                registro_actual.setdefault('keywords', []).append(valor)
            elif campo == 'VL':
                registro_actual['volume'] = valor
            elif campo == 'IS':
                registro_actual['issue'] = valor
            elif campo in ['SP', 'EP']:
                registro_actual['pages'] = valor
            elif campo == 'LA':
                registro_actual['language'] = valor
            elif campo == 'N1':
                registro_actual['notes'] = valor
    
    return registros

def cargar_resultados() -> list:
    """Carga y combina todos los archivos RIS generados"""
    archivos_ris = [
        'C:/Users/erikp/OneDrive/Documentos/GitHub/ProyectoAlgoritmos/requerimiento1/scrapy/resultadosBibliotecaCrai.ris', 
        'C:/Users/erikp/OneDrive/Documentos/GitHub/ProyectoAlgoritmos/requerimiento1/scrapy/resultadosGoogleAcademy.ris',
        'C:/Users/erikp/OneDrive/Documentos/GitHub/ProyectoAlgoritmos/requerimiento1/scrapy/resultadosIeeexplore.ris'
    ]
    resultados = []

    
    """for archivo in archivos_ris:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
                print(f"\n=== DEBUG: Contenido de {archivo} ===")
                print(contenido[:500])  # Muestra las primeras líneas
                
                datos = parsear_ris(contenido)
                print(f"\nRegistros parseados: {len(datos)}")
                if datos:
                    print("Ejemplo de registro:", datos[0])
                
                resultados.extend(datos)
        except Exception as e:
            print(f"Error crítico en {archivo}: {str(e)}")"""
    
    print("\n=== CARGANDO RESULTADOS ===")
    for archivo in archivos_ris:
        if not os.path.exists(archivo):
            print(f" Archivo no encontrado: {archivo}")
            continue
            
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
                datos = parsear_ris(contenido)
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
        'authors': item.get('authors', []),
        'year': str(item.get('year', '')).strip(),
        'source': item.get('journal') or item.get('source', ''),
        'publisher': item.get('publisher', ''),
        'abstract': item.get('abstract') or item.get('summary', '') or item.get('N2', ''),
        'url': item.get('url', ''),
        'doi': item.get('doi', ''),
        'keywords': item.get('keywords', []),
        'volume': item.get('volume', ''),
        'issue': item.get('issue', ''),
        'pages': item.get('pages', ''),
        'language': item.get('language', ''),
        'fuente': item.get('fuente', '')
    }
    
    # Convertir listas a strings
    if isinstance(cleaned['authors'], list):
        cleaned['authors'] = '; '.join(a for a in cleaned['authors'] if a)
    
    if isinstance(cleaned['keywords'], list):
        cleaned['keywords'] = '; '.join(k for k in cleaned['keywords'] if k)
    
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
    if isinstance(authors, str):
        authors = [a.strip() for a in authors.split(';')]
    
    for author in authors:
        ris += f"AU  - {author}\n"
    
    ris += f"PY  - {item['year']}\n"
    
    # Campos opcionales
    if item.get('source'): ris += f"JF  - {item['source']}\n"
    if item.get('publisher'): ris += f"PB  - {item['publisher']}\n"
    if item.get('abstract'): ris += f"AB  - {item['abstract']}\n"
    if item.get('url'): ris += f"UR  - {item['url']}\n"
    if item.get('doi'): ris += f"DO  - {item['doi']}\n"
    
    # Manejo de keywords (puede ser string o lista)
    if item.get('keywords'):
        if isinstance(item['keywords'], str):
            keywords = [k.strip() for k in item['keywords'].split(';')]
        else:
            keywords = item['keywords']
        
        for kw in keywords:
            ris += f"KW  - {kw}\n"
    
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
    #ejecutar_spiders()
    
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