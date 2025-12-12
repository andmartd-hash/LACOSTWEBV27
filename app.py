import streamlit as st
import pandas as pd
import os

# --- Configuración Visual ---
st.set_page_config(page_title="LACOSTWEB V27", layout="wide", page_icon="🧩")

# --- 1. CARGA DE DATOS ROBUSTA ---
@st.cache_data
def load_data():
    # Nombres de archivos esperados (claves internas)
    required_files = ["input", "countries", "risk", "offering", "slc", "lplat", "lband", "mcbr"]
    
    loaded_data = {}
    missing_files = []

    for key in required_files:
        # Buscamos variantes (input.csv, Input.csv, V12-BASE...input.csv)
        possible_names = [
            f"{key}.csv", 
            f"{key.capitalize()}.csv", 
            f"{key.upper()}.csv",
            f"V12-BASE.xlsx - {key}.csv", # Por si acaso subiste los nombres largos
            f"V12-BASE.xlsx - {key.capitalize()}.csv"
        ]
        
        file_found = False
        for filename in possible_names:
            if os.path.exists(filename):
                try:
                    # Leemos el CSV
                    df = pd.read_csv(filename)
                    # Limpiamos espacios en los nombres de columnas por si acaso
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

    # Cargar tablas
    dfs, missing = load_data()
    
    # Verificación de seguridad
    if missing:
        st.error("❌ FALTAN ARCHIVOS CLAVE")
        st.write(f"No encuentro: {', '.join(missing)}")
        st.code(os.listdir('.'))
        st.stop()
        
    if "input" not in dfs:
        st.error("❌ El archivo 'input.csv' es obligatorio para generar la vista.")
        st.stop()

    # --- 2. GENERADOR DINÁMICO DE FORMULARIO ---
    st.markdown("### Configuración del Escenario")
    st.info("Los campos a continuación se generan automáticamente desde `input.csv`.")

    # Tomamos el dataframe de configuración
    df_input = dfs["input"]
    
    # Diccionario para guardar lo que seleccione el usuario
    seleccion_usuario = {}

    # Creamos un contenedor (formulario)
    with st.form("form_cotizador"):
        # Usamos columnas para que no quede una lista eterna hacia abajo
        col1, col2 = st.columns(2)
        
        # Iteramos por cada fila del archivo INPUT
        # Asumimos que la Columna 0 es el NOMBRE DEL CAMPO
        # Asumimos que la Columna 1 (opcional) es la TABLA FUENTE (ej: countries, offering)
        
        campos = df_input.columns # Nombres de las columnas del input.csv
        col_nombre_campo = campos[0] # La primera columna suele ser el nombre (ej: "Variable")
        
        # Intentamos adivinar si hay una columna que indique la fuente de datos
        col_fuente = None
        if len(campos) > 1:
            col_fuente = campos[1] # La segunda columna suele ser la fuente

        count = 0
        for index, row in df_input.iterrows():
            label = str(row[col_nombre_campo])
            
            # Determinamos dónde poner el input (columna 1 o 2)
            donde_pintar = col1 if count % 2 == 0 else col2
            
            # LÓGICA INTELIGENTE:
            # 1. ¿Existe una tabla cargada con el mismo nombre que este campo? (Ej: "Countries")
            # 2. O ¿La segunda columna del input dice explícitamente la tabla?
            
            tabla_referencia = None
            
            # Intento A: Mirar si la columna 2 dice la tabla (ej: 'countries')
            if col_fuente and str(row[col_fuente]).lower() in dfs:
                tabla_referencia = dfs[str(row[col_fuente]).lower()]
            
            # Intento B: Mirar si el nombre del campo coincide con una tabla (ej: campo 'Risk' -> tabla 'risk')
            elif label.lower() in dfs:
                tabla_referencia = dfs[label.lower()]

            with donde_pintar:
                if tabla_referencia is not None:
                    # ES UNA LISTA DESPLEGABLE (SELECTBOX)
                    # Tomamos la primera columna de esa tabla maestra como opciones
                    opciones = tabla_referencia.iloc[:, 0].unique()
                    seleccion_usuario[label] = st.selectbox(f"Select {label}", options, key=label)
                else:
                    # ES UN CAMPO LIBRE (TEXTO O NUMERO)
                    # Por defecto lo ponemos como texto, o numérico si parece número
                    seleccion_usuario[label] = st.text_input(label, key=label)
            
            count += 1

        st.markdown("---")
        submitted = st.form_submit_button("💾 Calcular / Guardar Escenario")

    # --- 3. RESULTADOS / DEBUG ---
    if submitted:
        st.success("✅ Datos capturados correctamente")
        st.subheader("Resumen de Selección:")
        st.json(seleccion_usuario)
        
        # AQUÍ IRÍA TU LÓGICA DE CÁLCULO COMPLEJA
        # Usando 'seleccion_usuario["Offering"]', 'seleccion_usuario["FTE"]', etc.

    # --- Pestaña para ver la "tripa" (Debugging) ---
    with st.expander("🕵️ Ver Tablas Maestras (Debug)"):
        tab_sel = st.selectbox("Seleccionar tabla", list(dfs.keys()))
        st.dataframe(dfs[tab_sel], use_container_width=True)

if __name__ == "__main__":
    main()
