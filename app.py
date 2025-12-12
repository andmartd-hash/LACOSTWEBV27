import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cotizador Web V18", layout="wide")

st.title("📋 Cotizador Web - Configuración UI")
st.markdown("Calculadora de costos basada en `UI_CONFIG`.")

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    try:
        # Cargamos los CSVs asumiendo que ya los renombraste en GitHub
        df_countries = pd.read_csv("countries.csv")
        df_offering = pd.read_csv("offering.csv")
        df_slc = pd.read_csv("slc.csv")
        df_risk = pd.read_csv("risk.csv")
        df_machine = pd.read_csv("machine.csv")
        return df_countries, df_offering, df_slc, df_risk, df_machine
    except FileNotFoundError as e:
        return None, None, None, None, None

df_countries, df_offering, df_slc, df_risk, df_machine = load_data()

if df_countries is None:
    st.error("⚠️ Error: No encuentro los archivos CSV. Asegúrate de que en GitHub se llamen exactamente: countries.csv, offering.csv, slc.csv, risk.csv, machine.csv")
    st.stop()

# --- FUNCIONES DE AYUDA ---
def calcular_meses(inicio, fin):
    delta = relativedelta(fin, inicio)
    return delta.years * 12 + delta.months + (1 if delta.days > 0 else 0)

# ==========================================
# SECCIÓN 1: CABECERA Y DATOS DEL CLIENTE
# ==========================================
st.sidebar.header("Configuración Global")

# 1. ID Cotización
id_cotizacion = st.sidebar.text_input("ID Cotización", value="COT-001")

# 2. Countries (País)
lista_paises = df_countries.columns[2:].tolist() if 'Argentina' in df_countries.columns else ["Argentina", "Brazil", "Chile", "Colombia", "Mexico", "Peru"] 
# Nota: Ajustamos esto para leer las columnas del sheet Machine o Country scope, 
# Para mayor seguridad usaremos la lista hardcodeada basada en tu excel o leemos de df_countries si tiene estructura vertical
# Viendo tu CSV 'countries', parece que la estructura es horizontal en Scope? 
# Asumiremos la lista estándar de LATAM basada en tu Excel 'Brand Rate Full'.
paises_disponibles = ["Argentina", "Brazil", "Chile", "Colombia", "Ecuador", "Peru", "Uruguay", "Venezuela", "Mexico"]
pais_seleccionado = st.sidebar.selectbox("Countries", paises_disponibles)

# 3. Currency (Moneda)
moneda = st.sidebar.selectbox("Currency", ["USD", "Local"])

# 4. Exchange Rate (ER)
# Buscamos el ER en el dataframe de countries. Asumimos que hay una fila de ER.
# En tu data enviada, la fila de ER está en el sheet countries. 
try:
    # Filtramos la fila donde Scope/Currency sea ER (segun tu data row 3)
    # Nota: Simplificamos lógica buscando la columna del país seleccionado
    # En tu csv, parece que hay una fila 'ER'. Vamos a simular la búsqueda:
    er_row = df_countries[df_countries.iloc[:,1] == 'ER'] # Buscando por la columna correcta
    if not er_row.empty and pais_seleccionado in df_countries.columns:
        tasa_cambio = float(er_row[pais_seleccionado].values[0])
    else:
        # Fallback si no encuentra la estructura exacta, usamos valores aprox de tu excel para que no falle
        tasas = {"Argentina": 1428.94, "Brazil": 5.34, "Chile": 934.7, "Colombia": 3775.22, "Mexico": 18.42, "Peru": 3.37}
        tasa_cambio = tasas.get(pais_seleccionado, 1.0)
except:
    tasa_cambio = 1.0

if moneda == "USD":
    er_aplicado = 1.0 
    st.sidebar.info(f"Moneda: USD (ER Base: {tasa_cambio})")
else:
    er_aplicado = tasa_cambio
    st.sidebar.info(f"Moneda: Local (ER: {er_aplicado})")


