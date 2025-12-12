import streamlit as st
import pandas as pd
import os

# --- Configuración de la App ---
st.set_page_config(page_title="Cotizador V18", layout="wide", page_icon="🏗️")

# --- 1. CARGADOR INTELIGENTE (Detecta V18) ---
@st.cache_data
def load_data_v18():
    """
    Busca archivos en la carpeta que contengan las palabras clave.
    Funciona con nombres largos (V18-BASE...) o cortos.
    """
    # Mapa de: Clave Interna -> Palabra a buscar en el nombre del archivo
    keywords = {
        "config":    "ui_config",
        "countries": "countries",
        "risk":      "risk",
        "offering":  "offering",
        "slc":       "slc",
        "lplat":     "lplat",
        "lband":     "lband",
        "mcbr":      "mcbr"
    }
    
    loaded_data = {}
    missing_files = []
    
    # Listamos archivos reales en el servidor
    files_in_dir = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    for key, search_term in keywords.items():
        found_filename = None
        
        # Buscamos coincidencias (insensible a mayúsculas)
        for f in files_in_dir:
            if search_term.lower() in f.lower():
                found_filename = f
                break
        
        if found_filename:
            try:
                df = pd.read_csv(found_filename)
                df.columns = df.columns.str.strip() # Limpiar cabeceras
                df = df.dropna(how='all') # Eliminar vacíos
                loaded_data[key] = df
            except Exception as e:
                st.error(f"Error leyendo {found_filename}: {e}")
        else:
            missing_files.append(search_term)
            
    return loaded_data, missing_files

def main():
    st.title("🏗️ LACOSTWEB V18")

    # Cargar datos
    dfs, missing = load_data_v18()

    # Validaciones
    if missing:
        st.warning(f"⚠️ Atención: No encuentro archivos para: {', '.join(missing)}")
        st.info("Asegúrate de haber subido los archivos CSV a GitHub.")
    
    if "config" not in dfs:
        st.error("❌ ERROR: No se encuentra el archivo UI_CONFIG.")
        st.stop()

    # --- 2. MOTOR DE INTERFAZ (Tu lógica de 4 columnas) ---
    df_config = dfs["config"]
    
    # Detectamos columnas por posición (0, 1, 2, 3)
    # Col 0: Nombre del Campo
    # Col 1: Fuente (Tabla)
    # Col 2: Lógica (Instrucción)
    # Col 3: Ejemplo (Valor por defecto)
    try:
        col_nombre  = df_config.columns[0]
        col_fuente  = df_config.columns[1]
        col_logica  = df_config.columns[2]
        col_ejemplo = df_config.columns[3]
    except IndexError:
        st.error("⚠️ El archivo UI_CONFIG debe tener al menos 4 columnas.")
        st.stop()

    inputs_usuario = {}

    with st.form("form_v18"):
        st.subheader("Configuración del Escenario")
        
        # Columnas para organizar
        c1, c2 = st.columns(2)

        for idx, row in df_config.iterrows():
            if pd.isna(row[col_nombre]): continue
            
            # --- Extraer datos de las 4 columnas ---
            label = str(row[col_nombre]).strip()
            fuente = str(row[col_fuente]).strip().lower() if pd.notna(row[col_fuente]) else ""
            logica = str(row[col_logica]).strip() if pd.notna(row[col_logica]) else ""
            ejemplo = str(row[col_ejemplo]).strip() if pd.notna(row[col_ejemplo]) else ""
            
            # ID único
            uid = f"f_{idx}"
            target_col = c1 if idx % 2 == 0 else c2

            with target_col:
                # --- LÓGICA: LISTA O TEXTO ---
                
                tabla_datos = None
                # Si hay fuente, buscamos la tabla correspondiente
                if fuente:
                    for k in dfs.keys():
                        if fuente in k or k in fuente:
                            tabla_datos = dfs[k]
                            break
                
                if tabla_datos is not None:
                    # ES LISTA (DROPDOWN)
                    opciones = tabla_datos.iloc[:, 0].unique()
                    inputs_usuario[label] = st.selectbox(
                        label, 
                        opciones, 
                        key=uid,
                        help=f"ℹ️ {logica}" # Columna 3: Lógica
                    )
                else:
                    # ES CAMPO MANUAL (Usamos Columna 4: Ejemplo como default)
                    inputs_usuario[label] = st.text_input(
                        label, 
                        value=ejemplo, 
                        key=uid,
                        help=f"ℹ️ {logica}" # Columna 3: Lógica
                    )

        st.markdown("---")
        submitted = st.form_submit_button("✅ Calcular", type="primary")

    # --- 3. RESULTADOS ---
    if submitted:
        st.success("Datos capturados:")
        st.json(inputs_usuario)

if __name__ == "__main__":
    main()
