import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="LACOSTWEB V16", layout="wide", page_icon="💰")

# --- 1. CARGA INTELIGENTE DE ARCHIVOS ---
def find_file(keyword, file_list):
    for f in file_list:
        if keyword.lower() in f.lower() and f.endswith(".csv"):
            return f
    return None

@st.cache_data
def load_data():
    all_files = os.listdir('.')
    keywords = {
        "config": "ui_config", "countries": "countries", "risk": "risk",
        "offering": "offering", "slc": "slc", "lplat": "lplat",
        "lband": "lband", "mcbr": "mcbr"
    }
    data = {}
    missing = []
    
    for key, search in keywords.items():
        fname = find_file(search, all_files)
        if fname:
            try:
                df = pd.read_csv(fname)
                df.columns = df.columns.str.strip()
                df = df.dropna(how='all')
                data[key] = df
            except: missing.append(search)
        else:
            missing.append(search)
    return data, missing

def main():
    st.title("💰 LACOSTWEB V16 - Cotizador Financiero")

    dfs, missing = load_data()
    if missing:
        st.error(f"Faltan archivos: {missing}")
        st.stop()
    
    if "config" not in dfs:
        st.error("Falta UI_CONFIG")
        st.stop()

    # --- BARRA LATERAL (Variables Globales) ---
    with st.sidebar:
        st.header("Parámetros Financieros")
        trm = st.number_input("TRM (Tasa de Cambio)", value=4200.0, step=10.0)
        margen_target = st.slider("Margen Objetivo (%)", 0, 50, 20) / 100

    # --- 2. GENERACIÓN DEL FORMULARIO ---
    df_config = dfs["config"]
    col_label = df_config.columns[0]
    col_source = df_config.columns[1] if len(df_config.columns) > 1 else None

    user_inputs = {}

    with st.form("cotizador"):
        st.subheader("Configuración del Deal")
        c1, c2 = st.columns(2)

        for idx, row in df_config.iterrows():
            if pd.isna(row[col_label]): continue
            label = str(row[col_label]).strip()
            
            # Detectamos si es lista
            source_data = None
            if col_source and pd.notna(row[col_source]):
                src_name = str(row[col_source]).strip().lower()
                if src_name in dfs: source_data = dfs[src_name]
                elif src_name.lower() in dfs: source_data = dfs[src_name.lower()]

            # ID único
            uid = f"in_{idx}"
            target_col = c1 if idx % 2 == 0 else c2
            
            with target_col:
                if source_data is not None:
                    # LISTA
                    opts = source_data.iloc[:, 0].unique()
                    user_inputs[label] = st.selectbox(label, opts, key=uid)
                else:
                    # TEXTO / NUMERO
                    # Intentamos detectar si el label sugiere que es un numero
                    label_lower = label.lower()
                    if any(x in label_lower for x in ['fte', 'cost', 'precio', 'cantidad', 'qty', 'num']):
                         user_inputs[label] = st.number_input(label, value=0.0, step=1.0, key=uid)
                    else:
                        user_inputs[label] = st.text_input(label, key=uid)

        st.markdown("---")
        submitted = st.form_submit_button("✅ Calcular Resultados", type="primary")

    # --- 3. LÓGICA DE OPERACIÓN (LO QUE PEDISTE) ---
    if submitted:
        st.divider()
        st.subheader("📊 Resultados de la Operación")

        # Intentamos extraer las variables CLAVE del formulario dinámico
        # Buscamos en lo que el usuario llenó
        
        fte = 0.0
        costo_unit = 0.0
        moneda = "COP" # Default

        # Búsqueda inteligente de variables
        for key, val in user_inputs.items():
            k = key.lower()
            if "fte" in k or "cantidad" in k:
                try: fte = float(val)
                except: pass
            if "cost" in k or "precio" in k:
                try: costo_unit = float(val)
                except: pass
            if "moneda" in k or "curr" in k:
                moneda = str(val)

        # CÁLCULOS
        costo_total_base = fte * costo_unit
        
        # Conversión de moneda (Asumiendo salida en COP)
        # Si el input es USD y queremos COP
        costo_total_cop = costo_total_base
        if "USD" in moneda.upper():
            costo_total_cop = costo_total_base * trm
        
        # Precio de Venta sugerido
        precio_venta = costo_total_cop / (1 - margen_target) if margen_target < 1 else 0
        profit = precio_venta - costo_total_cop

        # VISUALIZACIÓN
        colA, colB, colC = st.columns(3)
        colA.metric("Costo Total (COP)", f"${costo_total_cop:,.0f}")
        colB.metric("Precio Venta Sugerido", f"${precio_venta:,.0f}")
        colC.metric("Margen Estimado", f"{profit:,.0f}", delta=f"{margen_target*100}%")
        
        with st.expander("Ver detalle de variables capturadas"):
            st.json(user_inputs)

if __name__ == "__main__":
    main()
