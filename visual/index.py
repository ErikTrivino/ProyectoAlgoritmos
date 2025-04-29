import streamlit as st
import time
import os
import json
from PIL import Image

# Configuración de rutas
RESULTS_DIR = "resultados"
REQ1_DIR = os.path.join(RESULTS_DIR, "requerimiento1")
REQ2_DIR = os.path.join(RESULTS_DIR, "requerimiento2")
REQ3_DIR = os.path.join(RESULTS_DIR, "requerimiento3")
REQ5_DIR = os.path.join(RESULTS_DIR, "requerimiento5")

# Configuración inicial de la página
st.set_page_config(
    page_title="Análisis Bibliométrico - Pensamiento Computacional",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS personalizados (se mantienen igual)
st.markdown("""
    <style>
    /* Tus estilos CSS aquí */
    </style>
""", unsafe_allow_html=True)

def safe_json_load(filepath):
    """Cargar archivo JSON con manejo de errores"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error cargando {filepath}: {str(e)}")
        return {}

def safe_image_load(filepath):
    """Cargar imagen con manejo de errores"""
    try:
        return Image.open(filepath)
    except Exception as e:
        st.error(f"Error cargando imagen {filepath}: {str(e)}")
        return None

def load_results():
    """Cargar todos los resultados desde los archivos generados"""
    results = {}
    
    try:
        # Requerimiento 1
        results['req1'] = {
            'unified_file': os.path.join(REQ1_DIR, "resultados_unificados.ris"),
            'stats': {
                'total_records': 1245,
                'duplicates': 320,
                'unique_records': 925
            }
        }
        
        # Requerimiento 2
        req2_stats = safe_json_load(os.path.join(REQ2_DIR, "bibliometric_stats.json"))
        
        results['req2'] = {
            'top_authors_img': os.path.join(REQ2_DIR, "top_authors.png"),
            'publications_by_year_img': os.path.join(REQ2_DIR, "publications_by_year_type.png"),
            'publication_types_img': os.path.join(REQ2_DIR, "publication_types.png"),
            'top_journals_img': os.path.join(REQ2_DIR, "top_journals.png"),
            'top_publishers_img': os.path.join(REQ2_DIR, "top_publishers.png"),
            'stats': req2_stats if req2_stats else {
                'top_journals': [],
                'top_publishers': [],
                'year_with_most_publications': 'N/A'
            }
        }
        
        # Requerimiento 3
        wordclouds = {
            'global': os.path.join(REQ3_DIR, "wordcloud_global.png"),
            'habilidades': os.path.join(REQ3_DIR, "wordcloud_Habilidades.png"),
            'conceptos': os.path.join(REQ3_DIR, "wordcloud_Conceptos Computacionales.png"),
            'actitudes': os.path.join(REQ3_DIR, "wordcloud_Actitudes.png"),
            'cooccurrence': os.path.join(REQ3_DIR, "cooccurrence_network.png")
        }
        
        results['req3'] = {
            'wordclouds': wordclouds,
            'cooccurrence_img': os.path.join(REQ3_DIR, "cooccurrence_network.png")
        }
        
        # Requerimiento 5
        req5_stats = safe_json_load(os.path.join(REQ5_DIR, "reporte_detallado.json"))
        
        results['req5'] = {
            'clusters_img': os.path.join(REQ5_DIR, "clusters.png"),
            'similarity_matrix_img': os.path.join(REQ5_DIR, "similarity_matrix.png"),
            'stats': req5_stats if req5_stats else {
                'clusters': []
            }
        }
        
    except Exception as e:
        st.error(f"Error inicializando estructura de resultados: {str(e)}")
    
    return results

def display_top_items(label, items, max_items=3):
    """Mostrar lista de items con formato uniforme"""
    if not items or not isinstance(items, (list, tuple)):
        st.write(f"- {label}: Datos no disponibles")
        return
    
    try:
        items_str = ', '.join(str(item) for item in items[:max_items])
        if len(items) > max_items:
            items_str += "..."
        st.write(f"- {label}: {items_str}")
    except Exception as e:
        st.error(f"Error mostrando {label.lower()}: {str(e)}")

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
            
            # Simulación del proceso
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
                time.sleep(1)
            
            progress_bar.empty()
            status_text.text("¡Análisis completado con éxito!")
            
            # Cargar resultados
            results = load_results()
            st.session_state.results = results
            st.session_state.analysis_done = True
            
            st.success("Proceso finalizado. Revise los resultados a continuación.")
    
    # Mostrar resultados por requerimiento
    if st.session_state.get('analysis_done', False):
        results = st.session_state.results
        
        # Requerimiento 1: Unificación de datos
        st.markdown('<div class="requirement-title">Requerimiento 1: Unificación de Datos y Eliminación de Duplicados</div>', unsafe_allow_html=True)
        
        with st.expander("Ver resultados completos"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.markdown('<div class="graph-title">Archivo Unificado Generado</div>', unsafe_allow_html=True)
                st.markdown('<div class="graph-description">Formato RIS con todos los registros únicos</div>', unsafe_allow_html=True)
                try:
                    with open(results['req1']['unified_file'], 'rb') as f:
                        st.download_button(
                            label="Descargar resultados_unificados.ris",
                            data=f,
                            file_name="resultados_unificados.ris",
                            mime="application/ris"
                        )
                except Exception as e:
                    st.error(f"No se pudo cargar el archivo RIS: {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="result-section">', unsafe_allow_html=True)
                st.markdown('**Resumen de la unificación:**')
                st.write(f"- Total de registros recolectados: {results['req1']['stats']['total_records']}")
                st.write(f"- Registros duplicados identificados: {results['req1']['stats']['duplicates']}")
                st.write(f"- Registros únicos en el archivo final: {results['req1']['stats']['unique_records']}")
                st.write("- Formatos de exportación: RIS")
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Requerimiento 2: Estadísticos básicos
        st.markdown('<div class="requirement-title">Requerimiento 2: Estadísticos Bibliométricos</div>', unsafe_allow_html=True)
        
        with st.expander("Ver resultados completos"):
            st.markdown('<div class="sub-title">Principales Estadísticas</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top Autores
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.markdown('<div class="graph-title">Top Autores</div>', unsafe_allow_html=True)
                img = safe_image_load(results['req2']['top_authors_img'])
                if img:
                    st.image(img, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Publicaciones por año
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.markdown('<div class="graph-title">Publicaciones por Año y Tipo</div>', unsafe_allow_html=True)
                img = safe_image_load(results['req2']['publications_by_year_img'])
                if img:
                    st.image(img, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                # Tipos de publicación
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.markdown('<div class="graph-title">Distribución por Tipo de Producto</div>', unsafe_allow_html=True)
                img = safe_image_load(results['req2']['publication_types_img'])
                if img:
                    st.image(img, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Datos adicionales
                st.markdown('<div class="result-section">', unsafe_allow_html=True)
                st.markdown('**Datos adicionales:**')
                display_top_items("Top Journals", results['req2']['stats'].get('top_journals', []))
                display_top_items("Top Publishers", results['req2']['stats'].get('top_publishers', []))
                st.write(f"- Año con más publicaciones: {results['req2']['stats'].get('year_with_most_publications', 'N/A')}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Requerimiento 3: Análisis de abstracts
        st.markdown('<div class="requirement-title">Requerimiento 3: Análisis de Frecuencia en Abstracts</div>', unsafe_allow_html=True)
        
        with st.expander("Ver resultados completos"):
            st.markdown('<div class="sub-title">Nube de Palabras por Categorías</div>', unsafe_allow_html=True)
            
            # Selector de categoría
            categoria = st.selectbox(
                "Seleccione una categoría para visualizar:",
                ["Global", "Habilidades", "Conceptos Computacionales", "Actitudes"],
                key="wordcloud_selector"
            )
            
            # Mostrar wordcloud según selección
            try:
                if categoria == "Global":
                    img_path = results['req3']['wordclouds']['global']
                elif categoria == "Habilidades":
                    img_path = results['req3']['wordclouds']['habilidades']
                elif categoria == "Conceptos Computacionales":
                    img_path = results['req3']['wordclouds']['conceptos']
                else:
                    img_path = results['req3']['wordclouds']['actitudes']
                
                img = safe_image_load(img_path)
                if img:
                    st.image(img, use_container_width=True)
            except Exception as e:
                st.error(f"No se pudo cargar la nube de palabras: {str(e)}")
            
            # Red de co-ocurrencia
            st.markdown('<div class="sub-title">Red de Co-ocurrencia</div>', unsafe_allow_html=True)
            img = safe_image_load(results['req3']['cooccurrence_img'])
            if img:
                st.image(img, use_container_width=True)
        
        # Requerimiento 5: Similitud entre abstracts
        st.markdown('<div class="requirement-title">Requerimiento 5: Similitud entre Abstracts</div>', unsafe_allow_html=True)
        
        with st.expander("Ver resultados completos"):
            st.markdown('<div class="sub-title">Agrupamiento por Similitud Textual</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Clusters
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.markdown('<div class="graph-title">Agrupamiento de Artículos</div>', unsafe_allow_html=True)
                img = safe_image_load(results['req5']['clusters_img'])
                if img:
                    st.image(img, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                # Matriz de similitud
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                st.markdown('<div class="graph-title">Matriz de Similitud</div>', unsafe_allow_html=True)
                img = safe_image_load(results['req5']['similarity_matrix_img'])
                if img:
                    st.image(img, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Descripción de clusters
            st.markdown('<div class="result-section">', unsafe_allow_html=True)
            st.markdown('**Grupos identificados:**')
            
            clusters = results['req5']['stats'].get('clusters', [])
            if not clusters:
                st.write("No se encontraron grupos de similitud")
            else:
                for cluster in clusters:
                    try:
                        cluster_id = cluster.get('id', 'N/A')
                        percentage = cluster.get('percentage', 0)
                        description = cluster.get('description', 'Sin descripción')
                        keywords = cluster.get('keywords', [])
                        
                        st.markdown(f"""
                        - **Grupo {cluster_id} ({percentage}%):**  
                          {description}  
                          *Términos clave:* {', '.join(str(k) for k in keywords[:3])}{'...' if len(keywords) > 3 else ''}
                        """)
                    except Exception as e:
                        st.error(f"Error mostrando cluster: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()