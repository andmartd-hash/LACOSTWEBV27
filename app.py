import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="LACostWeb V29", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    /* 1. ESTILO ULTRA COMPACTO (Global) */
    html, body, [class*="css"]  {
        font-size: 11px !important; /* Reducimos un punto más */
    }
    
    /* Títulos */
    h1 { font-size: 1.4rem !important; margin-bottom: 0.5rem !important; }
    h2 { font-size: 1.2rem !important; margin-top: 0.5rem !important; }
    h3 { font-size: 1.0rem !important; margin-top: 0.5rem !important; }
    
    /* Inputs y Selectbox COMPACTOS */
    .stSelectbox div[data-baseweb="select"] > div {
        font-size: 11px;
        min-height: 28px;
        padding: 0px 4px;
    }
    .stTextInput input, .stNumberInput input, .stDateInput input {
        font-size: 11px;
        min-height: 28px;
        padding: 0px 4px;
    }
    div[data-baseweb="input"] {
        min-height: 28px;
    }
    
    /* Sidebar Compacta */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        gap: 0.5rem; /* Menos espacio entre elementos del sidebar */
    }

    /* Reducir márgenes del cuerpo principal */
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 2rem;
    }
    
    /* Métricas */
    .stMetric { 
        background-color: #f0f2f6; 
        padding: 4px 8px; 
        border-radius: 4px; 
    }
    .stMetric label { font-size: 10px !important; }
    .stMetric div[data-testid="stMetricValue"] { font-size: 16px !important; }
    
    </style>
    """, unsafe_allow_html=True)

st.title("📊 LACostWeb V29")
st.markdown("Herramienta de costeo **UI_CONFIG V19**.")

# --- FUNCIÓN DE LIMPIEZA DE DATOS ---
def clean_decimal(val):
    if pd.isna(val) or val == "": return 0.0
    s_val = str(val).strip().replace("%", "").replace("$", "").replace("USD", "").replace(" ", "")
    try:
        return float(s_val)
    except:
        try:
            return float(s_val.replace(".", "").replace(",", "."))
        except:
            return 0.0

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    try:
        df_c = pd.read_csv("countries.csv")
        df_o = pd.read_csv("offering.csv")
        df_s = pd.read_csv("slc.csv")
        df_r = pd.read_csv("risk.csv")
        df_lp = pd.read_csv("lplat.csv")
        df_lb = pd.read_csv("lband.csv")
        return df_c, df_o, df_s, df_r, df_lp, df_lb
    except Exception:
        return None, None, None, None, None, None

df_countries, df_offering, df_slc, df_risk, df_lplat, df_lband = load_data()

if df_countries is None:
    st.error("⚠️ Error Crítico: Faltan archivos CSV.")
    st.stop()

# --- FUNCIONES AUXILIARES ---
def calcular_duracion(inicio, fin):
    delta = relativedelta(fin, inicio)
    meses = delta.years * 12 + delta.months + (1 if delta.days > 0 else 0)
    return max(1, meses)

# ==========================================
# BARRA LATERAL (SIDEBAR) - DATOS Y CONFIG
# ==========================================
st.sidebar.header("📝 Configuración y Cliente")

# 1. ID y Cliente (Movido aquí)
id_cot = st.sidebar.text_input("ID Cotización", "COT-2025-V29")
c_name = st.sidebar.text_input("Nombre Cliente")
c_num = st.sidebar.text_input("Número Cliente")

# 2. Fechas Contrato (Compacto en 2 columnas)
col_d1, col_d2 = st.sidebar.columns(2)
f_ini = col_d1.date_input("Inicio Contrato", date.today())
f_fin = col_d2.date_input("Fin Contrato", date.today().replace(year=date.today().year + 1))

dur_contrato = calcular_duracion(f_ini, f_fin)
st.sidebar.info(f"📅 Duración Contrato: **{dur_contrato} Meses**")

st.sidebar.markdown("---")
st.sidebar.subheader("🌎 Parámetros Económicos")

# 3. País y Moneda
cols_paises = [c for c in df_countries.columns if c not in ['Scope', 'Country', 'Unnamed: 0']]
pais = st.sidebar.selectbox("País", cols_paises)

moneda_tipo = st.sidebar.radio("Moneda", ["USD", "Local"], horizontal=True)

# 4. Tasa de Cambio (ER)
tasa_er = 1.0
try:
    row_er = df_countries[df_countries['Country'].astype(str).str.contains("ER", case=False, na=False)]
    if not row_er.empty:
        tasa_er = clean_decimal(row_er[pais].values[0])
except:
    pass

if moneda_tipo == "Local":
    st.sidebar.success(f"Tasa (ER): {tasa_er:,.2f}")
else:
    st.sidebar.success("Base: USD")

# 5. Riesgo (CORREGIDO MANUALMENTE)
riesgos_disp = df_risk['Risk'].unique()
riesgo_sel = st.sidebar.selectbox("Nivel Riesgo", riesgos_disp)

# Mapeo manual para asegurar los valores 2%, 5%, 8%
mapa_riesgo = {
    "Low": 0.02,
    "Medium": 0.05,
    "High": 0.08
}

if riesgo_sel in mapa_riesgo:
    contingencia = mapa_riesgo[riesgo_sel]
else:
    # Fallback por si el nombre es diferente (ej: Bajo, Alto)
    contingencia = 0.0
    try:
        row_risk = df_risk[df_risk['Risk'] == riesgo_sel]
        if not row_risk.empty:
            contingencia = clean_decimal(row_risk['Contingency'].values[0])
    except:
        pass

st.sidebar.write(f"Contingencia: **{contingencia*100:.1f}%**")


# ==========================================
# CUERPO PRINCIPAL (SOLO COSTOS)
# ==========================================

# --- 1. OFFERING ---
st.subheader("🛠️ 1. Offering / Service Cost")

# Fila 1: Selección Offering (Ancho controlado agregando columna vacía '_')
o1, o2, _ = st.columns([3, 1, 2]) 
offer_list = df_offering['Offering'].unique()
offer_sel = o1.selectbox("Offering", offer_list)
# Info extra
row_off = df_offering[df_offering['Offering'] == offer_sel].iloc[0]
o2.text_input("Info", f"L40: {row_off.get('L40','-')} | Conga: {row_off.get('Load in conga','-')}", disabled=True)

# (NUEVO) Campo de Descripción del Servicio
st.text_input("Service Description", placeholder="Descripción del servicio...")

# Fila 2: Cantidades y Factores
c1, c2, c3, c4, _ = st.columns([1, 2, 1, 1, 2])
qty = c1.number_input("QTY", min_value=1, value=1)
slc_op = c2.selectbox("SLC", df_slc['SLC'].unique())

uplf = 1.0
try:
    row_slc = df_slc[df_slc['SLC'] == slc_op]
    if not row_slc.empty:
        uplf = clean_decimal(row_slc['UPLF'].values[0])
except: pass
c3.metric("UPLF", uplf)

# Fechas Servicio
d_s1, d_s2, d_s3, _ = st.columns([2, 2, 1, 2])
fs_ini = d_s1.date_input("Inicio Servicio", f_ini)
fs_fin = d_s2.date_input("Fin Servicio", f_fin)
dur_serv = calcular_duracion(fs_ini, fs_fin)
d_s3.metric("Meses", dur_serv)

# Costos
u1, u2, _ = st.columns([1, 1, 1])
costo_unit_usd = u1.number_input("Costo Unitario (USD)", value=0.0, format="%.2f")
u2.text_input(f"Ref. Local ({pais})", value=f"{costo_unit_usd * tasa_er:,.2f}", disabled=True)

# Total Servicio
total_serv_usd = (costo_unit_usd * dur_serv) * qty * uplf
total_serv_final = total_serv_usd * tasa_er if moneda_tipo == "Local" else total_serv_usd
simbolo = "$" if moneda_tipo == "Local" else "USD"

st.info(f"Total Service: {simbolo} {total_serv_final:,.2f}")

st.markdown("---")

# --- 2. MACHINE / MANAGE ---
st.subheader("💻 2. Machine & Manage Cost")

# 1. (NUEVO) OFFERING PARA MACHINE
m_off1, m_off2, _ = st.columns([3, 1, 2])
# Usamos offer_list que ya cargamos arriba, pero con key única para no chocar
offer_man_sel = m_off1.selectbox("Offering (Manage)", offer_list, key="offer_man")
# Info extra
row_off_man = df_offering[df_offering['Offering'] == offer_man_sel].iloc[0]
m_off2.text_input("Info (Manage)", f"L40: {row_off_man.get('L40','-')} | Conga: {row_off_man.get('Load in conga','-')}", disabled=True)

# 2. SELECCIÓN DE CATEGORÍA Y MÁQUINA
rad1, rad2, _ = st.columns([1, 2, 1])
tipo_fuente = rad1.radio("Fuente Datos", ["Machine Category", "Brand Rate Full"])

if tipo_fuente == "Machine Category":
    df_active = df_lplat
    # CORREGIDO: LPLAT usa columna C (índice 2) para el nombre del item
    col_item_idx = 2 
else:
    df_active = df_lband
    # CORREGIDO: LBAND usa columna D (índice 3) para el nombre del item, "Def"
    col_item_idx = 3

# Items
try:
    items_disp = df_active.iloc[:, col_item_idx].dropna().unique().tolist()
except: items_disp = []

item_maq = rad2.selectbox("Item", items_disp)

precio_mes_raw = 0.0
if item_maq:
    try:
        fila = df_active[df_active.iloc[:, col_item_idx] == item_maq]
        if not fila.empty and pais in fila.columns:
            precio_mes_raw = clean_decimal(fila[pais].values[0])
    except: pass

# --- CORRECCIÓN DE LÓGICA DE MONEDA (Monthly Cost) ---
# Lógica: "si Currency=USD dividir el costo entre ER, si no multiplicar el costo *1"
# Interpretación: El dato viene en Local. Si seleccionamos USD, dividimos.
if moneda_tipo == "USD" and tasa_er > 0:
    precio_mes_final = precio_mes_raw / tasa_er
else:
    precio_mes_final = precio_mes_raw

st.write(f"Costo Mensual Base: **{simbolo} {precio_mes_final:,.2f}**")

# Manage Inputs
m1, m2, m3, m4, _ = st.columns([1, 1, 1, 1, 2])
horas = m1.number_input("Horas", min_value=0.0)
fm_ini = m2.date_input("Inicio Manage", f_ini)
fm_fin = m3.date_input("Fin Manage", f_fin)
dur_man = calcular_duracion(fm_ini, fm_fin)
m4.metric("Meses", dur_man)

# CÁLCULO MANAGE (Usando el precio ya ajustado)
# Total = Precio Ajustado * Horas * Duración
total_man_final = precio_mes_final * horas * dur_man

st.info(f"Total Manage: {simbolo} {total_man_final:,.2f}")

st.markdown("---")

# --- RESUMEN ---
st.header("💰 Resumen Final")
subtotal = total_serv_final + total_man_final
val_riesgo = subtotal * contingencia
total_total = subtotal + val_riesgo

k1, k2, k3 = st.columns(3)
k1.metric("Subtotal", f"{simbolo} {subtotal:,.2f}")
k2.metric(f"Riesgo ({contingencia*100:.1f}%)", f"{simbolo} {val_riesgo:,.2f}")
k3.metric("TOTAL", f"{simbolo} {total_total:,.2f}")
