"""
Arena Comercial — Dashboard de Gamificación (Streamlit)
--------------------------------------------------------
Antes era Flask + Jinja; ahora es una app Streamlit de una sola página.
La lógica de rangos/logros vive en ranks.py (sin cambios de negocio,
solo se le quitó la dependencia de Flask).
"""

import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from ranks import RANGOS, cargar_ranking

APP_DIR = Path(__file__).parent

st.set_page_config(page_title="Arena Comercial", page_icon="🏆", layout="wide")

# ---------------------------------------------------------------------------
# Estilos: fuentes + CSS del sistema de diseño
# ---------------------------------------------------------------------------
def inject_css():
    """
    OJO: cada tag va en su propia llamada a st.markdown, cada una por
    separado. Si se concatenan <link> + <style> en una sola llamada,
    Streamlit deja de reconocer el <style> como bloque HTML "en bruto" y
    el CSS se cuela como texto visible en la página en vez de aplicarse
    como hoja de estilos (justo el bug que se veía antes).
    """
    css = (APP_DIR / "assets" / "styles.css").read_text(encoding="utf-8")

    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800'
        '&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers de render (Python -> HTML, reemplazan lo que antes hacía Jinja/JS)
# ---------------------------------------------------------------------------
def particles_html(rango_id: str, size: str) -> str:
    """Genera partículas con posiciones/tiempos aleatorios en cada render
    (en la versión Flask esto lo hacía dashboard.js en el navegador)."""
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
    """Celebración de subida de rango: al no poder pintar un overlay a
    pantalla completa dentro del sandbox de un componente de Streamlit,
    se muestra como un banner protagonista con confeti animado en canvas."""
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
# App
# ---------------------------------------------------------------------------
inject_css()

ranking = cargar_ranking()

st.markdown(
    '<div class="arena-brand"><span class="arena-brand__mark">◆</span>'
    '<span class="arena-brand__text">ARENA COMERCIAL</span></div>'
    '<p class="arena-header__meta">Temporada en curso · datos desde data/comerciales.xlsx</p>',
    unsafe_allow_html=True,
)

nombres = [c["nombre"] for c in ranking]
nombre_seleccionado = st.selectbox("Ver dashboard como:", nombres, index=0)
yo = next(c for c in ranking if c["nombre"] == nombre_seleccionado)

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

st.markdown(
    f'<p class="panel-title" style="margin-top:32px;">Vitrina de logros — {yo["nombre"]}</p>',
    unsafe_allow_html=True,
)
st.markdown(achievements_html(yo["logros"]), unsafe_allow_html=True)
