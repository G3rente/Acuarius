"""
Arena Comercial — Dashboard de Gamificación (Streamlit)
--------------------------------------------------------
Incluye Login, Roles de Gerencia, Muro de Fuego, Recompensas (Barra de Energía),
Guerra de Facciones (con filtro estricto) y Conexión Dinámica a Google Sheets
con Modo a Prueba de Fallos.
"""

import random
import time
from pathlib import Path
import pandas as pd

import streamlit as st
import streamlit.components.v1 as components

from ranks import RANGOS, cargar_ranking

APP_DIR = Path(__file__).parent
USUARIOS_FILE = APP_DIR / "data" / "usuarios.xlsx"
URL_FILE = APP_DIR / "data" / "sheet_url.txt"

# URL por defecto (fallback)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/TU_ENLACE_AQUI/pub?output=csv"

st.set_page_config(page_title="Arena Comercial", page_icon="🏆", layout="wide")

# ---------------------------------------------------------------------------
# GESTIÓN DINÁMICA DE LA URL DE GOOGLE SHEETS
# ---------------------------------------------------------------------------
def obtener_url_sheets() -> str:
    """Lee la URL guardada en disco. Si el archivo aún no existe, usa la de por defecto."""
    if URL_FILE.exists():
        url_guardada = URL_FILE.read_text(encoding="utf-8").strip()
        if url_guardada:
            return url_guardada
    return SHEET_CSV_URL

def guardar_url_sheets(url: str) -> None:
    """Guarda la nueva URL de Google Sheets en un archivo de texto local."""
    URL_FILE.parent.mkdir(parents=True, exist_ok=True)
    URL_FILE.write_text(url.strip(), encoding="utf-8")

# ---------------------------------------------------------------------------
# AUTO-CONFIGURACIÓN INTELIGENTE DE USUARIOS Y EQUIPOS
# ---------------------------------------------------------------------------
def asegurar_columnas_usuarios():
    if USUARIOS_FILE.exists():
        df = pd.read_excel(USUARIOS_FILE)
        cambios = False
        
        if "puntos_ultimo_cofre" not in df.columns:
            df["puntos_ultimo_cofre"] = 0
            cambios = True
            
        if "equipo" not in df.columns or df["equipo"].isnull().all():
            equipos_dict = {
                "OROPEZA OL": "Aztecas", "JHONALBERT OL": "Astros", "FLORES OL": "Dominus", 
                "INFANTE OL": "Pegasus", "NASSER OL": "Pegasus", "GIBRAN OL": "Dominus",
                "NATASHA OL": "Pegasus", "JOSNEIKER OL": "Pegasus", "VIZCAÍNO OL": "Aztecas",
                "RACHELY OL": "Dominus", "OCHOA OL": "Dominus", "VELASQUEZ OL": "Astros",
                "VIZCAYA OL": "Astros", "LAREZ OL": "Aztecas", "HUMBERTO OL": "Dominus",
                "MINERVA OL": "Astros", "BARRIOS OL": "Dominus", "SOFIA OL": "Dominus",
                "ANDRADES OL": "Dominus", "LOPANO OL": "Dominus", "MORENO OL": "Aztecas",
                "NAVAS OL": "Dominus", "GABRIEL OL": "Aztecas", "COLÓN OL": "Pegasus",
                "HEISYS OL": "Aztecas", "PEÑA OL": "Astros", "JOIVER OL": "Dominus",
                "MARIANA OL": "Aztecas", "SUAREZ D OL": "Pegasus", "ALDRIANA OL": "Astros",
                "NAHUM OL": "Astros", "BORGES OL": "Astros", "JHOSTYN OL": "Dominus",
                "DANIEL OL": "Astros", "RAFAEL OL": "Dominus", "LUYSANGEL OL": "Astros",
                "EMANUEL OL": "Pegasus", "ALESSANDRA OL": "Pegasus", "KARIANNY OL": "Dominus",
                "REYES OL": "Dominus", "MARIELIS OL": "Aztecas", "MORALES OL": "Astros",
                "NORVELYS OL": "Dominus", "YULIANNY OL": "Dominus", "SUÁREZ D OL": "Pegasus",
                "SIERRA OL": "Astros"
            }
            df["equipo"] = df["nombre_comercial"].map(equipos_dict).fillna("")
            cambios = True
            
        if cambios:
            df.to_excel(USUARIOS_FILE, index=False)

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
# LÓGICAS NUEVAS (Datos y Muro)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_datos_sheets():
    try:
        url = obtener_url_sheets()
        if url and "TU_ENLACE_AQUI" not in url:
            # Leemos el CSV ignorando las líneas sucias que dan el error de las 12 columnas
            df = pd.read_csv(url, on_bad_lines='skip')
            
            # Limpiamos nombres de columnas por si hay espacios invisibles
            df.columns = df.columns.str.strip().str.upper()
            
            # Si el Excel es un registro de ventas (tiene COMERCIAL y PTS), lo sumamos automáticamente
            if 'COMERCIAL' in df.columns and 'PTS' in df.columns:
                # Renombramos a lo que entiende ranks.py
                df = df.rename(columns={'COMERCIAL': 'nombre', 'PTS': 'puntos'})
                
                # Convertimos los puntos a números por si acaso y rellenamos vacíos con 0
                df['puntos'] = pd.to_numeric(df['puntos'], errors='coerce').fillna(0)
                
                # LA MAGIA: Agrupamos por comercial y sumamos todos sus contratos repetidos
                df = df.groupby('nombre', as_index=False)['puntos'].sum()
                
            return df
        return None
    except Exception as e:
        # Silenciamos el error visual para no asustar al usuario
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
asegurar_columnas_usuarios()
inject_css()
verificar_login()

