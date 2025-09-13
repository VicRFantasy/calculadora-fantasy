import streamlit as st
import pandas as pd

# =======================
# Cargar jugadores desde Excel
# =======================
df = pd.read_excel("jugadores.xlsx")  # asegúrate que está en la misma carpeta que app.py
jugadores = dict(zip(df["Nombre"], df["Precio"]))

# =======================
# Presupuesto inicial
# =======================
presupuesto_inicial = 100

if "presupuesto" not in st.session_state:
    st.session_state.presupuesto = presupuesto_inicial
    st.session_state.seleccionados = {f"Ronda {i}": None for i in range(1, 9)}

# =======================
# Mostrar interfaz
# =======================
st.title("📊 Calculadora Fantasy ACB")
st.write("Selecciona tus jugadores y controla tu presupuesto.")

for ronda in st.session_state.seleccionados.keys():
    cols = st.columns([4, 1])  # desplegable (4) + botón ❌ (1)

    with cols[0]:
        jugador = st.selectbox(
            f"{ronda}",
            options=["(vacío)"] + df["Nombre"].tolist(),
            index=0 if st.session_state.seleccionados[ronda] is None 
            else df["Nombre"].tolist().index(st.session_state.seleccionados[ronda]) + 1,
            key=ronda
        )
        if jugador != "(vacío)":
            st.session_state.seleccionados[ronda] = jugador
        else:
            st.session_state.seleccionados[ronda] = None

    with cols[1]:
        if st.button("❌", key=f"del_{ronda}"):
            st.session_state.seleccionados[ronda] = None
            st.rerun()

# =======================
# Calcular presupuesto
# =======================
total_gastado = sum(
    jugadores[j] for j in st.session_state.seleccionados.values() if j
)
presupuesto_restante = presupuesto_inicial - total_gastado

st.sidebar.header("💰 Presupuesto")
st.sidebar.metric("Presupuesto inicial", f"{presupuesto_inicial}M")
st.sidebar.metric("Gastado", f"{total_gastado}M")
st.sidebar.metric("Restante", f"{presupuesto_restante}M")

# =======================
# Lista de jugadores elegidos
# =======================
st.subheader("👥 Tu equipo")
for ronda, jugador in st.session_state.seleccionados.items():
    if jugador:
        st.write(f"{ronda}: **{jugador}** - {jugadores[jugador]}M")
    else:
        st.write(f"{ronda}: _(vacío)_")

