import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="LACOSTWEB V14", layout="wide", page_icon="🏗️")

# --- 1. MAPEO EXACTO DE TUS ARCHIVOS V14 ---
# Aquí le decimos al código cómo se llaman tus archivos reales
FILE_MAP = {
    "ui_config": "V14-BASE.xlsx - UI_CONFIG.csv",
    "countries": "V14-BASE.xlsx - countries.csv",
    "risk":      "V14-BASE.xlsx - Risk.csv",
    "offering":  "V14-BASE.xlsx - Offering.csv",
    "slc":       "V14-BASE.xlsx - SLC.csv",
    "lplat":     "V14-BASE.xlsx - Lplat.csv",
    "lband":     "V14-BASE.xlsx - Lband.csv",
    "mcbr":      "V14-BASE.xlsx - MCBR.csv"
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
                # Limpiamos espacios en blanco en los nombres de las columnas
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
    
    # Validación estricta
    if missing:
        st.error("❌ FALTAN ARCHIVOS EN EL SERVIDOR:")
        st.code("\n".join(missing))
        st.warning("Sube los archivos con los nombres EXACTOS 'V14-BASE.xlsx - ...'")
        st.stop()

    if "ui_config" not in dfs:
        st.error("❌ Error: No se pudo leer UI_CONFIG. La app no puede iniciarse.")
        st.stop()

    # --- 2. MOTOR DE RENDERIZADO (OBEDECE A UI_CONFIG) ---
    df_config = dfs["ui_config"]
    
    # Asumimos estructura del UI_CONFIG:
    # Columna 0: LABEL (Nombre del campo)
    # Columna 1: SOURCE (Nombre de la tabla fuente, si aplica)
    # Columna 2: TYPE (Opcional, tipo de dato)
    
    cols_config = df_config.columns
    col_label_name = cols_config[0]
    col_source_name = cols_config[1] if len(cols_config) > 1 else None

    user_inputs = {}

    with st.form("main_form"):
        st.subheader("Configuración del Escenario")
        
        # Grid de 2 columnas
        c1, c2 = st.columns(2)

        for idx, row in df_config.iterrows():
            # 1. Obtener la etiqueta del campo
            raw_label = row[col_label_name]
            if pd.isna(raw_label): continue
            label = str(raw_label).strip()
            
            # Key única para Streamlit
            unique_key = f"input_{idx}_{label}"
            
            # 2. Determinar si tiene una fuente de datos asociada
            source_table = None
            if col_source_name and pd.notna(row[col_source_name]):
                source_key = str(row[col_source_name]).strip()
                
                # Buscamos coincidencias en los archivos cargados (case insensitive)
                for k in dfs.keys():
                    if k.lower() == source_key.lower():
                        source_table = dfs[k]
                        break
            
            # 3. Renderizar el Widget
            target_col = c1 if idx % 2 == 0 else c2
            
            with target_col:
                if source_table is not None:
                    # CASO: ES UNA LISTA (Dropdown)
                    # Tomamos la primera columna de la tabla fuente como opciones
                    options = source_table.iloc[:, 0].unique()
                    user_inputs[label] = st.selectbox(label, options, key=unique_key)
                else:
                    # CASO: ES TEXTO/NUMERO (Input manual)
                    user_inputs[label] = st.text_input(label, key=unique_key)

        st.markdown("---")
        submitted = st.form_submit_button("✅ Generar Cotización", type="primary")

    # --- 3. PROCESAMIENTO ---
    if submitted:
        st.success("Datos capturados:")
        st.json(user_inputs)
        
        # Aquí puedes agregar la lógica matemática después si la necesitas
        # Ejemplo: costo = float(user_inputs.get("Costo", 0)) * ...

    # --- DEBUG: Ver qué cargó el sistema ---
    with st.expander("Ver Tablas Maestras (Debug)"):
        st.write(f"Archivos cargados: {list(dfs.keys())}")
        sel = st.selectbox("Ver contenido de:", list(dfs.keys()))
        st.dataframe(dfs[sel], use_container_width=True)

if __name__ == "__main__":
    main()
