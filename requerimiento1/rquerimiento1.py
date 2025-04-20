import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
from datetime import datetime
import time
from unidecode import unidecode
import difflib
import re
from typing import List, Dict, Union

class DatabaseScraper:
    """Clase para manejar el scraping de diferentes bases de datos"""
    #NO SIRVE
    @staticmethod
    def scrape_pubmed(query: str) -> List[Dict[str, Union[str, List[str]]]]:
        """Scraping de PubMed"""
        print(f"Scrapeando PubMed para: {query}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        url = f"https://pubmed.ncbi.nlm.nih.gov/?term={query}"
        
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            for item in soup.select('.article-overview'):
                title_elem = item.select_one('.docsum-title')
                title = title_elem.text.strip() if title_elem else ''
                
                authors_elem = item.select_one('.docsum-authors')
                authors = authors_elem.text.strip() if authors_elem else ''
                
                journal_elem = item.select_one('.docsum-journal-citation')
                journal_info = journal_elem.text.strip() if journal_elem else ''
                
                # Extraer año de la información del journal
                year = ''
                year_match = re.search(r'\b(19|20)\d{2}\b', journal_info)
                if year_match:
                    year = year_match.group()
                
                abstract_elem = item.select_one('.full-view-snippet')
                abstract = abstract_elem.text.strip() if abstract_elem else ''
                
                doi_elem = item.select_one('.id-link')
                doi = doi_elem.text.strip() if doi_elem else ''
                
                articles.append({
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'abstract': abstract,
                    'doi': doi,
                    'journal': journal_info,
                    'type': 'article',
                    'source': 'PubMed'
                })
            
            return articles
            
        except Exception as e:
            print(f"Error al scrapear PubMed: {str(e)}")
            return []
    #no sirve
    @staticmethod
    def scrape_scopus(query: str) -> List[Dict[str, Union[str, List[str]]]]:
        """Scraping básico de Scopus (ejemplo)"""
        print(f"Scrapeando Scopus para: {query}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        url = f"https://www.scopus.com/results/results.uri?query={query}"
        
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            for item in soup.select('.searchArea .resultListRow'):
                title = item.select_one('.resultTitle').text.strip() if item.select_one('.resultTitle') else ''
                authors = item.select_one('.authorList').text.strip() if item.select_one('.authorList') else ''
                year = item.select_one('.ddmDocYear').text.strip() if item.select_one('.ddmDocYear') else ''
                abstract = item.select_one('.abstractSnippet').text.strip() if item.select_one('.abstractSnippet') else ''
                doi = item.select_one('.doiTextLink').text.strip() if item.select_one('.doiTextLink') else ''
                
                articles.append({
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'abstract': abstract,
                    'doi': doi,
                    'type': 'article',
                    'source': 'Scopus'
                })
            
            return articles
            
        except Exception as e:
            print(f"Error al scrapear Scopus: {str(e)}")
            return []
    #SIRVE
    @staticmethod
    def scrape_sciencedirect(query: str) -> List[Dict[str, Union[str, List[str]]]]:
        """Scraping básico de ScienceDirect (ejemplo)"""
        print(f"Scrapeando ScienceDirect para: {query}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        url = f"https://www.sciencedirect.com/search?qs={query}"
        
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            for item in soup.select('.ResultItem'):
                title = item.select_one('.result-item-title').text.strip() if item.select_one('.result-item-title') else ''
                authors = item.select_one('.author').text.strip() if item.select_one('.author') else ''
                year = item.select_one('.year').text.strip() if item.select_one('.year') else ''
                abstract = item.select_one('.abstract').text.strip() if item.select_one('.abstract') else ''
                doi = item.select_one('.doi').text.strip() if item.select_one('.doi') else ''
                
                articles.append({
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'abstract': abstract,
                    'doi': doi,
                    'type': 'article',
                    'source': 'ScienceDirect'
                })
            
            return articles
            
        except Exception as e:
            print(f"Error al scrapear ScienceDirect: {str(e)}")
            return []
    #SIRVE
    @staticmethod
    def scrape_semantic_scholar(query: str) -> List[Dict[str, Union[str, List[str]]]]:
        """Scraping de Semantic Scholar"""
        print(f"Scrapeando Semantic Scholar para: {query}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        url = f"https://www.semanticscholar.org/search?q={query}&sort=relevance"
        
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            for item in soup.select('[data-test-id="paper-row"]'):
                title_elem = item.select_one('[data-test-id="title-link"]')
                title = title_elem.text.strip() if title_elem else ''
                
                authors_elem = item.select_one('[data-test-id="authors-list"]')
                authors = authors_elem.text.strip() if authors_elem else ''
                
                year_elem = item.select_one('[data-test-id="year"]')
                year = year_elem.text.strip() if year_elem else ''
                
                abstract_elem = item.select_one('[data-test-id="abstract-text"]')
                abstract = abstract_elem.text.strip() if abstract_elem else ''
                
                doi_elem = item.select_one('[data-test-id="doi-link"]')
                doi = doi_elem.text.strip() if doi_elem else ''
                
                articles.append({
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'abstract': abstract,
                    'doi': doi,
                    'type': 'article',
                    'source': 'Semantic Scholar'
                })
            
            return articles
            
        except Exception as e:
            print(f"Error al scrapear Semantic Scholar: {str(e)}")
            return []
    #SIRVE
    @staticmethod
    def scrape_google_scholar(query: str) -> List[Dict[str, Union[str, List[str]]]]:
        """Scraping de Google Scholar"""
        print(f"Scrapeando Google Scholar para: {query}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        url = f"https://scholar.google.com/scholar?hl=en&q={query}"
        
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            for item in soup.select('.gs_r.gs_or.gs_scl'):
                title_elem = item.select_one('.gs_rt')
                title = title_elem.text.strip() if title_elem else ''
                
                authors_elem = item.select_one('.gs_a')
                authors = authors_elem.text.strip() if authors_elem else ''
                
                # Extraer año de la línea de autores
                year = ''
                if authors_elem:
                    year_match = re.search(r'\b(19|20)\d{2}\b', authors_elem.text)
                    if year_match:
                        year = year_match.group()
                
                abstract_elem = item.select_one('.gs_rs')
                abstract = abstract_elem.text.strip() if abstract_elem else ''
                
                # En Google Scholar no siempre hay DOI disponible
                doi = ''
                
                articles.append({
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'abstract': abstract,
                    'doi': doi,
                    'type': 'article',
                    'source': 'Google Scholar'
                })
            
            return articles
            
        except Exception as e:
            print(f"Error al scrapear Google Scholar: {str(e)}")
            return []
    #SIRVE
    @staticmethod
    def scrape_uniquindio_databases(query: str) -> List[Dict[str, Union[str, List[str]]]]:
        """Scraping para las bases de datos de la Universidad del Quindío"""
        print(f"Scrapeando bases de datos de la Universidad del Quindío para: {query}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # URL base del portal de bases de datos
        base_url = "https://library.uniquindio.edu.co/databases"
        
        try:
            # Primero obtenemos la lista de bases de datos disponibles
            response = requests.get(base_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Aquí necesitarías identificar los enlaces a las bases de datos específicas
            # Este es un ejemplo genérico que necesitaría ajustarse según la estructura real
            db_links = soup.select('.database-link')
            
            articles = []
            for link in db_links[:3]:  # Limitar a 3 bases para ejemplo
                db_name = link.text.strip()
                db_url = link['href']
                
                print(f"Accediendo a {db_name}...")
                
                # Simulamos acceso a una base de datos específica
                # En la práctica, necesitarías implementar el scraping específico para cada base
                time.sleep(2)
                
                # Ejemplo genérico de resultados
                articles.append({
                    'title': f"Ejemplo de artículo sobre {query} en {db_name}",
                    'authors': "Autor1, Autor2",
                    'year': "2023",
                    'abstract': f"Este es un ejemplo de abstract sobre {query} encontrado en {db_name}",
                    'doi': "10.1234/example.doi",
                    'type': 'article',
                    'source': f"Uniquindio DB: {db_name}"
                })
            
            return articles
            
        except Exception as e:
            print(f"Error al scrapear bases de datos de Uniquindio: {str(e)}")
            return []

    @staticmethod
    def scrape_database(url: str, query: str, source_name: str) -> List[Dict[str, Union[str, List[str]]]]:
        """Método genérico para scrapear cualquier base de datos"""
        print(f"Scrapeando {source_name} para: {query}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url.format(query=query), headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            for item in soup.select('.result-item'):
                title = item.select_one('.title').text.strip() if item.select_one('.title') else ''
                authors = item.select_one('.authors').text.strip() if item.select_one('.authors') else ''
                year = item.select_one('.year').text.strip() if item.select_one('.year') else ''
                
                articles.append({
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'abstract': '',
                    'doi': '',
                    'type': 'article',
                    'source': source_name
                })
            
            return articles
            
        except Exception as e:
            print(f"Error al scrapear {source_name}: {str(e)}")
            return []

class BibliographicUnifier:
    def __init__(self, output_format: str = 'ris', similarity_threshold: float = 0.85):
        """
        Inicializa el unificador bibliográfico
        
        Args:
            output_format: 'ris' o 'bibtex' - formato de salida
            similarity_threshold: umbral para considerar duplicados (0.7-0.95)
        """
        self.unique_entries: List[Dict] = []
        self.duplicate_entries: List[Dict] = []
        self.output_format = output_format.lower()
        self.similarity_threshold = similarity_threshold
        self.duplicate_stats = {
            'exact_duplicates': 0,
            'similar_duplicates': 0,
            'potential_duplicates': 0
        }
        self.sources_processed = set()
    
    def normalize_text(self, text: str) -> str:
        """Normaliza texto para comparación eliminando variaciones menores"""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        text = unidecode(text)  # Elimina acentos y caracteres especiales
        text = text.lower().strip()
        
        punctuation = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
        for char in punctuation:
            text = text.replace(char, ' ')
        
        stop_words = {'the', 'and', 'of', 'in', 'a', 'an', 'to', 'for', 'on', 'with'}
        words = [word for word in text.split() if word not in stop_words and len(word) > 2]
        return " ".join(words)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos usando SequenceMatcher"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def generate_entry_signature(self, entry: Dict) -> Dict:
        """Crea una firma normalizada para comparación robusta"""
        return {
            'title': self.normalize_text(entry.get('title', '')),
            'authors': self.normalize_authors(entry.get('authors', '')),
            'year': str(entry.get('year', '')).strip()[:4],  # Solo el año
            'doi': str(entry.get('doi', '')).lower().strip(),
            'journal': self.normalize_text(entry.get('journal', ''))
        }
    
    def normalize_authors(self, authors: str) -> str:
        """Normaliza nombres de autores para comparación consistente"""
        if pd.isna(authors) or not authors:
            return ""
        
        authors = unidecode(authors.lower())
        
        if ' and ' in authors:
            authors = authors.replace(' and ', '; ')
        elif ',' in authors and ';' not in authors:
            parts = [p.strip() for p in authors.split(',')]
            if len(parts) > 1 and ' ' not in parts[1]:
                authors = f"{parts[0]}, {parts[1]}"
        
        author_list = sorted([a.strip() for a in authors.split(';') if a.strip()])
        return '; '.join(author_list)
    
    def is_duplicate(self, entry1: Dict, entry2: Dict) -> bool:
        """Determina si dos entradas son duplicados usando múltiples criterios"""
        sig1 = self.generate_entry_signature(entry1)
        sig2 = self.generate_entry_signature(entry2)
        
        if sig1['doi'] and sig2['doi'] and sig1['doi'] == sig2['doi']:
            self.duplicate_stats['exact_duplicates'] += 1
            return True
        
        if sig1 == sig2:
            self.duplicate_stats['exact_duplicates'] += 1
            return True
        
        title_sim = self.calculate_similarity(sig1['title'], sig2['title'])
        if title_sim > self.similarity_threshold:
            author_sim = self.calculate_similarity(sig1['authors'], sig2['authors'])
            year_match = sig1['year'] == sig2['year']
            
            if author_sim > 0.7 and year_match:
                self.duplicate_stats['similar_duplicates'] += 1
                return True
            elif title_sim > 0.95:
                self.duplicate_stats['potential_duplicates'] += 1
                return True
        
        return False
    
    def find_duplicates(self, new_entry: Dict) -> List[int]:
        """Encuentra índices de entradas duplicadas en unique_entries"""
        duplicates = []
        for idx, existing_entry in enumerate(self.unique_entries):
            if self.is_duplicate(new_entry, existing_entry):
                duplicates.append(idx)
        return duplicates
    
    def merge_entries(self, entry1: Dict, entry2: Dict) -> Dict:
        """Combina dos entradas duplicadas conservando la información más completa"""
        merged = entry1.copy()
        
        if 'source' in entry1 and 'source' in entry2:
            if isinstance(entry1['source'], str):
                merged['source'] = [entry1['source'], entry2['source']]
            elif isinstance(entry1['source'], list):
                merged['source'] = entry1['source'] + [entry2['source']]
        
        if not merged.get('doi') and entry2.get('doi'):
            merged['doi'] = entry2['doi']
        
        if not merged.get('url') and entry2.get('url'):
            merged['url'] = entry2['url']
        elif merged.get('url') and entry2.get('url') and merged['url'] != entry2['url']:
            if isinstance(merged['url'], str):
                merged['url'] = [merged['url'], entry2['url']]
            else:
                merged['url'].append(entry2['url'])
        
        if not merged.get('abstract') and entry2.get('abstract'):
            merged['abstract'] = entry2['abstract']
        
        return merged
    
    def add_entry(self, entry: Dict, source: str) -> None:
        """Añade una entrada, detectando y manejando duplicados"""
        entry['source'] = source
        self.sources_processed.add(source)
        
        duplicates = self.find_duplicates(entry)
        
        if duplicates:
            duplicate_info = entry.copy()
            duplicate_info['duplicate_of'] = [self.unique_entries[i]['title'] for i in duplicates]
            duplicate_info['duplicate_sources'] = [self.unique_entries[i]['source'] for i in duplicates]
            self.duplicate_entries.append(duplicate_info)
            
            for idx in duplicates:
                self.unique_entries[idx] = self.merge_entries(self.unique_entries[idx], entry)
        else:
            self.unique_entries.append(entry)
    
    def scrape_and_load(self, query: str, database_urls: Dict[str, str]) -> None:
        """Realiza scraping de múltiples bases de datos y carga los datos"""
        for db_name, url in database_urls.items():
            try:
                if db_name.lower() == 'scopus':
                    articles = DatabaseScraper.scrape_scopus(query)
                elif db_name.lower() == 'sciencedirect':
                    articles = DatabaseScraper.scrape_sciencedirect(query)
                elif db_name.lower() == 'semantic scholar':
                    articles = DatabaseScraper.scrape_semantic_scholar(query)
                elif db_name.lower() == 'google scholar':
                    articles = DatabaseScraper.scrape_google_scholar(query)
                elif db_name.lower() == 'pubmed':
                    articles = DatabaseScraper.scrape_pubmed(query)
                elif db_name.lower() == 'uniquindio':
                    articles = DatabaseScraper.scrape_uniquindio_databases(query)
                else:
                    articles = DatabaseScraper.scrape_database(url, query, db_name)
                
                for article in articles:
                    self.add_entry(article, db_name)
                
                time.sleep(2)  # Espera para evitar bloqueos
                
            except Exception as e:
                print(f"Error al procesar {db_name}: {str(e)}")
                continue
    
    def export_to_ris(self, entries: List[Dict], filename: str) -> None:
        """Exporta entradas a formato RIS"""
        ris_lines = []
        for entry in entries:
            ris_lines.append(f"TY  - {self._get_ris_type(entry['type'])}")
            ris_lines.append(f"TI  - {entry['title']}")
            
            authors = entry['authors']
            if ';' in authors:
                for author in authors.split(';'):
                    ris_lines.append(f"AU  - {author.strip()}")
            elif ' and ' in authors:
                for author in authors.split(' and '):
                    ris_lines.append(f"AU  - {author.strip()}")
            else:
                ris_lines.append(f"AU  - {authors}")
            
            if entry.get('year'):
                ris_lines.append(f"PY  - {entry['year']}")
            if entry.get('journal'):
                ris_lines.append(f"JO  - {entry['journal']}")
            if entry.get('abstract'):
                ris_lines.append(f"AB  - {entry['abstract']}")
            if entry.get('doi'):
                ris_lines.append(f"DO  - {entry['doi']}")
            if entry.get('url'):
                ris_lines.append(f"UR  - {entry['url']}")
            
            if 'source' in entry:
                if isinstance(entry['source'], list):
                    ris_lines.extend([f"ZZ  - Source: {src}" for src in entry['source']])
                else:
                    ris_lines.append(f"ZZ  - Source: {entry['source']}")
            
            ris_lines.append("ER  - ")
            ris_lines.append("")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(ris_lines))
    
    def export_to_bibtex(self, entries: List[Dict], filename: str) -> None:
        """Exporta entradas a formato BibTeX"""
        bibtex_lines = []
        for idx, entry in enumerate(entries):
            first_author = entry['authors'].split(';')[0].split(',')[0].strip()
            entry_key = f"{first_author[:6]}{entry.get('year','')[:4]}{idx:03d}"
            
            bibtex_lines.append(f"@{self._get_bibtex_type(entry['type'])}{{{entry_key},")
            bibtex_lines.append(f"title = {{{entry['title']}}},")
            
            if ';' in entry['authors']:
                authors = " and ".join([a.strip() for a in entry['authors'].split(';')])
            else:
                authors = entry['authors']
            bibtex_lines.append(f"author = {{{authors}}},")
            
            if entry.get('year'):
                bibtex_lines.append(f"year = {{{entry['year']}}},")
            if entry.get('journal'):
                bibtex_lines.append(f"journal = {{{entry['journal']}}},")
            if entry.get('abstract'):
                bibtex_lines.append(f"abstract = {{{entry['abstract']}}},")
            if entry.get('doi'):
                bibtex_lines.append(f"doi = {{{entry['doi']}}},")
            if entry.get('url'):
                bibtex_lines.append(f"url = {{{entry['url']}}},")
            
            if 'source' in entry:
                if isinstance(entry['source'], list):
                    sources = ", ".join(entry['source'])
                else:
                    sources = entry['source']
                bibtex_lines.append(f"note = {{Source: {sources}}},")
            
            bibtex_lines.append("}\n")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(bibtex_lines))
    
    def _get_ris_type(self, doc_type: str) -> str:
        """Mapea tipos de documento a códigos RIS"""
        type_map = {
            'article': 'JOUR',
            'conference': 'CPAPER',
            'conferencepaper': 'CPAPER',
            'book': 'BOOK',
            'chapter': 'CHAP',
            'thesis': 'THES',
            'phdthesis': 'THES',
            'mastersthesis': 'THES',
            'report': 'RPRT',
            'default': 'GEN'
        }
        return type_map.get(doc_type.lower(), type_map['default'])
    
    def _get_bibtex_type(self, doc_type: str) -> str:
        """Mapea tipos de documento a códigos BibTeX"""
        type_map = {
            'article': 'article',
            'conference': 'inproceedings',
            'conferencepaper': 'inproceedings',
            'book': 'book',
            'chapter': 'incollection',
            'thesis': 'phdthesis',
            'phdthesis': 'phdthesis',
            'mastersthesis': 'mastersthesis',
            'report': 'techreport',
            'default': 'misc'
        }
        return type_map.get(doc_type.lower(), type_map['default'])
    
    def export_results(self, output_dir: str = "output") -> Dict:
        """Exporta todos los resultados a archivos"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unified_filename = os.path.join(output_dir, f"unified_results_{timestamp}.{self.output_format}")
        duplicates_filename = os.path.join(output_dir, f"duplicate_entries_{timestamp}.{self.output_format}")
        
        if self.output_format == 'ris':
            self.export_to_ris(self.unique_entries, unified_filename)
            self.export_to_ris(self.duplicate_entries, duplicates_filename)
        else:
            self.export_to_bibtex(self.unique_entries, unified_filename)
            self.export_to_bibtex(self.duplicate_entries, duplicates_filename)
        
        summary = {
            'timestamp': timestamp,
            'sources_processed': list(self.sources_processed),
            'unique_entries': len(self.unique_entries),
            'duplicate_entries': len(self.duplicate_entries),
            'duplicate_stats': self.duplicate_stats,
            'output_files': {
                'unified': unified_filename,
                'duplicates': duplicates_filename
            }
        }
        
        summary_filename = os.path.join(output_dir, f"summary_{timestamp}.json")
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        return summary

def main():
    print("=== Sistema Integrado de Web Scraping y Unificación Bibliográfica ===")
    print("Este sistema:")
    print("1. Realiza web scraping de múltiples bases de datos")
    print("2. Unifica los resultados eliminando duplicados")
    print("3. Genera dos archivos: unificado y duplicados\n")
    
    query = input("Ingrese el término de búsqueda (ej: 'computational thinking'): ").strip()
    
    database_urls = {
        'Scopus': 'https://www.scopus.com/results/results.uri?query={query}',
        'ScienceDirect': 'https://www.sciencedirect.com/search?qs={query}',
        'Semantic Scholar': 'https://www.semanticscholar.org/search?q={query}',
        'Google Scholar': 'https://scholar.google.com/scholar?q={query}',
        'PubMed': 'https://pubmed.ncbi.nlm.nih.gov/?term={query}',
        'Uniquindio': 'https://library.uniquindio.edu.co/databases'
    }
    
    output_format = input("Formato de salida (RIS/BibTeX): ").strip().lower()
    while output_format not in ['ris', 'bibtex']:
        print("Formato no válido. Use 'RIS' o 'BibTeX'")
        output_format = input("Formato de salida (RIS/BibTeX): ").strip().lower()
    
    similarity_threshold = float(input("Umbral de similitud (0.7-0.95): ") or 0.85)
    
    unifier = BibliographicUnifier(
        output_format=output_format,
        similarity_threshold=similarity_threshold
    )
    
    print("\nIniciando scraping de bases de datos...")
    unifier.scrape_and_load(query, database_urls)
    
    print("\nProcesando resultados y detectando duplicados...")
    summary = unifier.export_results()
    
    print("\n=== Proceso completado ===")
    print(f"Término de búsqueda: {query}")
    print(f"Bases de datos procesadas: {', '.join(summary['sources_processed'])}")
    print(f"Entradas únicas encontradas: {summary['unique_entries']}")
    print(f"Entradas duplicadas detectadas: {summary['duplicate_entries']}")
    print("\nEstadísticas de duplicados:")
    print(f"- Exactos: {summary['duplicate_stats']['exact_duplicates']}")
    print(f"- Similares: {summary['duplicate_stats']['similar_duplicates']}")
    print(f"- Potenciales: {summary['duplicate_stats']['potential_duplicates']}")
    print("\nArchivos generados:")
    print(f"- Archivo unificado: {summary['output_files']['unified']}")
    print(f"- Archivo de duplicados: {summary['output_files']['duplicates']}")
    print(f"- Resumen JSON: output/summary_{summary['timestamp']}.json")

if __name__ == "__main__":
    main()