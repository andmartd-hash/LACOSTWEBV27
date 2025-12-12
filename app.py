import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cotizador Web V18", layout="wide")

st.title("📋 Cotizador Web - IBM V18")
st.markdown("Calculadora de costos basada en `UI_CONFIG`.")

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    try:
        # Cargamos los CSVs con nombres estandarizados
        df_countries = pd.read_csv("countries.csv")
        df_offering = pd.read_csv("offering.csv")
        df_slc = pd.read_csv("slc.csv")
        df_risk = pd.read_csv("risk.csv")
        # Cargamos las dos bases de máquinas
        df_lplat = pd.read_csv("lplat.csv") # Machine Category
        df_lband = pd.read_csv("lband.csv") # Brand Rate
        return df_countries, df_offering, df_slc, df_risk, df_lplat, df_lband
    except FileNotFoundError as e:
        return None, None, None, None, None, None

df_countries, df_offering, df_slc, df_risk, df_lplat, df_lband = load_data()

if df_countries is None:
    st.error("⚠️ Error crítico: Faltan archivos. Asegúrate de tener en GitHub: countries.csv, offering.csv, slc.csv, risk.csv, lplat.csv, lband.csv")
    st.stop()

# --- FUNCIONES DE AYUDA ---
def calcular_meses(inicio, fin):
    delta = relativedelta(fin, inicio)
    return delta.years * 12 + delta.months + (1 if delta.days > 0 else 0)

# ==========================================
# SECCIÓN 1: CABECERA Y DATOS DEL CLIENTE
# ==========================================
st.sidebar.header("Configuración Global")

id_cotizacion = st.sidebar.text_input("ID Cotización", value="COT-001")

# --- PAÍS Y MONEDA ---
# Extraemos columnas de países del archivo lplat para asegurar coincidencia
# Asumimos que las columnas de países empiezan desde la columna 4 en adelante (Scope, MC/RR, Plat, Def...)
paises_disponibles = ["Argentina", "Brazil", "Chile", "Colombia", "Ecuador", "Peru", "Uruguay", "Venezuela", "Mexico"]
pais_seleccionado = st.sidebar.selectbox("País (Country)", paises_disponibles)

moneda = st.sidebar.selectbox("Moneda (Currency)", ["USD", "Local"])

# --- TASA DE CAMBIO (ER) ---
try:
    # Buscamos la fila de ER en countries.csv
    # Ajuste: Buscamos en la columna 'Country' o similar la fila que diga 'ER' o 'Exchange Rate'
    # Según tu CSV, parece que la estructura es Scope, Country, y luego las columnas de valores.
    # Vamos a intentar localizar el valor dinámicamente.
    if pais_seleccionado in df_countries.columns:
        # Intentamos obtener la fila donde la columna 1 (Country) sea 'ER'
        er_val = df_countries.loc[df_countries.iloc[:, 1] == 'ER', pais_seleccionado]
        if not er_val.empty:
            tasa_cambio = float(er_val.values[0])
        else:
            # Fallback manual si la estructura del CSV cambia
            tasas = {"Argentina": 1428.94, "Brazil": 5.34, "Chile": 934.7, "Colombia": 3775.22, "Mexico": 18.42, "Peru": 3.37}
            tasa_cambio = tasas.get(pais_seleccionado, 1.0)
    else:
        tasa_cambio = 1.0
except:
    tasa_cambio = 1.0

if moneda == "USD":
    st.sidebar.success(f"Moneda Base: USD")
else:
    st.sidebar.warning(f"Moneda Local. Tasa aplicada: {tasa_cambio:,.2f}")

# --- RIESGO ---
lista_riesgos = df_risk['Risk'].dropna().unique().tolist()
riesgo_seleccionado = st.sidebar.selectbox("Nivel de Riesgo (QA Risk)", lista_riesgos)
contingencia = df_risk[df_risk['Risk'] == riesgo_seleccionado]['Contingency'].values[0]
st.sidebar.write(f"Contingencia: {contingencia * 100:.0f}%")

# --- DATOS CLIENTE ---
c1, c2, c3 = st.columns(3)
customer_name = c1.text_input("Nombre Cliente")
customer_number = c2.text_input("Número Cliente")
c3.date_input("Fecha Cotización", date.today(), disabled=True)

d1, d2, d3 = st.columns(3)
contract_start = d1.date_input("Inicio Contrato", date.today())
contract_end = d2.date_input("Fin Contrato", date.today().replace(year=date.today().year + 1))
contract_duration = calcular_meses(contract_start, contract_end)
d3.metric("Duración Contrato", f"{contract_duration} Meses")

st.divider()

# ==========================================
# SECCIÓN 2: OFFERING / SERVICE COST
# ==========================================
st.subheader("1. Offering / Service Cost")

o1, o2, o3 = st.columns([2, 1, 1])
ofertas = df_offering['Offering'].unique().tolist()
offering_sel = o1.selectbox("Servicio (Offering)", ofertas)

# Info extra
row_off = df_offering[df_offering['Offering'] == offering_sel].iloc[0]
l40_val = row_off['L40'] if 'L40' in df_offering.columns else "-"
conga_val = row_off['Load in conga'] if 'Load in conga' in df_offering.columns else "-"
o2.text_input("L40 Code", l40_val, disabled=True)
o3.text_input("Conga Load", conga_val, disabled=True)

