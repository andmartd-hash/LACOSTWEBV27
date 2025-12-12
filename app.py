import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Cotizador V16 - Interfaz Limpia", layout="wide", page_icon="✨")

# --- 1. CARGADOR INTELIGENTE (Detecta tus archivos V16) ---
@st.cache_data
def load_data():
    # Palabras clave para identificar cada tabla, sin importar el prefijo "V16-BASE..."
    mapa_archivos = {
        "config":    "UI_CONFIG",
        "countries": "countries",
        "risk":      "risk",
        "offering":  "offering",
        "slc":       "slc",
        "lplat":     "lplat",
        "lband":     "lband",
        "mcbr":      "mcbr"
    }
    
    # 1. Obtenemos todos los archivos reales en la carpeta
    archivos_en_disco = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    datos_cargados = {}
    faltantes = []

    for clave_interna, palabra_clave in mapa_archivos.items():
        # Buscamos un archivo que contenga la palabra clave (ignora mayúsculas)
        archivo_encontrado = None
        for f in archivos_en_disco:
            if palabra_clave.lower() in f.lower():
                archivo_encontrado = f
                break
        
        if archivo_encontrado:
            try:
                df = pd.read_csv(archivo_encontrado)
                df.columns = df.columns.str.strip() # Limpieza de cabeceras
                df = df.dropna(how='all') # Limpieza de filas vacías
                datos_cargados[clave_interna] = df
            except Exception as e:
                st.error(f"Error leyendo {archivo_encontrado}: {e}")
        else:
            faltantes.append(palabra_clave)
            
    return datos_cargados, faltantes

def main():
    st.title("✨ Cotizador V16 - Interfaz Dinámica")

    # Cargar tablas
    dfs, missing = load_data()

    # Validación de seguridad
    if missing:
        st.warning(f"⚠️ Atención: No encuentro archivos con estas palabras clave: {', '.join(missing)}")
        st.info("Asegúrate de haber subido los archivos CSV a GitHub.")
    
    if "config" not in dfs:
        st.error("❌ ERROR CRÍTICO: No se encontró el archivo de configuración (UI_CONFIG).")
        st.stop()

    # --- 2. CONSTRUCCIÓN DE LA INTERFAZ ---
    df_config = dfs["config"]
    
    # Mapeo de columnas por posición (0, 1, 2, 3) para ser exactos con tu Excel
    try:
        col_nombre   = df_config.columns[0] # Campo 1: Nombre en la app
        col_fuente   = df_config.columns[1] # Campo 2: De dónde trae datos
        col_logica   = df_config.columns[2] # Campo 3: Qué debe hacer (Ayuda)
        col_ejemplo  = df_config.columns[3] # Campo 4: Ejemplo (Valor defecto)
    except IndexError:
        st.error("❌ Tu archivo UI_CONFIG debe tener al menos 4 columnas.")
        st.dataframe(df_config.head())
        st.stop()

    respuestas_usuario = {}

    with st.form("form_interfaz_v16"):
        st.subheader("Parámetros de Entrada")
        st.info("Los campos marcados con ℹ️ tienen instrucciones de lógica.")
        
        c1, c2 = st.columns(2)

        for idx, row in df_config.iterrows():
            # Si no hay nombre de campo, saltamos la fila
            if pd.isna(row[col_nombre]): continue
            
            # Extraer datos de la configuración
            label = str(row[col_nombre]).strip()
            fuente = str(row[col_fuente]).strip().lower() if pd.notna(row[col_fuente]) else ""
            logica = str(row[col_logica]).strip() if pd.notna(row[col_logica]) else ""
            ejemplo = str(row[col_ejemplo]).strip() if pd.notna(row[col_ejemplo]) else ""

            # Determinar dónde pintar (Izquierda o Derecha)
            target_col = c1 if idx % 2 == 0 else c2
            id_unico = f"input_{idx}"

            with target_col:
                # LÓGICA DE DECISIÓN: ¿Lista o Texto?
                
                tabla_datos = None
                # Buscamos si la "Fuente" coincide con alguna tabla cargada
                if fuente:
                    # Búsqueda exacta o parcial en las llaves de dfs
                    for k in dfs.keys():
                        if fuente in k or k in fuente:
                            tabla_datos = dfs[k]
                            break
                
                if tabla_datos is not None:
                    # --- ES UNA LISTA DESPLEGABLE ---
                    opciones = tabla_datos.iloc[:, 0].unique()
                    respuestas_usuario[label] = st.selectbox(
                        label, 
                        opciones, 
                        key=id_unico,
                        help=f"Instrucción: {logica}" # Aquí va tu columna 3
                    )
                else:
                    # --- ES UN CAMPO DE TEXTO/NUMERO ---
                    # Usamos la columna 4 (Ejemplo) como valor sugerido
                    respuestas_usuario[label] = st.text_input(
                        label, 
                        value=ejemplo, 
                        key=id_unico,
                        help=f"Instrucción: {logica}" # Aquí va tu columna 3
                    )

        st.markdown("---")
        submitted = st.form_submit_button("✅ Procesar Datos", type="primary")

    # --- 3. RESULTADOS (PRUEBA DE QUE FUNCIONA) ---
    if submitted:
        st.success("Interfaz generada y datos capturados correctamente.")
        st.write("Estos son los valores que ingresaste (listos para cálculo):")
        st.json(respuestas_usuario)

if __name__ == "__main__":
    main()