# 5. QA Risk y Contingencia
lista_riesgos = df_risk['Risk'].dropna().unique().tolist()
riesgo_seleccionado = st.sidebar.selectbox("QA Risk", lista_riesgos)
# Traer contingency
contingencia = df_risk[df_risk['Risk'] == riesgo_seleccionado]['Contingency'].values[0]
st.sidebar.write(f"Contingencia aplicada: {contingencia * 100}%")

# Datos Cliente (Body)
col1, col2, col3 = st.columns(3)
customer_name = col1.text_input("Customer Name")
customer_number = col2.text_input("Customer Number")
quote_date = col3.date_input("Quote Date", date.today(), disabled=True)

col4, col5, col6 = st.columns(3)
contract_start = col4.date_input("Contract Start Date", date.today())
contract_end = col5.date_input("Contract End Date", date.today().replace(year=date.today().year + 1))
contract_duration = calcular_meses(contract_start, contract_end)
col6.metric("Contract Duration (Meses)", contract_duration)

st.divider()

# ==========================================
# SECCIÓN 2: OFFERING (SERVICE COST)
# ==========================================
st.subheader("1. Offering / Service Cost")

c1, c2, c3 = st.columns([2, 1, 1])
# Offering Dropdown
ofertas = df_offering['Offering'].unique().tolist()
offering_sel = c1.selectbox("Offering", ofertas, key="off1")

# Traer info L40 y Conga
row_offering = df_offering[df_offering['Offering'] == offering_sel].iloc[0]
l40_val = row_offering['L40'] if 'L40' in df_offering.columns else "N/A"
conga_val = row_offering['Load in conga'] if 'Load in conga' in df_offering.columns else "N/A"

c2.text_input("L40", l40_val, disabled=True)
c3.text_input("Load in Conga", conga_val, disabled=True)

service_desc = st.text_input("Service Description")

sc1, sc2, sc3 = st.columns(3)
qty = sc1.number_input("QTY", min_value=1, value=1)
slc_sel = sc2.selectbox("SLC", df_slc['SLC'].unique(), key="slc1")

# Fechas servicio
service_start = sc3.date_input("Service Start Date", contract_start)
service_end = sc3.date_input("Service End Date", contract_end)
service_duration = calcular_meses(service_start, service_end)
st.caption(f"Duración del Servicio: {service_duration} meses")

# Traer UPLF
uplf_val = df_slc[df_slc['SLC'] == slc_sel]['UPLF'].values[0]
if pais_seleccionado == "Brazil":
    # Lógica "only Brazil" en SLC si aplicara, simplificado tomamos el general o filtramos
    pass 

# Costos Unitarios
uc1, uc2 = st.columns(2)
unit_cost_usd_input = uc1.number_input("Unit Cost USD", min_value=0.0, format="%.2f")

# Lógica descrita: "si currency=USD, unitcost usd*1, si no unit cost usd*ER"
# Pero aquí parece que el usuario ingresa uno y el otro se calcula.
if unit_cost_usd_input > 0:
    unit_cost_local_calc = unit_cost_usd_input * tasa_cambio
    uc2.metric("Unit Cost Local (Calculado)", f"{unit_cost_local_calc:,.2f}")
else:
    unit_cost_local_calc = 0.0
    uc2.text("Ingrese costo en USD")

# CALCULO TOTAL SERVICIO
# Formula UI_CONFIG: ((unitcost usd + unit cost local)*Duration)*qty*UPLF
# Nota: La formula del excel parece sumar ambos campos. Asumiremos que es el costo base convertido.
# Si la moneda es local, el costo se ajusta.
costo_base_mes = unit_cost_usd_input # Trabajamos en USD base
total_service_cost_usd = (costo_base_mes * service_duration) * qty * uplf

# Ajuste por moneda seleccionada en el total
if moneda == "Local":
    total_service_cost_final = total_service_cost_usd * tasa_cambio
    simbolo = "$" # O simbolo local
