import streamlit as st
import time
import os
import json
import subprocess
from PIL import Image

# Directorio base del proyecto (donde se encuentra este archivo .py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuración de rutas de resultados
RESULTS_DIR = os.path.join(BASE_DIR, "resultados")
REQ1_DIR = os.path.join(RESULTS_DIR, "requerimiento1")
REQ2_DIR = os.path.join(RESULTS_DIR, "requerimiento2")
REQ3_DIR = os.path.join(RESULTS_DIR, "requerimiento3")
REQ5_DIR = os.path.join(RESULTS_DIR, "requerimiento5")

# Rutas de scripts a ejecutar (rutas relativas al BASE_DIR)
SCRIPTS = {
    "req1": os.path.join(BASE_DIR, "requerimiento1", "scrapy", "MainScrapys.py"),
    "req2": os.path.join(BASE_DIR, "requerimiento2", "requerimiento2.py"),
    "req3": os.path.join(BASE_DIR, "requerimiento3", "requerimiento3.py"),
    "req5_endograma": os.path.join(BASE_DIR, "requerimiento5", "endograma.py"),
    "req5": os.path.join(BASE_DIR, "requerimiento5", "requerimiento5.py"),
}


# Configuración de página
st.set_page_config(
    page_title="Análisis Bibliométrico - Pensamiento Computacional",
    page_icon="📊",
    layout="wide"
)

# CSS (puedes agregar el tuyo)
st.markdown("""
    <style>
    /* Tus estilos personalizados */
    </style>
""", unsafe_allow_html=True)

# Funciones auxiliares
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
        results['req1'] = {
            'unified_file': os.path.join(REQ1_DIR, "resultados_unificados.ris"),
            'stats': {
                'total_records': 1245,
                'duplicates': 320,
                'unique_records': 925
            }
        }
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

# Función principal
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

    # Aquí seguiría el código que muestra los resultados (ya incluido en tu código original)
    if st.session_state.get('analysis_done', False):
        results = st.session_state.results
        # ... (el resto de visualización ya lo tienes)

if __name__ == "__main__":
    main()