# Detalles Servicio
s1, s2, s3, s4 = st.columns(4)
qty = s1.number_input("Cantidad (QTY)", min_value=1, value=1)
slc_list = df_slc['SLC'].unique()
slc_sel = s2.selectbox("SLC", slc_list)

# Buscando UPLF (Factor de Servicio)
try:
    uplf_val = df_slc[df_slc['SLC'] == slc_sel]['UPLF'].values[0]
except:
    uplf_val = 1.0

s2.caption(f"Factor UPLF: {uplf_val}")

service_start = s3.date_input("Inicio Servicio", contract_start)
service_end = s4.date_input("Fin Servicio", contract_end)
service_duration = calcular_meses(service_start, service_end)

# Costos
uc1, uc2 = st.columns(2)
unit_cost_usd = uc1.number_input("Costo Unitario (USD)", min_value=0.0, value=0.0, format="%.2f")

# Cálculo Unitario Local (informativo)
unit_cost_local = unit_cost_usd * tasa_cambio
uc2.metric("Costo Unitario Local (Ref)", f"{unit_cost_local:,.2f}")

# --- CÁLCULO TOTAL SERVICIO ---
# Corregido: Usamos 'uplf_val' que definimos arriba
# Formula UI: ((unitcost usd)*Duration)*qty*UPLF
costo_servicio_usd = (unit_cost_usd * service_duration) * qty * uplf_val

if moneda == "Local":
    costo_servicio_final = costo_servicio_usd * tasa_cambio
    simbolo = "$"
else:
    costo_servicio_final = costo_servicio_usd
    simbolo = "USD"

st.info(f"Total Service Cost: {simbolo} {costo_servicio_final:,.2f}")

st.divider()

# ==========================================
# SECCIÓN 3: MACHINE / MANAGE COST
# ==========================================
st.subheader("2. Machine Category / Manage Cost")

m1, m2 = st.columns(2)
tipo_maquina = m1.radio("Tipo de Categoría", ["Machine Category", "Brand Rate Full"], horizontal=True)

# Lógica de Selección de Lista según el archivo CSV correcto
if tipo_maquina == "Machine Category":
    # Usamos lplat.csv. Asumimos columna 'Machine Category' es la B (index 1) o se llama 'Machine Category'
    # Viendo tu snippet, la columna header es 'MC/RR' o 'Machine Category'
    # Buscamos la columna que tenga los nombres
    lista_items = df_lplat.iloc[:, 1].dropna().unique().tolist() # Columna B
    df_activo = df_lplat
else:
    # Usamos lband.csv (Brand Rate)
    lista_items = df_lband.iloc[:, 1].dropna().unique().tolist() # Columna B
    df_activo = df_lband

item_seleccionado = m2.selectbox("Seleccionar Item", lista_items)

# Búsqueda de Costo Mensual
costo_mensual = 0.0
try:
    # Filtramos la fila
    fila = df_activo[df_activo.iloc[:, 1] == item_seleccionado]
    if not fila.empty:
        # Buscamos la columna del país
        if pais_seleccionado in df_activo.columns:
            val = fila[pais_seleccionado].values[0]
            costo_mensual = float(val) if pd.notnull(val) else 0.0
        else:
            st.warning(f"No hay precio para {pais_seleccionado} en este item.")
except Exception as e:
    st.error(f"Error buscando precio: {e}")

st.write(f"Costo Mensual Base ({pais_seleccionado}): USD {costo_mensual:,.2f}")

# Inputs Manage
man1, man2, man3 = st.columns(3)
horas = man1.number_input("Horas Dedicadas", min_value=0.0, value=0.0)
manage_start = man2.date_input("Inicio Manage", contract_start)
manage_end = man3.date_input("Fin Manage", contract_end)
manage_duration = calcular_meses(manage_start, manage_end)

# --- CÁLCULO TOTAL MANAGE ---
costo_manage_usd = costo_mensual * horas * manage_duration

if moneda == "Local":
    # Si la base es USD y queremos local, multiplicamos por ER
    costo_manage_final = costo_manage_usd * tasa_cambio
else:
    costo_manage_final = costo_manage_usd

st.info(f"Total Manage Cost: {simbolo} {costo_manage_final:,.2f}")

# ==========================================
# TOTALES FINALES
# ==========================================
st.divider()
st.header("💰 Resumen Financiero")

total_neto = costo_servicio_final + costo_manage_final
total_con_riesgo = total_neto * (1 + contingencia)

col_fin1, col_fin2, col_fin3 = st.columns(3)
col_fin1.metric(f"Subtotal Neto ({moneda})", f"{total_neto:,.2f}")
col_fin2.metric("Contingencia", f"{contingencia*100}%")
col_fin3.metric(f"TOTAL FINAL ({moneda})", f"{total_con_riesgo:,.2f}")

if st.button("Generar Reporte"):
    st.balloons()
    st.success(f"Cotización generada para {customer_name}. Total: {simbolo} {total_con_riesgo:,.2f}")
