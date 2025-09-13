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
        # Los números enteros/decimales están en miles de euros
        return round(price_value / 1000, 2)
    elif isinstance(price_value, str):
        try:
            # Strings con € están en euros completos, necesitan división por millón
            cleaned = price_value.replace('€', '').replace(' ', '').replace('.', '')
            # Manejar comas decimales (reemplazar la última coma con punto)
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
    """Renderiza presupuesto y equipo en el container especificado"""
    
    # Calcular presupuesto
    total_gastado = sum(
        jugadores[j] for j in st.session_state.seleccionados.values() if j
    )
    presupuesto_restante = presupuesto_inicial - total_gastado
    
    # Tema ultra compacto (solo si se solicita)
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
    
    # Presupuesto compacto en una sola línea
    progress_pct = min(total_gastado / presupuesto_inicial, 1.0)
    progress_display = int(progress_pct * 100)
    
    # Mostrar solo lo esencial
    container.write(f"**Gastado:** {total_gastado * 1000000:,.0f}".replace(",", ".") + f" ({progress_display}%)")
    container.progress(progress_pct)
    
    # Presupuesto restante compacto
    if presupuesto_restante < 0:
        container.error(f"⚠️ -{abs(presupuesto_restante * 1000000):,.0f}".replace(",", "."))
    else:
        container.write(f"**Restante:** {presupuesto_restante * 1000000:,.0f}".replace(",", "."))
    
    # Lista de jugadores elegidos
    container.write("**👥 Tu equipo**")
    
    # Crear un diccionario para agrupar jugadores por posición
    jugadores_por_posicion = {"B": [], "A": [], "P": []}
    posiciones_nombres = {"B": "● Bases", "A": "■ Aleros", "P": "▲ Pívots"}
    
    # Agrupar jugadores seleccionados por posición
    for ronda, jugador in st.session_state.seleccionados.items():
        if jugador:
            # Buscar la posición del jugador
            posicion = df[df["Nombre"] == jugador]["Posición"].iloc[0]
            precio_formatted = f"{jugadores[jugador] * 1000000:,.0f}".replace(",", ".")
            jugadores_por_posicion[posicion].append(f"**{jugador}** - {precio_formatted}")
    
    # Mostrar por posición con chips
    for pos_code, pos_name in posiciones_nombres.items():
        # Contar jugadores en esta posición
        count = len(jugadores_por_posicion[pos_code])
        max_players = {"B": 2, "A": 3, "P": 3}[pos_code]  # Límites ideales por posición
        
        # Aplicar color al símbolo de posición
        symbol_colors = {"● Bases": "● Bases", "■ Aleros": "■ Aleros", "▲ Pívots": "▲ Pívots"}
        color_classes = {"● Bases": "B", "■ Aleros": "A", "▲ Pívots": "P"}
        
        symbol = pos_name[0]  # Obtener el símbolo (●, ■, ▲)
        text = pos_name[2:]   # Obtener el texto (Bases, Aleros, Pívots)
        color_class = color_classes[pos_name]
        
        container.markdown(
            f'<span class="position-symbol-{color_class}">{symbol}</span> **{text}:** {count}/{max_players}',
            unsafe_allow_html=True
        )
        
        if jugadores_por_posicion[pos_code]:
            for jugador_line in jugadores_por_posicion[pos_code]:
                # Extraer nombre y precio del string
                parts = jugador_line.split(" - ")
                nombre = parts[0].replace("**", "")
                precio = parts[1] if len(parts) > 1 else ""
                
                # Mostrar con chip de posición
                container.markdown(
                    f'<span class="chip {pos_code}">{pos_code}</span>{nombre} - {precio}', 
                    unsafe_allow_html=True
                )
        else:
            container.write("  • _(vacío)_")
        
        # Separador sutil
        container.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# =======================
# Presupuesto inicial
# =======================
presupuesto_inicial = 5  # 5 millones de euros

if "presupuesto" not in st.session_state:
    st.session_state.presupuesto = presupuesto_inicial

# Forzar reset para migrar de claves antiguas a Ronda 1-8
expected_keys = {f"Ronda {i}": None for i in range(1, 9)}
if "seleccionados" not in st.session_state or set(st.session_state.seleccionados.keys()) != set(expected_keys.keys()):
    st.session_state.seleccionados = expected_keys

# Contador para forzar recreación de widgets cuando se elimina un jugador
if "widget_counter" not in st.session_state:
    st.session_state.widget_counter = 0

# Tema de la aplicación
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# =======================
# CSS personalizado para diseño moderno
# =======================

