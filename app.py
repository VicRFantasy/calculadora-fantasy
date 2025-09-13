import streamlit as st

# --- Configuración de la página ---
st.set_page_config(page_title="Calculadora Draft Fantasy", layout="wide")

# --- Presupuesto inicial ---
PRESUPUESTO_INICIAL = 100
if "restante" not in st.session_state:
    st.session_state.restante = PRESUPUESTO_INICIAL

# --- Jugadores y precios ---
jugadores = {
    "Jugador A": 25,
    "Jugador B": 18,
    "Jugador C": 12,
    "Jugador D": 30,
    "Jugador E": 15,
    "Jugador F": 20,
    "Jugador G": 10,
    "Jugador H": 22
}

# --- Función para color según precio ---
def color_precio(precio):
    if precio <= 15:
        return "lightgreen"
    elif precio <= 22:
        return "lightsalmon"
    else:
        return "lightcoral"

# --- Título ---
st.title("📝 Calculadora Draft Fantasy")
st.markdown("Selecciona tus jugadores por ronda y observa tu presupuesto en tiempo real.")

# --- Layout de columnas ---
col1, col2 = st.columns([2, 1])

# --- Columna izquierda: selectboxes por ronda ---
selecciones = []
with col1:
    st.subheader("Rondas")
    for i in range(1, 9):
        seleccion = st.selectbox(
            f"Ronda {i}",
            options=["-- Sin jugador --"] + list(jugadores.keys()),
            key=f"ronda{i}"
        )
        selecciones.append(seleccion)

# --- Columna derecha: presupuesto ---
with col2:
    st.subheader("💰 Presupuesto")
    gasto = sum(jugadores[s] for s in selecciones if s in jugadores)
    restante = PRESUPUESTO_INICIAL - gasto
    st.metric("Presupuesto inicial", f"{PRESUPUESTO_INICIAL} M")
    st.metric("Gasto total", f"{gasto} M")
    st.metric("Presupuesto restante", f"{restante} M")
    if restante < 0:
        st.error("⚠️ Te has pasado del presupuesto")

# --- Draft board visual ---
st.subheader("📊 Jugadores seleccionados")
jug_elegidos = [s for s in selecciones if s != "-- Sin jugador --"]
if jug_elegidos:
    # Crear filas de tarjetas
    for s in jug_elegidos:
        precio = jugadores[s]
        st.markdown(f"""
        <div style="
            display: inline-block;
            background-color: {color_precio(precio)};
            padding: 15px;
            margin: 5px;
            border-radius: 10px;
            min-width: 120px;
            text-align: center;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        ">
            <strong>{s}</strong><br>
            {precio} M
        </div>
        """, unsafe_allow_html=True)
else:
    st.write("Ninguno seleccionado")