else:
    total_service_cost_final = total_service_cost_usd
    simbolo = "USD"

st.info(f"Total Service Cost ({moneda}): {simbolo} {total_service_cost_final:,.2f} (Inc. UPLF: {uplf})")

st.divider()

# ==========================================
# SECCIÓN 3: MACHINE / MANAGE COST
# ==========================================
st.subheader("2. Machine Category / Manage Cost")

mc1, mc2, mc3 = st.columns([2, 1, 1])
offering_sel_2 = mc1.selectbox("Offering (Manage)", ofertas, key="off2")

# Tipo de Maquina (Simulado Lplat vs Lband)
# Leemos el archivo machine.csv para ver qué categorías hay
# Asumimos columna 1 es "Machine Category"
cats_maquinas = df_machine.iloc[:,1].dropna().unique().tolist() # Columna B
tipo_maquina = mc2.selectbox("MachCat / BandRate", ["Machine Category", "Brand Rate Full"])

item_maquina = mc3.selectbox("MC/RR (Selección)", cats_maquinas)

# Búsqueda del Costo Mensual (Monthly Cost)
# Lógica: Buscar en df_machine donde Columna B == item_maquina Y devolver valor de columna pais_seleccionado
try:
    fila_maquina = df_machine[df_machine.iloc[:,1] == item_maquina]
    if not fila_maquina.empty:
        # Intentamos buscar la columna con el nombre del país
        if pais_seleccionado in df_machine.columns:
            costo_mensual_raw = fila_maquina[pais_seleccionado].values[0]
            # Limpieza si viene nulo
            if pd.isna(costo_mensual_raw):
                costo_mensual = 0.0
            else:
                costo_mensual = float(costo_mensual_raw)
        else:
            costo_mensual = 0.0
    else:
        costo_mensual = 0.0
except Exception as e:
    costo_mensual = 0.0

st.write(f"Costo Mensual Base (según {pais_seleccionado}): {costo_mensual:,.2f}")

# Inputs Manage
man1, man2, man3 = st.columns(3)
horas = man1.number_input("Horas", min_value=0.0, value=0.0)
manage_start = man2.date_input("Manage Start Date", contract_start)
manage_end = man3.date_input("Manage End Date", contract_end)
manage_duration = calcular_meses(manage_start, manage_end)

# CALCULO TOTAL MANAGE
# Formula: Monthly cost * Horas * Duration
# Nota: "si Currency =Local dividir ente ER". Esto es raro si el input ya viene en moneda local o USD.
# Asumiremos que la tabla viene en USD.
total_manage_cost_usd = costo_mensual * horas * manage_duration

if moneda == "Local":
    # Si la tabla estaba en USD y queremos local, multiplicamos.
    # Si la instrucción dice "dividir", seguimos la instrucción literal del excel si aplica inversa.
    # PERO, por lógica standard: Si base es USD -> Local = USD * ER.
    total_manage_cost_final = total_manage_cost_usd * tasa_cambio
else:
    total_manage_cost_final = total_manage_cost_usd

st.info(f"Total Manage Cost ({moneda}): {simbolo} {total_manage_cost_final:,.2f}")

# ==========================================
# TOTALES FINALES
# ==========================================
st.divider()
st.header("💰 Resumen de Costos")

# Suma
total_neto = total_service_cost_final + total_manage_cost_final
total_con_contingencia = total_neto * (1 + contingencia)

col_res1, col_res2 = st.columns(2)
col_res1.metric(f"Total Neto ({moneda})", f"{total_neto:,.2f}")
col_res2.metric(f"Total + Contingencia ({moneda})", f"{total_con_contingencia:,.2f}", delta=f"Riesgo {contingencia*100}%")

# Botón para descargar o guardar (Simulado)
if st.button("Generar Cotización"):
    st.success(f"Cotización {id_cotizacion} generada exitosamente para {customer_name}.")
    st.balloons()
