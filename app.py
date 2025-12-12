import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Cotizador IBM V18", layout="wide", page_icon="📊")

# Estilos CSS para que se vea más corporativo (IBM Style)
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; color: #0f62fe; }
    .stMetric { background-color: #f4f4f4; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Cotizador IBM - Cloud Web App")
st.markdown("Herramienta de costeo basada en **UI_CONFIG V18**.")

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    try:
        # Leemos los CSV asegurando que no haya problemas de encoding
        df_c = pd.read_csv("countries.csv")
        df_o = pd.read_csv("offering.csv")
        df_s = pd.read_csv("slc.csv")
        df_r = pd.read_csv("risk.csv")
        df_lp = pd.read_csv("lplat.csv") # Machine Category
        df_lb = pd.read_csv("lband.csv") # Brand Rate
        return df_c, df_o, df_s, df_r, df_lp, df_lb
    except Exception as e:
        return None, None, None, None, None, None

df_countries, df_offering, df_slc, df_risk, df_lplat, df_lband = load_data()

# Validación de carga
if df_countries is None:
    st.error("⚠️ Error Crítico: No se encuentran los archivos CSV en el repositorio.")
    st.warning("Verifica que los archivos se llamen exactamente: countries.csv, offering.csv, slc.csv, risk.csv, lplat.csv, lband.csv")
    st.stop()

# --- FUNCIONES AUXILIARES ---
def calcular_duracion(inicio, fin):
    delta = relativedelta(fin, inicio)
    meses = delta.years * 12 + delta.months + (1 if delta.days > 0 else 0)
    return max(1, meses) # Mínimo 1 mes

def limpiar_moneda(valor):
    """Convierte cualquier basura de texto a float"""
    if pd.isna(valor): return 0.0
    try:
        # Quitamos simbolos de moneda si existen y convertimos
        return float(str(valor).replace('$','').replace(',','').strip())
    except:
        return 0.0

# ==========================================
# BARRA LATERAL (SIDEBAR) - CONFIGURACIÓN
# ==========================================
st.sidebar.header("1. Configuración Global")

id_cot = st.sidebar.text_input("ID Cotización", "COT-2025-001")

# -- PAÍS --
# Extraemos columnas de países (Asumimos columnas desde la 5ta en adelante en countries.csv)
# Ojo: Hardcodeamos la lista para seguridad según tu UI_Config
lista_paises = ["Argentina", "Brazil", "Chile", "Colombia", "Ecuador", "Peru", "Uruguay", "Venezuela", "Mexico"]
pais = st.sidebar.selectbox("País (Country)", lista_paises)

moneda_tipo = st.sidebar.radio("Moneda (Currency)", ["USD", "Local"], horizontal=True)

# -- TASA DE CAMBIO (ER) --
tasa_er = 1.0
try:
    # Buscamos la fila donde la columna 'Country' (o col 1) es 'ER'
    # df_countries structure: Scope, Country, Arg, Bra...
    row_er = df_countries[df_countries.iloc[:, 1] == 'ER']
    if not row_er.empty and pais in row_er.columns:
        tasa_er = limpiar_moneda(row_er[pais].values[0])
    else:
        st.sidebar.error(f"No se encontró ER para {pais}, usando 1.0")
except:
    pass

if moneda_tipo == "Local":
    st.sidebar.info(f"Tasa de Cambio (ER): {tasa_er:,.2f}")
else:
    st.sidebar.success("Moneda Base: USD")

# -- RIESGO (FIX DEL ERROR) --
riesgos = df_risk['Risk'].dropna().unique().tolist()
riesgo_sel = st.sidebar.selectbox("Nivel de Riesgo (QA Risk)", riesgos)

# Aquí estaba el error: forzamos conversión a float
try:
    val_risk = df_risk[df_risk['Risk'] == riesgo_sel]['Contingency'].values[0]
    contingencia = float(val_risk)
except:
    contingencia = 0.0

st.sidebar.write(f"Contingencia aplicada: **{contingencia * 100:.1f}%**")

# ==========================================
# CUERPO PRINCIPAL
# ==========================================

# --- DATOS CLIENTE ---
with st.expander("📝 Datos del Cliente y Contrato", expanded=True):
    c1, c2, c3 = st.columns(3)
    c1.text_input("Customer Name", "Cliente Prueba")
    c2.text_input("Customer Number", "00001")
    c3.date_input("Quote Date", date.today(), disabled=True)

    d1, d2, d3 = st.columns(3)
    f_inicio = d1.date_input("Contract Start", date.today())
    f_fin = d2.date_input("Contract End", date.today().replace(year=date.today().year + 1))
    duracion_contrato = calcular_duracion(f_inicio, f_fin)
    d3.metric("Duración Contrato", f"{duracion_contrato} Meses")

# --- SECCIÓN 1: OFFERING / SERVICE ---
st.markdown("---")
st.subheader("🛠️ 1. Offering / Service Cost")

col_off1, col_off2 = st.columns([3, 1])
offering_list = df_offering['Offering'].unique()
offer_sel = col_off1.selectbox("Seleccione Offering", offering_list)

# Info extra del offering
row_off = df_offering[df_offering['Offering'] == offer_sel].iloc[0]
l40_txt = str(row_off['L40']) if 'L40' in row_off else "-"
conga_txt = str(row_off['Load in conga']) if 'Load in conga' in row_off else "-"
col_off2.caption(f"**L40:** {l40_txt} | **Conga:** {conga_txt}")

# Detalles del cálculo
s1, s2, s3, s4 = st.columns(4)
qty = s1.number_input("Cantidad (QTY)", min_value=1, value=1)
slc_op = s2.selectbox("SLC", df_slc['SLC'].unique())

# Buscar UPLF
try:
    uplf_raw = df_slc[df_slc['SLC'] == slc_op]['UPLF'].values[0]
    uplf = float(uplf_raw)
except:
    uplf = 1.0
s2.caption(f"Factor UPLF: {uplf}")

fs_ini = s3.date_input("Service Start", f_inicio)
fs_fin = s4.date_input("Service End", f_fin)
duracion_servicio = calcular_duracion(fs_ini, fs_fin)

# Costos
uc1, uc2 = st.columns(2)
costo_unit_usd = uc1.number_input("Costo Unitario (USD)", min_value=0.0, value=0.0, format="%.2f")

# Informativo Local
uc2.text_input("Costo Unitario Local (Ref)", value=f"{costo_unit_usd * tasa_er:,.2f}", disabled=True)

# CÁLCULO FINAL SERVICIO
# Formula: (Unit Cost * Duration * Qty * UPLF)
total_serv_usd = (costo_unit_usd * duracion_servicio) * qty * uplf

if moneda_tipo == "Local":
    total_serv_final = total_serv_usd * tasa_er
    simbolo = "$"
else:
    total_serv_final = total_serv_usd
    simbolo = "USD"

st.info(f"💰 Total Service Cost: {simbolo} {total_serv_final:,.2f}")

# --- SECCIÓN 2: MACHINE / MANAGE ---
st.markdown("---")
st.subheader("💻 2. Machine Category / Manage Cost")

m1, m2 = st.columns(2)
# Selector de tipo de base de datos
tipo_base = m1.radio("Fuente de Datos", ["Machine Category (LPLAT)", "Brand Rate Full (LBAND)"], horizontal=True)

# Lógica para seleccionar el DataFrame correcto
if "LPLAT" in tipo_base:
    df_active = df_lplat
    col_item_name = 'MC/RR' # Asumiendo nombre de columna estándar o indice 1
else:
    df_active = df_lband
    col_item_name = 'MC/RR'

# Obtener lista de items
try:
    # Usamos iloc[:, 1] porque el nombre suele estar en la segunda columna
    items_maquina = df_active.iloc[:, 1].dropna().unique().tolist()
    item_maq = m2.selectbox("Seleccione Hardware/Servicio", items_maquina)
except:
    st.error("Error leyendo columnas de máquina. Verifique estructura CSV.")
    items_maquina = []
    item_maq = None

# Buscar Precio Mensual
precio_mensual_base = 0.0
if item_maq:
    try:
        # Filtramos la fila
        fila = df_active[df_active.iloc[:, 1] == item_maq]
        # Buscamos la columna del país
        if pais in fila.columns:
            val_raw = fila[pais].values[0]
            precio_mensual_base = limpiar_moneda(val_raw)
        else:
            st.warning(f"No existe precio para {pais} en este item.")
    except Exception as e:
        st.error(f"Error extrayendo precio: {e}")

st.write(f"Costo Mensual Base ({pais}): **USD {precio_mensual_base:,.2f}**")

# Inputs Manage
man1, man2, man3 = st.columns(3)
horas = man1.number_input("Horas Dedicadas", min_value=0.0, value=0.0)
fm_ini = man2.date_input("Manage Start", f_inicio)
fm_fin = man3.date_input("Manage End", f_fin)
duracion_manage = calcular_duracion(fm_ini, fm_fin)

# CÁLCULO FINAL MANAGE
total_manage_usd = precio_mensual_base * horas * duracion_manage

if moneda_tipo == "Local":
    total_manage_final = total_manage_usd * tasa_er
else:
    total_manage_final = total_manage_usd

st.info(f"💰 Total Manage Cost: {simbolo} {total_manage_final:,.2f}")

# ==========================================
# RESUMEN FINANCIERO
# ==========================================
st.markdown("---")
st.header("📑 Resumen Financiero")

# Totales
subtotal = total_serv_final + total_manage_final
monto_riesgo = subtotal * contingencia
gran_total = subtotal + monto_riesgo

# Tarjetas métricas
c_res1, c_res2, c_res3, c_res4 = st.columns(4)
c_res1.metric("Subtotal", f"{simbolo} {subtotal:,.2f}")
c_res2.metric("Riesgo (Contingencia)", f"{contingencia*100:.1f}%", f"+ {simbolo} {monto_riesgo:,.2f}")
c_res3.metric("TOTAL FINAL", f"{simbolo} {gran_total:,.2f}", delta_color="normal")
c_res4.metric("Moneda", moneda_tipo, f"ER: {tasa_er:,.2f}")

# JSON para depuración (oculto en expander)
with st.expander("Ver desglose técnico"):
    st.json({
        "País": pais,
        "ER Aplicado": tasa_er,
        "UPLF": uplf,
        "Contingencia": contingencia,
        "Duración Contrato": duracion_contrato,
        "Costo Mensual Máquina": precio_mensual_base
    })

```

### Paso 3: Verifica tu `requirements.txt`
Asegúrate de que este archivo en GitHub tenga estas líneas para que funcionen las fechas y los datos:

```text
streamlit
pandas
python-dateutil
