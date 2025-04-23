import json
import re
import os
import math
import numpy as np
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple

class RISAnalyzer:
    def __init__(self, ris_file_path: str):
        self.ris_file_path = ris_file_path
        self.records = []
        self.abstracts = []
        self.titles = []
        
    def load_and_preprocess_data(self):
        """Carga y prepara los datos del archivo RIS"""
        print("🔍 Cargando y procesando datos RIS...")
        self.records = self._parse_ris_file()
        self.abstracts = [r['abstract'] for r in self.records if 'abstract' in r]
        self.titles = [r.get('title', f"Artículo {i}") for i, r in enumerate(self.records) if 'abstract' in r]
        print(f"✅ {len(self.abstracts)} artículos procesados con éxito")

    def _parse_ris_file(self) -> List[Dict]:
        """Parsea el archivo RIS y devuelve los registros"""
        records = []
        current_record = {}
        
        with open(self.ris_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('TY  - '):
                    current_record = {'type': line[6:]}
                elif line.startswith('TI  - '):
                    current_record['title'] = line[6:]
                elif line.startswith('AB  - '):
                    current_record['abstract'] = line[6:]
                elif line.startswith('PY  - '):
                    current_record['year'] = line[6:]
                elif line.startswith('ER  -'):
                    if 'abstract' in current_record:
                        records.append(current_record)
                    current_record = {}
        
        return records

class SimilarityAnalyzer:
    def __init__(self, abstracts: List[str], titles: List[str]):
        self.abstracts = abstracts
        self.titles = titles
        self.vectorizer = TFIDFVectorizer()
        self.similarity_matrix = None
        self.clusters = None
        
    def analyze(self):
        """Ejecuta todo el análisis de similitud"""
        print("\n🔧 Calculando similitudes entre abstracts...")
        self.vectorizer.fit(self.abstracts)
        vectors = self.vectorizer.transform(self.abstracts)
        self.similarity_matrix = self._cosine_similarity_matrix(vectors)
        self.clusters = self._enhanced_clustering(self.similarity_matrix)
        print("✅ Análisis completado")
        
    def _cosine_similarity_matrix(self, vectors: np.ndarray) -> np.ndarray:
        """Calcula matriz de similitud coseno"""
        return np.dot(vectors, vectors.T)
    
    def _enhanced_clustering(self, similarity_matrix: np.ndarray, 
                           base_threshold: float = 0.65) -> List[int]:
        """Algoritmo de clustering mejorado"""
        n = similarity_matrix.shape[0]
        clusters = [-1] * n
        current_cluster = 0
        
        # Primera pasada: agrupamiento estricto
        for i in range(n):
            if clusters[i] == -1:
                clusters[i] = current_cluster
                for j in range(i+1, n):
                    if similarity_matrix[i,j] >= base_threshold + 0.1 and clusters[j] == -1:
                        clusters[j] = current_cluster
                current_cluster += 1
        
        # Segunda pasada: agrupamiento más flexible para documentos no asignados
        for i in range(n):
            if clusters[i] == -1:
                best_sim = -1
                best_cluster = -1
                for j in range(n):
                    if i != j and similarity_matrix[i,j] > best_sim:
                        best_sim = similarity_matrix[i,j]
                        best_cluster = clusters[j]
                
                if best_sim >= base_threshold:
                    clusters[i] = best_cluster
                else:
                    clusters[i] = current_cluster
                    current_cluster += 1
        
        return clusters

class TFIDFVectorizer:
    """Implementación mejorada de TF-IDF"""
    def __init__(self):
        self.vocab = {}
        self.idf = {}
        self.vocab_size = 0
        
    def fit(self, documents: List[str]):
        """Calcula vocabulario e IDF con optimizaciones"""
        # Preprocesamiento paralelo (mejor rendimiento)
        processed_docs = [self._preprocess(doc) for doc in documents]
        
        # Construir vocabulario
        all_terms = [term for doc in processed_docs for term in doc]
        self.vocab = {term: idx for idx, term in enumerate(set(all_terms))}
        self.vocab_size = len(self.vocab)
        
        # Calcular IDF optimizado
        doc_counts = Counter()
        for doc in processed_docs:
            doc_counts.update(set(doc))  # Contar por documento único
            
        N = len(documents)
        self.idf = {term: math.log((N + 1) / (df + 1)) + 1 for term, df in doc_counts.items()}
    
    def transform(self, documents: List[str]) -> np.ndarray:
        """Transformación optimizada a vectores TF-IDF"""
        vectors = np.zeros((len(documents), self.vocab_size))
        processed_docs = [self._preprocess(doc) for doc in documents]
        
        for doc_idx, terms in enumerate(processed_docs):
            term_counts = Counter(terms)
            for term, count in term_counts.items():
                if term in self.vocab:
                    term_idx = self.vocab[term]
                    # TF (log-normalizado) * IDF
                    vectors[doc_idx, term_idx] = (1 + math.log(count)) * self.idf.get(term, 0)
        
        # Normalización L2 optimizada
        norms = np.sqrt(np.sum(vectors**2, axis=1, keepdims=True))
        norms[norms == 0] = 1
        return vectors / norms
    
    def _preprocess(self, text: str) -> List[str]:
        """Preprocesamiento de texto optimizado"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return re.sub(r'\s+', ' ', text).strip().split()

class Visualizer:
    """Clase para visualización mejorada"""
    @staticmethod
    def plot_clusters(vectors: np.ndarray, clusters: List[int], titles: List[str]):
        """Visualización 2D con títulos representativos en la leyenda"""
        reduced = Visualizer._pca_reduction(vectors)
        
        plt.figure(figsize=(16, 12))
        plt.style.use('seaborn-v0_8-darkgrid')

        unique_clusters = sorted(set(clusters))
        colors = plt.cm.nipy_spectral(np.linspace(0, 1, len(unique_clusters)))
        
        # Prepara información para la leyenda
        legend_info = []
        
        for cluster, color in zip(unique_clusters, colors):
            mask = np.array(clusters) == cluster
            cluster_indices = np.where(mask)[0]
            cluster_vectors = reduced[cluster_indices]
            
            # Encuentra el artículo más cercano al centroide (más representativo)
            centroid = np.mean(cluster_vectors, axis=0)
            distances = np.linalg.norm(cluster_vectors - centroid, axis=1)
            closest_idx = cluster_indices[np.argmin(distances)]
            representative_title = titles[closest_idx][:50] + "..." if len(titles[closest_idx]) > 50 else titles[closest_idx]
            
            # Dibuja los puntos
            plt.scatter(
                reduced[mask, 0], reduced[mask, 1],
                c=[color],
                label=f'Grupo {cluster}: {representative_title}',
                alpha=0.85,
                s=100,
                edgecolor='white',
                linewidth=1.5,
                zorder=2
            )
            
            # Añade anotación solo si el grupo es relevante
            if len(cluster_indices) >= max(1, 0.05 * len(clusters)):
                plt.annotate(
                    f"Gr. {cluster}", 
                    xy=(centroid[0], centroid[1]),
                    xytext=(10, 10),
                    textcoords='offset points',
                    fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="black", alpha=0.9)
                )
        
        # Personaliza la leyenda
        plt.legend(
            bbox_to_anchor=(1.35, 1),
            loc='upper left',
            frameon=True,
            shadow=True,
            title="Leyenda de Grupos (Título Representativo)",
            title_fontsize=12,
            fontsize=10,
            labelspacing=1.2
        )
        
        plt.title('Agrupamiento Temático de Artículos', fontsize=18)
        plt.tight_layout()
        return plt
    
    @staticmethod
    def _pca_reduction(vectors: np.ndarray) -> np.ndarray:
        """Reducción de dimensionalidad mejorada"""
        # Centrar los datos
        centered = vectors - np.mean(vectors, axis=0)
        
        # SVD en lugar de eigen decomposition (más estable numéricamente)
        U, s, Vt = np.linalg.svd(centered, full_matrices=False)
        reduced = np.dot(centered, Vt.T[:, :2])
        
        # Escalar para mejor visualización
        reduced[:, 0] = (reduced[:, 0] - np.min(reduced[:, 0])) / (np.max(reduced[:, 0]) - np.min(reduced[:, 0])) * 2 - 1
        reduced[:, 1] = (reduced[:, 1] - np.min(reduced[:, 1])) / (np.max(reduced[:, 1]) - np.min(reduced[:, 1])) * 2 - 1
        
        return reduced

    @staticmethod
    def plot_similarity_matrix(similarity_matrix: np.ndarray):
        """Visualización de la matriz de similitud"""
        plt.figure(figsize=(10, 8))
        plt.imshow(similarity_matrix, cmap='viridis', interpolation='nearest')
        plt.colorbar(label='Similitud')
        plt.title('Matriz de Similitud entre Abstracts', pad=20)
        plt.xlabel('Índice de Documento')
        plt.ylabel('Índice de Documento')
        plt.tight_layout()
        return plt

class ReportGenerator:
    """Generador de reportes mejorados"""
    @staticmethod
    def generate_cluster_report(clusters: List[int], titles: List[str], abstracts: List[str], 
                              similarity_matrix: np.ndarray) -> Dict:
        """Genera un reporte detallado de los clusters"""
        cluster_data = defaultdict(list)
        
        for idx, cluster_id in enumerate(clusters):
            cluster_data[cluster_id].append({
                "title": titles[idx],
                "abstract_preview": abstracts[idx][:150] + "...",
                "similarity_scores": {
                    "max": float(np.max(similarity_matrix[idx])),
                    "avg": float(np.mean(similarity_matrix[idx]))
                }
            })
        
        # Estadísticas de cada cluster
        report = {
            "total_clusters": len(cluster_data),
            "average_cluster_size": len(titles) / len(cluster_data),
            "clusters": []
        }
        
        for cluster_id, items in cluster_data.items():
            cluster_similarities = []
            for i, item in enumerate(items):
                for j in range(i+1, len(items)):
                    cluster_similarities.append(similarity_matrix[i,j])
            
            report["clusters"].append({
                "id": cluster_id,
                "size": len(items),
                "average_similarity": np.mean(cluster_similarities) if cluster_similarities else 0,
                "sample_titles": [item["title"] for item in items[:3]],
                "sample_abstracts": [item["abstract_preview"] for item in items[:2]]
            })
        
        return report

def main():
    # Configuración inicial
    ris_file = 'C:/Users/erikp/OneDrive/Documentos/GitHub/ProyectoAlgoritmos/resultados/requerimiento1/resultados_unificados.ris'
    output_dir = 'C:/Users/erikp/OneDrive/Documentos/GitHub/ProyectoAlgoritmos/resultados/requerimiento5'
    os.makedirs(output_dir, exist_ok=True)
    
     # 1. Cargar y preparar datos
    print("📂 Iniciando análisis...")
    analyzer = RISAnalyzer(ris_file)
    analyzer.load_and_preprocess_data()
    
    # 2. Análisis de similitud
    similarity_analyzer = SimilarityAnalyzer(analyzer.abstracts, analyzer.titles)
    similarity_analyzer.analyze()
    
    # 3. Generar visualizaciones
    print("\n🎨 Generando visualizaciones...")
    
    # Gráfico de clusters
    cluster_plot = Visualizer.plot_clusters(
        similarity_analyzer.vectorizer.transform(analyzer.abstracts),
        similarity_analyzer.clusters,
        analyzer.titles
    )
    cluster_plot.savefig(os.path.join(output_dir, 'clusters.png'), dpi=300, bbox_inches='tight')
    cluster_plot.close()
    
    # Matriz de similitud
    matrix_plot = Visualizer.plot_similarity_matrix(similarity_analyzer.similarity_matrix)
    matrix_plot.savefig(os.path.join(output_dir, 'similarity_matrix.png'), dpi=300)
    matrix_plot.close()
    
    # 4. Generar reporte
    print("📊 Generando reporte...")
    report = ReportGenerator.generate_cluster_report(
        similarity_analyzer.clusters,
        analyzer.titles,
        analyzer.abstracts,
        similarity_analyzer.similarity_matrix
    )
    
    with open(os.path.join(output_dir, 'reporte_detallado.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 5. Resultados
    print(f"\n🎉 Análisis completado. Resultados guardados en '{output_dir}':")
    print(f"- {output_dir}/clusters.png (Visualización de grupos)")
    print(f"- {output_dir}/similarity_matrix.png (Matriz de similitud)")
    print(f"- {output_dir}/reporte_detallado.json (Reporte detallado)")
    
    # Mostrar resumen
    print("\n📝 Resumen de grupos encontrados:")
    for cluster in sorted(report["clusters"], key=lambda x: x["size"], reverse=True):
        print(f"\nGrupo {cluster['id']} ({cluster['size']} artículos)")
        print(f"Similitud promedio: {cluster['average_similarity']:.2f}")
        print("Ejemplos de títulos:")
        for title in cluster["sample_titles"]:
            print(f"- {title[:50]}...")

if __name__ == "__main__":
    main()