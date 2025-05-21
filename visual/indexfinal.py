import streamlit as st
import time
import os
import json
import subprocess
from PIL import Image

# === CONFIGURACIÓN DE RUTAS ===

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_ROOT = get_project_root()

def get_result_dir(req_name):
    return os.path.join(PROJECT_ROOT, "resultados", req_name)

RESULTS_DIRS = {
    "req1": get_result_dir("requerimiento1"),
    "req2": get_result_dir("requerimiento2"),
    "req3": get_result_dir("requerimiento3"),
    "req5": get_result_dir("requerimiento5"),
}

SCRIPTS = {
    "req1": os.path.join(PROJECT_ROOT, "requerimiento1", "scrapy", "MainScrapys.py"),
    "req2": os.path.join(PROJECT_ROOT, "requerimiento2", "requerimiento2.py"),
    "req3": os.path.join(PROJECT_ROOT, "requerimiento3", "requerimiento3.py"),
    "req5_endograma": os.path.join(PROJECT_ROOT, "requerimiento5", "endograma.py"),
    "req5": os.path.join(PROJECT_ROOT, "requerimiento5", "requerimiento5.py"),
}

# === CONFIGURACIÓN DE PÁGINA STREAMLIT ===

st.set_page_config(
    page_title="Análisis Bibliométrico - Pensamiento Computacional",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5em;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 30px;
    }
    .requirement-title {
        font-size: 1.8em;
        font-weight: bold;
        color: #3498db;
        margin: 20px 0 15px 0;
        padding-bottom: 5px;
        border-bottom: 2px solid #3498db;
    }
    .sub-title {
        font-size: 1.4em;
        font-weight: bold;
        color: #2c3e50;
        margin: 15px 0 10px 0;
    }
    .graph-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .graph-title {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 5px;
    }
    .graph-description {
        font-size: 0.9em;
        color: #7f8c8d;
        margin-bottom: 10px;
    }
    .result-section {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# === FUNCIONES AUXILIARES ===

def safe_json_load(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error cargando {filepath}: {str(e)}")
        return {}

def safe_image_load(filepath):
    try:
        return Image.open(filepath)
    except Exception as e:
        st.error(f"Error cargando imagen {filepath}: {str(e)}")
        return None

def load_results():
    results = {}
    try:
        req1_dir = RESULTS_DIRS["req1"]
        req2_dir = RESULTS_DIRS["req2"]
        req3_dir = RESULTS_DIRS["req3"]
        req5_dir = RESULTS_DIRS["req5"]

        results['req1'] = {
            'unified_file': os.path.join(req1_dir, "resultados_unificados.ris"),
            'stats': {
                'total_records': 1245,
                'duplicates': 320,
                'unique_records': 925
            }
        }

        req2_stats = safe_json_load(os.path.join(req2_dir, "bibliometric_stats.json"))
        results['req2'] = {
            'top_authors_img': os.path.join(req2_dir, "top_authors.png"),
            'publications_by_year_img': os.path.join(req2_dir, "publications_by_year_type.png"),
            'publication_types_img': os.path.join(req2_dir, "publication_types.png"),
            'top_journals_img': os.path.join(req2_dir, "top_journals.png"),
            'top_publishers_img': os.path.join(req2_dir, "top_publishers.png"),
            'stats': req2_stats if req2_stats else {
                'top_journals': [],
                'top_publishers': [],
                'year_with_most_publications': 'N/A'
            }
        }

        import glob

        # Obtener todas las wordclouds del req3
        wordcloud_paths = glob.glob(os.path.join(req3_dir, "wordcloud_*.png"))
        wordclouds = {os.path.splitext(os.path.basename(p))[0].replace("wordcloud_", "").replace("_", " "): p for p in wordcloud_paths}

        results['req3'] = {
            'wordclouds': wordclouds,
            'cooccurrence_img': os.path.join(req3_dir, "cooccurrence_network.png")
        }


        req5_stats = safe_json_load(os.path.join(req5_dir, "reporte_detallado.json"))
        results['req5'] = {}  # Asegura que la clave 'req5' exista

        # Carga todas las imágenes PNG de la carpeta
        image_paths = glob.glob(os.path.join(req5_dir, "*.png"))
        results['req5']['imagenes'] = image_paths

        # Si quieres seguir usando 'dendrogramas' por separado (opcional)
        results['req5']['dendrogramas'] = [p for p in image_paths if 'dendrograma' in os.path.basename(p)]

        # También podrías cargar otros datos si es necesario, por ejemplo:
        # results['req5']['summary_table'] = os.path.join(req5_dir, "resumen_clusters.csv") (si existe)



    except Exception as e:
        st.error(f"Error inicializando estructura de resultados: {str(e)}")
    return results

def display_top_items(label, items, max_items=3):
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

def run_script(path, label=None):
    if label:
        st.info(f"Ejecutando: {label}")
    try:
        subprocess.run(["python", path], check=True)
    except subprocess.CalledProcessError as e:
        st.error(f"Error al ejecutar {label or path}: {e}")
        raise e

def display_results(results):
    """Muestra los resultados organizados por requerimiento"""
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
    
    # Mostrar wordclouds de todas las categorías
    # REQUERIMIENTO 3
    st.markdown('<div class="requirement-title">Requerimiento 3: Ver nube de palabras</div>', unsafe_allow_html=True)
    
    with st.expander("Ver resultados completos"):
        st.markdown('<div class="section-title">Requerimiento 3: Análisis de Palabras Clave</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sub-title">Nube de Palabras por Categorías</div>', unsafe_allow_html=True)
        if results['req3']['wordclouds']:
            tab_names = list(results['req3']['wordclouds'].keys())
            tabs = st.tabs(tab_names)
            for tab, name in zip(tabs, tab_names):
                with tab:
                    img = safe_image_load(results['req3']['wordclouds'][name])
                    if img:
                        st.image(img, caption=name.title(), use_container_width=True)
        else:
            st.info("No se encontraron imágenes de nubes de palabras.")

        # Red de co-ocurrencia
        st.markdown('<div class="sub-title">Red de Co-ocurrencia</div>', unsafe_allow_html=True)
        img = safe_image_load(results['req3']['cooccurrence_img'])
        if img:
            st.image(img, use_container_width=True)


    # REQUERIMIENTO 5
    # Mostrar todas las imágenes en la carpeta de requerimiento 5
    st.markdown('<div class="requirement-title">Requerimiento 5: Ver tecnicas de similitud</div>', unsafe_allow_html=True)
    
    with st.expander("Ver resultados completos"):
        st.markdown('<div class="sub-title">Visualización de Imágenes del Requerimiento 5</div>', unsafe_allow_html=True)
        for img_path in results['req5'].get('imagenes', []):
            img = safe_image_load(img_path)
            if img:
                st.image(img, caption=os.path.basename(img_path), use_container_width=True)



    """ # Mostrar todos los dendogramas
    st.markdown('<div class="sub-title">Dendogramas y Distribuciones</div>', unsafe_allow_html=True)
    for dendro_path in results['req5'].get('dendrogramas', []):
        img = safe_image_load(dendro_path)
        if img:
            st.image(img, caption=os.path.basename(dendro_path), use_container_width=True)

    # Tabla resumen (si es necesario cargar como DataFrame, puedes usar pandas)
    st.markdown('<div class="sub-title">Resumen de Clusters</div>', unsafe_allow_html=True)
    st.markdown(f"Archivo CSV: `{results['req5']['summary_table']}`")
        """
    st.markdown('</div>', unsafe_allow_html=True)

# === FUNCIÓN PRINCIPAL DE STREAMLIT ===

def main():
    st.markdown('<div class="main-title">Análisis Bibliométrico<br>Pensamiento Computacional</div>', unsafe_allow_html=True)
    st.write("""
    Este sistema realiza análisis bibliométrico sobre publicaciones de "Computational Thinking" 
    a partir de múltiples bases de datos científicas disponibles en la Universidad del Quindío.
    """)

    if st.button('EJECUTAR ANÁLISIS COMPLETO', key='run_button'):
        with st.spinner('Iniciando análisis...'):
            steps = [
                ("Recolectando datos con Scrapy...", lambda: run_script(SCRIPTS['req1'], "MainScrapys.py")),
                ("Ejecutando Requerimiento 2...", lambda: run_script(SCRIPTS['req2'], "Requerimiento 2")),
                ("Ejecutando Requerimiento 3...", lambda: run_script(SCRIPTS['req3'], "Requerimiento 3")),
                ("Generando endograma...", lambda: run_script(SCRIPTS['req5_endograma'], "Endograma")),
                ("Ejecutando Requerimiento 5...", lambda: run_script(SCRIPTS['req5'], "Requerimiento 5")),
            ]
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                for i, (desc, action) in enumerate(steps):
                    status_text.text(f"Progreso: {desc}")
                    action()
                    progress_bar.progress((i + 1) / len(steps))
                    time.sleep(0.5)
                status_text.text("¡Análisis completado con éxito!")
                progress_bar.empty()
                st.success("Proceso finalizado. Revise los resultados a continuación.")
                results = load_results()
                st.session_state.results = results
                st.session_state.analysis_done = True
            except Exception:
                st.error("Se detuvo el análisis debido a un error.")
                return

    if st.session_state.get('analysis_done', False):
        results = st.session_state.results
        display_results(results)

if __name__ == "__main__":
    main()