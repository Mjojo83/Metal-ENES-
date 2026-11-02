"""photo2pixel: de ilustración o foto de referencia a sprite de pixel art con aspecto dibujado.

Pasos: recorte → mate (rembg, color del borde o color fijo) → niveles automáticos sobre la
criatura → suavizado por desplazamiento de medias (zonas planas, como celdas de color) → pixelizado
de pixel_lab (rejilla real, paleta OKLab compartida, modo por bloque) → aplanado por mayoría 3×3
(mata el moteado que delata un filtro) → limpieza → contorno. Devuelve índices + paleta.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage

from pixelize import (Palette, SourceFrame, add_outline, cleanup, fit_palette, nearest_index,
                      oklab_to_srgb, pixelize_frame, placements, remove_background,
                      scale_for_height, srgb_to_oklab)

TRANSPARENT = -1
_session = None


def _rembg_session():
    global _session
    if _session is None:
        from rembg import new_session
        _session = new_session("isnet-general-use")
    return _session


def load_reference(path, crop=None, matte: str = "rembg", bg_tol: float = 40.0, flip: bool = False,
                   rotate: int = 0):
    """Devuelve (rgba uint8, alfa float 0..1). crop en fracciones (x0, y0, x1, y1); rotate en
    grados antihorarios (90 para acostar una criatura dibujada de pie en una tabla de tamaños)."""
    im = Image.open(path).convert("RGBA")
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    if rotate:
        im = im.rotate(rotate, expand=True, fillcolor=(255, 255, 255, 255))
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if matte == "rembg":
        from rembg import remove
        out = remove(im.convert("RGB"), session=_rembg_session())
        rgba = np.array(out)
        alpha = rgba[..., 3].astype(np.float32) / 255.0
    elif matte == "black":
        rgba = np.array(im)
        alpha = remove_background(rgba, (0, 0, 0), bg_tol)
    else:  # "border": el color del borde es el fondo
        rgba = np.array(im)
        alpha = remove_background(rgba, "auto", bg_tol)
    alpha = (alpha >= 0.5).astype(np.float32)
    # quitar motas del mate: nos quedamos con los componentes grandes
    labels, n = ndimage.label(alpha > 0)
    if n > 1:
        sizes = np.bincount(labels.ravel())
        sizes[0] = 0
        keep = sizes >= max(32, 0.02 * sizes.max())
        alpha = np.where(keep[labels], alpha, 0.0).astype(np.float32)
    return rgba, alpha


def auto_levels(rgba: np.ndarray, alpha: np.ndarray, lo: float = 0.22, hi: float = 0.88,
                strength: float = 1.0) -> np.ndarray:
    """Estira la luminosidad (OKLab L) de la criatura al rango [lo, hi] para que referencias
    oscuras o lavadas tengan las mismas tres bandas de sombra que las demás."""
    m = alpha > 0
    if m.sum() < 16 or strength <= 0:
        return rgba
    lab = srgb_to_oklab(rgba[..., :3].reshape(-1, 3)).reshape(rgba.shape[:2] + (3,))
    L = lab[..., 0]
    p2, p98 = np.percentile(L[m], [2, 98])
    if p98 - p2 < 1e-3:
        return rgba
    newL = lo + (L - p2) / (p98 - p2) * (hi - lo)
    lab[..., 0] = np.clip(L * (1 - strength) + newL * strength, 0, 1)
    out = rgba.copy()
    out[..., :3] = oklab_to_srgb(lab.reshape(-1, 3)).reshape(rgba.shape[:2] + (3,))
    return out


def smooth(rgba: np.ndarray, sp: int = 12, sr: int = 28) -> np.ndarray:
    """Desplazamiento de medias: convierte texturas y degradados en zonas planas."""
    try:
        import cv2
    except ImportError:
        return rgba
    rgb = np.ascontiguousarray(rgba[..., :3])
    out = rgba.copy()
    out[..., :3] = cv2.pyrMeanShiftFiltering(rgb, sp, sr)
    return out


def flatten(idx: np.ndarray, iterations: int = 1, keep: np.ndarray | None = None) -> np.ndarray:
    """Filtro de mayoría 3×3 sobre los índices (sin tocar la silueta): cada pixel toma el color
    más frecuente de su vecindad opaca si el suyo aparece 2 veces o menos. Quita el moteado y deja
    clústeres de color como los de un sprite dibujado a mano. `keep` protege pixeles (ojos, acentos)."""
    out = idx.copy()
    H, W = out.shape
    for _ in range(iterations):
        src = np.pad(out, 1, constant_values=TRANSPARENT)
        neigh = np.stack([src[dy:dy + H, dx:dx + W] for dy in range(3) for dx in range(3)])  # (9,H,W)
        opaque = out >= 0
        for y, x in zip(*np.nonzero(opaque)):
            col = neigh[:, y, x]
            col = col[col >= 0]
            if len(col) < 5:
                continue
            counts = np.bincount(col)
            v = out[y, x]
            if counts[v] <= 2 and counts.max() >= 4:
                if keep is None or not keep[y, x]:
                    out[y, x] = counts.argmax()
    return out


def pixelize_photo(rgba: np.ndarray, alpha: np.ndarray, height: int, n_colors: int = 10,
                   levels: float = 1.0, smooth_sp: int = 12, flatten_iters: int = 1,
                   despeckle: float = 0.12, min_island: int = 3, margin: int = 2):
    """Sprite (índices, Palette) a `height` px de alto con contorno, ancho según la referencia."""
    work = auto_levels(rgba, alpha, strength=levels)
    if smooth_sp > 0:
        work = smooth(work, smooth_sp)
    f = SourceFrame("ref", work, alpha)
    scale = scale_for_height([f], height, True)
    erode = int(min(8, max(1, scale * 0.25)))
    pal = fit_palette([f], n_colors, outline=True, erode=erode)
    x0, y0, x1, y1 = f.bbox()
    W = int(np.ceil((x1 - x0) / scale)) + 2 * margin + 2
    H = height + 2
    pf = pixelize_frame(f, pal, placements([f], scale)[0], (W, H), True, "mode", 0.5)
    idx = cleanup(pf.index, pal, min_island, despeckle)
    if flatten_iters:
        idx = flatten(idx, flatten_iters)
    idx = add_outline(idx, pal.outline)
    # recorte al contenido
    ys, xs = np.nonzero(idx >= 0)
    idx = idx[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return idx, pal
