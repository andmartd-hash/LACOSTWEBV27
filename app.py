import streamlit as st
import pandas as pd

# --- Configuración de la página ---
st.set_page_config(page_title="LACOSTWEB V27", layout="wide", page_icon="💼")

def main():
    st.title("💼 LACOSTWEB V27 - Cotizador Cloud")
    st.markdown("Bienvenido, **Andresma**. Sistema de gestión de costos y precios.")

    # --- BARRA LATERAL: Configuración Global ---
    with st.sidebar:
        st.header("⚙️ Configuración")
        # Definimos la Tasa de Cambio (ER)
        trm_actual = st.number_input("Tasa de Cambio (COP/USD)", value=4100.0, step=10.0)
        st.write(f"TRM aplicada: **${trm_actual:,.0f}**")

    # --- PESTAÑAS DE LA APLICACIÓN ---
    tab1, tab2 = st.tabs(["🧮 Calculadora de Costos", "📊 Base de Datos Histórica"])

    # --- PESTAÑA 1: CALCULADORA (Lógica de Negocio) ---
    with tab1:
        st.subheader("Nuevo Cálculo de Precio")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            descripcion = st.text_input("Descripción del Item", "Servicio Consultoría")
            moneda = st.selectbox("Moneda del Costo", ["COP", "USD"])
        
        with col2:
            costo_input = st.number_input("Costo Base", value=100.0, min_value=0.0)
            margen = st.slider("Margen Deseado (%)", 0, 100, 30) / 100

        with col3:
            # Lógica de conversión según tus reglas anteriores
            # Si es USD, convertimos a COP para mostrar, o viceversa según prefieras.
            # Aquí asumimos que queremos llegar a un precio en COP.
            
            costo_en_cop = 0.0
            if moneda == "USD":
                costo_en_cop = costo_input * trm_actual
            else:
                costo_en_cop = costo_input
            
            # Cálculo del Precio de Venta: Costo / (1 - Margen) 
            # (O Costo * (1+Margen) según tu fórmula preferida, usaré margen sobre venta)
            if margen < 1:
                precio_venta = costo_en_cop / (1 - margen)
            else:
                precio_venta = costo_en_cop  # Evitar división por cero

            st.metric(label="Costo Ajustado (COP)", value=f"${costo_en_cop:,.2f}")
            st.metric(label="Precio de Venta Sugerido", value=f"${precio_venta:,.2f}", delta=f"Margen: {margen*100}%")

    # --- PESTAÑA 2: DATOS INTEGRADOS (Sin subir archivo) ---
    with tab2:
        st.subheader("Registros del Sistema")
        
        # AQUÍ ES DONDE HARDCODEMOS TUS DATOS.
        # He puesto ejemplos, pero aquí pegaríamos tus filas reales.
        datos_base = {
            'ID': [101, 102, 103],
            'Servicio': ['Implementación Cloud', 'Soporte Mensual', 'Licencia IBM'],
            'Costo_USD': [500, 150, 1200],
            'Categoria': ['Proyectos', 'Recurrente', 'Software']
        }
        
        df = pd.DataFrame(datos_base)
        
        # Añadir columna calculada dinámica según la TRM del sidebar
        df['Costo_COP_Actual'] = df['Costo_USD'] * trm_actual
        
        st.dataframe(df, use_container_width=True)
        st.info("💡 Estos datos están integrados en el código. No se requiere archivo externo.")

if __name__ == "__main__":
    main()
