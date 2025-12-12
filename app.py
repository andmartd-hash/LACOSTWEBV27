import streamlit as st
import pandas as pd
import os

# --- Configuración Visual ---
st.set_page_config(page_title="LACOSTWEB FINAL", layout="wide", page_icon="✅")

# --- 1. CONFIGURACIÓN DE NOMBRES (LIMPIOS) ---
FILES = {
    "config":    "UI_CONFIG.csv",   # El único en MAYÚSCULAS
    "countries": "countries.csv",   # Todo el resto en minúsculas
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
                df = pd.read_csv(filename)
                df.columns = df.columns.str.strip() # Limpiar espacios en cabeceras
                df = df.dropna(how='all') # Eliminar filas vacías
                data[key] = df
            except Exception as e:
                st.error(f"Error leyendo {filename}: {e}")
        # Soporte para fallback por si subiste 'UI_CONGIF' con error de dedo
        elif key == "config" and os.path.exists("UI_CONGIF.csv"):
             data[key] = pd.read_csv("UI_CONGIF.csv")
        else:
            missing.append(filename)
            
    return data, missing

def main():
    st.title("✅ LACOSTWEB - Cotizador Corporativo")

    # Cargar datos
    dfs, missing = load_data()

    if missing:
        st.error("❌ FALTAN ARCHIVOS EN GITHUB")
        st.warning("Por favor renombra tus archivos para que coincidan con esta lista:")
        st.code("\n".join(missing))
        st.stop()

    if "config" not in dfs:
        st.error("❌ Falta el archivo UI_CONFIG.csv")
        st.stop()

    # --- 2. MOTOR DE UI (4 COLUMNAS) ---
    df_config = dfs["config"]
    
    # Mapeo de columnas según tu instrucción:
    # 1. Nombre del campo (App Label)
    # 2. Fuente de datos (Source Table)
    # 3. Qué hace el campo (Logic/Help)
    # 4. Ejemplo (Default Value)
    
    cols = df_config.columns
    c_nombre  = cols[0]
    c_fuente  = cols[1] if len(cols) > 1 else None
    c_logica  = cols[2] if len(cols) > 2 else None
    c_ejemplo = cols[3] if len(cols) > 3 else None

    inputs = {}

    with st.form("form_final"):
        st.subheader("Configuración del Escenario")
        
        c1, c2 = st.columns(2)

        for idx, row in df_config.iterrows():
            if pd.isna(row[c_nombre]): continue
            
            # --- Lectura de la Fila de Configuración ---
            label = str(row[c_nombre]).strip()
            fuente = str(row[c_fuente]).strip().lower() if c_fuente and pd.notna(row[c_fuente]) else ""
            logica = str(row[c_logica]).strip() if c_logica and pd.notna(row[c_logica]) else ""
            ejemplo = str(row[c_ejemplo]).strip() if c_ejemplo and pd.notna(row[c_ejemplo]) else ""

            # --- Identificar Fuente de Datos ---
            tabla_datos = None
            if fuente:
                # Buscar coincidencia exacta o parcial en las tablas cargadas
                if fuente in dfs: 
                    tabla_datos = dfs[fuente]
                elif fuente.lower() in dfs:
                    tabla_datos = dfs[fuente.lower()]

            # --- Renderizado del Widget ---
            uid = f"f_{idx}" # ID único
            col_destino = c1 if idx % 2 == 0 else c2

            with col_destino:
                if tabla_datos is not None:
                    # CASO 1: LISTA DESPLEGABLE (Si tiene fuente)
                    opciones = tabla_datos.iloc[:, 0].unique()
                    inputs[label] = st.selectbox(
                        label, 
                        options=opciones, 
                        key=uid,
                        help=f"ℹ️ {logica}" # Mostramos la lógica como ayuda
                    )
                else:
                    # CASO 2: CAMPO MANUAL (Texto o Número)
                    # Usamos el 'Ejemplo' para decidir si pintar número o texto
                    es_numero = False
                    val_defecto = 0.0
                    
                    # Intentamos ver si el ejemplo es un número
                    if ejemplo:
                        try:
                            val_defecto = float(ejemplo)
                            es_numero = True
                        except:
                            pass
                    
                    if es_numero:
                        inputs[label] = st.number_input(
                            label, 
                            value=val_defecto, 
                            key=uid, 
                            help=f"ℹ️ {logica}"
                        )
                    else:
                        inputs[label] = st.text_input(
                            label, 
                            value=ejemplo, 
                            key=uid, 
                            help=f"ℹ️ {logica}"
                        )

        st.markdown("---")
        submitted = st.form_submit_button("✅ Calcular", type="primary")

    # --- 3. PROCESAMIENTO ---
    if submitted:
        st.success("Información capturada con éxito.")
        st.write("Variables para cálculo:")
        st.json(inputs)
        
        # Nota: Aquí podemos agregar la matemática específica si me compartes
        # la fórmula exacta que quieres aplicar con estos campos.

if __name__ == "__main__":
    main()
