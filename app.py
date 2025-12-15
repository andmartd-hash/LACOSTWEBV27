import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="LACostWeb V29", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    /* ESTILO ULTRA COMPACTO Y UNIFORME */
    html, body, [class*="css"]  { font-size: 11px !important; }
    
    h1 { font-size: 1.4rem !important; margin-bottom: 0.5rem !important; }
    h2 { font-size: 1.2rem !important; margin-top: 0.5rem !important; }
    h3 { font-size: 1.0rem !important; margin-top: 0.5rem !important; }
    
    /* UNIFORMIZAR ALTURA DE TODOS LOS CAMPOS (GROSOR) */
    .stTextInput div[data-baseweb="input"],
    .stNumberInput div[data-baseweb="input"],
    .stSelectbox div[data-baseweb="select"],
    .stDateInput div[data-baseweb="input"],
    .stSelectbox div[data-baseweb="select"] > div {
        height: 30px !important;
        min-height: 30px !important;
        border-radius: 4px !important;
        align-items: center !important;
    }
    
    /* Texto interno de inputs */
    .stTextInput input, 
    .stNumberInput input, 
    .stDateInput input {
        font-size: 11px !important;
        height: 30px !important;
        min-height: 30px !important;
        padding: 0px 8px !important;
    }

    /* Ajustes de espaciado en sidebar y main */
    section[data-testid="stSidebar"] .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] { gap: 0.5rem; }
    .block-container { padding-top: 0.5rem; padding-bottom: 2rem; }
    
    /* Métricas */
    .stMetric { background-color: #f0f2f6; padding: 4px 8px; border-radius: 4px; }
    .stMetric label { font-size: 10px !important; }
    .stMetric div[data-testid="stMetricValue"] { font-size: 16px !important; }
    
    /* Estilo de Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e6f3ff;
        border-bottom: 2px solid #0f62fe;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 LACostWeb V29")
st.markdown("Herramienta de costeo **UI_CONFIG V19**.")

# --- FUNCIÓN DE LIMPIEZA DE DATOS ---
def clean_decimal(val):
    if pd.isna(val) or val == "": return 0.0
    s_val = str(val).strip().replace("%", "").replace("$", "").replace("USD", "").replace(" ", "")
    
    try:
        # LÓGICA ESTÁNDAR (US): 1,234.56
        clean = s_val.replace(",", "")
        return float(clean)
    except:
        return 0.0

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    try:
        df_c = pd.read_csv("countries.csv", dtype=str)
        df_o = pd.read_csv("offering.csv", dtype=str)
        df_s = pd.read_csv("slc.csv", dtype=str)
        df_r = pd.read_csv("risk.csv", dtype=str)
        df_lp = pd.read_csv("lplat.csv", dtype=str)
        df_lb = pd.read_csv("lband.csv", dtype=str)
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
    # Cálculo preciso con decimales (días / 30)
    meses_totales = delta.years * 12 + delta.months + (delta.days / 30.0)
    return max(0.1, round(meses_totales, 1))

# ==========================================
# BARRA LATERAL
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("📝 Cliente y Contrato")

# ID Automático (Consecutivo en Sesión)
if 'consecutivo_id' not in st.session_state:
    st.session_state.consecutivo_id = 1

id_cot_str = f"{st.session_state.consecutivo_id:04d}"
st.sidebar.text_input("ID Cotización", value=id_cot_str, disabled=True)

# Cliente
c_name = st.sidebar.text_input("Nombre Cliente")
c_num = st.sidebar.text_input("Número Cliente")

# Fechas Contrato
col_d1, col_d2 = st.sidebar.columns(2)
f_ini = col_d1.date_input("Inicio Contrato", date.today())
f_fin = col_d2.date_input("Fin Contrato", date.today().replace(year=date.today().year + 1))

dur_contrato = calcular_duracion(f_ini, f_fin)
st.sidebar.info(f"📅 Duración Contrato: **{dur_contrato} Meses**")

st.sidebar.markdown("---")
st.sidebar.subheader("🌎 Parámetros Económicos")

# País y Moneda
cols_paises = [c for c in df_countries.columns if c not in ['Scope', 'Country', 'Unnamed: 0', 'Currency', 'ER', 'Tax']]
pais = st.sidebar.selectbox("País", cols_paises)

moneda_tipo = st.sidebar.radio("Moneda", ["USD", "Local"], horizontal=True)

# Lógica Especial Brasil
is_brazil = (pais == 'Brazil')

# Tasa de Cambio (ER)
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

# Riesgo
riesgos_disp = df_risk['Risk'].unique()
riesgo_sel = st.sidebar.selectbox("Nivel Riesgo", riesgos_disp)

mapa_riesgo = { "Low": 0.02, "Medium": 0.05, "High": 0.08 }
if riesgo_sel in mapa_riesgo:
    contingencia = mapa_riesgo[riesgo_sel]
else:
    contingencia = 0.0
    try:
        row_risk = df_risk[df_risk['Risk'] == riesgo_sel]
        if not row_risk.empty:
            contingencia = clean_decimal(row_risk['Contingency'].values[0])
    except: pass

st.sidebar.write(f"Contingencia: **{contingencia*100:.1f}%**")


# ==========================================
# CUERPO PRINCIPAL
# ==========================================

simbolo = "$" if moneda_tipo == "Local" else "USD"

# CREAMOS LAS PESTAÑAS (SHEETS)
tab_offer, tab_manage = st.tabs(["🛠️ Servicios (Offering)", "💻 Máquinas (Manage)"])

# --- TAB 1: OFFERING ---
with tab_offer:
    st.caption("Configuración de costos de servicios.")
    
    # Fila 1: Selección Principal (4 columnas visuales: 3 para Offering, 1 para Info)
    o1, o2 = st.columns([3, 1]) 
    offer_list = df_offering['Offering'].unique()
    offer_sel = o1.selectbox("Offering", offer_list)
    row_off = df_offering[df_offering['Offering'] == offer_sel].iloc[0]
    o2.text_input("Info (L40 | Conga)", f"{row_off.get('L40','-')} | {row_off.get('Load in conga','-')}", disabled=True)

    # Fila 2: Descripción (Ancho completo)
    st.text_input("Service Description", placeholder="Detalle del servicio...")

    # Fila 3: Inputs Numéricos (4 Columnas Iguales para alineación)
    c1, c2, c3, c4 = st.columns(4)

    # Columna 1: Cantidad
    qty = c1.number_input("QTY", min_value=1, value=1)

    # Columna 2: SLC
    slc_op = c2.selectbox("SLC", df_slc['SLC'].unique())

    # Columna 3: UPLF (Métrica)
    uplf = 1.0
    try:
        row_slc = df_slc[df_slc['SLC'] == slc_op]
        if not row_slc.empty:
            uplf = clean_decimal(row_slc['UPLF'].values[0])
    except: pass
    c3.metric("UPLF", uplf)

    # Columna 4: Costo Unitario
    if is_brazil:
        costo_input = c4.number_input("Costo Unit. (BRL)", value=0.0, format="%.2f")
    else:
        costo_input = c4.number_input("Costo Unit. (USD)", value=0.0, format="%.2f")

    # Fila 4: Fechas (3 Columnas para que queden alineadas a la izquierda, dejando espacio para el total abajo)
    d1, d2, d3 = st.columns(3)

    fs_ini = d1.date_input("Inicio Servicio", f_ini)
    fs_fin = d2.date_input("Fin Servicio", f_fin)
    dur_serv = calcular_duracion(fs_ini, fs_fin)
    d3.metric("Duración (Meses)", f"{dur_serv:.1f}")

    # Cálculo Total Servicio
    if is_brazil:
        total_serv_local = (costo_input * dur_serv) * qty * uplf
        total_serv_usd = total_serv_local / tasa_er if tasa_er > 0 else 0.0
        total_serv_final = total_serv_local if moneda_tipo == "Local" else total_serv_usd
    else:
        total_serv_usd = (costo_input * dur_serv) * qty * uplf
        total_serv_local = total_serv_usd * tasa_er
        total_serv_final = total_serv_usd if moneda_tipo == "USD" else total_serv_local

    # LINEA DE TOTALIZADOR (Regresada como st.info)
    st.info(f"Total Service: {simbolo} {total_serv_final:,.2f}")

# --- TAB 2: MACHINE / MANAGE ---
with tab_manage:
    st.caption("Configuración de costos de máquina y gestión.")
    
    # Fila 1: Offering Manage (Igual que arriba: 3 y 1)
    m_off1, m_off2 = st.columns([3, 1])
    offer_man_sel = m_off1.selectbox("Offering (Manage)", offer_list, key="offer_man")
    row_off_man = df_offering[df_offering['Offering'] == offer_man_sel].iloc[0]
    m_off2.text_input("Info (Manage)", f"{row_off_man.get('L40','-')} | {row_off_man.get('Load in conga','-')}", disabled=True)

    # Fila 2: Configuración Máquina (Alineación vertical izquierda)
    # Dividimos en 2 columnas principales: 
    # r1 (Izquierda): Fuente y Item (uno bajo otro)
    # r2 (Derecha): Costo Mensual
    r1, r2 = st.columns([2, 1])

    with r1:
        tipo_fuente = st.radio("Fuente Datos", ["Machine Category", "Brand Rate Full"])

        if tipo_fuente == "Machine Category":
            df_active = df_lplat
            col_item_idx = 2 
        else:
            df_active = df_lband
            col_item_idx = 3

        # Filtro Brasil
        df_filtrado = df_active.copy()
        if tipo_fuente == "Machine Category" and 'Scope' in df_active.columns:
            if is_brazil:
                mask_br = df_active['Scope'].astype(str).str.contains("only Brazil", case=False, na=False)
                mask_gen = df_active['Scope'].isna() | (df_active['Scope'].astype(str).str.strip() == '') | (df_active['Scope'].astype(str) == 'nan')
                df_filtrado = df_active[mask_br | mask_gen]
            else:
                mask_br = df_active['Scope'].astype(str).str.contains("only Brazil", case=False, na=False)
                df_filtrado = df_active[~mask_br]

        # Items
        try:
            items_disp = df_filtrado.iloc[:, col_item_idx].dropna().unique().tolist()
        except: items_disp = []

        item_maq = st.selectbox("Item", items_disp)

    # Precio Mensual (Calculado pero mostrado en r2 para alinear)
    precio_mes_raw = 0.0
    if item_maq:
        try:
            fila = df_filtrado[df_filtrado.iloc[:, col_item_idx] == item_maq]
            if is_brazil and 'Scope' in fila.columns:
                fila_br = fila[fila['Scope'].astype(str).str.contains("only Brazil", case=False, na=False)]
                if not fila_br.empty: fila = fila_br
            
            if not fila.empty and pais in fila.columns:
                precio_mes_raw = clean_decimal(fila[pais].values[0])
        except: pass

    # Campo Costo Mensual
    with r2:
        if is_brazil:
            base_manage = precio_mes_raw
            label_mc = "Monthly Cost (BRL)"
        else:
            base_manage = precio_mes_raw / tasa_er if tasa_er > 0 else 0.0
            label_mc = "Monthly Cost (USD)"

        st.text_input(label_mc, value=f"{base_manage:,.2f}", disabled=True)

    # Fila 3: Inputs Manage (4 Columnas Iguales)
    man1, man2, man3, man4 = st.columns(4)

    horas = man1.number_input("Horas", min_value=0.0)
    fm_ini = man2.date_input("Inicio Manage", f_ini)
    fm_fin = man3.date_input("Fin Manage", f_fin)
    dur_man = calcular_duracion(fm_ini, fm_fin)
    man4.metric("Duración (Meses)", f"{dur_man:.1f}")

    # Cálculo Total Manage
    if is_brazil:
        total_man_local = base_manage * horas * dur_man
        total_man_usd = total_man_local / tasa_er if tasa_er > 0 else 0.0
        total_man_final = total_man_local if moneda_tipo == "Local" else total_man_usd
    else:
        total_man_usd = base_manage * horas * dur_man
        total_man_local = total_man_usd * tasa_er
        total_man_final = total_man_usd if moneda_tipo == "USD" else total_man_local

    st.info(f"Total Manage: {simbolo} {total_man_final:,.2f}")

st.markdown("---")

# --- RESUMEN ---
st.header("💰 Resumen Final")
subtotal = total_serv_final + total_man_final
val_riesgo = subtotal * contingencia
total_total = subtotal + val_riesgo

# Fila Superior: Subtotales por Categoría
c_res1, c_res2 = st.columns(2)
c_res1.metric("Subtotal Offering", f"{simbolo} {total_serv_final:,.2f}")
c_res2.metric("Subtotal Manage", f"{simbolo} {total_man_final:,.2f}")

# Fila Inferior: Totales Generales
st.divider()
k1, k3 = st.columns(2)
k1.metric("Subtotal General", f"{simbolo} {subtotal:,.2f}")
k3.metric("TOTAL FINAL (Inc. Riesgo)", f"{simbolo} {total_total:,.2f}")
