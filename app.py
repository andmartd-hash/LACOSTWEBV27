import streamlit as st
import pandas as pd

# --- Configuración de la página ---
st.set_page_config(page_title="LACOSTWEB V27", layout="wide")

def main():
    st.title("📊 LACOSTWEB V27 - Panel de Control")
    st.markdown("Hola **Andresma**. Sube tu archivo base para visualizar y analizar los datos.")

    # --- Carga del archivo ---
    uploaded_file = st.file_uploader("Sube aquí tu archivo Excel (.xlsx)", type=["xlsx"])

    if uploaded_file is not None:
        try:
            # Leemos el archivo Excel (carga todas las hojas)
            xl = pd.ExcelFile(uploaded_file)
            sheet_names = xl.sheet_names
            
            st.success("✅ Archivo cargado correctamente.")

            # Creamos pestañas dinámicas según las hojas del Excel
            tabs = st.tabs(sheet_names)

            for i, sheet in enumerate(sheet_names):
                with tabs[i]:
                    st.subheader(f"Hoja: {sheet}")
                    
                    # Leemos los datos de la hoja específica
                    df = pd.read_excel(uploaded_file, sheet_name=sheet)
                    
                    # Mostramos los datos de forma interactiva
                    st.dataframe(df, use_container_width=True)
                    
                    # --- Espacio para lógica futura ---
                    # Aquí podemos insertar tus cálculos de costos o filtros más adelante.
                    
        except Exception as e:
            st.error(f"Ocurrió un error al leer el archivo: {e}")
    else:
        st.info("👆 Por favor, carga el archivo Excel para comenzar.")

if __name__ == "__main__":
    main()