import streamlit as st
import pandas as pd
import re

# =======================
# Configuración de la página
# =======================
st.set_page_config(layout="wide", page_title="Fantasy ACB", page_icon="🏀", initial_sidebar_state="collapsed")

# =======================
# Cargar jugadores desde Excel
# =======================
df = pd.read_excel("jugadores.xlsx")
df.columns = df.columns.str.strip()
# Normalizar posiciones y nombres
df["Posición"] = df["Posición"].astype(str).str.strip().str.upper()
df["Nombre"] = df["Nombre"].astype(str).str.strip()

# =======================
# Parsing robusto de precios -> devuelve valor en millones (float)
# =======================
def parse_price_to_millions(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        # Si viene un número grande en euros -> a millones
        try:
            v = float(val)
            if v > 10000:  # euros completos
                return round(v / 1_000_000, 2)
            else:
                return round(v / 1_000_000, 2)
        except:
            return 0.0
    s = str(val).strip()
    s = s.replace('€', '').replace(' ', '')
    # casos mixtos: '1.180.000', '950.00', '585.00'
    # si tiene '.' y ',' -> suponemos '.' miles y ',' decimales
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    else:
        # si varios puntos -> eliminar puntos (son miles)
        if s.count('.') > 1:
            s = s.replace('.', '')
        else:
            # si tiene coma y no punto -> coma decimal
            if ',' in s and '.' not in s:
                s = s.replace(',', '.')
    # eliminar cualquier carácter no numérico salvo '.' 
    s = re.sub(r'[^0-9.]', '', s)
    if s == "":
        return 0.0
    try:
        euros = float(s)
    except:
        return 0.0
    # si la cifra es grande (>10000) tratamos como euros completos
    if euros > 10000:
        return round(euros / 1_000_000, 2)
    # si no, también la convertimos a millones (por seguridad)
    return round(euros / 1_000_000, 2)

df['Precio_Millones'] = df['Precio'].apply(parse_price_to_millions)

# lookups rápidos
price_mill = dict(zip(df['Nombre'], df['Precio_Millones']))
posicion_map = dict(zip(df['Nombre'], df['Posición']))

# =======================
# Estado inicial
# =======================
presupuesto_inicial = 5.0  # millones
if "seleccionados" not in st.session_state:
    st.session_state.seleccionados = {f"Ronda {i}": None for i in range(1, 9)}
if "widget_counter" not in st.session_state:
    st.session_state.widget_counter = 0
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# =======================
# CSS (chips, responsive, barra personalizada)
# =======================
st.markdown("""
<style>
/* Mostrar/ocultar según pantalla */
.desktop-only{display:block;}
.mobile-only{display:none;}
@media (max-width: 768px){
  .desktop-only{display:none !important;}
  .mobile-only{display:block !important;}
}

/* Divider */
.divider{height:1px;background:linear-gradient(90deg,transparent,rgba(0,0,0,.08),transparent);margin:10px 0}

/* Pastilla redondeada (chip) */
.chip{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;margin-right:8px;font-weight:600;color:#fff;min-width:26px;text-align:center}
.chip.B{background:#1D4ED8}
.chip.A{background:#059669}
.chip.P{background:#D97706}

/* Player line */
.player-line{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:6px 0;padding-right:4px}

/* Barra de presupuesto estilo: base azul y barra roja interior */
.progress-wrap{width:100%;background:#e6f4ff;border-radius:10px;height:14px;overflow:hidden;border:1px solid rgba(96,165,250,0.15)}
.progress-inner{height:100%;background:#ef4444;width:0%;transition:width .3s ease}

/* Adaptaciones móviles */
@media (max-width: 480px){
  .chip{min-width:22px;padding:2px 6px;font-size:10px}
  .player-line{gap:8px}
}
</style>
""", unsafe_allow_html=True)

# =======================
# Helpers de formato
# =======================
def format_euros_from_millions(mill):
    euros = int(round(mill * 1_000_000))
    return f"{euros:,}".replace(",", ".")  # separador de miles con punto

def safe_index_of(name, names_list):
    try:
        return names_list.index(name) + 1
    except ValueError:
        return 0

# =======================
# Render presupuesto y roster (con estilo pedido)
# =======================
def render_budget_and_team(container, show_theme_toggle=False, container_key=""):
    # Tema selector (fiable)
    if show_theme_toggle:
        sel = container.selectbox("Tema", ["dark", "light"], index=0 if st.session_state.theme=="dark" else 1, key=f"theme_sel_{container_key}")
        if sel != st.session_state.theme:
            st.session_state.theme = sel
            st.experimental_rerun()

    total_gastado = sum(price_mill.get(j, 0.0) for j in st.session_state.seleccionados.values() if j)
    restante = presupuesto_inicial - total_gastado
    pct = min(total_gastado / max(presupuesto_inicial, 1e-9), 1.0)

    container.markdown("**💰 Presupuesto**")
    container.write(f"**Gastado:** {format_euros_from_millions(total_gastado)} €  —  ({int(pct*100)}%)")

    # barra base azul (fondo) con barra roja interior proporcional
    container.markdown(f"""
    <div style="margin:6px 0">
      <div class="progress-wrap">
        <div class="progress-inner" style="width:{pct*100}%"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if restante < 0:
        container.error(f"⚠️ Te has pasado: -{format_euros_from_millions(abs(restante))} €")
    else:
        container.write(f"**Restante:** {format_euros_from_millions(restante)} €")

    container.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    container.markdown("**👥 Tu equipo**")

    # Agrupar por posición y mostrar con pastilla redondeada + nombre + precio
    grouped = {"B": [], "A": [], "P": []}
    for ronda, jugador in st.session_state.seleccionados.items():
        if jugador:
            pos = posicion_map.get(jugador, "B")
            grouped.setdefault(pos, []).append(jugador)

    labels = {"B": "Bases", "A": "Aleros", "P": "Pívots"}
    caps = {"B": 2, "A": 3, "P": 3}

    for code in ["B", "A", "P"]:
        container.markdown(f"**{labels[code]}:** {len(grouped.get(code, []))}/{caps[code]}")
        if grouped.get(code):
            for name in grouped[code]:
                precio = format_euros_from_millions(price_mill.get(name, 0.0))
                container.markdown(f'<div class="player-line"><div><span class="chip {code}">{code}</span> {name} – {precio} €</div></div>', unsafe_allow_html=True)
        else:
            container.write("  • _(vacío)_")
        container.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# =======================
# Cabecera
# =======================
st.markdown("""<h1 style="font-weight:700; background: linear-gradient(135deg, #60A5FA, #34D399); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Calculadora The Fantasy Basket ACB</h1>""", unsafe_allow_html=True)
st.markdown("### 🏆 Arma tu equipo ideal y controla tu presupuesto")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# =======================
# LAYOUT: Desktop (izq=presupuesto, der=selects) y Mobile (expander + selects)
# =======================

# Mobile: expander con presupuesto (visible solo en móvil gracias al CSS)
st.markdown('<div class="mobile-only">', unsafe_allow_html=True)
with st.expander("💰 Presupuesto y Equipo (abrir/cerrar)", expanded=False):
    render_budget_and_team(st, show_theme_toggle=True, container_key="mobile")
st.markdown('</div>', unsafe_allow_html=True)

# Desktop layout: left narrow panel (presupuesto), right wide (selects)
col_left, col_right = st.columns([1, 3], gap="large")

with col_left:
    st.markdown('<div class="desktop-only">', unsafe_allow_html=True)
    render_budget_and_team(col_left, show_theme_toggle=True, container_key="desktop")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown("### 🎯 Selección de Jugadores")
    right_col1, right_col2 = st.columns(2, gap="medium")
    rondas = list(st.session_state.seleccionados.keys())
    names = df["Nombre"].tolist()

    def render_ronda_widget(parent, ronda):
        cols = parent.columns([5, 1])
        key_sel = f"sel_{ronda}"
        key_del = f"del_{ronda}_{st.session_state.widget_counter}"
        with cols[0]:
            idx = safe_index_of(st.session_state.seleccionados.get(ronda), names)
            jugador = st.selectbox(
                f"{ronda}",
                options=["(vacío)"] + names,
                index=idx,
                key=key_sel
            )
            st.session_state.seleccionados[ronda] = None if jugador == "(vacío)" else jugador
        with cols[1]:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("❌", key=key_del):
                st.session_state.seleccionados[ronda] = None
                st.session_state.widget_counter += 1
                st.experimental_rerun()

    for r in rondas[:4]:
        render_ronda_widget(right_col1, r)
    for r in rondas[4:]:
        render_ronda_widget(right_col2, r)

# Mobile: también mostrar los selectboxes (apilados), visible solo en móvil
st.markdown('<div class="mobile-only">', unsafe_allow_html=True)
st.markdown("### 🎯 Selección de Jugadores")
names = df["Nombre"].tolist()
for ronda in list(st.session_state.seleccionados.keys()):
    cols = st.columns([5, 1])
    with cols[0]:
        idx = safe_index_of(st.session_state.seleccionados.get(ronda), names)
        jugador = st.selectbox(
            f"{ronda}",
            options=["(vacío)"] + names,
            index=idx,
            key=f"sel_mobile_{ronda}_{st.session_state.widget_counter}"
        )
        st.session_state.seleccionados[ronda] = None if jugador == "(vacío)" else jugador
    with cols[1]:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("❌", key=f"del_mobile_{ronda}_{st.session_state.widget_counter}"):
            st.session_state.seleccionados[ronda] = None
            st.session_state.widget_counter += 1
            st.experimental_rerun()
st.markdown('</div>', unsafe_allow_html=True)
