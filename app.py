"""
Area Comercial — Dashboard de Gamificación (Streamlit)
--------------------------------------------------------
Incluye Login, Roles de Gerencia, Muro de Fuego, Recompensas (Barra de Energía)
y Conexión en vivo a Google Sheets.
"""

import random
from pathlib import Path
import pandas as pd

import streamlit as st
import streamlit.components.v1 as components

from ranks import RANGOS, cargar_ranking

APP_DIR = Path(__file__).parent
USUARIOS_FILE = APP_DIR / "data" / "usuarios.xlsx"

# Pon aquí el enlace .csv de tu Google Sheets publicado en la web
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/TU_ENLACE_AQUI/pub?output=csv"

st.set_page_config(page_title="Arena Comercial", page_icon="🏆", layout="wide")

# ---------------------------------------------------------------------------
# Estilos: fuentes + CSS del sistema de diseño
# ---------------------------------------------------------------------------
def inject_css():
    css_path = APP_DIR / "assets" / "styles.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800'
        '&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    if css:
        st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Helpers de render (Python -> HTML)
# ---------------------------------------------------------------------------
def particles_html(rango_id: str, size: str) -> str:
    if rango_id not in ("maestro", "ascendente"):
        return ""
    n = 10 if size == "xl" else 6
    spans = []
    for _ in range(n):
        x = random.randint(10, 90)
        delay = round(random.uniform(0, 2), 2)
        dur = round(random.uniform(1.4, 3.0), 2)
        drift = random.randint(-8, 8)
        spans.append(
            f'<span class="badge__particle" style="--x:{x}%;--delay:{delay}s;'
            f'--dur:{dur}s;--x-drift:{drift}px;"></span>'
        )
    return "".join(spans)

def badge_html(rango_id: str, avatar: str, size: str = "xl") -> str:
    return (
        f'<div class="badge badge--{size} badge--{rango_id}">'
        f'<div class="badge__glow"></div><div class="badge__ring"></div>'
        f'<span class="badge__icon">{avatar}</span>'
        f"{particles_html(rango_id, size)}</div>"
    )

def hero_card_html(persona: dict) -> str:
    rango = persona["rango"]
    if rango["es_maximo"]:
        label = "Rango máximo alcanzado 🏆"
    else:
        label = (
            f'Te faltan <strong>{rango["puntos_para_subir"]} pts</strong> '
            f'para llegar a <strong>{rango["siguiente_rango"]}</strong>'
        )
    return f"""
    <div class="hero-card">
      <div>{badge_html(rango['id'], persona['avatar'], 'xl')}</div>
      <div class="hero-card__right">
        <p class="hero-card__eyebrow">Rango actual</p>
        <h1 class="hero-card__rank-name">{rango['nombre']}</h1>
        <p class="hero-card__player">{persona['nombre']} · {persona['puntos']} pts</p>
        <div class="progress__track">
          <div class="progress__fill rank-text--{rango['id']}"
               style="width:{rango['progreso']}%; background: linear-gradient(90deg, var(--{rango['id']}-2), var(--{rango['id']}-1));"></div>
        </div>
        <p class="progress__label">{label}</p>
      </div>
    </div>
    """

def podium_html(top3: list) -> str:
    crowns = ["👑", "🥈", "🥉"]
    slots = "".join(
        f"""
        <div class="podium__slot podium__slot--{i+1}">
          <div class="podium__crown">{crowns[i]}</div>
          {badge_html(c['rango']['id'], c['avatar'], 'md')}
          <p class="podium__name">{c['nombre']}</p>
          <p class="podium__points">{c['puntos']} pts</p>
          <p class="podium__rank rank-text--{c['rango']['id']}">{c['rango']['nombre']}</p>
        </div>"""
        for i, c in enumerate(top3)
    )
    return f'<div class="podium">{slots}</div>'

def ranking_table_html(ranking: list, nombre_seleccionado: str) -> str:
    rows = []
    for c in ranking:
        clases = []
        if c["puesto"] <= 3:
            clases.append("ranking-table__row--top")
        if c["nombre"] == nombre_seleccionado:
            clases.append("ranking-table__row--you")
        rows.append(f"""
        <tr class="{' '.join(clases)}">
          <td>#{c['puesto']}</td>
          <td class="ranking-table__name"><span>{c['avatar']}</span>{c['nombre']}</td>
          <td><span class="pill pill--{c['rango']['id']}">{c['rango']['nombre']}</span></td>
          <td>{c['puntos']}</td>
        </tr>""")
    return f"""
    <table class="ranking-table">
      <thead><tr><th>Puesto</th><th>Comercial</th><th>Rango</th><th>Puntos</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """

def achievements_html(logros: list) -> str:
    cards = []
    for l in logros:
        estado = "achievement--unlocked" if l["desbloqueado"] else "achievement--locked"
        candado = "" if l["desbloqueado"] else '<div class="achievement__lock">🔒</div>'
        cards.append(f"""
        <div class="achievement {estado}">
          <div class="achievement__icon">{l['icono']}</div>{candado}
          <p class="achievement__name">{l['nombre']}</p>
          <p class="achievement__desc">{l['desc']}</p>
        </div>""")
    return f'<div class="achievements-grid">{"".join(cards)}</div>'

def render_levelup(nombre_rango: str):
    html = f"""
    <div style="position:relative;height:320px;border-radius:20px;overflow:hidden;
                background:radial-gradient(circle at 50% 30%, #1b2430, #05070a);
                display:flex;align-items:center;justify-content:center;">
      <canvas id="confettiCanvas" style="position:absolute;inset:0;"></canvas>
      <div style="text-align:center;z-index:2;">
        <p style="margin:0;color:#8A97A6;letter-spacing:.2em;font-family:Inter,sans-serif;font-size:.8rem;">¡SUBIDA DE RANGO!</p>
        <p style="margin:6px 0 0;font-family:Orbitron,sans-serif;font-weight:800;font-size:2.6rem;
                   background:linear-gradient(90deg,#FFB020,#fff,#FFB020);-webkit-background-clip:text;
                   background-clip:text;color:transparent;">{nombre_rango}</p>
      </div>
    </div>
    <script>
      const canvas = document.getElementById('confettiCanvas');
      const ctx = canvas.getContext('2d');
      canvas.width = canvas.parentElement.offsetWidth;
      canvas.height = 320;
      const colors = ["#FFB020","#FFD877","#C79CFF","#4FB8D6","#FF7A3D"];
      const pieces = Array.from({{length: 120}}, () => ({{
        x: Math.random() * canvas.width,
        y: -20 - Math.random() * canvas.height * 0.5,
        size: 4 + Math.random() * 5,
        speedY: 2 + Math.random() * 3,
        speedX: -1.5 + Math.random() * 3,
        rotation: Math.random() * 360,
        rotationSpeed: -6 + Math.random() * 12,
        color: colors[Math.floor(Math.random() * colors.length)],
      }}));
      let frame = 0;
      function step() {{
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        pieces.forEach(p => {{
          p.x += p.speedX; p.y += p.speedY; p.rotation += p.rotationSpeed;
          ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rotation * Math.PI / 180);
          ctx.fillStyle = p.color; ctx.fillRect(-p.size/2, -p.size/2, p.size, p.size*0.6);
          ctx.restore();
        }});
        frame++;
        if (frame < 140) requestAnimationFrame(step); else ctx.clearRect(0,0,canvas.width,canvas.height);
      }}
      step();
    </script>
    """
    components.html(html, height=340)

# ---------------------------------------------------------------------------
# LÓGICAS NUEVAS: Google Sheets, Login y Muro de Fuego
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_datos_sheets():
    try:
        if "TU_ENLACE_AQUI" not in SHEET_CSV_URL:
            return pd.read_csv(SHEET_CSV_URL)
        return None
    except Exception as e:
        st.error(f"Error conectando a Google Sheets: {e}")
        return None