# --- CARGA SEGURA DE DATOS A PRUEBA DE FALLOS ---
df_vivo = cargar_datos_sheets()
ranking = []
try:
    if df_vivo is not None:
        ranking = cargar_ranking(df_vivo)
    else:
        ranking = cargar_ranking()
except Exception:
    # Si todo falla (ej: archivo local borrado y Sheets desconectado), ranking se queda vacío
    pass

# --- MENÚ LATERAL ---
with st.sidebar:
    st.markdown(f"**{st.session_state['usuario_actual']}**")
    st.caption(st.session_state["rol_actual"])
    st.divider()
    
    opciones = ["🏆 Ranking", "🎖️ Logros", "⚔️ Facciones"]
    if st.session_state["rol_actual"] == "Gerente":
        opciones.append("📊 Vista Estratégica")
        
    pagina = st.radio("Navegación", opciones, label_visibility="collapsed")
    st.divider()
    
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

# --- SELECTOR DE USUARIO Y PROTECCIÓN DE RUTAS ---
nombres = [c["nombre"] for c in ranking] if ranking else ["Sin Datos"]

if st.session_state["rol_actual"] == "Gerente":
    nombre_seleccionado = st.selectbox("Ver dashboard como:", nombres, index=0)
else:
    nombre_seleccionado = st.session_state["nombre_comercial"]

# Buscamos al usuario en la lista
try:
    yo = next((c for c in ranking if c["nombre"] == nombre_seleccionado), None)
except Exception:
    yo = None

# ESCUDO ANTI-BLOQUEO: Si no hay datos, bloquea todo EXCEPTO la Vista Estratégica
if not yo and pagina != "📊 Vista Estratégica":
    st.warning("⚠️ No hay conexión con la base de datos o el Google Sheets. Si eres Gerente, ve a la pestaña **📊 Vista Estratégica** y configura el enlace válido.")
    st.stop()


# --- RUTAS DE NAVEGACIÓN ---
if pagina == "🏆 Ranking":
    st.markdown(
        '<div class="arena-brand"><span class="arena-brand__mark">◆</span>'
        '<span class="arena-brand__text">ARENA COMERCIAL</span></div>'
        '<p class="arena-header__meta">Temporada en curso · Sincronización activa</p>',
        unsafe_allow_html=True,
    )
    
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
    
    RECOMPENSAS_ELITE = [
        "🎵 Eliges la música de la tienda hoy",
        "☕ Café pagado por el gerente",
        "🛌 Turno de descanso extra",
        "🅿️ Sitio de parking VIP durante una semana",
        "🍕 Invitación a comer",
    ]

    st.markdown("### 🎁 Cofre de Recompensa de la Élite")
    
    usuarios_df = pd.read_excel(USUARIOS_FILE)
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

