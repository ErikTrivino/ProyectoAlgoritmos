# -*- coding: utf-8 -*-
import os
import re
import string
from pathlib import Path
from collections import Counter

import matplotlib.pyplot as plt
import nltk
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import linkage, dendrogram

# === DESCARGA DE STOPWORDS ===
nltk.download('stopwords')
STOPWORDS = set(nltk.corpus.stopwords.words('english'))
PUNCT_RE = re.compile(f"[{re.escape(string.punctuation)}]")

# === CONFIGURACIÓN DE PATHS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

RIS_PATH = os.path.join(PROJECT_ROOT, "resultados", "requerimiento1", "resultados_unificados.ris")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "resultados", "requerimiento5")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# === LECTURA Y EXTRACCIÓN DE ABSTRACTS DESDE .RIS ===
abstracts = []
with open(RIS_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith("AB  - "):
            abstracts.append(line.replace("AB  - ", "").strip())

print(f"Se extrajeron {len(abstracts)} abstracts del archivo .ris")

# === PREPROCESAMIENTO ===
def preprocess_text(text):
    text = text.lower()
    text = PUNCT_RE.sub(" ", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS]
    return " ".join(tokens)

cleaned_abstracts = [preprocess_text(a) for a in abstracts]

# === GUARDAR ARCHIVOS PREPROCESADOS ===
preproc_file = os.path.join(OUTPUT_DIR, "preprocessed_abstracts.txt")
with open(preproc_file, 'w', encoding='utf-8') as f:
    for doc in cleaned_abstracts:
        f.write(doc + "\n")
print(f"Abstracts preprocesados guardados en: {preproc_file}")

# === VECTORIZACIÓN Y DENDROGRAMAS ===

# TF-IDF
X_tfidf = TfidfVectorizer().fit_transform(cleaned_abstracts)
dist_tfidf = 1 - cosine_similarity(X_tfidf)
Z1 = linkage(dist_tfidf, method='single')
plt.figure(figsize=(10, 6))
dendrogram(Z1)
plt.title("Dendrograma TF-IDF (Single Linkage)")
plt.savefig(os.path.join(OUTPUT_DIR, "dendrograma_algoritmo_uno.png"))
plt.close()

# CountVectorizer
X_count = CountVectorizer().fit_transform(cleaned_abstracts).toarray()
dist_count = 1 - cosine_similarity(X_count)
Z2 = linkage(dist_count, method='complete')
plt.figure(figsize=(10, 6))
dendrogram(Z2)
plt.title("Dendrograma CountVectorizer (Complete Linkage)")
plt.savefig(os.path.join(OUTPUT_DIR, "dendrograma_algoritmo_dos.png"))
plt.close()

# === DENDROGRAMA JERÁRQUICO TRUNCADO ===
Z = linkage(dist_count, method='complete')
plt.figure(figsize=(12, 8))
dendrogram(Z, truncate_mode='lastp', p=30)
plt.title('Dendrograma Jerárquico')
plt.xlabel('Índice del Abstract')
plt.ylabel('Distancia')
plt.savefig(os.path.join(OUTPUT_DIR, "dendrograma_jerarquico.png"))
plt.close()

# === CLUSTERING Y ANÁLISIS DE PALABRAS ===
for n_clusters in [4, 6, 8, 10]:
    clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage='complete')
    labels = clustering.fit_predict(dist_count)

    unique, counts = np.unique(labels, return_counts=True)
    print(f"\nDistribución con {n_clusters} clusters:")
    for cluster_id, count in dict(zip(unique, counts)).items():
        print(f"  Cluster {cluster_id}: {count} abstracts")

    clusters = {i: [] for i in range(n_clusters)}
    for i, label in enumerate(labels):
        clusters[label].append(abstracts[i])

    for cluster_id, cluster_abstracts in clusters.items():
        if len(cluster_abstracts) >= 5:
            print(f"\nCluster {cluster_id} - {len(cluster_abstracts)} abstracts")
            words = " ".join(cluster_abstracts).split()
            common = Counter(words).most_common(10)
            print("Palabras más frecuentes:")
            for word, count in common:
                print(f"  {word}: {count}")
            print("\nEjemplo de abstract:")
            print(cluster_abstracts[0][:150] + "...")

# === HISTOGRAMA DE CLUSTERS (USANDO 8) ===
n_clusters = 8
labels = AgglomerativeClustering(n_clusters=n_clusters, linkage='complete').fit_predict(dist_count)
plt.figure(figsize=(10, 6))
plt.hist(labels, bins=n_clusters, alpha=0.7)
plt.title(f'Distribución de Abstracts por Cluster (n={n_clusters})')
plt.xlabel('Cluster')
plt.ylabel('Número de Abstracts')
plt.xticks(range(n_clusters))
plt.savefig(os.path.join(OUTPUT_DIR, "distribucion_clusters_optimizado.png"))
plt.close()
