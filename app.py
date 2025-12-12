import streamlit as st
import pandas as pd
import os

# --- Configuración de la Página ---
st.set_page_config(page_title="Cotizador V17", layout="wide", page_icon="🏗️")

# --- 1. CARGADOR DE DATOS INTELIGENTE (V17) ---
@st.cache_data
def load_data_v17():
    # Palabras clave para identificar cada archivo en tu carpeta
    # El sistema busca archivos que contengan estas palabras
    keywords = {
        "config":    "UI_CONFIG",  # Busca 'UI_CONFIG'
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
    
    # Listamos todos los archivos en la carpeta actual
    all_files = os.listdir('.')
    
    for key, search_term in keywords.items():
        found = None
        # Buscamos coincidencias (case insensitive)
        for f in all_files:
            if search_term.lower() in f.lower() and f.endswith('.csv'):
                found = f
                break
        
        if found:
            try:
                # Leemos el CSV encontrado
                df = pd.read_csv(found)
                df.columns = df.columns.str.strip() # Limpiamos cabeceras
                df = df.dropna(how='all') # Limpiamos filas vacías
                loaded_data[key] = df
            except Exception as e:
                st.error(f"Error leyendo {found}: {e}")
        else:
            missing_files.append(search_term)
            
    return loaded_data, missing_files

def main():
    st.title("🏗️ LACOSTWEB V17 - Generador de Interfaz")

    # Cargar los datos
    dfs, missing = load_data_v17()

    # Validaciones iniciales
    if missing:
        st.warning(f"⚠️ Atención: No encuentro archivos para: {', '.join(missing)}")
        st.info("Asegúrate de que los archivos 'V17-BASE...' estén subidos en GitHub.")
    
    if "config" not in dfs:
        st.error("❌ ERROR CRÍTICO: No se encuentra el archivo UI_CONFIG.")
        st.stop()

    # --- 2. MOTOR DE INTERFAZ (Tu lógica de 4 columnas) ---
    df_config = dfs["config"]
    
    # Detectamos las 4 columnas por posición (0, 1, 2, 3)
    # Col 0: Nombre del Campo
    # Col 1: Fuente de Datos (Tabla)
    # Col 2: Lógica / Instrucción
    # Col 3: Ejemplo / Valor por defecto
    try:
        cols = df_config.columns
        c_nombre  = cols[0]
        c_fuente  = cols[1]
        c_logica  = cols[2]
        c_ejemplo = cols[3]
    except IndexError:
        st.error("⚠️ El archivo UI_CONFIG debe tener al menos 4 columnas (Nombre, Fuente, Lógica, Ejemplo).")
        st.stop()

    inputs_usuario = {}

    with st.form("form_v17"):
        st.subheader("Configuración del Escenario")
        
        # Grid de 2 columnas para organizar visualmente
        col_izq, col_der = st.columns(2)

        for idx, row in df_config.iterrows():
            if pd.isna(row[c_nombre]): continue
            
            # Extraemos la data de la fila
            label = str(row[c_nombre]).strip()
            fuente = str(row[c_fuente]).strip().lower() if pd.notna(row[c_fuente]) else ""
            logica = str(row[c_logica]).strip() if pd.notna(row[c_logica]) else ""
            ejemplo = str(row[c_ejemplo]).strip() if pd.notna(row[c_ejemplo]) else ""
            
            # ID único para Streamlit
            uid = f"field_{idx}"
            target_col = col_izq if idx % 2 == 0 else col_der

            with target_col:
                # --- DECISIÓN: ¿LISTA O TEXTO? ---
                
                tabla_asociada = None
                # Buscamos si la fuente coincide con algún archivo cargado
                if fuente:
                    for key in dfs.keys():
                        if fuente in key or key in fuente:
                            tabla_asociada = dfs[key]
                            break
                
                if tabla_asociada is not None:
                    # ES UNA LISTA DESPLEGABLE
                    opciones = tabla_asociada.iloc[:, 0].unique()
                    inputs_usuario[label] = st.selectbox(
                        label, 
                        opciones, 
                        key=uid,
                        help=f"ℹ️ {logica}" # Tu instrucción va aquí
                    )
                else:
                    # ES UN CAMPO DE TEXTO/NÚMERO
                    inputs_usuario[label] = st.text_input(
                        label, 
                        value=ejemplo, # Tu ejemplo va aquí como valor por defecto
                        key=uid,
                        help=f"ℹ️ {logica}"
                    )

        st.markdown("---")
        submitted = st.form_submit_button("✅ Procesar Datos", type="primary")

    # --- 3. RESULTADOS ---
    if submitted:
        st.success("Datos capturados correctamente.")
        st.write("Valores listos para procesar:")
        st.json(inputs_usuario)

if __name__ == "__main__":
    main()
