import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="LACOSTWEB V27", layout="wide", page_icon="⚙️")

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    # Lista de claves esperadas
    keys = ["input", "countries", "risk", "offering", "slc", "lplat", "lband", "mcbr"]
    loaded = {}
    missing = []

    for k in keys:
        # Buscamos variantes de nombre
        variants = [f"{k}.csv", f"{k.capitalize()}.csv", f"{k.upper()}.csv", 
                    f"V12-BASE.xlsx - {k}.csv"]
        found = False
        for v in variants:
            if os.path.exists(v):
                try:
                    df = pd.read_csv(v)
                    # Limpieza de columnas
                    df.columns = df.columns.str.strip()
                    # Limpieza de datos vacíos extraños
                    df = df.dropna(how='all') 
                    loaded[k] = df
                    found = True
                    break
                except: pass
        if not found: missing.append(k)
    return loaded, missing

def main():
    st.title("⚙️ LACOSTWEB V27 - Configurador de Input")

    dfs, missing = load_data()
    if missing:
        st.error(f"Faltan archivos: {missing}")
        st.stop()
    
    if "input" not in dfs:
        st.error("Falta input.csv")
        st.stop()

    df_input = dfs["input"]

    # --- 2. CONFIGURACIÓN MANUAL DE COLUMNAS ---
    with st.sidebar:
        st.header("🔧 Mapeo de Lógica")
        st.info("Ayúdame a entender tu archivo 'input.csv'. Selecciona qué columna es cuál:")
        
        cols = df_input.columns.tolist()
        
        # El usuario elige cuál columna tiene el NOMBRE (Label)
        col_label = st.selectbox("¿Columna de NOMBRE/ETIQUETA?", cols, index=0)
        
        # El usuario elige cuál columna tiene la FUENTE (Source/List)
        # (Ej: donde dice 'Countries', 'Offering', etc.)
        col_source = st.selectbox("¿Columna de FUENTE/LISTA?", ["(Ninguna)"] + cols, index=1 if len(cols)>1 else 0)

        st.divider()
        st.write("Tablas disponibles para cruzar:", list(dfs.keys()))

    # --- 3. VISUALIZADOR DE DIAGNÓSTICO ---
    with st.expander("👀 Ver contenido real de input.csv (Para verificar)", expanded=True):
        st.dataframe(df_input.head(10), use_container_width=True)

    # --- 4. RENDERIZADO DEL FORMULARIO ---
    st.subheader("Vista Previa del Formulario")
    
    user_selections = {}
    
    with st.form("form_dinamico"):
        c1, c2 = st.columns(2)
        
        # Iteramos usando las columnas que TÚ elegiste
        for idx, row in df_input.iterrows():
            
            # 1. Obtener Etiqueta
            label_val = row[col_label]
            if pd.isna(label_val): continue # Saltar filas vacías
            label = str(label_val).strip()
            
            # Clave única
            unique_key = f"field_{idx}_{label}"
            
            # 2. Determinar si es Lista o Texto
            es_lista = False
            lista_opciones = []
            
            # Si el usuario configuró una columna de fuente
            if col_source != "(Ninguna)" and pd.notna(row[col_source]):
                fuente_str = str(row[col_source]).strip().lower()
                
                # Buscamos si esa fuente existe como tabla cargada (ej: 'countries')
                # O si es una referencia directa a un nombre de archivo
                
                # Búsqueda exacta
                if fuente_str in dfs:
                    es_lista = True
                    # Asumimos que la lista está en la 1ra columna de esa tabla
                    lista_opciones = dfs[fuente_str].iloc[:, 0].unique()
                
                # Búsqueda parcial (ej: Input dice 'Risk' y la tabla es 'risk')
                elif fuente_str.lower() in dfs:
                    es_lista = True
                    lista_opciones = dfs[fuente_str.lower()].iloc[:, 0].unique()

            # Pintar el control
            target_col = c1 if idx % 2 == 0 else c2
            with target_col:
                if es_lista:
                    user_selections[label] = st.selectbox(f"{label}", lista_opciones, key=unique_key)
                else:
                    user_selections[label] = st.text_input(f"{label}", key=unique_key)

        st.markdown("---")
        if st.form_submit_button("Validar"):
            st.success("Formulario generado con tu lógica.")
            st.write(user_selections)

if __name__ == "__main__":
    main()
