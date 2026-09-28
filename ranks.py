"""

Lógica de negocio de la gamificación: rangos, progreso y logros.

Independiente del framework (antes la usaba Flask, ahora Streamlit).

"""



from pathlib import Path

import pandas as pd



DATA_FILE = Path(__file__).parent / "data" / "comerciales.xlsx"



# ---------------------------------------------------------------------------

# BAREMO DE RANGOS (orden = orden de progresión)

# ---------------------------------------------------------------------------

RANGOS = [

    {"id": "bronce",     "nombre": "Bronce",     "min": 0,  "max": 5},

    {"id": "plata",      "nombre": "Plata",      "min": 6,  "max": 8},

    {"id": "oro",        "nombre": "Oro",        "min": 9,  "max": 12},

    {"id": "platino",    "nombre": "Platino",    "min": 13, "max": 18},

    {"id": "ascendente", "nombre": "Ascendente", "min": 19, "max": 25},

    {"id": "maestro",    "nombre": "Maestro",    "min": 26, "max": 30},

]



# ---------------------------------------------------------------------------

# CATÁLOGO DE LOGROS

# ---------------------------------------------------------------------------

LOGROS_CATALOGO = [

    {"id": "primera_venta",       "nombre": "Primera Venta del Día",          "icono": "🌅", "desc": "Cierra la primera venta del día."},

    {"id": "hattrick_renoves",    "nombre": "Hat-Trick de Renoves",           "icono": "🎩", "desc": "3 ventas por la mañana"},

    {"id": "conversion_perfecta", "nombre": "Conversión Multicanal Perfecta", "icono": "🎯", "desc": "100% de conversión combinando 2+ canales."},

    {"id": "racha_semanal",       "nombre": "Racha Semanal",                  "icono": "🔥", "desc": "Objetivo cumplido 5 días seguidos."},

]





def calcular_rango(puntos: int) -> dict:

    """Devuelve el rango, el progreso (0-100) y los puntos que faltan."""

    puntos = max(0, min(puntos, RANGOS[-1]["max"]))



    for i, rango in enumerate(RANGOS):

        if rango["min"] <= puntos <= rango["max"]:

            ancho_banda = rango["max"] - rango["min"] + 1

            avance_en_banda = puntos - rango["min"] + 1

            progreso = round((avance_en_banda / ancho_banda) * 100, 1)



            siguiente = RANGOS[i + 1] if i + 1 < len(RANGOS) else None

            puntos_para_subir = (siguiente["min"] - puntos) if siguiente else 0



            return {

                **rango,

                "progreso": progreso,

                "siguiente_rango": siguiente["nombre"] if siguiente else None,

                "puntos_para_subir": puntos_para_subir,

                "es_maximo": siguiente is None,

            }



    return {**RANGOS[0], "progreso": 0, "siguiente_rango": RANGOS[1]["nombre"],

            "puntos_para_subir": RANGOS[1]["min"], "es_maximo": False}





def construir_logros(logros_ids) -> list:

    # pandas convierte las celdas vacías del Excel en NaN (float), no en "".

    if not isinstance(logros_ids, str):

        logros_ids = ""

    ids_desbloqueados = {x.strip() for x in logros_ids.split(",") if x.strip()}

    return [

        {**logro, "desbloqueado": logro["id"] in ids_desbloqueados}

        for logro in LOGROS_CATALOGO

    ]





def cargar_ranking(data_file: Path = DATA_FILE) -> list:

    df = pd.read_excel(data_file)

    comerciales = []



    for _, fila in df.iterrows():

        puntos = int(fila["puntos"])

        comerciales.append({

            "nombre": fila["nombre"],

            "avatar": fila.get("avatar", "🙂") if isinstance(fila.get("avatar"), str) else "🙂",

            "puntos": puntos,

            "rango": calcular_rango(puntos),

            "logros": construir_logros(fila.get("logros", "")),

        })



    comerciales.sort(key=lambda c: c["puntos"], reverse=True)

    for i, c in enumerate(comerciales, start=1):

        c["puesto"] = i



    return comerciales 

