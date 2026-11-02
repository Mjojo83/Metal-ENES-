"""Núcleo del pixelizador.

Convierte imágenes grandes (render de Blender, salida de IA, boceto) en pixel art con rejilla real,
paleta corta, contorno y el origen en la planta de los pies. No toca archivos: recibe y devuelve
arreglos de numpy. La entrada/salida vive en pixel_lab.py, export.py y aseprite.py.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

TRANSPARENT = -1
_CROSS = ndimage.generate_binary_structure(2, 1)   # vecindad de 4
_SQUARE = ndimage.generate_binary_structure(2, 2)  # vecindad de 8


# --- Color: sRGB <-> OKLab (distancias perceptuales para paleta y limpieza) ---------------------

_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])
_M1_INV = np.linalg.inv(_M1)
_M2_INV = np.linalg.inv(_M2)


def srgb_to_oklab(rgb) -> np.ndarray:
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return np.cbrt(lin @ _M1.T) @ _M2.T


def oklab_to_srgb(lab) -> np.ndarray:
    lin = np.clip(((np.asarray(lab, dtype=np.float64) @ _M2_INV.T) ** 3) @ _M1_INV.T, 0.0, 1.0)
    c = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.clip(np.round(c * 255.0), 0, 255).astype(np.uint8)


def nearest_index(lab, palette_lab, chunk: int = 65536) -> np.ndarray:
    """Índice del color de paleta más cercano (en OKLab) para cada fila de `lab`."""
    lab = np.asarray(lab, dtype=np.float64).reshape(-1, 3)
    out = np.empty(len(lab), dtype=np.int16)
    for s in range(0, len(lab), chunk):
        d = ((lab[s:s + chunk, None, :] - palette_lab[None, :, :]) ** 2).sum(-1)
        out[s:s + chunk] = d.argmin(1)
    return out


@dataclass
class Palette:
    colors: np.ndarray          # (k, 3) uint8
    names: list
    outline: int | None = None  # índice del color de contorno, si lo hay

    @property
    def lab(self) -> np.ndarray:
        return srgb_to_oklab(self.colors)

    def darkest(self) -> int:
        return int(self.lab[:, 0].argmin())


# --- Fondo -----------------------------------------------------------------------------------

@dataclass
class SourceFrame:
    name: str
    rgba: np.ndarray    # (h, w, 4) uint8, tal como llegó
    alpha: np.ndarray   # cobertura 0..1 del personaje, ya sin fondo

    @property
    def opaque(self) -> np.ndarray:
        return self.alpha >= 0.5

    def bbox(self):
        """(x0, y0, x1, y1) del contenido, con x1/y1 exclusivos; None si está vacío."""
        ys, xs = np.nonzero(self.opaque)
        if len(xs) == 0:
            return None
        return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def has_transparency(rgba: np.ndarray) -> bool:
    return bool((rgba[..., 3] < 250).mean() > 0.01)


def remove_background(rgba: np.ndarray, bg="auto", tol: float = 40.0,
                      everywhere: bool = False) -> np.ndarray:
    """Cobertura (0..1) del personaje.

    bg="auto" usa el canal alfa si la imagen trae transparencia (render de Blender) y si no,
    toma el color del borde como fondo; bg="alpha" usa solo el alfa; o un color (r, g, b).
    El fondo se borra rellenando desde el borde, así que un color parecido *dentro* del personaje
    (ojos, una camisa blanca) sobrevive. everywhere=True lo borra en toda la imagen.
    """
    alpha = rgba[..., 3].astype(np.float32) / 255.0
    if bg == "alpha" or (bg == "auto" and has_transparency(rgba)):
        return alpha
    rgb = rgba[..., :3].astype(np.float32)
    if bg == "auto":
        border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
        color = np.median(border, axis=0)
    else:
        color = np.asarray(bg, dtype=np.float32)
    near = np.sqrt(((rgb - color) ** 2).sum(-1)) < tol
    if everywhere:
        background = near
    else:
        labels, _ = ndimage.label(near, structure=_CROSS)
        edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
        background = np.isin(labels, edge[edge > 0])
    return np.where(background, 0.0, alpha).astype(np.float32)


# --- Paleta ----------------------------------------------------------------------------------

def _kmeans(x: np.ndarray, k: int, rng, iters: int = 30) -> np.ndarray:
    n = len(x)
    k = min(k, n)
    # k-means++: también elige colores raros pero distintos (ojos, un acento), no solo los grandes
    centers = [x[rng.integers(n)]]
    d2 = ((x - centers[0]) ** 2).sum(1)
    for _ in range(1, k):
        if d2.sum() <= 0:
            break
        i = rng.choice(n, p=d2 / d2.sum())
        centers.append(x[i])
        d2 = np.minimum(d2, ((x - x[i]) ** 2).sum(1))
    c = np.array(centers)
    for _ in range(iters):
        labels = nearest_index(x, c)
        new = np.array([x[labels == j].mean(0) if (labels == j).any() else c[j]
                        for j in range(len(c))])
        if np.allclose(new, c, atol=1e-5):
            break
        c = new
    counts = np.bincount(nearest_index(x, c), minlength=len(c)).astype(np.float64)
    keep = counts > 0
    return c[keep], counts[keep]


def _merge_close(c: np.ndarray, counts: np.ndarray, min_dist: float):
    """Junta colores que el ojo no distingue (k-means parte una zona grande en dos tonos casi
    iguales cuando sobran colores, y eso a 48 px se ve como ruido)."""
    c, counts = c.copy(), counts.copy()
    while len(c) > 1:
        d = np.sqrt(((c[:, None] - c[None]) ** 2).sum(-1))
        np.fill_diagonal(d, np.inf)
        i, j = np.unravel_index(d.argmin(), d.shape)
        if d[i, j] >= min_dist:
            break
        c[i] = (c[i] * counts[i] + c[j] * counts[j]) / (counts[i] + counts[j])
        counts[i] += counts[j]
        c, counts = np.delete(c, j, 0), np.delete(counts, j)
    return c, counts


def _drop_blends(lab: np.ndarray, counts: np.ndarray, max_share: float = 0.02, tol: float = 0.04):
    """Quita colores escasos que son la mezcla de otros dos: el antialiasing entre dos zonas de
    color (pelo/piel, playera/brazo) deja tonos intermedios que no son parte del diseño. Un color
    escaso pero que *no* es mezcla (un ojo, un botón rojo) se queda."""
    rgb = oklab_to_srgb(lab).astype(np.float64) / 255.0
    share = counts / counts.sum()
    drop = []
    for k in np.argsort(share):
        if share[k] >= max_share:
            break
        others = [i for i in range(len(rgb)) if i != k and i not in drop]
        for a in others:
            for b in others:
                if a >= b:
                    continue
                ab = rgb[b] - rgb[a]
                t = float(np.dot(rgb[k] - rgb[a], ab) / max(np.dot(ab, ab), 1e-9))
                if 0.1 < t < 0.9 and np.linalg.norm(rgb[a] + t * ab - rgb[k]) < tol:
                    drop.append(k)
                    break
            if k in drop:
                break
    keep = np.setdiff1d(np.arange(len(lab)), drop)
    return lab[keep], counts[keep]


def _unique_rows(a: np.ndarray) -> np.ndarray:
    _, first = np.unique(a, axis=0, return_index=True)
    return a[np.sort(first)]


def outline_color_for(colors: np.ndarray) -> np.ndarray:
    """Contorno oscuro pero no negro: el color más oscuro, más oscuro todavía y algo desaturado."""
    lab = srgb_to_oklab(colors)
    dark = lab[lab[:, 0].argmin()].copy()
    dark[0] = min(dark[0] * 0.55, 0.22)
    dark[1:] *= 0.8
    return oklab_to_srgb(dark)


def fit_palette(frames, n_colors: int, outline: bool = True, erode: int = 1,
                seed: int = 0, max_samples: int = 40000, merge: float = 0.04) -> Palette:
    """Una sola paleta para TODOS los frames (si cada frame tuviera la suya, la animación
    parpadearía). Se ajusta en OKLab con el interior del personaje, sin el halo del borde.
    `n_colors` es un máximo: los tonos repetidos y las mezclas de antialiasing se descartan."""
    samples = []
    for f in frames:
        m = f.opaque
        inner = ndimage.binary_erosion(m, iterations=erode) if erode > 0 else m
        samples.append(f.rgba[..., :3][inner if inner.sum() >= 64 else m])
    px = np.concatenate(samples)
    if len(px) == 0:
        raise ValueError("no hay píxeles de personaje para sacar la paleta")
    rng = np.random.default_rng(seed)
    if len(px) > max_samples:
        px = px[rng.choice(len(px), max_samples, replace=False)]
    n_content = max(1, n_colors - (1 if outline else 0))
    centers, counts = _kmeans(srgb_to_oklab(px), n_content, rng)
    centers, counts = _merge_close(centers, counts, merge)
    centers, counts = _drop_blends(centers, counts)
    centers = centers[np.argsort(centers[:, 0])]  # de oscuro a claro
    colors = _unique_rows(oklab_to_srgb(centers))
    names = [f"c{i:02d}" for i in range(len(colors))]
    if not outline:
        return Palette(colors, names)
    line = outline_color_for(colors)
    return Palette(np.vstack([line[None, :], colors]), ["outline"] + names, outline=0)


# --- Colocación: escala y ancla --------------------------------------------------------------

@dataclass
class Placement:
    scale: float      # píxeles de la fuente por píxel del juego
    anchor_x: float   # x de la fuente que cae en el centro horizontal del lienzo
    ground_y: float   # y de la fuente donde está la planta de los pies


def scale_for_height(frames, height: int, outline: bool = True) -> float:
    """Escala para que el frame más alto mida `height` px, contorno incluido."""
    tallest = max(b[3] - b[1] for b in (f.bbox() for f in frames) if b)
    inner = height - (2 if outline else 0)
    if inner <= 0:
        raise ValueError(f"altura {height} demasiado chica")
    return tallest / inner


def placements(frames, scale: float, align: str = "feet", ground_y=None, anchor_x=None):
    """align="feet": cada frame se apoya en su píxel más bajo y se centra con el torso (la mitad
    de arriba se mueve menos que las piernas). Sirve para tiras de IA, donde el personaje se
    mueve un poco entre frames.
    align="source": todos los frames comparten el mismo origen de la imagen fuente. Sirve para
    renders de Blender con la cámara fija, donde la posición ya es la buena."""
    if align == "source":
        g = ground_y if ground_y is not None else max(f.bbox()[3] for f in frames)
        return [Placement(scale, anchor_x if anchor_x is not None else f.rgba.shape[1] / 2, g)
                for f in frames]
    out = []
    for f in frames:
        x0, y0, x1, y1 = f.bbox()
        top = f.opaque[y0:y0 + max(1, round((y1 - y0) * 0.6)), x0:x1]
        xs = np.nonzero(top)[1]
        ax = x0 + xs.mean() + 0.5 if len(xs) else (x0 + x1) / 2
        out.append(Placement(scale, anchor_x if anchor_x is not None else ax, y1))
    return out


# --- Pixelizado ------------------------------------------------------------------------------

@dataclass
class PixelFrame:
    index: np.ndarray       # (H, W) int16, -1 = transparente
    reference: np.ndarray   # (H, W, 4) uint8: la fuente promediada por celda (capa _ref_pose)
    source_box: tuple       # (x0, y0, x1, y1) de la fuente que cubre el lienzo
    overflow: list          # lados por los que el personaje no cabe en el lienzo


def pixelize_frame(frame: SourceFrame, palette: Palette, place: Placement, cell,
                   outline: bool = True, method: str = "mode",
                   coverage: float = 0.5) -> PixelFrame:
    """Muestrea el lienzo completo (W×H) directamente de la fuente. Cada píxel del juego es un
    bloque de scale×scale píxeles de la fuente: es opaco si el personaje cubre al menos
    `coverage` del bloque, y toma el color de paleta que más se repite en él ("mode") o el del
    promedio del bloque ("mean"). El renglón de abajo queda libre para el contorno."""
    W, H = cell
    pad = 1 if outline else 0
    s = place.scale
    h_src, w_src = frame.alpha.shape
    xs = place.anchor_x + (np.arange(W + 1) - W / 2) * s
    ys = place.ground_y + (np.arange(H + 1) - (H - pad)) * s
    xr, yr = np.round(xs).astype(int), np.round(ys).astype(int)
    xc, yc = np.clip(xr, 0, w_src), np.clip(yr, 0, h_src)

    # Solo se cuantiza la parte de la fuente que cubre el lienzo.
    X0, X1, Y0, Y1 = xc[0], xc[-1], yc[0], yc[-1]
    alpha = frame.alpha[Y0:Y1, X0:X1]
    rgb = frame.rgba[Y0:Y1, X0:X1, :3]
    opaque = alpha >= 0.5
    pal_lab = palette.lab
    src_idx = np.full(alpha.shape, TRANSPARENT, np.int16)
    if opaque.any():
        src_idx[opaque] = nearest_index(srgb_to_oklab(rgb[opaque]), pal_lab)

    index = np.full((H, W), TRANSPARENT, np.int16)
    ref = np.zeros((H, W, 4), np.uint8)
    for r in range(H):
        y0, y1 = yc[r] - Y0, yc[r + 1] - Y0
        ny = yr[r + 1] - yr[r]
        if y1 <= y0 or ny <= 0:
            continue
        for c in range(W):
            x0, x1 = xc[c] - X0, xc[c + 1] - X0
            nx = xr[c + 1] - xr[c]
            if x1 <= x0 or nx <= 0:
                continue
            a = alpha[y0:y1, x0:x1]
            total = float(a.sum())
            if total <= 0:
                continue
            cov = total / (ny * nx)  # lo que cae fuera de la imagen cuenta como transparente
            mean = (rgb[y0:y1, x0:x1] * a[..., None]).sum((0, 1)) / total
            ref[r, c, :3] = np.clip(np.round(mean), 0, 255)
            ref[r, c, 3] = min(255, round(cov * 255))
            if cov < coverage:
                continue
            if method == "mode":
                ids = src_idx[y0:y1, x0:x1]
                ids = ids[ids >= 0]
                if len(ids):
                    index[r, c] = np.bincount(ids).argmax()
            else:
                m = opaque[y0:y1, x0:x1]
                if m.any():
                    lab = srgb_to_oklab(rgb[y0:y1, x0:x1][m]).mean(0, keepdims=True)
                    index[r, c] = nearest_index(lab, pal_lab)[0]

    # ¿Cabe? El contenido tiene que dejar libre el margen del contorno.
    bx0, by0, bx1, by1 = frame.bbox()
    half = s / 2
    overflow = []
    if by0 < ys[pad] - half:
        overflow.append("arriba")
    if by1 > ys[H - pad] + half:
        overflow.append("abajo")
    if bx0 < xs[pad] - half:
        overflow.append("izquierda")
    if bx1 > xs[W - pad] + half:
        overflow.append("derecha")
    return PixelFrame(index, ref, (xs[0], ys[0], xs[-1], ys[-1]), overflow)


def cleanup(index: np.ndarray, palette: Palette, min_island: int = 3,
            despeckle: float = 0.12) -> np.ndarray:
    """Quita lo que delata una conversión automática:
    - islas sueltas de menos de `min_island` px (motas que dejó el fondo);
    - agujeritos de 1-2 px dentro del personaje (si no, el contorno los vuelve puntos negros);
    - píxeles solitarios rodeados por un mismo color *parecido* (ruido de sombreado). Si el
      color es muy distinto (un ojo, un botón) se respeta: el umbral es distancia OKLab."""
    idx = index.copy()
    H, W = idx.shape
    opaque = idx >= 0
    if min_island > 1 and opaque.any():
        labels, n = ndimage.label(opaque, structure=_SQUARE)
        if n > 1:
            sizes = np.bincount(labels.ravel())
            sizes[0] = 0
            drop = sizes < min_island
            drop[0] = False
            drop[sizes.argmax()] = False
            idx[drop[labels]] = TRANSPARENT

    holes, n = ndimage.label(idx < 0, structure=_CROSS)
    if n:
        edge = set(np.unique(np.concatenate([holes[0], holes[-1], holes[:, 0], holes[:, -1]])))
        sizes = np.bincount(holes.ravel())
        for lab in range(1, n + 1):
            if lab in edge or sizes[lab] > 2:
                continue
            for y, x in zip(*np.nonzero(holes == lab)):
                neigh = [idx[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                         if 0 <= yy < H and 0 <= xx < W and idx[yy, xx] >= 0]
                if neigh:
                    idx[y, x] = np.bincount(neigh).argmax()

    if despeckle > 0:
        lab = palette.lab
        src = idx.copy()
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                v = src[y, x]
                if v < 0:
                    continue
                n4 = (src[y - 1, x], src[y + 1, x], src[y, x - 1], src[y, x + 1])
                if n4[0] < 0 or n4[0] == v or any(k != n4[0] for k in n4):
                    continue
                if np.sqrt(((lab[v] - lab[n4[0]]) ** 2).sum()) < despeckle:
                    idx[y, x] = n4[0]
    return idx


def add_outline(index: np.ndarray, outline_index: int) -> np.ndarray:
    """Contorno de 1 px por fuera de la silueta, en vecindad de 4 (sin esquinas: se ve más
    limpio a esta resolución)."""
    idx = index.copy()
    opaque = idx >= 0
    ring = ndimage.binary_dilation(opaque, structure=_CROSS) & ~opaque
    idx[ring] = outline_index
    return idx


def to_rgba(index: np.ndarray, palette: Palette) -> np.ndarray:
    out = np.zeros(index.shape + (4,), np.uint8)
    m = index >= 0
    out[m, :3] = palette.colors[index[m]]
    out[m, 3] = 255
    return out
