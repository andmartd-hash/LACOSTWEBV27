import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Cotizador IBM V19", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; color: #0f62fe; }
    .stMetric { background-color: #f4f4f4; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Cotizador IBM - V19 Cloud App")
st.markdown("Herramienta de costeo blindada para **UI_CONFIG V19**.")

# --- FUNCIÓN DE LIMPIEZA DE DATOS (NUEVA) ---
def clean_decimal(val):
    """
    Convierte cualquier formato (texto, %, comas) a número decimal (float).
    Ejemplo: "2,5%" -> 0.025 | "$ 1.500,00" -> 1500.0
    """
    if pd.isna(val) or val == "":
        return 0.0
    
    s_val = str(val).strip()
    
    # Manejo de porcentajes
    is_percent = False
    if "%" in s_val:
        is_percent = True
        s_val = s_val.replace("%", "")
    
    # Limpieza de simbolos de moneda y miles
    # Asumimos punto como decimal si hay punto y coma, o estructura inglesa
    # Si viene de excel español, la coma es decimal. Intentamos normalizar.
    s_val = s_val.replace("$", "").replace("USD", "").replace(" ", "")
    
    try:
        # Intento directo
        num = float(s_val)
    except:
        try:
            # Intento formato europeo/latam (1.000,00) -> Reemplazar punto por nada, coma por punto
            clean_s = s_val.replace(".", "").replace(",", ".")
            num = float(clean_s)
        except:
            return 0.0
            
    if is_percent:
        return num / 100.0 if num > 1.0 else num # Ajuste heurístico, si es 2% -> 0.02
    return num

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    try:
        # Carga tolerante a errores de delimitador
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
    st.error("⚠️ Error Crítico: No se encuentran los archivos CSV.")
    st.info("Asegúrate de renombrar tus archivos en GitHub a: countries.csv, offering.csv, slc.csv, risk.csv, lplat.csv, lband.csv")
    st.stop()

# --- FUNCIONES AUXILIARES ---
def calcular_duracion(inicio, fin):
    delta = relativedelta(fin, inicio)
    meses = delta.years * 12 + delta.months + (1 if delta.days > 0 else 0)
    return max(1, meses)

# ==========================================
# BARRA LATERAL (SIDEBAR)
# ==========================================
st.sidebar.header("1. Configuración Global")
id_cot = st.sidebar.text_input("ID Cotización", "COT-2025-V19")

# -- PAÍS --
# Leemos columnas desde la 3ra en adelante para encontrar paises (V19 structure: Scope, Country, Arg...)
cols_paises = [c for c in df_countries.columns if c not in ['Scope', 'Country', 'Unnamed: 0']]
pais = st.sidebar.selectbox("País (Country)", cols_paises)

moneda_tipo = st.sidebar.radio("Moneda", ["USD", "Local"], horizontal=True)

# -- TASA DE CAMBIO (ER) --
tasa_er = 1.0
try:
    # Buscamos la fila donde la columna 'Country' contiene 'ER' o 'Exchange Rate'
    # Filtramos ignorando mayúsculas/minúsculas
    row_er = df_countries[df_countries['Country'].astype(str).str.contains("ER", case=False, na=False)]
    if not row_er.empty:
        val_er = row_er[pais].values[0]
        tasa_er = clean_decimal(val_er)
    else:
        st.sidebar.warning("No se encontró fila 'ER' en countries.csv, usando 1.0")
except Exception as e:
    st.sidebar.error(f"Error leyendo ER: {e}")

if moneda_tipo == "Local":
    st.sidebar.info(f"Tasa (ER): {tasa_er:,.2f}")
else:
    st.sidebar.success("Base: USD")

# -- RIESGO (FIXED) --
# Lógica: Buscar Contingency basado en Risk
riesgos_disp = df_risk['Risk'].unique()
riesgo_sel = st.sidebar.selectbox("Nivel de Riesgo", riesgos_disp)

contingencia = 0.0
try:
    row_risk = df_risk[df_risk['Risk'] == riesgo_sel]
    if not row_risk.empty:
        # Usamos la función clean_decimal para evitar el ValueError
        raw_val = row_risk['Contingency'].values[0]
        contingencia = clean_decimal(raw_val)
except:
    pass

st.sidebar.write(f"Contingencia: **{contingencia*100:.1f}%**")

# ==========================================
# CUERPO PRINCIPAL
# ==========================================
with st.expander("📝 Datos Cliente", expanded=True):
    c1, c2, c3 = st.columns(3)
    c1.text_input("Nombre Cliente")
    c2.text_input("Número Cliente")
    d1, d2 = st.columns(2)
    f_ini = d1.date_input("Inicio Contrato", date.today())
    f_fin = d2.date_input("Fin Contrato", date.today().replace(year=date.today().year + 1))
    dur_contrato = calcular_duracion(f_ini, f_fin)
    st.caption(f"Duración calculada: {dur_contrato} meses")

# --- 1. OFFERING ---
st.markdown("---")
st.subheader("🛠️ 1. Offering / Service Cost")

# Selectores
o1, o2 = st.columns([3,1])
offer_list = df_offering['Offering'].unique()
offer_sel = o1.selectbox("Offering", offer_list)

# Info extra
row_off = df_offering[df_offering['Offering'] == offer_sel].iloc[0]
o2.text_input("L40 / Conga", f"{row_off.get('L40','-')} | {row_off.get('Load in conga','-')}", disabled=True)

# Inputs Numéricos
c_qty, c_slc, c_uplf = st.columns([1,2,1])
qty = c_qty.number_input("QTY", min_value=1, value=1)
slc_op = c_slc.selectbox("SLC", df_slc['SLC'].unique())

# UPLF Lookup
uplf = 1.0
try:
    row_slc = df_slc[df_slc['SLC'] == slc_op]
    if not row_slc.empty:
        uplf = clean_decimal(row_slc['UPLF'].values[0])
except:
    pass
c_uplf.metric("Factor UPLF", uplf)

# Fechas Servicio
d_s1, d_s2 = st.columns(2)
fs_ini = d_s1.date_input("Inicio Servicio", f_ini)
fs_fin = d_s2.date_input("Fin Servicio", f_fin)
dur_serv = calcular_duracion(fs_ini, fs_fin)

# Costos Unitarios
u1, u2 = st.columns(2)
costo_unit_usd = u1.number_input("Costo Unitario (USD)", value=0.0, format="%.2f")
# Si la moneda es local, mostramos la conversión estimada
costo_ref_local = costo_unit_usd * tasa_er
u2.text_input(f"Ref. Local ({pais})", value=f"{costo_ref_local:,.2f}", disabled=True)

# CÁLCULO SERVICIO
# Formula V19: ((unitcost usd)*Duration)*qty*UPLF
total_serv_usd = (costo_unit_usd * dur_serv) * qty * uplf

if moneda_tipo == "Local":
    total_serv_final = total_serv_usd * tasa_er
    simbolo = "$"
else:
    total_serv_final = total_serv_usd
    simbolo = "USD"

st.info(f"Total Service Cost: {simbolo} {total_serv_final:,.2f}")

# --- 2. MACHINE / MANAGE ---
st.markdown("---")
st.subheader("💻 2. Machine & Manage Cost")

rad1, rad2 = st.columns([1,3])
tipo_fuente = rad1.radio("Fuente", ["Machine Category", "Brand Rate Full"])

# Selección de DataFrame y Columna Clave
if tipo_fuente == "Machine Category":
    df_active = df_lplat
    key_col = "Machine Category" # Fallback name
else:
    df_active = df_lband
    key_col = "Brand Rate Full" # Fallback name

# Intentamos encontrar la columna correcta del item (suele ser la 2da columna, indice 1)
# En V19 parece llamarse 'MC/RR'
col_item_idx = 1 
items_disp = []
try:
    items_disp = df_active.iloc[:, col_item_idx].dropna().unique().tolist()
except:
    st.error("Error leyendo columnas de items.")

item_maq = rad2.selectbox("Seleccione Item", items_disp)

# Buscar Precio
precio_mes = 0.0
if item_maq:
    try:
        # Filtramos por la columna indice 1
        fila = df_active[df_active.iloc[:, col_item_idx] == item_maq]
        if not fila.empty and pais in fila.columns:
            precio_mes = clean_decimal(fila[pais].values[0])
        else:
            st.warning(f"No hay precio para {pais}")
    except Exception as e:
        st.error(f"Error buscando precio: {e}")

st.write(f"Costo Mensual Base: **USD {precio_mes:,.2f}**")

# Manage Inputs
m1, m2, m3 = st.columns(3)
horas = m1.number_input("Horas", min_value=0.0)
fm_ini = m2.date_input("Inicio Manage", f_ini)
fm_fin = m3.date_input("Fin Manage", f_fin)
dur_man = calcular_duracion(fm_ini, fm_fin)

total_man_usd = precio_mes * horas * dur_man
if moneda_tipo == "Local":
    total_man_final = total_man_usd * tasa_er
else:
    total_man_final = total_man_usd

st.info(f"Total Manage Cost: {simbolo} {total_man_final:,.2f}")

# --- RESUMEN ---
st.markdown("---")
st.header("💰 Resumen Final")

subtotal = total_serv_final + total_man_final
val_riesgo = subtotal * contingencia
total_total = subtotal + val_riesgo

k1, k2, k3 = st.columns(3)
k1.metric("Subtotal", f"{simbolo} {subtotal:,.2f}")
k2.metric(f"Riesgo ({contingencia*100:.1f}%)", f"{simbolo} {val_riesgo:,.2f}")
k3.metric("TOTAL", f"{simbolo} {total_total:,.2f}")

if st.checkbox("Mostrar Dataframes (Debug)"):
    st.write("Countries:", df_countries.head())
    st.write("Risk:", df_risk)
