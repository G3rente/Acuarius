# Arena Comercial — Dashboard de Gamificación (Streamlit)

Misma app que la versión Flask, reescrita sobre Streamlit. Un solo comando
para arrancarla, sin plantillas ni carpeta `static/`.

## Estructura

```
streamlit-sales-gamification/
├── app.py                  # App Streamlit (UI completa)
├── ranks.py                # Lógica de rangos, progreso y logros (sin Flask)
├── requirements.txt
├── data/
│   └── comerciales.xlsx    # nombre, puntos, avatar, logros — tu Excel adaptado
└── assets/
    └── styles.css          # Mismos tokens/animaciones que la versión Flask
```

## Puesta en marcha

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre en `http://localhost:8501`. El selector superior ("Ver dashboard
como:") cambia de comercial sin recargar nada más — útil porque Streamlit,
a diferencia de Flask, no tiene un usuario logueado por request.

## Qué cambió respecto a la versión Flask

- **Sin `templates/` ni Jinja**: el HTML de la insignia, el podio, la tabla
  y los logros se genera con funciones Python en `app.py` y se inyecta con
  `st.markdown(..., unsafe_allow_html=True)`.
- **Sin `dashboard.js`**: las partículas de las insignias Ascendente/Maestro
  ahora se generan en Python (posiciones aleatorias en cada render) en vez
  de con JavaScript en el navegador.
- **Level Up**: como un componente de Streamlit no puede pintar un overlay
  a pantalla completa (vive dentro de un iframe), la celebración se muestra
  como un banner con confeti en `<canvas>` justo debajo del botón, en vez
  de cubrir toda la pantalla. Si más adelante quieres el overlay a pantalla
  completa de verdad, hay que montarlo como página HTML publicada aparte
  (o un componente custom de Streamlit), y decírmelo.
- El baremo de rangos y el catálogo de logros (`ranks.py`) son exactamente
  los mismos que en `app.py` de la versión Flask — no cambió ninguna regla
  de negocio, solo el framework.

## Datos

`data/comerciales.xlsx` es tu archivo original adaptado a las columnas
`nombre, puntos, avatar, logros`. La columna `logros` está vacía porque tu
Excel original no traía esa información — rellénala (IDs separados por
comas: `primera_venta`, `hattrick_renoves`, `conversion_perfecta`,
`racha_semanal`) cuando tengas ese dato.
