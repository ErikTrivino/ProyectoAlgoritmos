import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import os
from datetime import datetime
import json
from pathlib import Path
class BibliometricAnalyzer:
    def __init__(self, unified_file_path):
        self.unified_file_path = unified_file_path
        self.df = None
        self.results = {
            'top_authors': None,
            'publications_by_year_type': None,
            'publication_types': None,
            'top_journals': None,
            'top_publishers': None
        }

    def load_data(self):
        if self.unified_file_path.endswith('.ris'):
            self._load_ris_data()
        elif self.unified_file_path.endswith('.bib'):
            self._load_bibtex_data()
        else:
            raise ValueError("Formato de archivo no soportado. Use RIS (.ris) o BibTeX (.bib)")

    def _load_ris_data(self):
        entries = []
        current_entry = {}

        with open(self.unified_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('TY  - '):
                    if current_entry:
                        entries.append(current_entry)
                    current_entry = {'type': line[6:]}
                elif line.startswith('ER  -'):
                    entries.append(current_entry)
                    current_entry = {}
                else:
                    try:
                        tag, value = line.split('  - ', 1)
                        if tag in current_entry:
                            if isinstance(current_entry[tag], list):
                                current_entry[tag].append(value)
                            else:
                                current_entry[tag] = [current_entry[tag], value]
                        else:
                            current_entry[tag] = value
                    except ValueError:
                        continue

        processed_entries = []
        for entry in entries:
            processed_entry = {}
            for key, value in entry.items():
                if isinstance(value, list):
                    if key == 'AU':
                        processed_entry[key] = '; '.join(value)
                    else:
                        processed_entry[key] = value[0]
                else:
                    processed_entry[key] = value
            processed_entries.append(processed_entry)

        self.df = pd.DataFrame(processed_entries)
        self._clean_data()

    def _load_bibtex_data(self):
        entries = []
        current_entry = {}
        in_entry = False

        with open(self.unified_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('@'):
                    if current_entry and in_entry:
                        entries.append(current_entry)
                    current_entry = {}
                    in_entry = True
                    parts = line.split('{', 1)
                    current_entry['type'] = parts[0][1:]
                elif '=' in line and in_entry:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.split('}')[0].strip().strip('{},')
                    current_entry[key] = value
                elif line.startswith('}'):
                    if current_entry and in_entry:
                        entries.append(current_entry)
                    in_entry = False

        self.df = pd.DataFrame(entries)
        self._clean_data()

    def _clean_data(self):
        type_mapping = {
            'JOUR': 'article',
            'CPAPER': 'conference',
            'BOOK': 'book',
            'CHAP': 'chapter',
            'inproceedings': 'conference',
            'incollection': 'chapter',
            'phdthesis': 'thesis',
            'mastersthesis': 'thesis'
        }

        if 'type' in self.df.columns:
            self.df['type'] = self.df['type'].map(lambda x: type_mapping.get(x, x.lower()))

        if 'AU' in self.df.columns:
            self.df['first_author'] = self.df['AU'].apply(self._extract_first_author)
        elif 'author' in self.df.columns:
            self.df['first_author'] = self.df['author'].apply(self._extract_first_author)

        if 'PY' in self.df.columns:
            self.df['year'] = pd.to_numeric(self.df['PY'], errors='coerce')
        elif 'year' in self.df.columns:
            self.df['year'] = pd.to_numeric(self.df['year'], errors='coerce')

        if 'JO' in self.df.columns:
            self.df['journal'] = self.df['JO']
        elif 'journal' not in self.df.columns:
            self.df['journal'] = ''

        if 'PB' in self.df.columns:
            self.df['publisher'] = self.df['PB']
        elif 'publisher' not in self.df.columns:
            self.df['publisher'] = ''

    def _extract_first_author(self, authors):
        if pd.isna(authors) or not authors:
            return ''
        if isinstance(authors, list):
            authors = '; '.join(authors)
        if ';' in authors:
            return authors.split(';')[0].strip()
        elif ' and ' in authors:
            return authors.split(' and ')[0].strip()
        elif ',' in authors:
            parts = authors.split(',')
            return f"{parts[0].strip()}, {parts[1].strip().split()[0]}" if len(parts) > 1 else authors.strip()
        else:
            return authors.strip()

    def calculate_statistics(self):
        if self.df is None:
            self.load_data()

        self.results['top_authors'] = self.df['first_author'].value_counts().head(15)

        if 'year' in self.df.columns and 'type' in self.df.columns:
            self.results['publications_by_year_type'] = self.df.groupby(['year', 'type']).size().unstack(fill_value=0)

        if 'type' in self.df.columns:
            self.results['publication_types'] = self.df['type'].value_counts()

        if 'journal' in self.df.columns:
            self.results['top_journals'] = self.df['journal'].value_counts().head(15)

        if 'publisher' in self.df.columns:
            self.results['top_publishers'] = self.df['publisher'].value_counts().head(15)

    def generate_visualizations(self, output_dir='output'):
        os.makedirs(output_dir, exist_ok=True)

        if self.results['top_authors'] is not None:
            plt.figure(figsize=(12, 6))
            self.results['top_authors'].plot(kind='barh', color='steelblue')
            plt.title('Top 15 Autores por Producción')
            plt.xlabel('Número de Publicaciones')
            plt.ylabel('Autor')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.savefig(f"{output_dir}/top_authors.png")
            plt.close()

        if self.results['publications_by_year_type'] is not None:
            plt.figure(figsize=(12, 6))
            self.results['publications_by_year_type'].plot(kind='bar', stacked=True)
            plt.title('Publicaciones por Año y Tipo')
            plt.xlabel('Año')
            plt.ylabel('Número de Publicaciones')
            plt.legend(title='Tipo')
            plt.tight_layout()
            plt.savefig(f"{output_dir}/publications_by_year_type.png")
            plt.close()

        if self.results['publication_types'] is not None:
            plt.figure(figsize=(8, 8))
            self.results['publication_types'].plot(kind='pie', autopct='%1.1f%%')
            plt.title('Distribución de Tipos de Publicación')
            plt.ylabel('')
            plt.tight_layout()
            plt.savefig(f"{output_dir}/publication_types.png")
            plt.close()

        if self.results['top_journals'] is not None:
            plt.figure(figsize=(12, 6))
            self.results['top_journals'].plot(kind='barh', color='green')
            plt.title('Top 15 Journals por Publicaciones')
            plt.xlabel('Número de Publicaciones')
            plt.ylabel('Journal')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.savefig(f"{output_dir}/top_journals.png")
            plt.close()

        if self.results['top_publishers'] is not None:
            plt.figure(figsize=(12, 6))
            self.results['top_publishers'].plot(kind='barh', color='purple')
            plt.title('Top 15 Publishers por Publicaciones')
            plt.xlabel('Número de Publicaciones')
            plt.ylabel('Publisher')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.savefig(f"{output_dir}/top_publishers.png")
            plt.close()

    def export_results(self, output_dir=None):
        #output_dir = r"C:/Users/erikp/OneDrive/Documentos/GitHub/ProyectoAlgoritmos/resultados/requerimiento2"
        # Directorio base: carpeta que contiene el script actual
        base_dir = Path(__file__).resolve().parent
        # Subir un nivel para llegar al nivel donde está la carpeta 'resultados' externa
        project_root = base_dir.parent
        # Definir rutas relativas desde el root del proyecto
        #ris_file = project_root / 'resultados' / 'requerimiento1' / 'resultados_unificados.ris'
        output_dir = project_root / 'resultados' / 'requerimiento2'
        os.makedirs(output_dir, exist_ok=True)

        self.generate_visualizations(output_dir)

        results_data = {
            'metadata': {
                'source_file': self.unified_file_path,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'total_publications': len(self.df)
            },
            'top_authors': self.results['top_authors'].to_dict() if self.results['top_authors'] is not None else None,
            'publications_by_year_type': self.results['publications_by_year_type'].to_dict() if self.results['publications_by_year_type'] is not None else None,
            'publication_types': self.results['publication_types'].to_dict() if self.results['publication_types'] is not None else None,
            'top_journals': self.results['top_journals'].to_dict() if self.results['top_journals'] is not None else None,
            'top_publishers': self.results['top_publishers'].to_dict() if self.results['top_publishers'] is not None else None
        }

        json_path = os.path.join(output_dir, "bibliometric_stats.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2)

        return {
            'json_file': json_path,
            'visualizations': [
                os.path.join(output_dir, fn) for fn in os.listdir(output_dir)
                if fn.endswith(".png")
            ]
        }

def main():
    print("=== Analizador Bibliométrico - Requerimiento 2 ===")
    print("Este script genera estadísticas a partir del archivo unificado\n")
    
    unified_file = 'resultados/requerimiento1/resultados_unificados.ris'
    while not os.path.exists(unified_file):
        print("Archivo no encontrado. Intente nuevamente.")
        unified_file = input("Ruta al archivo unificado (RIS o BibTeX): ").strip()

    analyzer = BibliometricAnalyzer(unified_file)
    
    print("\nProcesando datos...")
    analyzer.load_data()
    analyzer.calculate_statistics()

    print("\nGenerando reportes y visualizaciones...")
    output_files = analyzer.export_results()

    print("\n=== Proceso completado ===")
    print(f"Archivo de entrada: {unified_file}")
    print(f"Total de publicaciones procesadas: {len(analyzer.df)}")
    print("\nArchivos generados:")
    print(f"- Reporte JSON: {output_files['json_file']}")
    print("\nVisualizaciones generadas:")
    for viz in output_files['visualizations']:
        print(f"- {viz}")

if __name__ == "__main__":
    main()
