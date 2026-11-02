"""weapons: las tres armas dibujadas pixel a pixel, para ponerlas en la mano de cada personaje.

Son piezas chicas (≤ 16×7) y se dibujan a mano con una rejilla de letras, como se haría en
Aseprite; comparten seis colores que se añaden a la paleta de cada personaje. El origen de cada
arma es su esquina inferior izquierda (la culata/empuñadura), que se apoya en el ancla de la mano.
"""
from __future__ import annotations

import numpy as np

# nombre → color
COLORS = {
    "D": (26, 28, 34),      # gunmetal oscuro / contorno del arma
    "M": (92, 98, 110),     # gunmetal
    "L": (164, 170, 182),   # brillo del metal
    "W": (124, 74, 38),     # madera
    "w": (74, 42, 22),      # madera en sombra
    "B": (214, 160, 60),    # latón / acento
}

# Rejillas (mirando a la derecha). '.' = transparente.
GRIDS = {
    # escopeta recortada de doble cañón: bomba de madera y dos tubos
    "shotgun": [
        "..DDDDDDDDDDDDD.",
        ".DLLLLLLLLLLLLLD",
        ".DMMMMMMMMMMMMMD",
        "DwWWWwDMMMMMMMMD",
        "DwWWwDDDDDDDDDD.",
        "DwwwD...........",
        ".DDD............",
    ],
    # ametralladora pesada: cuerpo grueso, tambor abajo, freno de boca
    "hmg": [
        "...DDDDDDDDDDDDD",
        "..DMLLMMMMMMMMLMD",
        ".DDMMMMMMMMMMMMMD",
        "DMMMDMMMMMMMMDLLD",
        "DMMMDDDDDDDDDDDD.",
        ".DMMD...........",
        ".DDDD...........",
    ],
}


def extend_palette(palette: np.ndarray):
    """Añade los colores de las armas a una paleta (sin duplicar). Devuelve (paleta, {letra: índice})."""
    pal = [tuple(int(v) for v in c) for c in palette]
    index = {}
    for key, color in COLORS.items():
        if color in pal:
            index[key] = pal.index(color)
        else:
            pal.append(color)
            index[key] = len(pal) - 1
    return np.array(pal, np.uint8), index


def sprite(name: str, index: dict):
    """Devuelve (mapa de índices, (gx, gy)) con el origen en la esquina inferior izquierda."""
    rows = GRIDS[name]
    w = max(len(r) for r in rows)
    idx = np.full((len(rows), w), -1, np.int16)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                idx[y, x] = index[ch]
    return idx, (0, len(rows) - 1)
