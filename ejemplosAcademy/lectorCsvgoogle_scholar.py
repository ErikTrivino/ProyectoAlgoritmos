import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import networkx as nx
from collections import defaultdict

# 1. Cargar datos
df = pd.read_csv("google_scholar_results.csv")

# Mostrar estructura de los datos
print(" Primeras filas del dataset:")
print(df.head())

# 2. Estadísticas básicas
print("\n🔍 Estadísticas descriptivas:")
print(f"- Total de publicaciones: {len(df)}")
print(f"- Año más antiguo: {df['year'].min()}")
print(f"- Año más reciente: {df['year'].max()}")

# Conteo de publicaciones por año
year_counts = df['year'].value_counts().sort_index()
plt.figure(figsize=(10, 5))
year_counts.plot(kind='bar', color='skyblue')
plt.title("Publicaciones por año")
plt.xlabel("Año")
plt.ylabel("Número de publicaciones")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("publicaciones_por_año.png")  # Guardar gráfico
plt.show()

# 3. Nube de palabras de títulos
text = " ".join(df['title'].dropna())
wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.title("Nube de palabras de títulos (Computational Thinking)")
plt.savefig("nube_palabras.png")  # Guardar imagen
plt.show()

# 4. Red de coautoría (autores más frecuentes)
# Extraer autores y contar colaboraciones
author_counts = defaultdict(int)
coauthors = defaultdict(list)

for authors in df['authors'].dropna():
    authors_list = [a.strip() for a in authors.split(",")]
    for author in authors_list:
        author_counts[author] += 1
    # Registrar colaboraciones (pares de autores)
    for i in range(len(authors_list)):
        for j in range(i + 1, len(authors_list)):
            pair = tuple(sorted([authors_list[i], authors_list[j]]))
            coauthors[pair] += 1

# Top 10 autores más productivos
top_authors = pd.Series(author_counts).sort_values(ascending=False).head(10)
print("\n🏆 Top 10 autores más productivos:")
print(top_authors)

# Crear red de coautoría
G = nx.Graph()
for pair, count in coauthors.items():
    if count >= 2:  # Solo conexiones con al menos 2 colaboraciones
        G.add_edge(pair[0], pair[1], weight=count)

# Dibujar la red
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, k=0.3)
nx.draw_networkx_nodes(G, pos, node_size=200, node_color='lightblue')
nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.5)
nx.draw_networkx_labels(G, pos, font_size=8, font_family='sans-serif')
plt.title("Red de coautoría en Computational Thinking")
plt.axis("off")
plt.savefig("red_coautoria.png")  # Guardar gráfico
plt.show()

# 5. Exportar resultados a un nuevo CSV
df_analysis = pd.DataFrame({
    "author": list(author_counts.keys()),
    "publications": list(author_counts.values())
}).sort_values("publications", ascending=False)
df_analysis.to_csv("autores_publicaciones.csv", index=False)
print("\n✅ Resultados guardados en 'autores_publicaciones.csv'")