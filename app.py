import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="LACOSTWEB V27", layout="wide", page_icon="🏢")

@st.cache_data
def load_data():
    # Lista de archivos requeridos (claves internas)
    required_files = ["input", "countries", "risk", "offering", "slc", "lplat", "lband", "mcbr"]
    
    loaded_data = {}
    missing_files = []

    # Buscamos variaciones de nombre para cada archivo
    for key in required_files:
        # Intentos posibles: "risk.csv", "Risk.csv", "RISK.csv"
        possible_names = [f"{key}.csv", f"{key.capitalize()}.csv", f"{key.upper()}.csv"]
        
        file_found = False
        for filename in possible_names:
            if os.path.exists(filename):
                try:
                    loaded_data[key] = pd.read_csv(filename)
                    file_found = True
                    break # Encontramos uno, dejamos de buscar
                except Exception as e:
                    st.error(f"Error leyendo {filename}: {e}")
        
        if not file_found:
            missing_files.append(f"{key}.csv (o variantes)")
    
    return loaded_data, missing_files

def main():
    st.title("🏢 LACOSTWEB V27 - Cotizador Corporativo")

    dfs, missing = load_data()
    
    if missing:
        st.error("❌ AÚN NO VEO LOS ARCHIVOS")
        st.warning("El servidor ve exactamente estos archivos en tu carpeta (copia esto si sigue fallando):")
        st.code(os.listdir('.')) # Muestra la verdad absoluta del servidor
        st.stop()
    
    st.success("✅ ¡Conectado! Todos los archivos cargados.")
    
    # --- RESTO DE LA APP ---
    with st.sidebar:
        st.header("Configuración")
        if "countries" in dfs:
            col = dfs["countries"].columns[0]
            st.selectbox("País", dfs["countries"][col].unique())
        moneda = st.radio("Moneda", ["USD", "COP"])
        trm = st.number_input("TRM", value=4150.0)

    tab1, tab2 = st.tabs(["Cotizador", "Datos"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            if "offering" in dfs: st.selectbox("Offering", dfs["offering"].iloc[:,0].unique())
            if "lband" in dfs: st.selectbox("Band", dfs["lband"].iloc[:,0].unique())
        with c2:
            if "lplat" in dfs: st.selectbox("Platform", dfs["lplat"].iloc[:,0].unique())
            fte = st.number_input("FTE", 1.0)
        with c3:
            costo = st.number_input("Costo Unitario", 0.0)
            mon_input = st.selectbox("Moneda", ["COP", "USD"])
        
        st.divider()
        val_final = costo * trm if mon_input=="USD" and moneda=="COP" else costo
        if mon_input=="COP" and moneda=="USD": val_final = costo / trm
        st.metric(f"Total {moneda}", f"{val_final * fte:,.2f}")

    with tab2:
        sel = st.selectbox("Ver tabla", list(dfs.keys()))
        st.dataframe(dfs[sel], use_container_width=True)

if __name__ == "__main__":
    main()
