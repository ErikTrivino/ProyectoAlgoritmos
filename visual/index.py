import streamlit as st
import time
import os
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Configuración inicial de la página
st.set_page_config(
    page_title="Análisis Bibliométrico - Pensamiento Computacional",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5em !important;
        color: #2e86ab;
        text-align: center;
        padding: 0.5em;
        margin-bottom: 0.5em;
    }
    .sub-title {
        font-size: 1.5em !important;
        color: #3a7ca5;
        border-bottom: 2px solid #3a7ca5;
        padding-bottom: 0.3em;
    }
    .stButton>button {
        background-color: #2e86ab;
        color: white;
        font-size: 1.2em;
        padding: 0.5em 2em;
        margin: 1em auto;
        display: block;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #1f6f96;
        transform: scale(1.05);
    }
    .progress-bar {
        margin: 2em 0;
    }
    .graph-container {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1em;
        margin-bottom: 1.5em;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .graph-title {
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5em;
    }
    .graph-description {
        font-size: 0.9em;
        color: #555;
        text-align: center;
        margin-bottom: 1em;
    }
    </style>
""", unsafe_allow_html=True)

# Función para mostrar gráficos de ejemplo (serán reemplazados por tus gráficos reales)
def generar_graficos_ejemplo():
    # Gráfico 1: Top autores
    fig1, ax1 = plt.subplots()
    autores = ['Autor A', 'Autor B', 'Autor C', 'Autor D', 'Autor E']
    publicaciones = [45, 32, 28, 22, 18]
    ax1.barh(autores, publicaciones, color='#2e86ab')
    ax1.set_title('Top 5 Autores por Publicaciones')
    
    # Gráfico 2: Publicaciones por año
    fig2, ax2 = plt.subplots()
    años = [2018, 2019, 2020, 2021, 2022]
    counts = [120, 145, 180, 210, 240]
    ax2.plot(años, counts, marker='o', color='#3a7ca5')
    ax2.set_title('Publicaciones por Año')
    ax2.grid(True)
    
    # Gráfico 3: Tipos de producto
    fig3, ax3 = plt.subplots()
    tipos = ['Artículos', 'Conferencias', 'Capítulos', 'Libros']
    sizes = [65, 20, 10, 5]
    ax3.pie(sizes, labels=tipos, autopct='%1.1f%%', colors=['#2e86ab', '#3a7ca5', '#5ab9ea', '#84d0f4'])
    ax3.set_title('Distribución por Tipo de Producto')
    
    # Gráfico 4: Word cloud (imagen de ejemplo)
    wordcloud_img = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
    
    return fig1, fig2, fig3, wordcloud_img

# Función principal
def main():
    # Título principal
    st.markdown('<div class="main-title">Análisis Bibliométrico<br>Pensamiento Computacional</div>', unsafe_allow_html=True)
    
    # Sección de introducción
    st.write("""
    Este sistema realiza análisis bibliométrico sobre publicaciones de "Computational Thinking" 
    a partir de múltiples bases de datos científicas disponibles en la Universidad del Quindío.
    """)
    
    # Botón de ejecución
    if st.button('EJECUTAR ANÁLISIS COMPLETO', key='run_button'):
        with st.spinner('Iniciando análisis...'):
            
            # Barra de progreso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulación del proceso (será reemplazado por tus scripts)
            steps = [
                "Recolectando datos de las bases de datos...",
                "Procesando y unificando información...",
                "Generando estadísticas básicas...",
                "Analizando contenido de abstracts...",
                "Creando visualizaciones...",
                "Finalizando..."
            ]
            
            for i, step in enumerate(steps):
                progress_bar.progress((i + 1) / len(steps))
                status_text.text(f"Progreso: {step}")
                time.sleep(2)  # Simulación de tiempo de procesamiento
            
            progress_bar.empty()
            status_text.text("¡Análisis completado con éxito!")
            
            # Mostrar mensaje de completado
            st.success("Proceso finalizado. Revise los resultados en las pestañas siguientes.")
            
            # Generar gráficos de ejemplo (aquí integrarás tus gráficos reales)
            fig1, fig2, fig3, wordcloud_img = generar_graficos_ejemplo()
            
            # Almacenar los gráficos en session state para mostrarlos en las pestañas
            st.session_state.fig1 = fig1
            st.session_state.fig2 = fig2
            st.session_state.fig3 = fig3
            st.session_state.wordcloud_img = wordcloud_img
            st.session_state.analysis_done = True
    
    # Mostrar pestañas con resultados (si el análisis se ha completado)
    if st.session_state.get('analysis_done', False):
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Estadísticas Básicas", 
            "📝 Análisis de Abstracts", 
            "🕸️ Red de Co-palabras", 
            "🗂️ Grupos de Similitud"
        ])
        
        with tab1:
            st.markdown('<div class="sub-title">Estadísticas Básicas</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.markdown('<div class="graph-title">Top 15 Autores</div>', unsafe_allow_html=True)
                st.markdown('<div class="graph-description">Autores con mayor número de publicaciones</div>', unsafe_allow_html=True)
                st.pyplot(st.session_state.fig1)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.markdown('<div class="graph-title">Distribución por Tipo de Producto</div>', unsafe_allow_html=True)
                st.markdown('<div class="graph-description">Porcentaje de cada tipo de publicación</div>', unsafe_allow_html=True)
                st.pyplot(st.session_state.fig3)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.markdown('<div class="graph-title">Publicaciones por Año</div>', unsafe_allow_html=True)
                st.markdown('<div class="graph-description">Evolución temporal de las publicaciones</div>', unsafe_allow_html=True)
                st.pyplot(st.session_state.fig2)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.markdown('<div class="graph-title">Top 15 Journals</div>', unsafe_allow_html=True)
                st.markdown('<div class="graph-description">Revistas con más publicaciones</div>', unsafe_allow_html=True)
                # Versión correcta
                st.image(Image.fromarray(np.random.randint(0, 255, (300, 500, 3), dtype=np.uint8), 'RGB'), use_column_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.markdown('<div class="sub-title">Análisis de Abstracts</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="graph-container">', unsafe_allow_html=True)
            st.markdown('<div class="graph-title">Nube de Palabras por Categorías</div>', unsafe_allow_html=True)
            st.markdown('<div class="graph-description">Términos más frecuentes en los abstracts organizados por categorías</div>', unsafe_allow_html=True)
            st.image(st.session_state.wordcloud_img, use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("""
            **Frecuencia de conceptos clave:**
            - **Habilidades:** Problem solving (85%), Algorithmic thinking (72%), Debug (65%)
            - **Conceptos Computacionales:** Loops (78%), Conditionals (72%), Functions (68%)
            - **Actitudes:** Motivation (82%), Engagement (75%), Self-efficacy (70%)
            """)
        
        with tab3:
            st.markdown('<div class="sub-title">Red de Co-palabras</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="graph-container">', unsafe_allow_html=True)
            st.markdown('<div class="graph-title">Keyword Co-occurrence Network</div>', unsafe_allow_html=True)
            st.markdown('<div class="graph-description">Relaciones entre términos frecuentes en los abstracts</div>', unsafe_allow_html=True)
            st.image(Image.fromarray(np.random.randint(0, 255, (300, 500, 3), dtype=np.uint8), 'RGB'), use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("""
            **Interpretación:**
            - Los nodos representan palabras clave encontradas en los abstracts
            - Las conexiones muestran co-ocurrencia en los mismos documentos
            - El tamaño del nodo indica frecuencia de aparición
            - El grosor de la línea indica fuerza de la relación
            """)
        
        with tab4:
            st.markdown('<div class="sub-title">Grupos de Artículos por Similitud</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="graph-container">', unsafe_allow_html=True)
            st.markdown('<div class="graph-title">Agrupamiento por Similitud de Abstracts</div>', unsafe_allow_html=True)
            st.markdown('<div class="graph-description">Grupos temáticos identificados mediante análisis de similitud textual</div>', unsafe_allow_html=True)
            # Versión correcta
            st.image(Image.fromarray(np.random.randint(0, 255, (300, 500, 3), dtype=np.uint8), 'RGB'), use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("""
            **Grupos identificados:**
            1. Enseñanza de programación en educación básica (32%)
            2. Evaluación de habilidades computacionales (28%)
            3. Herramientas tecnológicas para CT (22%)
            4. Aspectos psicológicos y motivacionales (18%)
            """)

if __name__ == "__main__":
    main()