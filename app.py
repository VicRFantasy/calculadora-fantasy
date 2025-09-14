import streamlit as st
import pandas as pd

# =======================
# Configuración de página moderna
# =======================
st.set_page_config(
    layout="wide",
    page_title="Fantasy ACB",
    page_icon="🏀",
    initial_sidebar_state="collapsed"
)

# =======================
# Cargar jugadores desde Excel
# =======================
df = pd.read_excel("jugadores.xlsx")  # asegúrate que está en la misma carpeta que app.py

# Convertir precios de formato mixto a números (en millones de euros)
def convert_price_to_millions(price_value):
    if isinstance(price_value, (int, float)):
        return round(price_value / 1000, 2)
    elif isinstance(price_value, str):
        try:
            cleaned = price_value.replace('€', '').replace(' ', '').replace('.', '')
            if ',' in cleaned:
                parts = cleaned.rsplit(',', 1)
                cleaned = parts[0] + '.' + parts[1] if len(parts) == 2 else cleaned.replace(',', '')
            price_num = float(cleaned)
            return round(price_num / 1000000, 2)
        except (ValueError, AttributeError) as e:
            st.error(f"Error converting price '{price_value}': {e}")
            return 0.0
    return 0.0

df['Precio_Millones'] = df['Precio'].apply(convert_price_to_millions)
jugadores = dict(zip(df["Nombre"], df["Precio_Millones"]))

# =======================
# Función para renderizar presupuesto y equipo
# =======================
def render_budget_and_team(container, show_theme_toggle=False, container_key=""):
    total_gastado = sum(
        jugadores[j] for j in st.session_state.seleccionados.values() if j
    )
    presupuesto_restante = presupuesto_inicial - total_gastado

    if show_theme_toggle:
        col1, col2 = container.columns(2)
        with col1:
            if container.button("🌙", key=f"dark_btn_{container_key}", use_container_width=True):
                st.session_state.theme = "dark"
                st.rerun()
        with col2:
            if container.button("☀️", key=f"light_btn_{container_key}", use_container_width=True):
                st.session_state.theme = "light" 
                st.rerun()
    
    container.write("**💰 Presupuesto**")
    progress_pct = min(total_gastado / presupuesto_inicial, 1.0)
    progress_display = int(progress_pct * 100)
    container.write(f"**Gastado:** {total_gastado * 1000000:,.0f}".replace(",", ".") + f" ({progress_display}%)")
    container.progress(progress_pct)

    if presupuesto_restante < 0:
        container.error(f"⚠️ -{abs(presupuesto_restante * 1000000):,.0f}".replace(",", "."))
    else:
        container.write(f"**Restante:** {presupuesto_restante * 1000000:,.0f}".replace(",", "."))
    
    container.write("**👥 Tu equipo**")
    jugadores_por_posicion = {"B": [], "A": [], "P": []}
    posiciones_nombres = {"B": "● Bases", "A": "■ Aleros", "P": "▲ Pívots"}
    
    for ronda, jugador in st.session_state.seleccionados.items():
        if jugador:
            posicion = df[df["Nombre"] == jugador]["Posición"].iloc[0]
            precio_formatted = f"{jugadores[jugador] * 1000000:,.0f}".replace(",", ".")
            jugadores_por_posicion[posicion].append(f"**{jugador}** - {precio_formatted}")
    
    for pos_code, pos_name in posiciones_nombres.items():
        count = len(jugadores_por_posicion[pos_code])
        max_players = {"B": 2, "A": 3, "P": 3}[pos_code]
        symbol = pos_name[0]
        text = pos_name[2:]
        container.markdown(
            f'<span class="position-symbol-{pos_code}">{symbol}</span> **{text}:** {count}/{max_players}',
            unsafe_allow_html=True
        )
        if jugadores_por_posicion[pos_code]:
            for jugador_line in jugadores_por_posicion[pos_code]:
                parts = jugador_line.split(" - ")
                nombre = parts[0].replace("**", "")
                precio = parts[1] if len(parts) > 1 else ""
                container.markdown(
                    f'<span class="chip {pos_code}">{pos_code}</span>{nombre} - {precio}', 
                    unsafe_allow_html=True
                )
        else:
            container.write("  • _(vacío)_")
        container.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# =======================
