import streamlit as st
import pandas as pd
import os

# --- Configuración de la página ---
st.set_page_config(page_title="LACOSTWEB V27", layout="wide", page_icon="🏢")

# --- Función para cargar datos ---
@st.cache_data
def load_data():
    # AHORA SI: Nombres cortos confirmados por el diagnóstico
    file_map = {
        "input": "input.csv",
        "countries": "countries.csv",
        "risk": "risk.csv",        # ¡Asegúrate de subir este!
        "offering": "offering.csv",
        "slc": "slc.csv",          # ¡Asegúrate de subir este!
        "lplat": "lplat.csv",
        "lband": "lband.csv",
        "mcbr": "mcbr.csv"
    }

    loaded_data = {}
    missing_files = []

    for key, filename in file_map.items():
        # Verificación insensible a mayúsculas/minúsculas para evitar errores tontos
        if os.path.exists(filename):
            try:
                loaded_data[key] = pd.read_csv(filename)
            except Exception as e:
                st.error(f"Error leyendo {filename}: {e}")
        # Intento alternativo (por si se subió como Risk.csv en vez de risk.csv)
        elif os.path.exists(filename.capitalize()):
             try:
                loaded_data[key] = pd.read_csv(filename.capitalize())
             except Exception as e:
                st.error(f"Error leyendo {filename}: {e}")
        else:
            missing_files.append(filename)
    
    return loaded_data, missing_files

def main():
    st.title("🏢 LACOSTWEB V27 - Cotizador Corporativo")

    # Intentamos cargar los datos
    dfs, missing = load_data()
    
    # --- BLOQUE DE DIAGNÓSTICO ---
    if missing:
        st.error("❌ AÚN FALTAN ARCHIVOS")
        st.write("Por favor sube estos archivos a GitHub:")
        st.code("\n".join(missing))
        st.stop()
    
    # Si llegamos aquí, ¡todo cargó!
    st.success("✅ Sistema iniciado. Tablas maestras cargadas.")
    
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("1. Configuración del Deal")
        
        # Selector de PAÍS
        if not dfs["countries"].empty:
            # Asumimos columna 0 si no hay nombre específico, ajusta si es necesario
            col_pais = dfs["countries"].columns[0]
            lista_paises = dfs["countries"][col_pais].unique()
            pais_selec = st.selectbox("Seleccionar País", lista_paises)
        
        moneda = st.radio("Moneda de Salida", ["USD", "COP"])
        trm = st.number_input("TRM / Tasa de Cambio", value=4150.0)

    # --- PESTAÑAS ---
    tab_cotizador, tab_datos = st.tabs(["🧮 Cotizador", "📂 Tablas Maestras"])

    with tab_cotizador:
        st.subheader("2. Definición del Servicio")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            col_off = dfs["offering"].columns[0]
            lista_offerings = dfs["offering"][col_off].unique()
            offering_selec = st.selectbox("Offering / Servicio", lista_offerings)

            col_band = dfs["lband"].columns[0]
            lista_bands = dfs["lband"][col_band].unique()
            band_selec = st.selectbox("Band / Nivel", lista_bands)

        with col2:
            col_plat = dfs["lplat"].columns[0]
            lista_plat = dfs["lplat"][col_plat].unique()
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
