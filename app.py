import streamlit as st
import pandas as pd
import os

# --- Configuración Visual ---
st.set_page_config(page_title="LACOSTWEB V12", layout="wide", page_icon="📋")

# --- 1. CONFIGURACIÓN EXACTA DE ARCHIVOS V12 ---
# Usamos los nombres TAL CUAL los subiste (incluyendo el error de tipeo CONGIF)
FILES = {
    "config":    "V12-BASE.xlsx - UI_CONGIF.csv", # <--- OJO: Lee CONGIF
    "countries": "V12-BASE.xlsx - countries.csv",
    "risk":      "V12-BASE.xlsx - risk.csv",
    "offering":  "V12-BASE.xlsx - offering.csv",
    "slc":       "V12-BASE.xlsx - slc.csv",
    "lplat":     "V12-BASE.xlsx - lplat.csv",
    "lband":     "V12-BASE.xlsx - lband.csv",
    "mcbr":      "V12-BASE.xlsx - mcbr.csv"
}

@st.cache_data
def load_data():
    data = {}
    missing = []

    for key, filename in FILES.items():
        if os.path.exists(filename):
            try:
                # Leemos el CSV
                df = pd.read_csv(filename)
                df.columns = df.columns.str.strip() # Limpiar cabeceras
                df = df.dropna(how='all') # Limpiar vacíos
                data[key] = df
            except Exception as e:
                st.error(f"Error leyendo {filename}: {e}")
        else:
            missing.append(filename)
    return data, missing

def main():
    st.title("📋 LACOSTWEB V12 - Configuración Detallada")

    # Cargar datos
    dfs, missing = load_data()

    if missing:
        st.error("❌ FALTAN ARCHIVOS EN EL SERVIDOR")
        st.code("\n".join(missing))
        st.stop()

    if "config" not in dfs:
        st.error("❌ Falta el archivo de configuración UI_CONGIF.csv")
        st.stop()

    # --- 2. MOTOR DE INTERFAZ BASADO EN TUS 4 PUNTOS ---
    df_config = dfs["config"]
    
    # Asumimos que el CSV tiene las columnas en este orden (0, 1, 2, 3)
    # Col 0: NOMBRE DEL CAMPO (Label)
    # Col 1: FUENTE DE DATOS (Source)
    # Col 2: LÓGICA / INSTRUCCIÓN (Help Text)
    # Col 3: EJEMPLO (Placeholder / Default)
    
    # Obtener nombres de columnas por índice para no fallar por nombres
    cols = df_config.columns
    c_nombre  = cols[0]
    c_fuente  = cols[1] if len(cols) > 1 else None
    c_logica  = cols[2] if len(cols) > 2 else None
    c_ejemplo = cols[3] if len(cols) > 3 else None

    # Diccionario para guardar lo que el usuario llena
    inputs = {}

    with st.form("form_v12"):
        st.subheader("Parametrización del Escenario")
        
        # Grid de 2 columnas
        col_izq, col_der = st.columns(2)

        for idx, row in df_config.iterrows():
            if pd.isna(row[c_nombre]): continue
            
            # 1. NOMBRE DEL CAMPO
            label = str(row[c_nombre]).strip()
            
            # 2. DONDE SE TRAEN LOS DATOS
            fuente = str(row[c_fuente]).strip() if c_fuente and pd.notna(row[c_fuente]) else ""
            
            # 3. LO QUE DEBE HACER (Se mostrará como ayuda/tooltip)
            logica = str(row[c_logica]).strip() if c_logica and pd.notna(row[c_logica]) else ""
            
            # 4. EJEMPLO (Valor por defecto)
            ejemplo = str(row[c_ejemplo]).strip() if c_ejemplo and pd.notna(row[c_ejemplo]) else ""

            # --- Lógica de Renderizado ---
            uid = f"field_{idx}"
            destino = col_izq if idx % 2 == 0 else col_der
            
            with destino:
                # ¿Tiene fuente de datos vinculada?
                tabla_datos = None
                
                # Intentamos buscar la tabla en los archivos cargados
                if fuente.lower() in [k.lower() for k in dfs.keys()]:
                    # Buscamos la llave exacta
                    for k in dfs.keys():
                        if k.lower() == fuente.lower():
                            tabla_datos = dfs[k]
                            break
                
                if tabla_datos is not None:
                    # ES UNA LISTA DESPLEGABLE
                    opciones = tabla_datos.iloc[:, 0].unique()
                    # Mostramos la lógica en el 'help' para que sepas qué hace
                    inputs[label] = st.selectbox(label, options=opciones, key=uid, help=f"Lógica: {logica}")
                else:
                    # ES UN CAMPO MANUAL (Usamos el EJEMPLO como valor sugerido)
                    # Si el ejemplo parece número, usamos number_input
                    try:
                        val_defecto = float(ejemplo)
                        inputs[label] = st.number_input(label, value=val_defecto, key=uid, help=f"Lógica: {logica}")
                    except:
                        inputs[label] = st.text_input(label, value=ejemplo, key=uid, help=f"Lógica: {logica}")

        st.markdown("---")
        submitted = st.form_submit_button("✅ Calcular Escenario", type="primary")

    # --- 3. LÓGICA DE OPERACIÓN FINAL ---
    if submitted:
        st.success("Datos capturados según tu configuración:")
        
        # Mostrar las variables capturadas
        st.json(inputs)
        
        # AQUÍ APLICAMOS LA LÓGICA GENÉRICA DE COTIZACIÓN
        # Intentamos detectar las variables clave basándonos en nombres comunes
        # (Aunque el usuario defina los nombres, buscamos patrones)
        
        try:
            # Buscamos valores numéricos en los inputs
            valores = {k: float(v) for k, v in inputs.items() if isinstance(v, (int, float))}
            
            # Buscamos palabras clave
            trm = next((v for k, v in valores.items() if "trm" in k.lower() or "tasa" in k.lower()), 0)
            fte = next((v for k, v in valores.items() if "fte" in k.lower() or "cant" in k.lower()), 1)
            costo = next((v for k, v in valores.items() if "cost" in k.lower() or "precio" in k.lower()), 0)
            
            # Si encontramos al menos Costo, hacemos una proyección básica
            if costo > 0:
                st.divider()
                st.subheader("🧮 Cálculo Automático")
                
                total = costo * fte
                if trm > 0 and total < 100000: # Asumimos que si es pequeño está en USD
                    total_cop = total * trm
                    st.metric("Total Estimado (COP)", f"${total_cop:,.2f}", delta="Proyectado con TRM")
                else:
                    st.metric("Total Estimado", f"{total:,.2f}")
                    
        except Exception as e:
            st.warning("No se pudo realizar el cálculo automático. Revisa que los campos numéricos estén correctos.")

if __name__ == "__main__":
    main()