elif pagina == "⚔️ Facciones":
    st.markdown(
        '<div class="arena-brand"><span class="arena-brand__mark">⚔️</span>'
        '<span class="arena-brand__text">GUERRA DE FACCIONES</span></div>'
        '<p class="arena-header__meta">Todos contra Todos · El mejor equipo se lleva la gloria</p>',
        unsafe_allow_html=True,
    )
    
    usuarios_df = pd.read_excel(USUARIOS_FILE)
    equipo_map = dict(zip(usuarios_df['nombre_comercial'], usuarios_df['equipo']))
    
    facciones = {
        "Aztecas": {"puntos": 0, "gerente": "Joselito", "color": "#10B981", "shadow": "rgba(16,185,129,0.5)", "mvp_nombre": "-", "mvp_puntos": -1},
        "Pegasus": {"puntos": 0, "gerente": "Joselito", "color": "#3B82F6", "shadow": "rgba(59,130,246,0.5)", "mvp_nombre": "-", "mvp_puntos": -1},
        "Dominus": {"puntos": 0, "gerente": "Majus", "color": "#EF4444", "shadow": "rgba(239,68,68,0.5)", "mvp_nombre": "-", "mvp_puntos": -1},
        "Astros": {"puntos": 0, "gerente": "Majus", "color": "#8B5CF6", "shadow": "rgba(139,92,246,0.5)", "mvp_nombre": "-", "mvp_puntos": -1}
    }
    
    # 3. Sumar puntos y buscar MVPs (Filtro estricto y regla de comerciales en blanco)
    for c in ranking:
        nombre = c["nombre"]
        puntos = c["puntos"]
        
        nombre_limpio = str(nombre).strip().lower()
        if nombre_limpio in ("", "nan", "none", "nat"):
            equipo_str = "Dominus" 
            nombre_mostrar = "Comercial Anónimo"
        else:
            # Obtener el equipo y normalizarlo (por ej. 'aztecas' -> 'Aztecas')
            equipo_crudo = equipo_map.get(nombre, "")
            equipo_str = str(equipo_crudo).strip().title()
            nombre_mostrar = nombre
            
        # FILTRO ESTRICTO: Si no es Aztecas, Pegasus, Dominus o Astros, lo ignora totalmente.
        if equipo_str in facciones:
            facciones[equipo_str]["puntos"] += puntos
            if puntos > facciones[equipo_str]["mvp_puntos"]:
                facciones[equipo_str]["mvp_puntos"] = puntos
                facciones[equipo_str]["mvp_nombre"] = nombre_mostrar
                
    facciones_ordenadas = sorted(facciones.items(), key=lambda x: x[1]["puntos"], reverse=True)
    max_puntos = facciones_ordenadas[0][1]["puntos"] if facciones_ordenadas[0][1]["puntos"] > 0 else 1
    
    html_cards = "<div style='display: flex; flex-direction: column; gap: 24px; margin-top: 20px;'>"
    for rank, (eq_nombre, eq_data) in enumerate(facciones_ordenadas):
        porcentaje = (eq_data["puntos"] / max_puntos) * 100
        corona = "👑 " if rank == 0 else ""
        
        html_cards += f"""<div style="background-color: #111827; border-radius: 16px; padding: 24px; border: 1px solid #1F2937; position: relative; overflow: hidden;">
<div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 16px;">
<div>
<h2 style="margin: 0; color: #fff; font-family: 'Orbitron', sans-serif; font-size: 2rem; letter-spacing: 2px; text-transform: uppercase;">{corona}{eq_nombre}</h2>
<p style="margin: 4px 0 0 0; color: #9CA3AF; font-size: 1rem;">Comandante: <strong style="color: #fff;">{eq_data['gerente']}</strong></p>
</div>
<div style="text-align: right;">
<h3 style="margin: 0; color: {eq_data['color']}; font-family: 'Orbitron', sans-serif; font-size: 2.5rem; text-shadow: 0 0 10px {eq_data['shadow']};">
{eq_data['puntos']} <span style="font-size:1.2rem; color:#9CA3AF; text-shadow: none;">PTS</span>
</h3>
<p style="margin: 4px 0 0 0; color: #D1D5DB; font-size: 1rem;">⭐ MVP: <strong style="color: #fff;">{eq_data['mvp_nombre']}</strong> ({eq_data['mvp_puntos']} pts)</p>
</div>
</div>
<div style="background-color: #374151; border-radius: 10px; height: 28px; width: 100%; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);">
<div style="background: linear-gradient(90deg, {eq_data['color']}88, {eq_data['color']}); height: 100%; border-radius: 10px; width: {porcentaje}%; transition: width 1s ease-out; box-shadow: 0 0 20px {eq_data['shadow']};"></div>
</div>
</div>"""
    html_cards += "</div>"
    st.markdown(html_cards, unsafe_allow_html=True)

elif pagina == "📊 Vista Estratégica":
    st.title("📊 Vista Estratégica")
    st.markdown("### 🔗 Conexión a Google Sheets")
    
    url_actual = obtener_url_sheets()
    st.caption(f"URL activa: `{url_actual}`" if url_actual and "TU_ENLACE_AQUI" not in url_actual else "Sin URL configurada todavía.")
    
    with st.form("form_sheets"):
        nueva_url = st.text_input(
            "Pega aquí el enlace CSV de Google Sheets (Archivo → Compartir → Publicar en la web → formato CSV)",
            value=url_actual if "TU_ENLACE_AQUI" not in url_actual else "",
        )
        sincronizar = st.form_submit_button("⚡ Enlazar y Sincronizar")
        
    if sincronizar:
        if nueva_url.strip():
            guardar_url_sheets(nueva_url)
            st.cache_data.clear()
            st.success("✅ URL guardada y caché limpiada. Refrescando la arena...")
            time.sleep(1.5)
            st.rerun()
        else:
            st.error("Por favor, pega una URL válida antes de intentar sincronizar.")
