"""puppet: animación por piezas sobre mapas de índices de paleta.

Todas las operaciones trabajan sobre un mapa de índices (H×W, int16, -1 = transparente) y
preservan el pixel: espejos, corrimientos por bandas, escalado por vecino más cercano, giros de
90° exactos y, para ángulos libres, un giro tipo RotSprite (EPX ×8 → giro → muestreo al centro).
Así los cuadros derivados conservan la paleta y el grosor de línea del cuadro original, que es lo
que hace que una animación generada se lea como pixel art dibujado a mano.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

TRANSPARENT = -1
_CROSS = ndimage.generate_binary_structure(2, 1)
_SQUARE = ndimage.generate_binary_structure(2, 2)


# --- utilidades ------------------------------------------------------------------------------

def empty(h: int, w: int) -> np.ndarray:
    return np.full((h, w), TRANSPARENT, np.int16)


def bbox(idx: np.ndarray):
    ys, xs = np.nonzero(idx >= 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def paste(dst: np.ndarray, src: np.ndarray, x: int, y: int, under: bool = False) -> np.ndarray:
    """Pega `src` sobre `dst` en (x, y); los transparentes de src no tapan. under=True pinta
    solo donde dst está vacío (para meter una pieza detrás de otra)."""
    out = dst.copy()
    H, W = out.shape
    h, w = src.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return out
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    d = out[y0:y1, x0:x1]
    m = s >= 0
    if under:
        m &= d < 0
    d[m] = s[m]
    return out


def crop(idx: np.ndarray):
    b = bbox(idx)
    if b is None:
        return idx[:0, :0], (0, 0)
    x0, y0, x1, y1 = b
    return idx[y0:y1, x0:x1].copy(), (x0, y0)


def region_mask(shape, rows=None, cols=None) -> np.ndarray:
    m = np.zeros(shape, bool)
    r0, r1 = (0, shape[0]) if rows is None else rows
    c0, c1 = (0, shape[1]) if cols is None else cols
    m[r0:r1, c0:c1] = True
    return m


def take(idx: np.ndarray, mask: np.ndarray):
    """Separa (pieza, resto). La pieza conserva el tamaño del lienzo."""
    piece = np.where(mask, idx, TRANSPARENT).astype(np.int16)
    rest = np.where(mask, TRANSPARENT, idx).astype(np.int16)
    return piece, rest


def shift(idx: np.ndarray, dx: int, dy: int) -> np.ndarray:
    out = empty(*idx.shape)
    return paste(out, idx, dx, dy)


def mirror_x(idx: np.ndarray, center_x2: int) -> np.ndarray:
    """Espejo horizontal alrededor de x = center_x2 / 2 (así el centro puede caer a medio pixel)."""
    H, W = idx.shape
    out = empty(H, W)
    xs = np.arange(W)
    src = center_x2 - xs
    ok = (src >= 0) & (src < W)
    out[:, xs[ok]] = idx[:, src[ok]]
    return out


def scale_nearest(idx: np.ndarray, sx: float, sy: float, anchor=(0.0, 1.0)) -> np.ndarray:
    """Escala por vecino más cercano manteniendo el tamaño del lienzo; anchor=(ax, ay) en 0..1
    dice qué punto del bbox se queda fijo (por defecto el centro abajo: los pies)."""
    b = bbox(idx)
    if b is None:
        return idx.copy()
    x0, y0, x1, y1 = b
    piece = idx[y0:y1, x0:x1]
    h, w = piece.shape
    nw, nh = max(1, round(w * sx)), max(1, round(h * sy))
    ys = np.minimum((np.arange(nh) + 0.5) / sy, h - 1).astype(int)
    xs = np.minimum((np.arange(nw) + 0.5) / sx, w - 1).astype(int)
    scaled = piece[ys][:, xs]
    ax, ay = anchor
    fx = x0 + ax * w - ax * nw
    fy = y0 + ay * h - ay * nh
    out = empty(*idx.shape)
    return paste(out, scaled, int(round(fx)), int(round(fy)))


def rot90(idx: np.ndarray, k: int, pivot) -> np.ndarray:
    """Giro exacto de k·90° (k>0 = antihorario en pantalla) alrededor de un pixel pivote,
    manteniendo el lienzo. Sin pérdida: solo reacomoda pixeles."""
    H, W = idx.shape
    px, py = pivot
    piece, (ox, oy) = crop(idx)
    if piece.size == 0:
        return idx.copy()
    k %= 4
    h, w = piece.shape
    # coordenadas relativas al pivote (centro del pixel pivote)
    rx, ry = ox - px, oy - py           # esquina superior izquierda de la pieza respecto al pivote
    rot = np.rot90(piece, k)            # np.rot90 gira antihorario en coordenadas de matriz
    # esquina de la pieza girada: giro antihorario en pantalla (y hacia abajo) de (x, y) es (y, -x)
    # (el +1 viene de girar alrededor del CENTRO del pixel pivote, no de su esquina)
    if k == 0:
        nx, ny = rx, ry
    elif k == 1:
        nx, ny = ry, -(rx + w) + 1
    elif k == 2:
        nx, ny = -(rx + w) + 1, -(ry + h) + 1
    else:
        nx, ny = -(ry + h) + 1, rx
    out = empty(H, W)
    return paste(out, rot, int(round(px + nx)), int(round(py + ny)))


# --- EPX / RotSprite ---------------------------------------------------------------------------

def epx(idx: np.ndarray) -> np.ndarray:
    """Scale2x/EPX sobre índices: ×2 suavizando diagonales sin inventar colores."""
    P = idx
    A = np.pad(P, ((1, 0), (0, 0)), constant_values=TRANSPARENT)[:-1]   # arriba
    D = np.pad(P, ((0, 1), (0, 0)), constant_values=TRANSPARENT)[1:]    # abajo
    C = np.pad(P, ((0, 0), (1, 0)), constant_values=TRANSPARENT)[:, :-1]  # izquierda
    B = np.pad(P, ((0, 0), (0, 1)), constant_values=TRANSPARENT)[:, 1:]   # derecha
    e1 = np.where((C == A) & (C != D) & (A != B), A, P)
    e2 = np.where((A == B) & (A != C) & (B != D), B, P)
    e3 = np.where((D == C) & (D != B) & (C != A), C, P)
    e4 = np.where((B == D) & (B != A) & (D != C), D, P)
    H, W = P.shape
    out = np.empty((H * 2, W * 2), np.int16)
    out[0::2, 0::2] = e1
    out[0::2, 1::2] = e2
    out[1::2, 0::2] = e3
    out[1::2, 1::2] = e4
    return out


def rotate_free(idx: np.ndarray, angle_deg: float, pivot, up: int = 3) -> np.ndarray:
    """Giro libre tipo RotSprite: EPX ×(2^up), giro por vecino más cercano y muestreo al centro de
    cada pixel del lienzo. angle_deg > 0 gira antihorario en pantalla."""
    if abs(angle_deg) < 1e-6:
        return idx.copy()
    if abs(angle_deg % 90) < 1e-6:
        return rot90(idx, int(round(angle_deg / 90)), pivot)
    H, W = idx.shape
    s = 2 ** up
    big = idx
    for _ in range(up):
        big = epx(big)
    th = math.radians(angle_deg)
    cos, sin = math.cos(th), math.sin(th)
    px, py = (pivot[0] + 0.5) * s, (pivot[1] + 0.5) * s
    # para cada pixel destino (centro), buscar el origen aplicando el giro inverso
    ys, xs = np.mgrid[0:H, 0:W]
    dx = (xs + 0.5) * s - px
    dy = (ys + 0.5) * s - py
    # giro antihorario en pantalla (y abajo): destino = R(-θ)·origen en coords de matriz
    sx = cos * dx - sin * dy + px
    sy = sin * dx + cos * dy + py
    # muestreo de 3×3 subpuntos para votar el color (evita que se pierdan líneas de 1 px)
    out = empty(H, W)
    votes = {}
    offs = [(-0.3, -0.3), (0.0, -0.3), (0.3, -0.3), (-0.3, 0), (0, 0), (0.3, 0), (-0.3, 0.3), (0, 0.3), (0.3, 0.3)]
    samples = []
    for ox, oy in offs:
        ix = np.floor(sx + ox * s).astype(int)
        iy = np.floor(sy + oy * s).astype(int)
        ok = (ix >= 0) & (ix < W * s) & (iy >= 0) & (iy < H * s)
        v = np.full((H, W), TRANSPARENT, np.int16)
        v[ok] = big[iy[ok], ix[ok]]
        samples.append(v)
    stack = np.stack(samples)                     # (9, H, W)
    opaque = (stack >= 0).sum(0)
    for y in range(H):
        for x in range(W):
            if opaque[y, x] < 5:
                continue
            col = stack[:, y, x]
            col = col[col >= 0]
            out[y, x] = np.bincount(col).argmax()
    return out


# --- acabado -----------------------------------------------------------------------------------

def seal_outline(idx: np.ndarray, outline: int, protect: np.ndarray | None = None) -> np.ndarray:
    """Cualquier pixel opaco que no sea contorno y toque transparencia (vecindad de 4) pasa a ser
    contorno. Repara las costuras que dejan los cortes y espejos sin engrosar la silueta."""
    out = idx.copy()
    opaque = out >= 0
    edge = opaque & ~ndimage.binary_erosion(opaque, structure=_CROSS, border_value=0)
    fix = edge & (out != outline)
    if protect is not None:
        fix &= ~protect
    out[fix] = outline
    return out


def remove_islands(idx: np.ndarray, min_size: int = 3) -> np.ndarray:
    out = idx.copy()
    opaque = out >= 0
    labels, n = ndimage.label(opaque, structure=_SQUARE)
    if n <= 1:
        return out
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    drop = sizes < min_size
    drop[sizes.argmax()] = False
    out[drop[labels]] = TRANSPARENT
    return out


def fill_pinholes(idx: np.ndarray) -> np.ndarray:
    """Rellena agujeros de 1 px totalmente rodeados con el color mayoritario de sus vecinos."""
    out = idx.copy()
    H, W = out.shape
    holes = out < 0
    labels, n = ndimage.label(holes, structure=_CROSS)
    if n == 0:
        return out
    edge = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])))
    sizes = np.bincount(labels.ravel())
    for lab in range(1, n + 1):
        if lab in edge or sizes[lab] > 2:
            continue
        for y, x in zip(*np.nonzero(labels == lab)):
            neigh = [out[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                     if 0 <= yy < H and 0 <= xx < W and out[yy, xx] >= 0]
            if neigh:
                out[y, x] = np.bincount(neigh).argmax()
    return out


def finish(idx: np.ndarray, outline: int, min_island: int = 3) -> np.ndarray:
    return seal_outline(fill_pinholes(remove_islands(idx, min_island)), outline)


# --- lienzo ------------------------------------------------------------------------------------

def to_canvas(idx: np.ndarray, cell, feet_y: int | None = None, center_x: float | None = None,
              pad_bottom: int = 1) -> np.ndarray:
    """Centra el sprite en un lienzo W×H con los pies (fila más baja opaca, o feet_y) apoyados en
    H - 1 - pad_bottom. center_x (en coordenadas del sprite) cae en el centro del lienzo; si no se
    da, se usa el centro del bbox."""
    W, H = cell
    b = bbox(idx)
    if b is None:
        return empty(H, W)
    x0, y0, x1, y1 = b
    fy = (y1 - 1) if feet_y is None else feet_y
    cx = (x0 + x1) / 2 if center_x is None else center_x
    ox = int(round(W / 2 - cx))
    oy = (H - 1 - pad_bottom) - fy
    return paste(empty(H, W), idx, ox, oy)


def to_rgba(idx: np.ndarray, palette: np.ndarray) -> np.ndarray:
    out = np.zeros(idx.shape + (4,), np.uint8)
    m = idx >= 0
    out[m, :3] = palette[idx[m]]
    out[m, 3] = 255
    return out