def verificar_login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if st.session_state["autenticado"]:
        return  
        
    st.markdown(
        '<div class="arena-brand"><span class="arena-brand__mark">◆</span>'
        '<span class="arena-brand__text">ARENA COMERCIAL</span></div>',
        unsafe_allow_html=True,
    )
    st.subheader("🔐 Inicia sesión para ver tu ranking")
    
    with st.form("login_form"):
        usuario_input = st.text_input("Usuario")
        clave_input = st.text_input("Contraseña", type="password")
        enviado = st.form_submit_button("Entrar")
        
    if enviado:
        try:
            usuarios = pd.read_excel(USUARIOS_FILE)
            fila = usuarios[
                (usuarios["usuario"].astype(str).str.lower() == usuario_input.strip().lower())
                & (usuarios["contraseña"].astype(str) == clave_input)
            ]
            if not fila.empty:
                st.session_state["autenticado"] = True
                st.session_state["usuario_actual"] = usuario_input
                st.session_state["rol_actual"] = fila.iloc[0]["rol"]
                st.session_state["nombre_comercial"] = fila.iloc[0]["nombre_comercial"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
        except FileNotFoundError:
            st.error(f"Error: No se encuentra el archivo '{USUARIOS_FILE}'. Asegúrate de haberlo subido a la carpeta 'data/'.")
            
    st.stop()  

def detectar_muro_de_fuego(ranking_actual: list) -> list:
    orden_rangos = [r["id"] for r in RANGOS]
    anterior = st.session_state.get("ranking_anterior")
    mensajes = []
    
    if anterior:
        actuales_por_nombre = {c["nombre"]: c for c in ranking_actual}
        for nombre, snap_previo in anterior.items():
            actual = actuales_por_nombre.get(nombre)
            if not actual:
                continue
            subio_de_rango = (
                orden_rangos.index(actual["rango"]["id"])
                > orden_rangos.index(snap_previo["rango_id"])
            )
            if not subio_de_rango or snap_previo["puesto"] == 1:
                continue
                
            nombre_superado = next(
                (n for n, p in anterior.items() if p["puesto"] == snap_previo["puesto"] - 1),
                None,
            )
            if not nombre_superado:
                continue
            superado_actual = actuales_por_nombre.get(nombre_superado)
            if superado_actual and actual["puntos"] > superado_actual["puntos"]:
                mensajes.append(
                    f"🔥 ¡BRUTAL! **{nombre}** acaba de subir a rango "
                    f"**{actual['rango']['nombre']}** con sus últimos contratos y ha "
                    f"dejado a **{nombre_superado}** mordiendo el polvo en el "
                    f"retrovisor. ¡A espabilar! 💥"
                )
                
    st.session_state["ranking_anterior"] = {
        c["nombre"]: {"puntos": c["puntos"], "rango_id": c["rango"]["id"], "puesto": c["puesto"]}
        for c in ranking_actual
    }
    return mensajes

# ---------------------------------------------------------------------------
# APP PRINCIPAL
# ---------------------------------------------------------------------------
inject_css()
verificar_login()

# Intentamos usar los datos en vivo de Google Sheets si están configurados
df_vivo = cargar_datos_sheets()
try:
    # Si 'ranks.py' ya está adaptado para recibir el DataFrame:
    ranking = cargar_ranking(df_vivo) if df_vivo is not None else cargar_ranking()
except TypeError:
    # Si 'ranks.py' todavía no acepta el parámetro, usamos el método antiguo
    ranking = cargar_ranking()

# --- MENÚ LATERAL ---
with st.sidebar:
    st.markdown(f"**{st.session_state['usuario_actual']}**")
    st.caption(st.session_state["rol_actual"])
    st.divider()
    
    opciones = ["🏆 Ranking", "🎖️ Logros"]
    if st.session_state["rol_actual"] == "Gerente":
        opciones.append("📊 Vista Estratégica")
        
    pagina = st.radio("Navegación", opciones, label_visibility="collapsed")
    st.divider()
    
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

# --- SELECTOR DE USUARIO (GERENTE VS COMERCIAL) ---
nombres = [c["nombre"] for c in ranking]

if st.session_state["rol_actual"] == "Gerente":
    nombre_seleccionado = st.selectbox("Ver dashboard como:", nombres, index=0)
else:
    nombre_seleccionado = st.session_state["nombre_comercial"]

try:
    yo = next(c for c in ranking if c["nombre"] == nombre_seleccionado)
except StopIteration:
    st.error(f"Error: El comercial '{nombre_seleccionado}' no está en la base de datos de comerciales.")
    st.stop()

# --- RUTAS DE NAVEGACIÓN ---
if pagina == "🏆 Ranking":
    
    st.markdown(
        '<div class="arena-brand"><span class="arena-brand__mark">◆</span>'
        '<span class="arena-brand__text">ARENA COMERCIAL</span></div>'
        '<p class="arena-header__meta">Temporada en curso · Sincronización activa</p>',
        unsafe_allow_html=True,
    )
    
    # Renderizamos el Muro de Fuego
    for mensaje in detectar_muro_de_fuego(ranking):
        st.success(mensaje)

    st.markdown(hero_card_html(yo), unsafe_allow_html=True)

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("▶ Simular subida de rango"):
            idx_actual = next(i for i, r in enumerate(RANGOS) if r["nombre"] == yo["rango"]["nombre"])
            siguiente = RANGOS[idx_actual + 1] if idx_actual + 1 < len(RANGOS) else RANGOS[-1]
            render_levelup(siguiente["nombre"])

    st.markdown('<p class="panel-title">Clasificación del equipo</p>', unsafe_allow_html=True)
    st.markdown(podium_html(ranking[:3]), unsafe_allow_html=True)
    st.markdown(ranking_table_html(ranking, nombre_seleccionado), unsafe_allow_html=True)

elif pagina == "🎖️ Logros":
    st.markdown(
        f'<p class="panel-title" style="margin-top:32px;">Vitrina de logros — {yo["nombre"]}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(achievements_html(yo["logros"]), unsafe_allow_html=True)
    
    st.divider()
    
    # --- MECÁNICA DE COFRES Y BARRA DE ENERGÍA ---
    RECOMPENSAS_ELITE = [
        "🎵 Eliges la música de la tienda hoy",
        "☕ Café pagado por el gerente",
        "🛌 Turno de descanso extra",
        "🅿️ Sitio de parking VIP durante una semana",
        "🍕 Invitación a comer",
    ]

    st.markdown("### 🎁 Cofre de Recompensa de la Élite")
    
    # Leer usuarios y AUTO-CORREGIR el Excel si falta la columna
    usuarios_df = pd.read_excel(USUARIOS_FILE)
    
    if "puntos_ultimo_cofre" not in usuarios_df.columns:
        usuarios_df["puntos_ultimo_cofre"] = 0
        usuarios_df.to_excel(USUARIOS_FILE, index=False)
        
    fila_usuario = usuarios_df[usuarios_df["usuario"].astype(str).str.lower() == st.session_state["usuario_actual"].lower()]
    
    puntos_ultimo_cofre = fila_usuario.iloc[0].get("puntos_ultimo_cofre", 0)
    if pd.isna(puntos_ultimo_cofre):
        puntos_ultimo_cofre = 0
        
    puntos_actuales = yo["puntos"]
    puntos_acumulados = puntos_actuales - puntos_ultimo_cofre
    puntos_objetivo = 10
    
    progreso = min(max(puntos_acumulados, 0), puntos_objetivo)
    porcentaje = (progreso / puntos_objetivo) * 100

    barra_html = f"""
    <div style="background-color: #111827; border-radius: 12px; padding: 16px; margin-bottom: 24px; border: 1px solid #1F2937;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="color: #10B981; font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">Energía del Cofre</span>
            <span style="color: #fff; font-family: 'Inter', sans-serif; font-weight: 600;">{progreso} / {puntos_objetivo} pts</span>
        </div>
        <div style="background-color: #374151; border-radius: 8px; height: 18px; width: 100%; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);">
            <div style="background: linear-gradient(90deg, #059669, #34D399); height: 100%; border-radius: 8px; width: {porcentaje}%; transition: width 0.8s ease-out; box-shadow: 0 0 10px #34D399;"></div>
        </div>
    </div>
    """
    st.markdown(barra_html, unsafe_allow_html=True)

    rango_id_usuario = yo["rango"]["id"]
    tiene_acceso_cofre = rango_id_usuario in ("ascendente", "maestro")

    if not tiene_acceso_cofre:
        st.button("🔒 Cofre bloqueado — alcanza Ascendente (19+ pts) para desbloquear", disabled=True)
    else:
        if progreso >= puntos_objetivo:
            if st.button("✨ ¡ENERGÍA AL MÁXIMO! ABRIR COFRE ✨", type="primary"):
                idx = fila_usuario.index[0]
                usuarios_df.at[idx, "puntos_ultimo_cofre"] = puntos_actuales
                usuarios_df.to_excel(USUARIOS_FILE, index=False)
                
                premio = random.choice(RECOMPENSAS_ELITE)
                st.balloons()
                st.success(f"🎉 ¡Has ganado: {premio}!")
                st.rerun()
        else:
            faltan = puntos_objetivo - progreso
            st.button(f"⚡ Consigue {faltan} puntos más para recargar", disabled=True)

elif pagina == "📊 Vista Estratégica":
    st.title("📊 Vista Estratégica")
    st.info("Próximamente: Panel de Control de Tienda")
    st.write("Bienvenido a la vista de mando. Pronto integraremos KPIs globales aquí.")
