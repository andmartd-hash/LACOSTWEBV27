import streamlit as st
import pandas as pd
import os

# --- Configuración ---
st.set_page_config(page_title="LACOSTWEB V15", layout="wide", page_icon="⚡")

# --- 1. CONFIGURACIÓN DE NOMBRES DE ARCHIVO ---
# Ajustado a tu solicitud: Todo en minúscula, excepto UI_CONFIG.csv
FILES = {
    "config":    "UI_CONFIG.csv",   # <--- Único en mayúsculas
    "countries": "countries.csv",   # Minúscula
    "risk":      "risk.csv",        # Minúscula
    "offering":  "offering.csv",    # Minúscula
    "slc":       "slc.csv",         # Minúscula
    "lplat":     "lplat.csv",       # Minúscula
    "lband":     "lband.csv",       # Minúscula
    "mcbr":      "mcbr.csv"         # Minúscula
}

@st.cache_data
def load_data():
    data = {}
    missing = []

    for key, filename in FILES.items():
        if os.path.exists(filename):
            try:
                df = pd.read_csv(filename)
                # Limpieza estándar
                df.columns = df.columns.str.strip()
                df = df.dropna(how='all')
                data[key] = df
            except Exception as e:
                st.error(f"Error leyendo {filename}: {e}")
        else:
            missing.append(filename)
            
    return data, missing

def main():
    st.title("⚡ LACOSTWEB V15")

    # Carga de datos
    dfs, missing = load_data()

    if missing:
        st.error("❌ FALTAN ARCHIVOS (Revisa mayúsculas/minúsculas):")
        st.code("\n".join(missing))
        st.warning("Asegúrate de renombrar tus archivos en GitHub exactamente como se muestra arriba.")
        st.stop()

    if "config" not in dfs:
        st.error("❌ Falta UI_CONFIG.csv")
        st.stop()

    # --- 2. GENERADOR DE FORMULARIO ---
    df_config = dfs["config"]
    
    # Asumimos Col 0 = Label, Col 1 = Source
    cols = df_config.columns
    col_label = cols[0]
    col_source = cols[1] if len(cols) > 1 else None

    user_inputs = {}

    with st.form("form_v15"):
        st.subheader("Datos del Escenario")
        
        c1, c2 = st.columns(2)

        for idx, row in df_config.iterrows():
            if pd.isna(row[col_label]): continue
            
            label = str(row[col_label]).strip()
            
            # Buscar tabla asociada para lista desplegable
            tabla_fuente = None
            if col_source and pd.notna(row[col_source]):
                # Convertimos lo que dice el Excel a minúscula para buscar la llave
                nombre_fuente = str(row[col_source]).strip().lower()
                
                # Buscamos en las tablas cargadas
                if nombre_fuente in dfs:
                    tabla_fuente = dfs[nombre_fuente]
                # Intento extra: a veces el excel dice "Risk" y la llave es "risk"
                elif nombre_fuente.lower() in dfs:
                    tabla_fuente = dfs[nombre_fuente.lower()]

            # Renderizar
            col_destino = c1 if idx % 2 == 0 else c2
            unique_key = f"field_{idx}"

            with col_destino:
                if tabla_fuente is not None:
                    # SELECTBOX
                    opciones = tabla_fuente.iloc[:, 0].unique()
                    user_inputs[label] = st.selectbox(label, opciones, key=unique_key)
                else:
                    # TEXT INPUT
                    user_inputs[label] = st.text_input(label, key=unique_key)

        st.markdown("---")
        submitted = st.form_submit_button("✅ Procesar", type="primary")

    if submitted:
        st.success("Datos capturados:")
        st.json(user_inputs)

if __name__ == "__main__":
    main()
