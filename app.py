import streamlit as st
import pandas as pd
import os

# --- Configuración Visual ---
st.set_page_config(page_title="LACOSTWEB V13", layout="wide", page_icon="📝")

# --- 1. CARGA DE DATOS INTELIGENTE ---
@st.cache_data
def load_data():
    # Estas son las claves internas que usaremos en el código
    required_keys = ["ui_config", "countries", "risk", "offering", "slc", "lplat", "lband", "mcbr"]
    
    loaded_data = {}
    missing_files = []

    for key in required_keys:
        # El sistema buscará el archivo con estos posibles nombres (en orden de prioridad)
        # 1. Nombre corto limpio (ej: risk.csv)
        # 2. Nombre con mayúscula (ej: Risk.csv)
        # 3. Nombre original largo (ej: V13-BASE.xlsx - Risk.csv)
        possible_filenames = [
            f"{key}.csv", 
            f"{key.capitalize()}.csv",
            f"{key.upper()}.csv",
            f"V13-BASE.xlsx - {key}.csv",           # Nombre exacto minúscula
            f"V13-BASE.xlsx - {key.capitalize()}.csv", # Nombre exacto Capitalizado
            f"V13-BASE.xlsx - {key.upper()}.csv"       # Nombre exacto MAYÚSCULA
        ]
        
        # Caso especial para UI_CONFIG que a veces viene en mayúsculas
        if key == "ui_config":
            possible_filenames.append("V13-BASE.xlsx - UI_CONFIG.csv")

        file_found = False
        for filename in possible_filenames:
            if os.path.exists(filename):
                try:
                    df = pd.read_csv(filename)
                    # Limpiamos nombres de columnas (quitamos espacios extra)
                    df.columns = df.columns.str.strip()
                    # Eliminamos filas completamente vacías
                    df = df.dropna(how='all')
                    loaded_data[key] = df
                    file_found = True
                    break # Encontramos el archivo, dejamos de buscar
                except Exception as e:
                    print(f"Error leyendo {filename}: {e}")
        
        if not file_found:
            missing_files.append(key)
    
    return loaded_data, missing_files

def main():
    st.title("📝 LACOSTWEB V13 - Cotizador")
    st.markdown("**Andresma**, el sistema está listo con la configuración V13.")

    # Cargar tablas
    dfs, missing = load_data()
    
    # Verificación de seguridad
    if missing:
        st.error(f"❌ FALTAN ARCHIVOS: {', '.join(missing)}")
        st.warning("Verifica que hayas subido los archivos CSV a GitHub.")
        st.code(f"Archivos visibles en el servidor: {os.listdir('.')}")
        st.stop()
        
    if "ui_config" not in dfs:
        st.error("❌ Error Crítico: No se pudo cargar la tabla de configuración (UI_CONFIG).")
        st.stop()

    # --- 2. GENERADOR DEL FORMULARIO (Basado en UI_CONFIG) ---
    df_config = dfs["ui_config"]
    
    # Detectamos las columnas del archivo de configuración
    # Asumimos: Columna 0 = Nombre del Campo (Label)
    # Asumimos: Columna 1 = Fuente de Datos (Source Table)
    cols = df_config.columns
    col_label = cols[0]
    col_source = cols[1] if len(cols) > 1 else None

    seleccion_usuario = {}

    with st.form("form_cotizacion"):
        c1, c2 = st.columns(2)
        
        for idx, row in df_config.iterrows():
            # Obtener nombre del campo
            val_label = row[col_label]
            if pd.isna(val_label): continue # Saltar filas vacías
            
            label = str(val_label).strip()
            unique_key = f"input_{idx}_{label}" # Llave única interna
            
            # Determinar columna visual (Izquierda o Derecha)
            col_destino = c1 if idx % 2 == 0 else c2
            
            # --- LÓGICA: ¿Es Lista o Texto? ---
            es_lista = False
            opciones = []
            
            # 1. Verificar si la columna "Source" tiene un nombre de tabla válido
            if col_source and pd.notna(row[col_source]):
                fuente = str(row[col_source]).strip().lower()
                
                # Buscamos en las tablas cargadas
                if fuente in dfs:
                    es_lista = True
                    opciones = dfs[fuente].iloc[:, 0].unique()
                elif fuente.lower() in dfs: # Intento extra lowercase
                    es_lista = True
                    opciones = dfs[fuente.lower()].iloc[:, 0].unique()
            
            # 2. Si no hay source, verificar si el nombre del campo coincide con una tabla
            if not es_lista and label.lower() in dfs:
                es_lista = True
                opciones = dfs[label.lower()].iloc[:, 0].unique()

            # --- DIBUJAR ---
            with col_destino:
                if es_lista:
                    seleccion_usuario[label] = st.selectbox(label, options=opciones, key=unique_key)
                else:
                    seleccion_usuario[label] = st.text_input(label, key=unique_key)

        st.markdown("---")
        submitted = st.form_submit_button("💾 Guardar Cotización", type="primary")

    # --- 3. RESULTADOS ---
    if submitted:
        st.success("✅ Datos capturados correctamente")
        st.json(seleccion_usuario)

    # --- DEBUG (Opcional, para ver tablas) ---
    with st.expander("🔍 Ver Tablas Maestras (Admin)"):
        tab_sel = st.selectbox("Seleccionar Tabla", list(dfs.keys()))
        st.dataframe(dfs[tab_sel], use_container_width=True)

if __name__ == "__main__":
    main()