# Presupuesto inicial y estado
# =======================
presupuesto_inicial = 5
if "seleccionados" not in st.session_state:
    st.session_state.seleccionados = {f"Ronda {i}": None for i in range(1, 9)}
if "widget_counter" not in st.session_state:
    st.session_state.widget_counter = 0
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# =======================
# Título
# =======================
st.markdown("""
<h1 style="font-weight: 700; background: linear-gradient(135deg, #60A5FA, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
Calculadora The Fantasy Basket ACB
</h1>
""", unsafe_allow_html=True)
st.markdown("### 🏆 Arma tu equipo ideal y controla tu presupuesto")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# =======================
# Layout adaptativo
# =======================
is_mobile = st.experimental_get_query_params().get("mobile", ["false"])[0] == "true"

if is_mobile:
    # En móvil → tabs
    tab1, tab2 = st.tabs(["🎯 Seleccionar Jugadores", "💰 Presupuesto y Equipo"])
    with tab1:
        col1, col2 = st.columns(2, gap="medium")
        rondas = list(st.session_state.seleccionados.keys())
        rondas_col1, rondas_col2 = rondas[:4], rondas[4:]
        for ronda in rondas_col1:
            jugador = st.selectbox(
                f"{ronda}",
                options=["(vacío)"] + df["Nombre"].tolist(),
                index=0 if st.session_state.seleccionados[ronda] is None else df["Nombre"].tolist().index(st.session_state.seleccionados[ronda]) + 1,
                key=f"{ronda}_{st.session_state.widget_counter}"
            )
            st.session_state.seleccionados[ronda] = None if jugador == "(vacío)" else jugador
        for ronda in rondas_col2:
            jugador = st.selectbox(
                f"{ronda}",
                options=["(vacío)"] + df["Nombre"].tolist(),
                index=0 if st.session_state.seleccionados[ronda] is None else df["Nombre"].tolist().index(st.session_state.seleccionados[ronda]) + 1,
                key=f"{ronda}_{st.session_state.widget_counter}"
            )
            st.session_state.seleccionados[ronda] = None if jugador == "(vacío)" else jugador
    with tab2:
        render_budget_and_team(st, show_theme_toggle=True, container_key="main")

else:
    # En desktop → dos columnas: izquierda presupuesto, derecha jugadores
    col_left, col_right = st.columns([1, 2], gap="large")
    with col_left:
        render_budget_and_team(st, show_theme_toggle=True, container_key="desktop")
    with col_right:
        st.markdown("### 🎯 Selección de Jugadores")
        col1, col2 = st.columns(2, gap="medium")
        rondas = list(st.session_state.seleccionados.keys())
        rondas_col1, rondas_col2 = rondas[:4], rondas[4:]
        with col1:
            for ronda in rondas_col1:
                jugador = st.selectbox(
                    f"{ronda}",
                    options=["(vacío)"] + df["Nombre"].tolist(),
                    index=0 if st.session_state.seleccionados[ronda] is None else df["Nombre"].tolist().index(st.session_state.seleccionados[ronda]) + 1,
                    key=f"{ronda}_{st.session_state.widget_counter}"
                )
                st.session_state.seleccionados[ronda] = None if jugador == "(vacío)" else jugador
        with col2:
            for ronda in rondas_col2:
                jugador = st.selectbox(
                    f"{ronda}",
                    options=["(vacío)"] + df["Nombre"].tolist(),
                    index=0 if st.session_state.seleccionados[ronda] is None else df["Nombre"].tolist().index(st.session_state.seleccionados[ronda]) + 1,
                    key=f"{ronda}_{st.session_state.widget_counter}"
                )
                st.session_state.seleccionados[ronda] = None if jugador == "(vacío)" else jugador
