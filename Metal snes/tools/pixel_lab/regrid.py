"""regrid: recupera la rejilla real de una imagen de "falso pixel art" (IA, JPEG).

Las imágenes de los personajes vienen a 1200×896 con bloques de ~13-14 px por pixel, bordes
borrosos de JPEG y una rejilla que no es exactamente uniforme. Aquí se detecta el periodo y la fase
de la rejilla por el gradiente, se toma la mediana del interior de cada celda, se quita el fondo por
inundación desde el borde y se reduce la paleta en OKLab. El resultado es el sprite a su
resolución nativa (unos 43-47 px de alto) con una paleta corta: un pixel de la imagen es un pixel
del juego.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage

from pixelize import _kmeans, _merge_close, nearest_index, oklab_to_srgb, srgb_to_oklab

TRANSPARENT = -1


def detect_period(signal: np.ndarray, p0: float, span: float = 0.6):
    """Periodo y fase que maximizan la energía del gradiente sobre las líneas de la rejilla."""
    sig = signal - signal.mean()
    n = len(sig)
    best = (p0, 0.0, -np.inf)
    for p in np.arange(p0 - span, p0 + span, 0.01):
        k = np.arange(int(n / p) + 1)
        for phi in np.arange(0, p, 0.25):
            pos = np.round(phi + k * p).astype(int)
            pos = pos[(pos >= 0) & (pos < n)]
            s = sig[pos].sum()
            if s > best[2]:
                best = (p, phi, s)
    return best[0], best[1]


def _boundaries(phase: float, period: float, length: int) -> np.ndarray:
    b = np.round(phase + 1 + np.arange(-1, int(length / period) + 2) * period).astype(int)
    b = b[(b >= 0) & (b <= length)]
    if b[0] > 0:
        b = np.concatenate([[0], b])
    if b[-1] < length:
        b = np.concatenate([b, [length]])
    return np.unique(b)


def regrid(path, period_hint: float = 14.0, n_colors: int = 16, merge: float = 0.05,
           bg_tol: float = 38.0, erase_boxes=(), erase_color_boxes=()):
    """Devuelve (índices H×W, paleta K×3 uint8, info). erase_boxes: rectángulos (x0, y0, x1, y1)
    en coordenadas del sprite recortado que se vacían (sombras del suelo, restos de fondo).
    erase_color_boxes: (x0, y0, x1, y1, (r, g, b), tol) vacía solo los pixeles parecidos a ese color."""
    im = np.array(Image.open(path).convert("RGB")).astype(np.float32)
    h, w = im.shape[:2]
    gx = np.abs(np.diff(im, axis=1)).sum(-1).sum(0)
    gy = np.abs(np.diff(im, axis=0)).sum(-1).sum(1)
    px, phx = detect_period(gx, period_hint)
    py, phy = detect_period(gy, period_hint)
    xb, yb = _boundaries(phx, px, w), _boundaries(phy, py, h)
    cols, rows = len(xb) - 1, len(yb) - 1
    cells = np.zeros((rows, cols, 3), np.float32)
    for r in range(rows):
        y0, y1 = yb[r], yb[r + 1]
        my = max(1, (y1 - y0) // 4)
        for c in range(cols):
            x0, x1 = xb[c], xb[c + 1]
            mx = max(1, (x1 - x0) // 4)
            block = im[y0 + my:max(y0 + my + 1, y1 - my), x0 + mx:max(x0 + mx + 1, x1 - mx)]
            cells[r, c] = np.median(block.reshape(-1, 3), axis=0)
    border = np.concatenate([cells[0], cells[-1], cells[:, 0], cells[:, -1]])
    bg = np.median(border, axis=0)
    near = np.sqrt(((cells - bg) ** 2).sum(-1)) < bg_tol
    labels, _ = ndimage.label(near)
    edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    fg = ~np.isin(labels, edge[edge > 0])
    ys, xs = np.nonzero(fg)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    cells, fg = cells[y0:y1, x0:x1], fg[y0:y1, x0:x1]
    for (bx0, by0, bx1, by1) in erase_boxes:
        fg[by0:by1, bx0:bx1] = False
    for (bx0, by0, bx1, by1, color, tol) in erase_color_boxes:
        sub = cells[by0:by1, bx0:bx1]
        hit = np.sqrt(((sub - np.asarray(color, np.float32)) ** 2).sum(-1)) < tol
        fg[by0:by1, bx0:bx1] &= ~hit
    # recorte final al bbox y paleta
    ys, xs = np.nonzero(fg)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    cells, fg = cells[y0:y1, x0:x1], fg[y0:y1, x0:x1]
    rng = np.random.default_rng(0)
    lab = srgb_to_oklab(cells[fg])
    centers, counts = _kmeans(lab, n_colors, rng)
    centers, counts = _merge_close(centers, counts, merge)
    centers = centers[np.argsort(centers[:, 0])]
    idx = np.full(fg.shape, TRANSPARENT, np.int16)
    idx[fg] = nearest_index(lab, centers)
    palette = oklab_to_srgb(centers)
    info = {"period": (float(px), float(py)), "phase": (float(phx), float(phy)),
            "grid": (cols, rows), "bg": bg.astype(int).tolist()}
    return idx, palette, info
