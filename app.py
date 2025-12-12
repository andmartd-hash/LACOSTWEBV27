import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="LACOSTWEB V16", layout="wide", page_icon="🕵️")

# --- FUNCIÓN DE BÚSQUEDA INTELIGENTE ---
def find_file_by_keyword(keyword, file_list):
    """Busca un archivo que contenga la palabra clave (sin importar mayúsculas/minúsculas)"""
    for filename in file_list:
        if keyword.lower() in filename.lower() and filename.endswith(".csv"):
            return filename
    return None

@st.cache_data
def load_data():
    # 1. Obtenemos la lista REAL de archivos en el servidor
    all_files = os.listdir('.')
    
    # 2. Definimos qué buscar (palabras clave)
    keywords = {
        "config":    "ui_config", # Buscará algo que diga "ui_config"
        "countries": "countries",
        "risk":      "risk",
        "offering":  "offering",
        "slc":       "slc",
        "lplat":     "lplat",
        "lband":     "lband",
        "mcbr":      "mcbr"
    }

    data = {}
    missing = []
    found_files_log = {}

    for key, search_term in keywords.items():
        # Usamos la función inteligente
        found_filename = find_file_by_keyword(search_term, all_files)
        
        if found_filename:
            try:
                df = pd.read_csv(found_filename)
                df.columns = df.columns.str.strip()
                df = df.dropna(how='all')
                data[key] = df
                found_files_log[key] = found_filename
            except Exception as e:
                st.error(f"Error leyendo {found_filename}: {e}")
        else:
            missing.append(search_term)
            
    return data, missing, all_files, found_files_log

def main():
    st.title("🕵️ LACOSTWEB - Auto-Detector")

    # Carga datos
    dfs, missing, all_files, log = load_data()

    # --- DIAGNÓSTICO ---
    if missing:
        st.error("❌ AÚN FALTAN ARCHIVOS")
        st.write("El sistema buscó archivos que tuvieran estas palabras pero no encontró nada:")
        st.code("\n".join(missing))
        
        st.warning("🧐 ESTO ES LO QUE REALMENTE HAY EN EL SERVIDOR (Mira los nombres):")
        st.code("\n".join(all_files))
        st.stop()

    # Si todo cargó, mostramos qué archivos encontró para tu tranquilidad
    with st.expander("✅ Archivos Detectados Correctamente (Click para ver detalles)"):
        st.write(log)

    if "config" not in dfs:
        st.error("❌ Error: Se encontraron archivos, pero no la configuración UI_CONFIG.")
        st.stop()

    # --- MOTOR DE LA APP ---
    df_config = dfs["config"]
    cols = df_config.columns
    col_label = cols[0]
    col_source = cols[1] if len(cols) > 1 else None

    user_inputs = {}

    with st.form("auto_form"):
        st.subheader("Configuración del Escenario")
        c1, c2 = st.columns(2)

        for idx, row in df_config.iterrows():
            if pd.isna(row[col_label]): continue
            label = str(row[col_label]).strip()
            
            # Búsqueda de fuente
            tabla_asociada = None
            if col_source and pd.notna(row[col_source]):
                nombre_excel = str(row[col_source]).strip().lower()
                
                # Buscamos en las llaves cargadas
                if nombre_excel in dfs:
                    tabla_asociada = dfs[nombre_excel]
                elif nombre_excel.lower() in dfs:
                    tabla_asociada = dfs[nombre_excel.lower()]

            # Renderizar
            destino = c1 if idx % 2 == 0 else c2
            key_id = f"input_{idx}"

            with destino:
                if tabla_asociada is not None:
                    opciones = tabla_asociada.iloc[:, 0].unique()
                    user_inputs[label] = st.selectbox(label, opciones, key=key_id)
                else:
                    user_inputs[label] = st.text_input(label, key=key_id)

        st.markdown("---")
        if st.form_submit_button("✅ Calcular"):
            st.success("Datos capturados:")
            st.json(user_inputs)

if __name__ == "__main__":
    main()
