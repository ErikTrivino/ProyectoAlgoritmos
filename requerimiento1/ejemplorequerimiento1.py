import pandas as pd
import json
from typing import List, Dict, Union
import hashlib
import os

class BibliographicUnifier:
    def __init__(self):
        self.unique_entries = []
        self.duplicate_entries = []
        self.seen_hashes = set()
    
    def generate_entry_hash(self, entry: Dict) -> str:
        """Genera un hash único para cada entrada bibliográfica"""
        # Usamos título, autores y año como base para identificar duplicados
        hash_str = f"{entry.get('title', '')}-{entry.get('authors', '')}-{entry.get('year', '')}"
        return hashlib.md5(hash_str.encode('utf-8')).hexdigest()
    
    def add_entry(self, entry: Dict, source: str) -> None:
        """Añade una entrada al unificador, detectando duplicados"""
        entry_hash = self.generate_entry_hash(entry)
        entry['source'] = source  # Añadimos la fuente de origen
        
        if entry_hash in self.seen_hashes:
            # Es un duplicado, añadir a la lista de duplicados
            self.duplicate_entries.append(entry)
        else:
            # Es único, añadir a la lista principal
            self.unique_entries.append(entry)
            self.seen_hashes.add(entry_hash)
    
    def load_data_from_csv(self, filepath: str, source: str) -> None:
        """Carga datos desde un archivo CSV"""
        df = pd.read_csv(filepath)
        for _, row in df.iterrows():
            entry = {
                'title': row.get('title', ''),
                'authors': row.get('authors', ''),
                'year': str(row.get('year', '')),
                'abstract': row.get('abstract', ''),
                'journal': row.get('journal', ''),
                'doi': row.get('doi', ''),
                'url': row.get('url', ''),
                'type': row.get('type', 'article')
            }
            self.add_entry(entry, source)
    
    def load_data_from_json(self, filepath: str, source: str) -> None:
        """Carga datos desde un archivo JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for entry in data:
                self.add_entry(entry, source)
    
    def export_to_ris(self, entries: List[Dict], filename: str) -> None:
        """Exporta entradas a formato RIS"""
        ris_lines = []
        for entry in entries:
            ris_lines.append("TY  - %s" % self._get_ris_type(entry['type']))
            ris_lines.append("TI  - %s" % entry['title'])
            for author in entry['authors'].split(' and '):
                ris_lines.append("AU  - %s" % author.strip())
            if entry.get('year'):
                ris_lines.append("PY  - %s" % entry['year'])
            if entry.get('journal'):
                ris_lines.append("JO  - %s" % entry['journal'])
            if entry.get('abstract'):
                ris_lines.append("AB  - %s" % entry['abstract'])
            if entry.get('doi'):
                ris_lines.append("DO  - %s" % entry['doi'])
            if entry.get('url'):
                ris_lines.append("UR  - %s" % entry['url'])
            ris_lines.append("ER  - ")
            ris_lines.append("")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(ris_lines))
    
    def export_to_bibtex(self, entries: List[Dict], filename: str) -> None:
        """Exporta entradas a formato BibTeX"""
        bibtex_lines = []
        for idx, entry in enumerate(entries):
            entry_key = f"{entry['authors'].split(',')[0].strip()}{entry['year']}{idx}"
            bibtex_lines.append(f"@{self._get_bibtex_type(entry['type'])}{{{entry_key},")
            bibtex_lines.append(f"title = {{{entry['title']}}},")
            bibtex_lines.append(f"author = {{{entry['authors']}}},")
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
            bibtex_lines.append("}\n")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(bibtex_lines))
    
    def _get_ris_type(self, doc_type: str) -> str:
        """Mapea tipos de documento a códigos RIS"""
        type_map = {
            'article': 'JOUR',
            'conference': 'CPAPER',
            'book': 'BOOK',
            'chapter': 'CHAP',
            'thesis': 'THES'
        }
        return type_map.get(doc_type.lower(), 'GEN')
    
    def _get_bibtex_type(self, doc_type: str) -> str:
        """Mapea tipos de documento a códigos BibTeX"""
        type_map = {
            'article': 'article',
            'conference': 'inproceedings',
            'book': 'book',
            'chapter': 'incollection',
            'thesis': 'phdthesis'
        }
        return type_map.get(doc_type.lower(), 'misc')

def main():
    # 1. Inicializar el unificador
    unifier = BibliographicUnifier()
    
    # 2. Cargar datos de diferentes fuentes (ejemplo)
    print("Cargando datos de diferentes fuentes...")
    if os.path.exists('scopus_results.csv'):
        unifier.load_data_from_csv('scopus_results.csv', 'Scopus')
    if os.path.exists('wos_results.json'):
        unifier.load_data_from_json('wos_results.json', 'Web of Science')
    if os.path.exists('google_scholar_results.csv'):
        unifier.load_data_from_csv('google_scholar_results.csv', 'Google Scholar')
    
    # 3. Exportar resultados
    print("\nResultados:")
    print(f"- Entradas únicas: {len(unifier.unique_entries)}")
    print(f"- Entradas duplicadas: {len(unifier.duplicate_entries)}")
    
    print("\nExportando archivos...")
    # Archivo unificado (elegir RIS o BibTeX)
    unifier.export_to_ris(unifier.unique_entries, 'unified_results.ris')
    # unifier.export_to_bibtex(unifier.unique_entries, 'unified_results.bib')
    
    # Archivo de duplicados (elegir RIS o BibTeX)
    unifier.export_to_ris(unifier.duplicate_entries, 'duplicate_entries.ris')
    # unifier.export_to_bibtex(unifier.duplicate_entries, 'duplicate_entries.bib')
    
    print("\nProceso completado:")
    print("- Archivo unificado: unified_results.ris")
    print("- Archivo de duplicados: duplicate_entries.ris")

if __name__ == "__main__":
    main()