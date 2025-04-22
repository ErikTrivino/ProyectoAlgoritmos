import json
import re
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import networkx as nx
import os
from itertools import combinations

# Cargar la estructura de categorías desde el JSON
with open('C:/Users/erikp/OneDrive/Documentos/GitHub/ProyectoAlgoritmos/requerimiento3/categorias.json', 'r', encoding='utf-8') as f:
    categorias_data = json.load(f)

# Preparar estructura de sinónimos y categorías
sinonimos = {}
categorias = {}
for categoria in categorias_data['Categorías']:
    cat_name = categoria['nombre']
    categorias[cat_name] = []
    for variable in categoria['variables']:
        # Procesar variables con sinónimos (separados por -)
        vars_split = [v.strip() for v in variable.split('-') if v.strip()]
        primary_var = vars_split[0]
        categorias[cat_name].append(primary_var)
        for synonym in vars_split[1:]:
            sinonimos[synonym.lower()] = primary_var.lower()

# Función para parsear archivo RIS
def parse_ris_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    records = []
    current_record = {}
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('AB  - '):
            current_record['abstract'] = line[6:]
        elif line.startswith('ER  -'):
            if current_record and 'abstract' in current_record:
                records.append(current_record)
            current_record = {}
    
    return records

# Función para normalizar texto
def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)  # Remove punctuation
    return text

# Función para encontrar términos en abstracts
def find_terms_in_abstract(abstract, categoria):
    abstract_norm = normalize_text(abstract)
    terms_found = set()
    
    for term in categorias[categoria]:
        term_norm = term.lower()
        # Buscar término completo
        if re.search(r'\b' + re.escape(term_norm) + r'\b', abstract_norm):
            terms_found.add(term)
        # Buscar sinónimos
        for syn, primary in sinonimos.items():
            if primary == term_norm and re.search(r'\b' + re.escape(syn) + r'\b', abstract_norm):
                terms_found.add(term)
    
    return terms_found

# Función para generar nube de palabras
def generate_wordcloud(frequencies, title):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(frequencies)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.title(title, fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    return plt

# Función para generar gráfico de co-ocurrencia
def generate_cooccurrence_graph(cooccurrence_matrix, min_edges=5):
    G = nx.Graph()
    
    # Añadir nodos
    for term in cooccurrence_matrix.keys():
        G.add_node(term)
    
    # Añadir aristas con pesos
    for (term1, term2), count in cooccurrence_matrix.items():
        if count >= min_edges:
            G.add_edge(term1, term2, weight=count)
    
    # Dibujar el grafo
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=0.5)
    
    # Dibujar nodos
    nx.draw_networkx_nodes(G, pos, node_size=50)
    
    # Dibujar aristas
    nx.draw_networkx_edges(G, pos, alpha=0.3)
    
    # Dibujar etiquetas
    nx.draw_networkx_labels(G, pos, font_size=8)
    
    plt.title('Red de Co-ocurrencia de Términos', fontsize=14)
    plt.axis('off')
    return plt

# Procesar archivo RIS
filepath = r'C:/Users/erikp/OneDrive/Documentos/GitHub/ProyectoAlgoritmos/requerimiento1/scrapy/resultados_unificados_20250421_125021.ris'
records = parse_ris_file(filepath)

# Inicializar estructuras para frecuencias
freq_global = Counter()
freq_por_categoria = {cat: Counter() for cat in categorias.keys()}
cooccurrence_matrix = Counter()

# Procesar cada abstract
for record in records:
    abstract = record.get('abstract', '')
    if not abstract:
        continue
    
    # Encontrar términos por categoría
    terms_in_record = set()
    for categoria in categorias.keys():
        terms = find_terms_in_abstract(abstract, categoria)
        if terms:
            freq_por_categoria[categoria].update(terms)
            terms_in_record.update(terms)
    
    # Actualizar frecuencias globales
    freq_global.update(terms_in_record)
    
    # Actualizar matriz de co-ocurrencia
    for pair in combinations(sorted(terms_in_record), 2):
        cooccurrence_matrix[pair] += 1

# Generar reporte de frecuencias
print("=== FRECUENCIAS GLOBALES ===")
for term, count in freq_global.most_common():
    print(f"{term}: {count}")

print("\n=== FRECUENCIAS POR CATEGORÍA ===")
for categoria, counter in freq_por_categoria.items():
    print(f"\n{categoria}:")
    for term, count in counter.most_common():
        print(f"  {term}: {count}")

# Generar visualizaciones
output_dir = "visualizations"
os.makedirs(output_dir, exist_ok=True)

# Nube de palabras global
wc_global = generate_wordcloud(freq_global, "Nube de palabras - Global")
wc_global.savefig(os.path.join(output_dir, "wordcloud_global.png"))
wc_global.close()

# Nubes de palabras por categoría
for categoria, counter in freq_por_categoria.items():
    if counter:
        wc_cat = generate_wordcloud(counter, f"Nube de palabras - {categoria}")
        wc_cat.savefig(os.path.join(output_dir, f"wordcloud_{categoria}.png"))
        wc_cat.close()

# Gráfico de co-ocurrencia
co_graph = generate_cooccurrence_graph(cooccurrence_matrix)
co_graph.savefig(os.path.join(output_dir, "cooccurrence_network.png"))
co_graph.close()

print("\nProceso completado. Visualizaciones guardadas en:", output_dir)