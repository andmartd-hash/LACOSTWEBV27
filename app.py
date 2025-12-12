import streamlit as st
import pandas as pd

# --- Configuración de la página ---
st.set_page_config(page_title="LACOSTWEB V27", layout="wide", page_icon="🏢")

# --- Función para cargar datos (Cacheada para velocidad) ---
@st.cache_data
def load_data():
    try:
        # Cargamos los CSV que subiste a GitHub junto con el código
        # Asegúrate de que los nombres de archivo coincidan exactamente
        data = {
            "input": pd.read_csv("input.csv"),
            "countries": pd.read_csv("countries.csv"),
            "risk": pd.read_csv("risk.csv"),
            "offering": pd.read_csv("offering.csv"),
            "slc": pd.read_csv("slc.csv"),
            "lplat": pd.read_csv("lplat.csv"),
            "lband": pd.read_csv("lband.csv"),
            "mcbr": pd.read_csv("mcbr.csv")
        }
        return data
    except FileNotFoundError as e:
        st.error(f"❌ Error: No se encuentra el archivo {e.filename}. Asegúrate de subir los CSV a GitHub con los nombres correctos.")
        return None

def main():
    st.title("🏢 LACOSTWEB V27 - Cotizador Corporativo")
    st.markdown("**Andresma**, el sistema ha cargado tus tablas maestras V12-BASE.")

    # Cargar datos
    dfs = load_data()
    
    if dfs:
        # --- BARRA LATERAL: Parámetros Globales ---
        with st.sidebar:
            st.header("1. Configuración del Deal")
            
            # Selector de PAÍS (Usando datos reales de countries.csv)
            # Asumimos que la columna se llama 'Country' o la primera columna
            lista_paises = dfs["countries"].iloc[:, 0].unique()
            pais_selec = st.selectbox("Seleccionar País", lista_paises)
            
            # Selector de MONEDA
            moneda = st.radio("Moneda de Salida", ["USD", "COP"])
            
            trm = st.number_input("TRM / Tasa de Cambio", value=4150.0)

        # --- PESTAÑAS ---
        tab_cotizador, tab_datos = st.tabs(["🧮 Cotizador", "📂 Tablas Maestras"])

        # --- PESTAÑA 1: COTIZADOR ---
        with tab_cotizador:
            st.subheader("2. Definición del Servicio")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Selector de OFFERING (Usando datos reales de offering.csv)
                lista_offerings = dfs["offering"].iloc[:, 0].unique()
                offering_selec = st.selectbox("Offering / Servicio", lista_offerings)

                # Selector de BAND (Usando datos reales de lband.csv)
                lista_bands = dfs["lband"].iloc[:, 0].unique()
                band_selec = st.selectbox("Band / Nivel", lista_bands)

            with col2:
                # Selector de PLATAFORMA (Usando datos reales de lplat.csv)
                lista_plat = dfs["lplat"].iloc[:, 0].unique()
                plat_selec = st.selectbox("Plataforma", lista_plat)
                
                # Inputs numéricos manuales
                fte_cantidad = st.number_input("Cantidad FTE / Unidades", value=1.0, min_value=0.0)

            with col3:
                costo_unitario = st.number_input("Costo Unitario (Input)", value=0.0)
                moneda_input = st.selectbox("Moneda del Costo", ["COP", "USD"])

            st.markdown("---")
            st.subheader("3. Resultados")

            # --- LÓGICA DE CÁLCULO (Replicando tu regla de negocio) ---
            # Regla: Si costo es USD y queremos COP -> Multiplicar por TRM.
            # Regla: Si costo es USD y queremos USD -> Igual.
            
            costo_final = 0.0
            
            if moneda_input == "USD":
                if moneda == "COP":
                    costo_final = costo_unitario * trm
                else:
                    costo_final = costo_unitario
            elif moneda_input == "COP":
                if moneda == "USD":
                    costo_final = costo_unitario / trm
                else:
                    costo_final = costo_unitario
            
            # Cálculo total
            total = costo_final * fte_cantidad

            # Mostrar métricas
            c1, c2, c3 = st.columns(3)
            c1.metric(label=f"Costo Unitario ({moneda})", value=f"{costo_final:,.2f}")
            c2.metric(label="Cantidad", value=fte_cantidad)
            c3.metric(label=f"💰 TOTAL ESTIMADO ({moneda})", value=f"{total:,.2f}")

            # Mostrar info de referencia de las tablas (Lookups)
            st.info(f"Parametros seleccionados: País **{pais_selec}** | Offering **{offering_selec}** | Banda **{band_selec}**")

        # --- PESTAÑA 2: VISOR DE DATOS ---
        with tab_datos:
            st.write("Visualiza tus tablas maestras cargadas desde los CSV:")
            
            opcion_tabla = st.selectbox("Ver tabla:", ["countries", "offering", "risk", "slc", "lplat", "lband", "mcbr", "input"])
            st.dataframe(dfs[opcion_tabla], use_container_width=True)

if __name__ == "__main__":
    main()