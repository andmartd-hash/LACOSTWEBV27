import streamlit as st
import pandas as pd
import os

# --- Configuración Visual ---
st.set_page_config(page_title="LACOSTWEB V27", layout="wide", page_icon="🧩")

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    required_files = ["input", "countries", "risk", "offering", "slc", "lplat", "lband", "mcbr"]
    loaded_data = {}
    missing_files = []

    for key in required_files:
        possible_names = [
            f"{key}.csv", f"{key.capitalize()}.csv", f"{key.upper()}.csv",
            f"V12-BASE.xlsx - {key}.csv", f"V12-BASE.xlsx - {key.capitalize()}.csv"
        ]
        
        file_found = False
        for filename in possible_names:
            if os.path.exists(filename):
                try:
                    df = pd.read_csv(filename)
                    # Limpiamos nombres de columnas (quita espacios extra)
                    df.columns = df.columns.str.strip() 
                    loaded_data[key] = df
                    file_found = True
                    break
                except Exception as e:
                    st.error(f"Error leyendo {filename}: {e}")
        
        if not file_found:
            missing_files.append(key)
    
    return loaded_data, missing_files

def main():
    st.title("🧩 LACOSTWEB V27 - Cotizador Dinámico")

    dfs, missing = load_data()
    
    if missing:
        st.error(f"❌ FALTAN ARCHIVOS: {', '.join(missing)}")
        st.stop()
        
    if "input" not in dfs:
        st.error("❌ Se requiere 'input.csv' para generar la vista.")
        st.stop()

    # --- 2. GENERADOR DE FORMULARIO ---
    st.info("Configuración generada desde `input.csv`")

    df_input = dfs["input"]
    seleccion_usuario = {}

    with st.form("form_cotizador"):
        col1, col2 = st.columns(2)
        
        # Obtenemos nombres de columnas del input.csv
        campos = df_input.columns
        col_nombre_campo = campos[0] # Asumimos col 0 es el Label
        
        # Intentamos detectar columna fuente (Col 1)
        col_fuente = campos[1] if len(campos) > 1 else None

        # --- CORRECCIÓN DE ERROR DUPLICATE KEY ---
        # Usamos 'enumerate' para tener un índice único (idx)
        for idx, row in df_input.iterrows():
            
            # Convertimos a string y manejamos vacíos
            label_raw = row[col_nombre_campo]
            label = str(label_raw).strip() if pd.notna(label_raw) else f"Campo_{idx}"
            
            # Llave única interna para evitar el crash
            unique_key = f"{label}_{idx}"

            donde_pintar = col1 if idx % 2 == 0 else col2
            
            # Lógica para decidir si es lista o texto
            tabla_referencia = None
            
            # 1. Chequeo por columna explicita
            if col_fuente and pd.notna(row[col_fuente]):
                nombre_tabla = str(row[col_fuente]).lower().strip()
                if nombre_tabla in dfs:
                    tabla_referencia = dfs[nombre_tabla]
            
            # 2. Chequeo por coincidencia de nombre
            if tabla_referencia is None and label.lower() in dfs:
                tabla_referencia = dfs[label.lower()]

            with donde_pintar:
                if tabla_referencia is not None:
                    # SELECTBOX
                    opciones = tabla_referencia.iloc[:, 0].unique()
                    # Usamos unique_key aquí para evitar el error
                    seleccion_usuario[label] = st.selectbox(label, options=opciones, key=unique_key)
                else:
                    # TEXT INPUT
                    # Usamos unique_key aquí para evitar el error
                    seleccion_usuario[label] = st.text_input(label, key=unique_key)

        st.markdown("---")
        # El botón de submit DEBE estar dentro del bloque 'with st.form'
        submitted = st.form_submit_button("💾 Calcular Escenario")

    # --- 3. RESULTADOS ---
    if submitted:
        st.success("✅ Datos capturados")
        st.write("Valores seleccionados:")
        st.json(seleccion_usuario)

    # --- Debug ---
    with st.expander("Ver Tablas (Admin)"):
        t = st.selectbox("Tabla", list(dfs.keys()))
        st.dataframe(dfs[t])

if __name__ == "__main__":
    main()
