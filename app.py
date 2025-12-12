import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="LACOSTWEB V14", layout="wide", page_icon="🏗️")

# --- 1. MAPEO DE NOMBRES CORTOS ---
# El código buscará estos archivos EXACTOS en tu repositorio.
FILE_MAP = {
    "ui_config": "UI_CONFIG.csv",   # ESTE EN MAYÚSCULA
    "countries": "countries.csv",   # El resto en minúscula
    "risk":      "risk.csv",
    "offering":  "offering.csv",
    "slc":       "slc.csv",
    "lplat":     "lplat.csv",
    "lband":     "lband.csv",
    "mcbr":      "mcbr.csv"
}

@st.cache_data
def load_data():
    loaded_data = {}
    missing_files = []

    for key, filename in FILE_MAP.items():
        if os.path.exists(filename):
            try:
                # Leemos el CSV
                df = pd.read_csv(filename)
                # Limpiamos espacios en blanco en columnas
                df.columns = df.columns.str.strip()
                # Eliminamos filas vacías
                df = df.dropna(how='all')
                loaded_data[key] = df
            except Exception as e:
                st.error(f"Error leyendo {filename}: {e}")
        else:
            missing_files.append(filename)
    
    return loaded_data, missing_files

def main():
    st.title("🏗️ LACOSTWEB V14")

    # Cargar datos
    dfs, missing = load_data()
    
    # Validación
    if missing:
        st.error("❌ NO ENCUENTRO LOS ARCHIVOS:")
        st.code("\n".join(missing))
        st.warning("⚠️ IMPORTANTE: Debes renombrar tus archivos en GitHub para que coincidan con esta lista (minúsculas).")
        st.write("Archivos que SÍ veo actualmente en la carpeta:", os.listdir('.'))
        st.stop()

    if "ui_config" not in dfs:
        st.error("❌ Error: No se pudo leer UI_CONFIG.csv")
        st.stop()

    # --- 2. MOTOR DINÁMICO ---
    df_config = dfs["ui_config"]
    
    # Asumimos estructura: Col 0 = Label, Col 1 = Source
    cols_config = df_config.columns
    col_label_name = cols_config[0]
    col_source_name = cols_config[1] if len(cols_config) > 1 else None

    user_inputs = {}

    with st.form("main_form"):
        st.subheader("Datos del Proyecto")
        
        c1, c2 = st.columns(2)

        for idx, row in df_config.iterrows():
            raw_label = row[col_label_name]
            if pd.isna(raw_label): continue
            label = str(raw_label).strip()
            
            unique_key = f"in_{idx}_{label}"
            
            # Buscar fuente de datos
            source_table = None
            if col_source_name and pd.notna(row[col_source_name]):
                source_key = str(row[col_source_name]).strip().lower() # Convertimos a minúscula para buscar
                
                # Buscamos en el diccionario de datos cargados
                if source_key in dfs: # Búsqueda directa (ej: 'risk')
                    source_table = dfs[source_key]
                elif source_key.lower() in dfs: # Búsqueda de seguridad
                    source_table = dfs[source_key.lower()]

            # Renderizar
            target_col = c1 if idx % 2 == 0 else c2
            with target_col:
                if source_table is not None:
                    # SELECTBOX
                    options = source_table.iloc[:, 0].unique()
                    user_inputs[label] = st.selectbox(label, options, key=unique_key)
                else:
                    # TEXT INPUT
                    user_inputs[label] = st.text_input(label, key=unique_key)

        st.markdown("---")
        submitted = st.form_submit_button("✅ Calcular", type="primary")

    if submitted:
        st.success("Información capturada:")
        st.json(user_inputs)

if __name__ == "__main__":
    main()
