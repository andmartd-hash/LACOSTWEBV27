import streamlit as st
import pandas as pd
import os

# --- Configuración de la página ---
st.set_page_config(page_title="LACOSTWEB V27", layout="wide", page_icon="🏢")

# --- Función para cargar datos ---
@st.cache_data
def load_data():
    # Diccionario con los nombres EXACTOS de tus archivos
    # Si cambias los nombres en GitHub, debes cambiarlos aquí también.
    file_map = {
        "input": "V12-BASE.xlsx - input.csv",
        "countries": "V12-BASE.xlsx - countries.csv",
        "risk": "V12-BASE.xlsx - Risk.csv",
        "offering": "V12-BASE.xlsx - Offering.csv",
        "slc": "V12-BASE.xlsx - SLC.csv",
        "lplat": "V12-BASE.xlsx - Lplat.csv",
        "lband": "V12-BASE.xlsx - Lband.csv",
        "mcbr": "V12-BASE.xlsx - MCBR.csv"
    }

    loaded_data = {}
    missing_files = []

    for key, filename in file_map.items():
        if os.path.exists(filename):
            try:
                loaded_data[key] = pd.read_csv(filename)
            except Exception as e:
                st.error(f"Error leyendo {filename}: {e}")
        else:
            missing_files.append(filename)
    
    return loaded_data, missing_files

def main():
    st.title("🏢 LACOSTWEB V27 - Cotizador Corporativo")

    # Intentamos cargar los datos
    dfs, missing = load_data()
    
    # --- BLOQUE DE DIAGNÓSTICO DE ERRORES ---
    if missing:
        st.error("❌ FALTAN ARCHIVOS IMPORTANTE")
        st.write("El sistema no encuentra estos archivos en la carpeta principal:")
        st.code("\n".join(missing))
        
        st.warning("🧐 DIAGNÓSTICO: Estos son los archivos que SÍ veo en el servidor:")
        # Esto imprimirá la lista real de archivos en la nube para que veamos el error
        files_in_dir = os.listdir('.')
        st.code("\n".join(files_in_dir))
        
        st.stop() # Detiene la app aquí si faltan archivos
    
    # Si todo está bien, continuamos...
    st.success("✅ Todas las tablas maestras (V12-BASE) cargadas correctamente.")
    
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("1. Configuración del Deal")
        
        # Selector de PAÍS
        # Ajustamos para leer la columna correcta, asumiendo que es la primera si no sabemos el nombre
        if not dfs["countries"].empty:
            lista_paises = dfs["countries"].iloc[:, 0].unique()
            pais_selec = st.selectbox("Seleccionar País", lista_paises)
        
        moneda = st.radio("Moneda de Salida", ["USD", "COP"])
        trm = st.number_input("TRM / Tasa de Cambio", value=4150.0)

    # --- PESTAÑAS ---
    tab_cotizador, tab_datos = st.tabs(["🧮 Cotizador", "📂 Tablas Maestras"])

    with tab_cotizador:
        st.subheader("2. Definición del Servicio")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            lista_offerings = dfs["offering"].iloc[:, 0].unique()
            offering_selec = st.selectbox("Offering / Servicio", lista_offerings)

            lista_bands = dfs["lband"].iloc[:, 0].unique()
            band_selec = st.selectbox("Band / Nivel", lista_bands)

        with col2:
            lista_plat = dfs["lplat"].iloc[:, 0].unique()
            plat_selec = st.selectbox("Plataforma", lista_plat)
            fte_cantidad = st.number_input("Cantidad FTE", value=1.0)

        with col3:
            costo_unitario = st.number_input("Costo Unitario (Input)", value=0.0)
            moneda_input = st.selectbox("Moneda Costo", ["COP", "USD"])

        st.markdown("---")
        
        # Cálculo simple
        costo_final = costo_unitario * trm if (moneda_input=="USD" and moneda=="COP") else costo_unitario
        if moneda_input=="COP" and moneda=="USD": costo_final = costo_unitario / trm
        
        total = costo_final * fte_cantidad

        c1, c2 = st.columns(2)
        c1.metric(f"Total ({moneda})", f"{total:,.2f}")

    with tab_datos:
        opcion = st.selectbox("Ver tabla", list(dfs.keys()))
        st.dataframe(dfs[opcion], use_container_width=True)

if __name__ == "__main__":
    main()
