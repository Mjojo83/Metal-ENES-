"""cel: pixel art con aspecto dibujado a mano a partir de una referencia (foto o ilustración).

Lo que delata una conversión automática es el ruido: cientos de clústeres de 1-2 px, degradados
y texturas. Un sprite dibujado tiene pocos materiales, cada uno con tres tonos planos (sombra, medio,
luz), una línea oscura exterior, algunas líneas interiores donde se solapan partes, un brillo
puntual y uno o dos acentos (ojos, garras). Este módulo construye exactamente eso:

  1. reducción por área (premultiplicada) a la altura objetivo → imagen chica y suave
  2. materiales: k-means en OKLab (peso bajo en L) → etiquetas suavizadas por mayoría
  3. bandas: la luminosidad de cada material se corta en 3 tonos y se limpian islas
  4. paleta: tono por (material, banda) separados a propósito, contorno casi negro
  5. tinta interior: bordes fuertes de la referencia entre regiones distintas
  6. acentos: manchas pequeñas de color muy distinto al material (ojos) sobreviven
  7. brillo: 1 px en los bordes superiores de la banda clara
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

from pixelize import _kmeans, nearest_index, oklab_to_srgb, srgb_to_oklab

TRANSPARENT = -1
_CROSS = ndimage.generate_binary_structure(2, 1)
_SQUARE = ndimage.generate_binary_structure(2, 2)


def _majority(labels: np.ndarray, mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    """Filtro de mayoría 3×3 sobre etiquetas enteras, solo dentro de la máscara."""
    out = labels.copy()
    H, W = out.shape
    for _ in range(iterations):
        src = np.pad(out, 1, constant_values=-1)
        neigh = np.stack([src[dy:dy + H, dx:dx + W] for dy in range(3) for dx in range(3)])
        for y, x in zip(*np.nonzero(mask)):
            col = neigh[:, y, x]
            col = col[col >= 0]
            if len(col) == 0:
                continue
            counts = np.bincount(col)
            if counts.max() >= 5:
                out[y, x] = counts.argmax()
    return out


def _absorb_small(labels: np.ndarray, mask: np.ndarray, min_size: int) -> np.ndarray:
    """Las islas de una etiqueta con menos de min_size px pasan a la etiqueta vecina mayoritaria."""
    out = labels.copy()
    changed = True
    while changed:
        changed = False
        for lab in np.unique(out[mask]):
            comp, n = ndimage.label((out == lab) & mask, structure=_SQUARE)
            if n == 0:
                continue
            sizes = np.bincount(comp.ravel())
            for c in range(1, n + 1):
                if sizes[c] >= min_size:
                    continue
                region = comp == c
                ring = ndimage.binary_dilation(region, structure=_SQUARE) & ~region & mask
                neigh = out[ring]
                neigh = neigh[neigh != lab]
                if len(neigh):
                    out[region] = np.bincount(neigh).argmax()
                    changed = True
    return out


def downsample(rgba: np.ndarray, alpha: np.ndarray, height: int, margin: int = 1):
    """Reduce por área la zona de la criatura a `height` px de alto (sin contorno)."""
    import cv2
    ys, xs = np.nonzero(alpha > 0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb = rgba[y0:y1, x0:x1, :3].astype(np.float32)
    a = alpha[y0:y1, x0:x1].astype(np.float32)
    scale = (y1 - y0) / height
    W = max(1, int(round((x1 - x0) / scale)))
    pre = rgb * a[..., None]
    small_pre = cv2.resize(pre, (W, height), interpolation=cv2.INTER_AREA)
    small_a = cv2.resize(a, (W, height), interpolation=cv2.INTER_AREA)
    rgb_small = np.where(small_a[..., None] > 1e-3, small_pre / np.maximum(small_a[..., None], 1e-3), 0)
    mask = small_a >= 0.5
    # también una versión en gris de alta resolución para la tinta
    gray = cv2.cvtColor(np.ascontiguousarray(rgb.astype(np.uint8)), cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (0, 0), max(1.0, scale * 0.35)), 60, 140)
    edges = (edges > 0) & (a > 0.5)
    k = max(1, int(round(scale * 0.6)))
    if k > 1:
        edges = cv2.dilate(edges.astype(np.uint8), np.ones((k, k), np.uint8)) > 0
    edge_small = cv2.resize(edges.astype(np.float32), (W, height), interpolation=cv2.INTER_AREA)
    # margen transparente alrededor
    pad = margin + 1
    rgb_p = np.pad(rgb_small, ((pad, pad), (pad, pad), (0, 0)))
    mask_p = np.pad(mask, pad)
    edge_p = np.pad(edge_small, pad)
    return np.clip(rgb_p, 0, 255), mask_p, edge_p


def cel_shade(rgb: np.ndarray, mask: np.ndarray, edge: np.ndarray, n_materials: int = 3,
              bands: int = 3, band_sep: float = 0.07, ink_threshold: float = 0.35,
              accent_distance: float = 0.20, highlight: bool = True, min_region: int = 4,
              outline_color=(16, 12, 20), seed: int = 0, material_merge: float = 0.11,
              shadow_sep: float = 0.17, light_sep: float = 0.14, band_blur: float = 2.0,
              chroma_boost: float = 1.3, band_percentiles=(45, 82)):
    """Devuelve (índices, paleta uint8) con contorno exterior incluido."""
    H, W = mask.shape
    min_region = max(min_region, int(mask.sum() * 0.006))
    lab = srgb_to_oklab(rgb.reshape(-1, 3)).reshape(H, W, 3)
    # luz suavizada dentro de la silueta (normalizada por la máscara para no oscurecer bordes)
    m = mask.astype(np.float64)
    L_s = ndimage.gaussian_filter(lab[..., 0] * m, band_blur) / np.maximum(ndimage.gaussian_filter(m, band_blur), 1e-6)
    lab_shade = lab.copy()
    lab_shade[..., 0] = np.where(mask, L_s, lab[..., 0])
    # más croma: las referencias son apagadas, el pixel art es franco
    lab[..., 1:] *= chroma_boost
    pts = lab[mask]
    rng = np.random.default_rng(seed)
    # --- materiales: color (a, b) con poco peso en la luz
    feat = np.column_stack([pts[:, 0] * 0.6, pts[:, 1] * 1.4, pts[:, 2] * 1.4])
    k = min(n_materials, max(1, len(pts) // 12))
    centers, counts = _kmeans(feat, k, rng)
    # dos materiales que el ojo no distingue se funden (una criatura café es UN material)
    merged = True
    while merged and len(centers) > 1:
        merged = False
        d = np.sqrt(((centers[:, None] - centers[None]) ** 2).sum(-1))
        np.fill_diagonal(d, np.inf)
        i, j = np.unravel_index(d.argmin(), d.shape)
        if d[i, j] < material_merge:
            centers[i] = (centers[i] * counts[i] + centers[j] * counts[j]) / (counts[i] + counts[j])
            counts[i] += counts[j]
            centers, counts = np.delete(centers, j, 0), np.delete(counts, j)
            merged = True
    mat = np.full((H, W), -1, np.int16)
    mat[mask] = nearest_index(feat, centers)
    mat = _majority(mat, mask, 2)
    mat = _absorb_small(mat, mask, max(min_region * 3, int(mask.sum() * 0.02)))
    materials = np.unique(mat[mask])
    # --- acentos: pixeles muy lejos del centro de su material, en manchas chicas
    mat_lab_mean = {m: lab[mask & (mat == m)].mean(0) for m in materials}
    dist = np.zeros((H, W))
    for m in materials:
        sel = mask & (mat == m)
        dist[sel] = np.sqrt(((lab[sel] - mat_lab_mean[m]) ** 2).sum(1))
    accent_mask = mask & (dist > accent_distance)
    comp, n = ndimage.label(accent_mask, structure=_SQUARE)
    sizes = np.bincount(comp.ravel()) if n else np.array([0])
    keep = np.zeros_like(accent_mask)
    for c in range(1, n + 1):
        if 1 <= sizes[c] <= max(6, int(mask.sum() * 0.01)):
            keep |= comp == c
    accent_mask = keep
    # --- bandas de luz por material
    band = np.zeros((H, W), np.int16)
    palette = []          # lista de (r, g, b)
    index = np.full((H, W), TRANSPARENT, np.int16)
    for m in materials:
        sel = mask & (mat == m) & ~accent_mask
        if sel.sum() == 0:
            continue
        L = lab_shade[..., 0]
        lo, hi = np.percentile(L[sel], list(band_percentiles))
        if hi - lo < 0.03:          # material plano: una sola banda central
            b = np.full((H, W), 1, np.int16)
        else:
            b = np.where(L < lo, 0, np.where(L < hi, 1, 2)).astype(np.int16)
        b = np.where(sel, b, -1).astype(np.int16)
        b = _majority(b, sel, 2)
        b = _absorb_small(b, sel, min_region)
        band[sel] = b[sel]
        base = lab[sel].mean(0)
        offsets = (-shadow_sep, 0.0, light_sep)
        for bi in range(bands):
            tone = base.copy()
            tone[0] = np.clip(base[0] + offsets[bi], 0.10, 0.95)
            # sombra más saturada y un poco fría; luz menos saturada y cálida (como en los personajes)
            tone[1:] *= 1.25 if bi == 0 else (0.8 if bi == 2 else 1.0)
            if bi == 0:
                tone[2] -= 0.02
            elif bi == 2:
                tone[2] += 0.01
            palette.append(tuple(int(v) for v in oklab_to_srgb(tone[None, :])[0]))
            index[sel & (b == bi)] = len(palette) - 1
    # --- acentos: color medio de cada mancha (ojos oscuros/claros, garras)
    dark_acc = accent_mask & (lab[..., 0] < 0.45)
    light_acc = accent_mask & ~dark_acc
    if dark_acc.any():
        col = lab[dark_acc].mean(0)
        col[0] = 0.16
        palette.append(tuple(int(v) for v in oklab_to_srgb(col[None, :])[0]))
        index[dark_acc] = len(palette) - 1
    if light_acc.any():
        col = lab[light_acc].mean(0)
        col[0] = min(0.97, col[0] + 0.08)
        palette.append(tuple(int(v) for v in oklab_to_srgb(col[None, :])[0]))
        index[light_acc] = len(palette) - 1
    # --- tinta: contorno exterior + líneas interiores
    palette.append(tuple(outline_color))
    ink = len(palette) - 1
    opaque = index >= 0
    ring = ndimage.binary_dilation(opaque, structure=_CROSS) & ~opaque
    index[ring] = ink
    # interior: borde fuerte de la referencia y cambio de región (material o banda) con un vecino
    region_id = mat * 8 + np.maximum(band, 0)
    diff = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0)):
        a = region_id[:H - dy, :W - dx]
        b2 = region_id[dy:, dx:]
        d = (a != b2) & opaque[:H - dy, :W - dx] & opaque[dy:, dx:]
        diff[:H - dy, :W - dx] |= d
    interior_ink = opaque & (((edge > ink_threshold) & diff) | (edge > 0.9)) & ~accent_mask
    # sin manchas: solo pixeles de tinta con al menos otro vecino de tinta o del contorno
    cand = interior_ink | ring
    neigh = ndimage.convolve(cand.astype(int), np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]]), mode="constant")
    interior_ink &= neigh >= 1
    index[interior_ink] = ink
    # --- brillo: 1 px en el borde superior/izquierdo de la banda clara
    if highlight:
        light = np.zeros((H, W), bool)
        for m_i, m in enumerate(materials):
            light |= (mat == m) & (band == 2) & opaque & (index != ink)
        up = np.zeros_like(light)
        up[1:, :] = light[1:, :] & ~opaque[:-1, :]
        up[1:, :] |= light[1:, :] & (index[:-1, :] == ink)
        left = np.zeros_like(light)
        left[:, 1:] = light[:, 1:] & (index[:, :-1] == ink)
        hl = (up | left) & light
        comp_h, n_h = ndimage.label(hl, structure=_SQUARE)
        if n_h:
            sizes_h = np.bincount(comp_h.ravel())
            hl &= sizes_h[comp_h] >= 3
        if hl.any():
            # un solo color de brillo para todo el sprite (más claro y menos saturado que la luz)
            src = srgb_to_oklab(np.array([palette[i] for i in np.unique(index[hl])]))
            base = src.mean(0)
            base[0] = min(0.98, base[0] + 0.10)
            base[1:] *= 0.6
            palette.append(tuple(int(v) for v in oklab_to_srgb(base[None, :])[0]))
            index[hl] = len(palette) - 1
    # limpieza final: motas de 1-2 px que no sean tinta ni acento
    protect = (index == ink) | accent_mask
    opaque2 = index >= 0
    comp, n = ndimage.label(opaque2, structure=_SQUARE)
    for col_i in np.unique(index[opaque2 & ~protect]):
        cc, m2 = ndimage.label((index == col_i) & ~protect, structure=_SQUARE)
        sizes = np.bincount(cc.ravel())
        for c in range(1, m2 + 1):
            if sizes[c] > 2:
                continue
            region = cc == c
            ring2 = ndimage.binary_dilation(region, structure=_CROSS) & ~region & opaque2 & (index != ink)
            vals = index[ring2]
            if len(vals):
                index[region] = np.bincount(vals).argmax()
    # recorte
    ys, xs = np.nonzero(index >= 0)
    index = index[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return index, np.array(palette, np.uint8), ink


def cel_pixelize(rgba: np.ndarray, alpha: np.ndarray, height: int, n_materials: int = 3, **kw):
    """Devuelve (índices, paleta, índice_de_tinta)."""
    rgb, mask, edge = downsample(rgba, alpha, height)
    return cel_shade(rgb, mask, edge, n_materials=n_materials, **kw)
