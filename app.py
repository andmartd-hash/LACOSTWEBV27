import streamlit as st
import pandas as pd
import os

# --- Configuración Inicial ---
st.set_page_config(page_title="LACOSTWEB V14", layout="wide", page_icon="🛠️")

# --- 1. DEFINICIÓN DE ARCHIVOS (Tal cual lo pediste) ---
# El código buscará estos nombres EXACTOS en tu carpeta de GitHub.
FILES = {
    "config":    "UI_CONFIG.csv",  # El único en mayúsculas
    "countries": "countries.csv",  # Todo el resto en minúsculas
    "risk":      "risk.csv",
    "offering":  "offering.csv",
    "slc":       "slc.csv",
    "lplat":     "lplat.csv",
    "lband":     "lband.csv",
    "mcbr":      "mcbr.csv"
}

@st.cache_data
def load_data():
    data = {}
    missing = []

    for key, filename in FILES.items():
        if os.path.exists(filename):
            try:
                # Leemos el archivo
                df = pd.read_csv(filename)
                # Limpiamos nombres de columnas (quita espacios invisibles)
                df.columns = df.columns.str.strip()
                # Eliminamos filas vacías que a veces quedan en Excel
                df = df.dropna(how='all')
                data[key] = df
            except Exception as e:
                st.error(f"Error leyendo {filename}: {e}")
        else:
            missing.append(filename)
            
    return data, missing

def main():
    st.title("🛠️ LACOSTWEB V14")

    # Carga de tablas
    dfs, missing = load_data()

    # Si faltan archivos, avisamos y paramos.
    if missing:
        st.error("❌ FALTAN ARCHIVOS EN GITHUB")
        st.warning("Por favor, asegúrate de que tus archivos en GitHub tengan ESTOS nombres exactos:")
        st.code("\n".join(missing))
        st.stop()

    if "config" not in dfs:
        st.error("❌ Falta el archivo UI_CONFIG.csv")
        st.stop()

    # --- 2. GENERACIÓN DE CAMPOS (MOTOR DE LA TOOL) ---
    # Usamos UI_CONFIG para saber qué campos pintar.
    df_config = dfs["config"]
    
    # Asumimos:
    # Columna 0 = Nombre del Campo (Label)
    # Columna 1 = Tabla Fuente (Source) - opcional
    cols = df_config.columns
    col_label = cols[0]
    col_source = cols[1] if len(cols) > 1 else None

    # Diccionario para guardar lo que el usuario escriba/seleccione
    inputs_usuario = {}

    with st.form("cotizador_form"):
        st.subheader("Configuración del Escenario")
        
        # Grid de 2 columnas para que se vea ordenado
        c1, c2 = st.columns(2)

        for idx, row in df_config.iterrows():
            # Validación básica para no procesar filas vacías
            if pd.isna(row[col_label]): continue
            
            label_campo = str(row[col_label]).strip()
            
            # Buscamos si este campo debe ser una lista desplegable
            tabla_fuente = None
            
            # LÓGICA:
            # 1. Miramos si la columna 'Fuente' del excel dice algo (ej: "Risk")
            # 2. Convertimos eso a minúscula ("risk") y buscamos si tenemos ese archivo cargado.
            if col_source and pd.notna(row[col_source]):
                nombre_fuente = str(row[col_source]).strip().lower()
                if nombre_fuente in dfs:
                    tabla_fuente = dfs[nombre_fuente]
            
            # Renderizamos el campo en la columna 1 o 2 (intercalado)
            col_destino = c1 if idx % 2 == 0 else c2
            key_unica = f"field_{idx}" # ID interno para Streamlit

            with col_destino:
                if tabla_fuente is not None:
                    # ES LISTA (DROPDOWN)
                    # Tomamos la primera columna de esa tabla como las opciones
                    opciones = tabla_fuente.iloc[:, 0].unique()
                    inputs_usuario[label_campo] = st.selectbox(label_campo, opciones, key=key_unica)
                else:
                    # ES TEXTO LIBRE
                    inputs_usuario[label_campo] = st.text_input(label_campo, key=key_unica)

        st.markdown("---")
        boton_calcular = st.form_submit_button("✅ Procesar Datos", type="primary")

    # --- 3. RESULTADO ---
    if boton_calcular:
        st.success("Campos capturados correctamente:")
        st.json(inputs_usuario)
        
        # Aquí podremos agregar la matemática más adelante.

if __name__ == "__main__":
    main()
