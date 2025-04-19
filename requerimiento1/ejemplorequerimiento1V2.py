import pandas as pd
import json
from typing import List, Dict, Union
import hashlib
import os
import difflib
from unidecode import unidecode
import matplotlib.pyplot as plt

class BibliographicUnifier:
    def __init__(self, similarity_threshold=0.85):
        self.unique_entries = []
        self.duplicate_entries = []
        self.seen_hashes = set()
        self.similarity_threshold = similarity_threshold
        self.duplicate_stats = {
            'exact_duplicates': 0,
            'similar_duplicates': 0,
            'potential_duplicates': 0
        }
    
    def normalize_text(self, text: str) -> str:
        """Normaliza texto para comparación"""
        if not isinstance(text, str):
            return ""
        text = unidecode(text)  # Elimina acentos y caracteres especiales
        text = text.lower().strip()
        # Elimina palabras comunes que no aportan a la unicidad
        stop_words = {'the', 'and', 'of', 'in', 'a', 'an', 'to', 'for'}
        words = [word for word in text.split() if word not in stop_words]
        return " ".join(words)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos usando SequenceMatcher"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def generate_entry_signature(self, entry: Dict) -> Dict:
        """Crea una firma normalizada para comparación"""
        return {
            'title': self.normalize_text(entry.get('title', '')),
            'authors': self.normalize_text(entry.get('authors', '')),
            'year': str(entry.get('year', '')).strip(),
            'journal': self.normalize_text(entry.get('journal', ''))
        }
    
    def is_duplicate(self, entry1: Dict, entry2: Dict) -> bool:
        """Determina si dos entradas son duplicados"""
        sig1 = self.generate_entry_signature(entry1)
        sig2 = self.generate_entry_signature(entry2)
        
        # Comparación exacta
        if sig1 == sig2:
            self.duplicate_stats['exact_duplicates'] += 1
            return True
        
        # Comparación de título (umbral alto)
        title_sim = self.calculate_similarity(sig1['title'], sig2['title'])
        if title_sim > self.similarity_threshold:
            # Verificar autores y año
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
        """Encuentra índices de entradas duplicadas"""
        duplicates = []
        for idx, existing_entry in enumerate(self.unique_entries):
            if self.is_duplicate(new_entry, existing_entry):
                duplicates.append(idx)
        return duplicates
    
    def add_entry(self, entry: Dict, source: str) -> None:
        """Añade una entrada, detectando duplicados"""
        entry['source'] = source
        duplicates = self.find_duplicates(entry)
        
        if duplicates:
            # Añadir a duplicados
            self.duplicate_entries.append(entry)
            # Añadir información sobre los originales
            entry['duplicate_of'] = [self.unique_entries[i]['title'] for i in duplicates]
        else:
            # Es único, añadir a la lista principal
            self.unique_entries.append(entry)
    
    def load_data_from_csv(self, filepath: str, source: str) -> None:
        """Carga datos desde CSV con manejo de errores"""
        try:
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
        except Exception as e:
            print(f"Error al cargar {filepath}: {str(e)}")
    
    def visualize_duplicates(self):
        """Genera visualización de estadísticas de duplicados"""
        labels = ['Exactos', 'Similares', 'Potenciales']
        values = [
            self.duplicate_stats['exact_duplicates'],
            self.duplicate_stats['similar_duplicates'],
            self.duplicate_stats['potential_duplicates']
        ]
        
        plt.figure(figsize=(8, 6))
        bars = plt.bar(labels, values, color=['#ff9999','#66b3ff','#99ff99'])
        plt.title('Tipos de Duplicados Detectados')
        plt.ylabel('Cantidad')
        
        # Añadir valores en las barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.savefig('duplicate_stats.png')
        plt.close()
    
    def export_results(self):
        """Exporta todos los resultados"""
        # Exportar archivos principales
        self.export_to_ris(self.unique_entries, 'unified_results.ris')
        self.export_to_ris(self.duplicate_entries, 'duplicate_entries.ris')
        
        # Exportar reporte de duplicados detallado
        self.export_duplicates_report()
        
        # Generar visualización
        self.visualize_duplicates()
    
    def export_duplicates_report(self):
        """Exporta un reporte detallado de duplicados"""
        report = []
        for dup in self.duplicate_entries:
            report.append({
                'duplicate_title': dup['title'],
                'duplicate_authors': dup['authors'],
                'duplicate_source': dup['source'],
                'original_titles': dup.get('duplicate_of', []),
                'match_type': self.get_match_type(dup)
            })
        
        df = pd.DataFrame(report)
        df.to_csv('duplicates_detailed_report.csv', index=False)
    
    def get_match_type(self, entry: Dict) -> str:
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

    # (Los métodos export_to_ris y export_to_bibtex permanecen iguales que antes)
    # ... [resto de métodos de exportación] ...

def main():
    print("=== Procesador de Datos Bibliográficos ===")
    print("Configurando unificador...")
    
    # Configuración ajustable
    similarity_threshold = 0.85  # Puedes ajustar este valor entre 0.7 y 0.95
    
    unifier = BibliographicUnifier(similarity_threshold=similarity_threshold)
    
    # Cargar datos de ejemplo (reemplaza con tus archivos reales)
    sample_data = {
        'scopus_sample.csv': [
            {'title': 'Computational Thinking', 'authors': 'Wing, J.M.', 'year': '2006', 
             'journal': 'Communications of the ACM', 'doi': '10.1145/1118178.1118215'},
            {'title': 'Demystifying computational thinking', 'authors': 'Shute, V.J.; Sun, C.', 
             'year': '2017', 'journal': 'Educational Research Review'}
        ],
        'wos_sample.csv': [
            {'title': 'Computational Thinking', 'authors': 'Wing, Jeannette M.', 
             'year': '2006', 'journal': 'COMMUN ACM', 'doi': '10.1145/1118178.1118215'},
            {'title': 'The concept of computational thinking', 'authors': 'Smith, John', 
             'year': '2018', 'journal': 'Computer Science Education'}
        ]
    }
    
    # Crear archivos de muestra
    for filename, data in sample_data.items():
        pd.DataFrame(data).to_csv(filename, index=False)
    
    # Procesar archivos
    for filename in sample_data.keys():
        if os.path.exists(filename):
            print(f"\nProcesando {filename}...")
            unifier.load_data_from_csv(filename, filename.split('_')[0])
    
    # Exportar resultados
    print("\nExportando resultados...")
    unifier.export_results()
    
    # Mostrar resumen
    print("\n=== Resumen Final ===")
    print(f"Entradas únicas: {len(unifier.unique_entries)}")
    print(f"Entradas duplicadas: {len(unifier.duplicate_entries)}")
    print("\nEstadísticas de duplicados:")
    print(f"- Exactos: {unifier.duplicate_stats['exact_duplicates']}")
    print(f"- Similares: {unifier.duplicate_stats['similar_duplicates']}")
    print(f"- Potenciales: {unifier.duplicate_stats['potential_duplicates']}")
    print("\nArchivos generados:")
    print("- unified_results.ris (entradas únicas)")
    print("- duplicate_entries.ris (entradas duplicadas)")
    print("- duplicates_detailed_report.csv (reporte detallado)")
    print("- duplicate_stats.png (visualización)")

if __name__ == "__main__":
    main()