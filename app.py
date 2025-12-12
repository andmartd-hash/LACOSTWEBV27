import streamlit as st
import pandas as pd
from datetime import date

# Configuración de la página
st.set_page_config(page_title="Cotizador IBM V18", layout="wide")

st.title("📊 Cotizador IBM - V18 Web App")
st.markdown("Bienvenido Andresma. Esta app reemplaza tu Excel complejo.")

# 1. Cargar datos (Cache para que sea rápido)
@st.cache_data
def load_data():
    # Asegúrate de que los nombres coincidan con los que subiste a GitHub
    countries = pd.read_csv("V18-BASE.xlsx - countries.csv")
    offering = pd.read_csv("V18-BASE.xlsx - offering.csv")
    slc = pd.read_csv("V18-BASE.xlsx - slc.csv")
    risk = pd.read_csv("V18-BASE.xlsx - risk.csv")
    return countries, offering, slc, risk

try:
    df_countries, df_offering, df_slc, df_risk = load_data()
    st.success("Bases de datos cargadas correctamente.")
except Exception as e:
    st.error(f"Error cargando archivos: {e}. Verifica que los CSV estén en el repo.")
    st.stop()

# --- SECCIÓN DE ENTRADAS (INPUTS) ---
st.sidebar.header("Configuración de Cotización")

# Selección de País
country_list = df_countries['Country'].unique()
selected_country = st.sidebar.selectbox("Selecciona el País", country_list)

# Filtrar moneda basada en país (Lógica de tu UI_CONFIG)
country_data = df_countries[df_countries['Country'] == selected_country].iloc[0]
currency = st.sidebar.radio("Moneda", ["USD", "Local"])
exchange_rate = country_data['ER'] if currency == "Local" else 1.0

st.sidebar.metric("Tasa de Cambio (ER)", f"{exchange_rate:,.2f}")

# Selección de Offering
offering_list = df_offering['Offering'].unique()
selected_offering = st.selectbox("Selecciona el Offering (Servicio)", offering_list)

# Selección de SLC
slc_list = df_slc['SLC'].unique()
selected_slc = st.selectbox("Selecciona SLC", slc_list)

# Selección de Riesgo
risk_list = df_risk['Risk'].unique()
selected_risk = st.selectbox("Nivel de Riesgo", risk_list)

# Fechas y Duración
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Inicio de Contrato", date.today())
with col2:
    end_date = st.date_input("Fin de Contrato", date.today())

# Cálculo simple de meses (aproximado)
duration_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
st.info(f"Duración calculada: {duration_months} meses")

# Inputs manuales de costos
st.divider()
st.subheader("Costos Unitarios")
c1, c2, c3 = st.columns(3)
qty = c1.number_input("Cantidad (QTY)", min_value=1, value=1)
unit_cost = c2.number_input("Costo Unitario (USD)", min_value=0.0, value=100.0)

# --- LÓGICA DE CÁLCULO (Simulando tus fórmulas de Excel) ---
# Aquí replicamos la lógica: "si currency=USD, unitcost usd*1..."
final_cost_usd = unit_cost * qty * duration_months

# Factor de contingencia
risk_factor = df_risk[df_risk['Risk'] == selected_risk]['Contingency'].iloc[0]
total_con_riesgo = final_cost_usd * (1 + risk_factor)

# Factor SLC (UPLF)
uplf_row = df_slc[df_slc['SLC'] == selected_slc]
# Nota: Aquí habría que filtrar por Scope si aplica, simplificado por ahora:
uplf = uplf_row['UPLF'].iloc[0] if not uplf_row.empty else 1.0

grand_total = total_con_riesgo * uplf

# --- RESULTADOS ---
st.divider()
st.header("💰 Resultados de la Cotización")

res_col1, res_col2 = st.columns(2)
res_col1.metric("Costo Base Total (USD)", f"${final_cost_usd:,.2f}")
res_col2.metric("Total Final (Inc. Riesgo + SLC)", f"${grand_total:,.2f}")

# Mostrar tabla de desglose
st.write("Detalle de factores aplicados:")
st.json({
    "País": selected_country,
    "Tasa Cambio": exchange_rate,
    "Factor Riesgo": risk_factor,
    "Factor SLC (UPLF)": uplf
})