# Aplicar estilos dinámicos según el tema
if st.session_state.theme == "dark":
    # Tema oscuro
    st.markdown("""
    <style>
    /* Ocultar header solo en desktop, mostrarlo en móvil para hamburger */
    @media (min-width: 769px) {
        [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    }
    @media (max-width: 768px) {
        [data-testid="stHeader"], [data-testid="stToolbar"] { display: flex !important; }
    }
    #MainMenu, footer { display: none !important; }

    /* Padding seguro para evitar cortar el título */
    .block-container { padding-top: 0.75rem !important; padding-bottom: 2rem; overflow: visible !important; }
    .block-container > :first-child { margin-top: 0 !important; }

    /* Asegurar que nada corte el título */
    main, .main { overflow: visible !important; }
    
    /* Mejoras para móvil */
    @media (max-width: 768px) {
        .block-container { 
            padding-left: 0.5rem !important; 
            padding-right: 0.5rem !important; 
        }
        h1 { font-size: 1.5rem !important; }
        .stButton>button { font-size: 0.8rem !important; }
    }
    
    /* Fondo oscuro completo */
    html, body, .stApp {
        background-color: #0F172A !important;
        color: #E5E7EB !important;
    }
    
    /* Sidebar oscuro con texto blanco */
    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        color: #E5E7EB !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #E5E7EB !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] div {
        color: #E5E7EB !important;
    }
    
    /* Métricas del sidebar en blanco */
    [data-testid="stSidebar"] [data-testid="metric-container"] {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        padding: 8px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="metric-container"] * {
        color: #E5E7EB !important;
    }
    
    /* Botones modernos oscuros */
    .stButton>button {
        border-radius:10px;
        background:transparent;
        border:1px solid rgba(255,255,255,.15);
        color:#E5E7EB !important;
        transition:all 0.2s;
    }
    .stButton>button:hover {
        background:rgba(96,165,250,.15);
        border-color:#60A5FA;
        transform:translateY(-1px);
    }
    
    /* Botones de tema más pequeños */
    [data-testid="stSidebar"] .stButton>button {
        height: 2rem !important;
        min-height: 2rem !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 1rem !important;
    }
    
    /* Separadores oscuros */
    .divider {
        height:1px;
        background:linear-gradient(90deg,transparent,rgba(255,255,255,.1),transparent);
        margin:12px 0;
    }
    
    /* Chips de posición */
    .chip{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;margin-right:6px;font-weight:500}
    .chip.B{background:#1D4ED8;color:#fff}
    .chip.A{background:#059669;color:#fff}
    .chip.P{background:#D97706;color:#fff}
    
    /* Símbolos de posición con colores */
    .position-symbol-B { color: #1D4ED8; font-weight: bold; }
    .position-symbol-A { color: #059669; font-weight: bold; }
    .position-symbol-P { color: #D97706; font-weight: bold; }
    
    /* Títulos mejorados - evitar que afecte emojis */
    h1{background:linear-gradient(135deg, #60A5FA, #34D399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:700}
    h2{color:#60A5FA;font-weight:600}
    h3{color:#34D399;font-weight:500}
    
    /* Fix para que los emojis mantengan sus colores reales */
    h1 span.emoji {
        -webkit-text-fill-color: initial !important;
        background: none !important;
        color: initial !important;
    }
    
    /* Progress bar oscuro */
    [data-testid="stSidebar"] .stProgress > div > div > div {
        background-color: #60A5FA !important;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    # Tema claro
    st.markdown("""
    <style>
    /* Ocultar header solo en desktop, mostrarlo en móvil para hamburger */
    @media (min-width: 769px) {
        [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    }
    @media (max-width: 768px) {
        [data-testid="stHeader"], [data-testid="stToolbar"] { display: flex !important; }
    }
    #MainMenu, footer { display: none !important; }

    /* Padding seguro para evitar cortar el título */
    .block-container { padding-top: 0.75rem !important; padding-bottom: 2rem; overflow: visible !important; }
    .block-container > :first-child { margin-top: 0 !important; }

    /* Asegurar que nada corte el título */
    main, .main { overflow: visible !important; }
    
    /* Mejoras para móvil */
    @media (max-width: 768px) {
        .block-container { 
            padding-left: 0.5rem !important; 
            padding-right: 0.5rem !important; 
        }
        h1 { font-size: 1.5rem !important; }
        .stButton>button { font-size: 0.8rem !important; }
    }
    
    /* Fondo claro completo */
    html, body, .stApp {
        background-color: #ffffff !important;
        color: #374151 !important;
    }
    
    /* Sidebar claro */
    [data-testid="stSidebar"] {
        background-color: #f9fafb !important;
        color: #374151 !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #374151 !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] div {
        color: #374151 !important;
    }
    
    /* Métricas del sidebar en claro */
    [data-testid="stSidebar"] [data-testid="metric-container"] {
        background-color: rgba(0,0,0,0.02) !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
        border-radius: 8px !important;
        padding: 8px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="metric-container"] * {
        color: #374151 !important;
    }
    
    /* Botones modernos claros */
    .stButton>button {
        border-radius:10px;
        background:transparent;
        border:1px solid rgba(0,0,0,.15);
        color:#374151 !important;
        transition:all 0.2s;
    }
    .stButton>button:hover {
        background:rgba(96,165,250,.10);
        border-color:#60A5FA;
        transform:translateY(-1px);
    }
    
    /* Botones de tema más pequeños */
    [data-testid="stSidebar"] .stButton>button {
        height: 2rem !important;
        min-height: 2rem !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 1rem !important;
    }
    
    /* Separadores claros */
    .divider {
        height:1px;
        background:linear-gradient(90deg,transparent,rgba(0,0,0,.1),transparent);
        margin:12px 0;
    }
    
    /* Chips de posición */
    .chip{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;margin-right:6px;font-weight:500}
    .chip.B{background:#1D4ED8;color:#fff}
    .chip.A{background:#059669;color:#fff}
    .chip.P{background:#D97706;color:#fff}
    
    /* Símbolos de posición con colores */
    .position-symbol-B { color: #1D4ED8; font-weight: bold; }
    .position-symbol-A { color: #059669; font-weight: bold; }
    .position-symbol-P { color: #D97706; font-weight: bold; }
    
    /* Títulos mejorados - evitar que afecte emojis */
    h1{background:linear-gradient(135deg, #60A5FA, #34D399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:700}
    h2{color:#60A5FA;font-weight:600}
    h3{color:#34D399;font-weight:500}
    
    /* Fix para que los emojis mantengan sus colores reales */
    h1 span.emoji {
        -webkit-text-fill-color: initial !important;
        background: none !important;
        color: initial !important;
    }
    
    /* Progress bar claro */
    [data-testid="stSidebar"] .stProgress > div > div > div {
        background-color: #60A5FA !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =======================
# Mostrar interfaz
# =======================
st.markdown("""
<h1 style="font-weight: 700; background: linear-gradient(135deg, #60A5FA, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
Calculadora The Fantasy Basket ACB
</h1>
""", unsafe_allow_html=True)
st.markdown("### 🏆 Arma tu equipo ideal y controla tu presupuesto")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# =======================
# Tabs principales para móvil
# =======================
tab1, tab2 = st.tabs(["🎯 Seleccionar Jugadores", "💰 Presupuesto y Equipo"])

with tab1:
    # Dividir en dos columnas para mejor organización
    col1, col2 = st.columns(2, gap="medium")
    
    # Lista de rondas dividida en dos
    rondas = list(st.session_state.seleccionados.keys())
    rondas_col1 = rondas[:4]  # Ronda 1-4
    rondas_col2 = rondas[4:]  # Ronda 5-8
    
    # Columna izquierda (Rondas 1-4)
    with col1:
        st.markdown("#### 🎯 Rondas 1-4")
        for ronda in rondas_col1:
            cols = st.columns([5, 1])
            
            with cols[0]:
                jugador = st.selectbox(
                    f"{ronda}",
                    options=["(vacío)"] + df["Nombre"].tolist(),
                    index=0 if st.session_state.seleccionados[ronda] is None 
                    else df["Nombre"].tolist().index(st.session_state.seleccionados[ronda]) + 1,
                    key=f"{ronda}_{st.session_state.widget_counter}"
                )
                if jugador != "(vacío)":
                    st.session_state.seleccionados[ronda] = jugador
                else:
                    st.session_state.seleccionados[ronda] = None
    
            with cols[1]:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("❌", key=f"del_{ronda}_{st.session_state.widget_counter}"):
                    st.session_state.seleccionados[ronda] = None
                    # Incrementar contador para forzar recreación de widgets
                    st.session_state.widget_counter += 1
                    st.rerun()
    
    # Columna derecha (Rondas 5-8)
    with col2:
        st.markdown("#### 🎯 Rondas 5-8")
        for ronda in rondas_col2:
            cols = st.columns([5, 1])
            
            with cols[0]:
                jugador = st.selectbox(
                    f"{ronda}",
                    options=["(vacío)"] + df["Nombre"].tolist(),
                    index=0 if st.session_state.seleccionados[ronda] is None 
                    else df["Nombre"].tolist().index(st.session_state.seleccionados[ronda]) + 1,
                    key=f"{ronda}_{st.session_state.widget_counter}"
                )
                if jugador != "(vacío)":
                    st.session_state.seleccionados[ronda] = jugador
                else:
                    st.session_state.seleccionados[ronda] = None
    
            with cols[1]:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("❌", key=f"del_{ronda}_{st.session_state.widget_counter}"):
                    st.session_state.seleccionados[ronda] = None
                    # Incrementar contador para forzar recreación de widgets
                    st.session_state.widget_counter += 1
                    st.rerun()

with tab2:
    # Usar la función para renderizar presupuesto y equipo con toggle de tema
    render_budget_and_team(st, show_theme_toggle=True, container_key="main")

# =======================
# Sidebar (Desktop) - usar función reutilizable
# =======================
render_budget_and_team(st.sidebar, show_theme_toggle=True, container_key="sidebar")

