import streamlit as st
import pandas as pd
import os

# --- Configuración Visual ---
st.set_page_config(page_title="LACOSTWEB V16", layout="wide", page_icon="🚀")

# --- 1. CONFIGURACIÓN DE ARCHIVOS V16 ---
# Aquí están los nombres EXACTOS de los archivos que subiste.
# El código buscará estos nombres largos.
FILES = {
    "config":    "V16-BASE.xlsx - UI_CONFIG.csv", # Mayúscula
    "countries": "V16-BASE.xlsx - countries.csv", # Minúscula
    "risk":      "V16-BASE.xlsx - risk.csv",      # Minúscula
    "offering":  "V16-BASE.xlsx - offering.csv",  # Minúscula
    "slc":       "V16-BASE.xlsx - slc.csv",       # Minúscula
    "lplat":     "V16-BASE.xlsx - lplat.csv",     # Minúscula
    "lband":     "V16-BASE.xlsx - lband.csv",     # Minúscula
    "mcbr":      "V16-BASE.xlsx - mcbr.csv"       # Minúscula
}

@st.cache_data
def load_data():
    data = {}
    missing = []

    for key, filename in FILES.items():
        if os.path.exists(filename):
            try:
                # Leemos el CSV
                df = pd.read_csv(filename)
                # Limpiamos espacios en los nombres de las columnas
                df.columns = df.columns.str.strip()
                # Limpiamos filas vacías
                df = df.dropna(how='all')
                data[key] = df
            except Exception as e:
                st.error(f"Error leyendo el archivo {filename}: {e}")
        else:
            missing.append(filename)
            
    return data, missing

def main():
    st.title("🚀 LACOSTWEB V16")
    st.markdown("**Andresma**, sistema listo. Versión V16.")

    # --- Carga de Datos ---
    dfs, missing = load_data()

    if missing:
        st.error("❌ FALTAN ARCHIVOS EN EL SERVIDOR")
        st.warning("El código espera estos nombres EXACTOS (V16):")
        st.code("\n".join(missing))
        st.stop()

    if "config" not in dfs:
        st.error("❌ Error: No se encuentra 'UI_CONFIG.csv'")
        st.stop()

    # --- 2. MOTOR DE UI (DINÁMICO) ---
    df_config = dfs["config"]
    
    # Identificamos columnas de configuración
    # Col 0 = Label, Col 1 = Source
    cols = df_config.columns
    col_label = cols[0]
    col_source = cols[1] if len(cols) > 1 else None

    user_inputs = {}

    with st.form("form_v16"):
        st.subheader("Configuración del Proyecto")
        
        c1, c2 = st.columns(2)

        for idx, row in df_config.iterrows():
            if pd.isna(row[col_label]): continue
            
            label = str(row[col_label]).strip()
            
            # --- BÚSQUEDA DE FUENTE DE DATOS ---
            tabla_asociada = None
            
            if col_source and pd.notna(row[col_source]):
                # Obtenemos el nombre que dice el Excel (ej: "Risk")
                nombre_excel = str(row[col_source]).strip().lower()
                
                # Buscamos en nuestras llaves (countries, risk, etc.)
                if nombre_excel in dfs:
                    tabla_asociada = dfs[nombre_excel]
                elif nombre_excel.lower() in dfs:
                    tabla_asociada = dfs[nombre_excel.lower()]

            # --- RENDERIZADO ---
            destino = c1 if idx % 2 == 0 else c2
            key_id = f"v16_{idx}_{label}"

            with destino:
                if tabla_asociada is not None:
                    # ES LISTA
                    opciones = tabla_asociada.iloc[:, 0].unique()
                    user_inputs[label] = st.selectbox(label, opciones, key=key_id)
                else:
                    # ES TEXTO
                    user_inputs[label] = st.text_input(label, key=key_id)

        st.markdown("---")
        submitted = st.form_submit_button("✅ Calcular Cotización", type="primary")

    # --- 3. RESULTADOS ---
    if submitted:
        st.success("Datos capturados correctamente:")
        st.json(user_inputs)

if __name__ == "__main__":
    main()
