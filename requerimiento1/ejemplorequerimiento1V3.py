import pandas as pd
import json
from typing import List, Dict, Union
import hashlib
import os
import difflib
from unidecode import unidecode
from datetime import datetime

class BibliographicUnifier:
    def __init__(self, output_format='ris', similarity_threshold=0.85):
        """
        Inicializa el unificador bibliográfico
        
        Args:
            output_format: 'ris' o 'bibtex' - formato de salida
            similarity_threshold: umbral para considerar duplicados (0.7-0.95)
        """
        self.unique_entries = []
        self.duplicate_entries = []
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
        
        # Elimina puntuación y palabras comunes
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
        
        # Formato: "Apellido, Nombre; Apellido2, Nombre2" o "Nombre Apellido and Nombre2 Apellido2"
        authors = unidecode(authors.lower())
        
        # Intenta estandarizar el formato
        if ' and ' in authors:
            authors = authors.replace(' and ', '; ')
        elif ',' in authors and ';' not in authors:
            parts = [p.strip() for p in authors.split(',')]
            if len(parts) > 1 and ' ' not in parts[1]:
                # Asume formato "Apellido, Nombre"
                authors = f"{parts[0]}, {parts[1]}"
        
        # Ordena alfabéticamente para hacer la comparación consistente
        author_list = sorted([a.strip() for a in authors.split(';') if a.strip()])
        return '; '.join(author_list)
    
    def is_duplicate(self, entry1: Dict, entry2: Dict) -> bool:
        """Determina si dos entradas son duplicados usando múltiples criterios"""
        sig1 = self.generate_entry_signature(entry1)
        sig2 = self.generate_entry_signature(entry2)
        
        # 1. Comparación por DOI (el más confiable)
        if sig1['doi'] and sig2['doi'] and sig1['doi'] == sig2['doi']:
            self.duplicate_stats['exact_duplicates'] += 1
            return True
        
        # 2. Comparación exacta de firma normalizada
        if sig1 == sig2:
            self.duplicate_stats['exact_duplicates'] += 1
            return True
        
        # 3. Comparación de título y autores
        title_sim = self.calculate_similarity(sig1['title'], sig2['title'])
        if title_sim > self.similarity_threshold:
            author_sim = self.calculate_similarity(sig1['authors'], sig2['authors'])
            year_match = sig1['year'] == sig2['year']
            
            if author_sim > 0.7 and year_match:
                self.duplicate_stats['similar_duplicates'] += 1
                return True
            elif title_sim > 0.95:  # Títulos casi idénticos
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
        
        # Combina fuentes
        if 'source' in entry1 and 'source' in entry2:
            if isinstance(entry1['source'], str):
                merged['source'] = [entry1['source'], entry2['source']]
            elif isinstance(entry1['source'], list):
                merged['source'] = entry1['source'] + [entry2['source']]
        
        # Conserva el DOI si uno lo tiene y el otro no
        if not merged.get('doi') and entry2.get('doi'):
            merged['doi'] = entry2['doi']
        
        # Combina URLs
        if not merged.get('url') and entry2.get('url'):
            merged['url'] = entry2['url']
        elif merged.get('url') and entry2.get('url') and merged['url'] != entry2['url']:
            if isinstance(merged['url'], str):
                merged['url'] = [merged['url'], entry2['url']]
            else:
                merged['url'].append(entry2['url'])
        
        # Combina abstracts
        if not merged.get('abstract') and entry2.get('abstract'):
            merged['abstract'] = entry2['abstract']
        
        return merged
    
    def add_entry(self, entry: Dict, source: str) -> None:
        """Añade una entrada, detectando y manejando duplicados"""
        entry['source'] = source
        self.sources_processed.add(source)
        
        duplicates = self.find_duplicates(entry)
        
        if duplicates:
            # Es un duplicado, registrar información
            duplicate_info = entry.copy()
            duplicate_info['duplicate_of'] = [self.unique_entries[i]['title'] for i in duplicates]
            duplicate_info['duplicate_sources'] = [self.unique_entries[i]['source'] for i in duplicates]
            self.duplicate_entries.append(duplicate_info)
            
            # Mejorar la entrada original con información adicional
            for idx in duplicates:
                self.unique_entries[idx] = self.merge_entries(self.unique_entries[idx], entry)
        else:
            # Es único, añadir a la lista principal
            self.unique_entries.append(entry)
    
    def load_data_from_csv(self, filepath: str, source: str) -> None:
        """Carga datos desde un archivo CSV"""
        try:
            df = pd.read_csv(filepath)
            for _, row in df.iterrows():
                entry = {
                    'title': row.get('title', ''),
                    'authors': row.get('authors', ''),
                    'year': str(row.get('year', '')),
                    'abstract': row.get('abstract', ''),
                    'journal': row.get('journal', ''),
                    'doi': str(row.get('doi', '')).lower().strip(),
                    'url': row.get('url', ''),
                    'type': row.get('type', 'article')
                }
                self.add_entry(entry, source)
        except Exception as e:
            print(f"Error al cargar {filepath}: {str(e)}")
    
    def load_data_from_json(self, filepath: str, source: str) -> None:
        """Carga datos desde un archivo JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data:
                    # Normaliza la estructura del JSON
                    normalized_entry = {
                        'title': entry.get('title', ''),
                        'authors': entry.get('authors', ''),
                        'year': str(entry.get('year', '')),
                        'abstract': entry.get('abstract', ''),
                        'journal': entry.get('journal', ''),
                        'doi': str(entry.get('doi', '')).lower().strip(),
                        'url': entry.get('url', ''),
                        'type': entry.get('type', 'article')
                    }
                    self.add_entry(normalized_entry, source)
        except Exception as e:
            print(f"Error al cargar {filepath}: {str(e)}")
    
    def export_to_ris(self, entries: List[Dict], filename: str) -> None:
        """Exporta entradas a formato RIS"""
        ris_lines = []
        for entry in entries:
            ris_lines.append(f"TY  - {self._get_ris_type(entry['type'])}")
            ris_lines.append(f"TI  - {entry['title']}")
            
            # Manejo de autores (diferentes formatos)
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
            
            # Fuente de origen (custom tag)
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
            # Generar clave única para la entrada
            first_author = entry['authors'].split(';')[0].split(',')[0].strip()
            entry_key = f"{first_author[:6]}{entry.get('year','')[:4]}{idx:03d}"
            
            bibtex_lines.append(f"@{self._get_bibtex_type(entry['type'])}{{{entry_key},")
            bibtex_lines.append(f"title = {{{entry['title']}}},")
            
            # Formatear autores correctamente
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
            
            # Fuente de origen (campo note)
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
    
    def export_duplicates_report(self, filename: str) -> None:
        """Exporta un reporte detallado de duplicados"""
        report_data = []
        for dup in self.duplicate_entries:
            report_entry = {
                'duplicate_title': dup.get('title', ''),
                'duplicate_authors': dup.get('authors', ''),
                'duplicate_source': dup.get('source', ''),
                'duplicate_doi': dup.get('doi', ''),
                'original_titles': "; ".join(dup.get('duplicate_of', [])),
                'original_sources': "; ".join(dup.get('duplicate_sources', [])),
                'match_type': self._get_match_type(dup)
            }
            report_data.append(report_entry)
        
        df = pd.DataFrame(report_data)
        
        # Exportar en el mismo formato que los archivos principales
        if self.output_format == 'ris':
            self._export_duplicates_to_ris(df, filename)
        else:
            self._export_duplicates_to_bibtex(df, filename)
    
    def _get_match_type(self, entry: Dict) -> str:
        """Determina el tipo de coincidencia para duplicados"""
        if 'duplicate_of' not in entry:
            return "unknown"
        
        original_title = entry['duplicate_of'][0]
        title_sim = self.calculate_similarity(
            self.normalize_text(entry['title']),
            self.normalize_text(original_title)
        )
        
        if title_sim == 1.0:
            return "exact"
        elif title_sim > self.similarity_threshold:
            return "similar"
        else:
            return "potential"
    
    def _export_duplicates_to_ris(self, df: pd.DataFrame, filename: str) -> None:
        """Exporta reporte de duplicados en formato RIS"""
        ris_lines = []
        for _, row in df.iterrows():
            ris_lines.append("TY  - DUPL")  # Tipo especial para duplicados
            ris_lines.append(f"TI  - {row['duplicate_title']}")
            ris_lines.append(f"AU  - {row['duplicate_authors']}")
            ris_lines.append(f"ZZ  - Original Titles: {row['original_titles']}")
            ris_lines.append(f"ZZ  - Original Sources: {row['original_sources']}")
            ris_lines.append(f"ZZ  - Match Type: {row['match_type']}")
            ris_lines.append(f"ZZ  - Source: {row['duplicate_source']}")
            if row['duplicate_doi']:
                ris_lines.append(f"DO  - {row['duplicate_doi']}")
            ris_lines.append("ER  - ")
            ris_lines.append("")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(ris_lines))
    
    def _export_duplicates_to_bibtex(self, df: pd.DataFrame, filename: str) -> None:
        """Exporta reporte de duplicados en formato BibTeX"""
        bibtex_lines = []
        for idx, row in df.iterrows():
            entry_key = f"dup{idx:04d}"
            bibtex_lines.append(f"@duplicate{{{entry_key},")
            bibtex_lines.append(f"title = {{{row['duplicate_title']}}},")
            bibtex_lines.append(f"author = {{{row['duplicate_authors']}}},")
            bibtex_lines.append(f"originaltitles = {{{row['original_titles']}}},")
            bibtex_lines.append(f"originalsources = {{{row['original_sources']}}},")
            bibtex_lines.append(f"matchtype = {{{row['match_type']}}},")
            bibtex_lines.append(f"source = {{{row['duplicate_source']}}},")
            if row['duplicate_doi']:
                bibtex_lines.append(f"doi = {{{row['duplicate_doi']}}},")
            bibtex_lines.append("}\n")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(bibtex_lines))
    
    def export_results(self, output_dir: str = "output") -> None:
        """Exporta todos los resultados a archivos"""
        # Crear directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Generar nombres de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unified_filename = os.path.join(output_dir, f"unified_results_{timestamp}.{self.output_format}")
        duplicates_filename = os.path.join(output_dir, f"duplicate_entries_{timestamp}.{self.output_format}")
        report_filename = os.path.join(output_dir, f"duplicates_report_{timestamp}.{self.output_format}")
        
        # Exportar archivos principales
        if self.output_format == 'ris':
            self.export_to_ris(self.unique_entries, unified_filename)
            self.export_to_ris(self.duplicate_entries, duplicates_filename)
        else:
            self.export_to_bibtex(self.unique_entries, unified_filename)
            self.export_to_bibtex(self.duplicate_entries, duplicates_filename)
        
        # Exportar reporte de duplicados
        self.export_duplicates_report(report_filename)
        
        # Generar resumen
        summary = {
            'timestamp': timestamp,
            'sources_processed': list(self.sources_processed),
            'unique_entries': len(self.unique_entries),
            'duplicate_entries': len(self.duplicate_entries),
            'duplicate_stats': self.duplicate_stats,
            'output_files': {
                'unified': unified_filename,
                'duplicates': duplicates_filename,
                'report': report_filename
            }
        }
        
        # Guardar resumen como JSON
        summary_filename = os.path.join(output_dir, f"summary_{timestamp}.json")
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        return summary

def main():
    print("=== Sistema de Unificación Bibliográfica ===")
    print("Este sistema procesa datos de múltiples fuentes y genera:")
    print("1. Un archivo unificado con entradas únicas")
    print("2. Un archivo con entradas duplicadas detectadas")
    print("3. Un reporte detallado de duplicados\n")
    
    # Configuración
    output_format = input("Formato de salida (RIS/BibTeX): ").strip().lower()
    while output_format not in ['ris', 'bibtex']:
        print("Formato no válido. Use 'RIS' o 'BibTeX'")
        output_format = input("Formato de salida (RIS/BibTeX): ").strip().lower()
    
    similarity_threshold = float(input("Umbral de similitud (0.7-0.95): ") or 0.85)
    
    # Inicializar unificador
    unifier = BibliographicUnifier(
        output_format=output_format,
        similarity_threshold=similarity_threshold
    )
    
    # Cargar datos (ejemplo con archivos de muestra)
    sample_files = {
        'scopus_sample.csv': [
            {'title': 'Computational Thinking', 'authors': 'Wing, J.M.', 'year': '2006', 
             'journal': 'Communications of the ACM', 'doi': '10.1145/1118178.1118215',
             'type': 'article', 'abstract': 'Discusses computational thinking as a fundamental skill...'},
            {'title': 'Demystifying computational thinking', 'authors': 'Shute, V.J.; Sun, C.', 
             'year': '2017', 'journal': 'Educational Research Review', 'type': 'article'}
        ],
        'wos_sample.csv': [
            {'title': 'Computational Thinking', 'authors': 'Wing, Jeannette M.', 
             'year': '2006', 'journal': 'COMMUN ACM', 'doi': '10.1145/1118178.1118215',
             'type': 'article', 'abstract': 'Discusses computational thinking as a fundamental skill...'},
            {'title': 'The concept of computational thinking', 'authors': 'Smith, John', 
             'year': '2018', 'journal': 'Computer Science Education', 'type': 'article'}
        ]
    }
    
    # Crear archivos de muestra
    for filename, data in sample_files.items():
        pd.DataFrame(data).to_csv(filename, index=False)
    
    # Procesar archivos
    for filename in sample_files.keys():
        if os.path.exists(filename):
            print(f"\nProcesando {filename}...")
            unifier.load_data_from_csv(filename, filename.split('_')[0].upper())
    
    # Exportar resultados
    print("\nExportando resultados...")
    summary = unifier.export_results()
    
    # Mostrar resumen
    print("\n=== Resumen Final ===")
    print(f"Fuentes procesadas: {', '.join(summary['sources_processed'])}")
    print(f"Entradas únicas: {summary['unique_entries']}")
    print(f"Entradas duplicadas: {summary['duplicate_entries']}")
    print("\nEstadísticas de duplicados:")
    print(f"- Exactos: {summary['duplicate_stats']['exact_duplicates']}")
    print(f"- Similares: {summary['duplicate_stats']['similar_duplicates']}")
    print(f"- Potenciales: {summary['duplicate_stats']['potential_duplicates']}")
    print("\nArchivos generados:")
    print(f"- Unificado: {summary['output_files']['unified']}")
    print(f"- Duplicados: {summary['output_files']['duplicates']}")
    print(f"- Reporte: {summary['output_files']['report']}")
    print(f"- Resumen: output/summary_{summary['timestamp']}.json")

if __name__ == "__main__":
    main()