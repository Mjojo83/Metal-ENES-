#!/usr/bin/env python3
"""make_props: piezas chicas dibujadas pixel a pixel + tiles, fondos, fuente bitmap y SFX.

Balas, fogonazos, chispas, humo de muerte, esporas, cajas de armas, iconos de HUD, retícula; el
tileset de cueva (16×16) y los fondos de parallax (320×224) se generan con ruido de valor sobre la
paleta del piso; la fuente 5×7 se exporta como BMFont (.fnt + .png) para que Godot la importe como
fuente de mapa de bits (paso 3.6: nada de TTF escalada a 320×224). Los efectos de sonido son
síntesis propia (sin derechos), 22 050 Hz mono.

    python tools/pixel_lab/make_props.py --root .
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import weapons  # noqa: E402

# ----------------------------------------------------------------------------------------------
# Rejillas a mano. Cada letra es un color de la tabla; '.' transparente.
# ----------------------------------------------------------------------------------------------
INK = {
    "k": (20, 16, 24), "w": (255, 250, 230), "y": (255, 214, 72), "o": (255, 140, 40), "r": (214, 60, 48),
    "g": (120, 200, 90), "G": (60, 120, 60), "b": (90, 170, 230), "B": (30, 70, 140), "p": (200, 120, 220),
    "s": (120, 120, 130), "S": (60, 60, 70), "t": (190, 190, 200), "W": (150, 96, 50), "d": (96, 58, 30),
    "e": (200, 200, 210), "f": (255, 240, 180), "m": (130, 110, 160), "n": (80, 64, 100),
}


def grid_to_rgba(rows, ink=INK):
    w = max(len(r) for r in rows)
    out = np.zeros((len(rows), w, 4), np.uint8)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                out[y, x, :3] = ink[ch]
                out[y, x, 3] = 255
    return out


def sheet(frames):
    return np.concatenate(frames, axis=1)


def save(path: Path, rgba):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(path)


VFX = {
    "bullet_pistol": [[
        ".yyyk.",
        "yffyyk",
        ".yyyk.",
    ]],
    "bullet_pellet": [[
        ".yk",
        "yfk",
        ".kk",
    ]],
    "bullet_hmg": [[
        ".oooyk.",
        "oyffyyk",
        ".oooyk.",
    ]],
    "spore": [[
        "..gg..",
        ".gGGg.",
        "gGffGg",
        "gGGGGg",
        ".gGGg.",
        "..gg..",
    ], [
        "..GG..",
        ".GggG.",
        "GgffgG",
        "GggggG",
        ".GggG.",
        "..GG..",
    ]],
    "muzzle_flash": [[
        "...yy...",
        "..yffy..",
        ".yfffyo.",
        "yffffyoo",
        ".yfffyo.",
        "..yffy..",
        "...yy...",
        "........",
    ], [
        "........",
        "...oy...",
        "..oyfy..",
        ".oyffyo.",
        "..oyfy..",
        "...oy...",
        "........",
        "........",
    ]],
    "hit_spark": [[
        "........",
        "...w....",
        "..wfw...",
        ".wfffw..",
        "..wfw...",
        "...w....",
        "........",
        "........",
    ], [
        "...w....",
        ".w...w..",
        "........",
        "w..f..w.",
        "........",
        ".w...w..",
        "...w....",
        "........",
    ], [
        "w.....w.",
        "........",
        "........",
        "........",
        "........",
        "........",
        "w.....w.",
        "........",
    ]],
}

# humo de muerte: círculos irregulares que crecen y se deshacen
def puff_frames():
    frames = []
    rng = np.random.default_rng(7)
    for i, (r, a) in enumerate([(5, 255), (8, 230), (10, 170), (11, 90)]):
        img = np.zeros((24, 24, 4), np.uint8)
        yy, xx = np.mgrid[0:24, 0:24]
        d = np.sqrt((xx - 11.5) ** 2 + (yy - 11.5) ** 2) + rng.normal(0, 0.8, (24, 24))
        core = d < r * 0.55
        mid = d < r
        img[mid, :3] = (180, 170, 160)
        img[core, :3] = (230, 225, 215)
        img[mid, 3] = 255
        ring = (d >= r) & (d < r + 1.2)
        img[ring, :3] = (90, 80, 90)
        img[ring, 3] = 255 if i < 2 else 0
        if i == 3:  # se deshace: agujeros
            holes = rng.random((24, 24)) < 0.45
            img[holes, 3] = 0
        frames.append(img)
    return frames


ICONS = {
    "icon_pistol": [
        "kkkkkkkk.",
        "kSsssssk.",
        "kkkSkkkk.",
        "..kSk....",
        "..kkk....",
    ],
    "life": [
        ".rr.rr.",
        "rffrrrr",
        "rrrrrrr",
        ".rrrrr.",
        "..rrr..",
        "...r...",
    ],
    "reticle": [
        "..w..",
        ".....",
        "w.k.w",
        ".....",
        "..w..",
    ],
    "infinity": [
        ".ww.ww.",
        "w..w..w",
        "w..w..w",
        ".ww.ww.",
    ],
}


def crate(weapon_name: str, index_colors):
    """Caja de munición de madera con el arma encima (pickup)."""
    rows = [
        "kkkkkkkkkkkkkkkkkk",
        "kWWWWWWWWWWWWWWWWk",
        "kWddWWWWWWWWWWddWk",
        "kWdWWWWWWWWWWWWdWk",
        "kWWWWWWWWWWWWWWWWk",
        "kWWWWWWWWWWWWWWWWk",
        "kWdWWWWWWWWWWWWdWk",
        "kWddWWWWWWWWWWddWk",
        "kWWWWWWWWWWWWWWWWk",
        "kkkkkkkkkkkkkkkkkk",
    ]
    box = grid_to_rgba(rows)
    pal, ix = weapons.extend_palette(np.zeros((0, 3), np.uint8))
    gun, _ = weapons.sprite(weapon_name, ix)
    gh, gw = gun.shape
    out = np.zeros((box.shape[0] + 4, max(box.shape[1], gw + 2), 4), np.uint8)
    out[4:, :box.shape[1]] = box
    ox = (out.shape[1] - gw) // 2
    for y in range(gh):
        for x in range(gw):
            v = gun[y, x]
            if v >= 0:
                out[1 + y, ox + x, :3] = pal[v]
                out[1 + y, ox + x, 3] = 255
    return out


# ----------------------------------------------------------------------------------------------
# Fuente 5×7 (fila 0 = acento, filas 1-6 letra). Las minúsculas usan la misma forma (versalitas).
# ----------------------------------------------------------------------------------------------
GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001"],
    "B": ["11110", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "11100", "10010", "10001", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "11011", "10001"],
    "X": ["10001", "01010", "00100", "00100", "01010", "10001"],
    "Y": ["10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000"],
    "8": ["01110", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "01110"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00100"],
    ",": ["00000", "00000", "00000", "00000", "00100", "01000"],
    ":": ["00000", "00100", "00000", "00000", "00100", "00000"],
    ";": ["00000", "00100", "00000", "00000", "00100", "01000"],
    "!": ["00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00010", "00100", "00000", "00100"],
    "¡": ["00100", "00000", "00100", "00100", "00100", "00100"],
    "¿": ["00100", "00000", "00100", "01000", "10001", "01110"],
    "-": ["00000", "00000", "11111", "00000", "00000", "00000"],
    "+": ["00000", "00100", "01110", "00100", "00000", "00000"],
    "=": ["00000", "11111", "00000", "11111", "00000", "00000"],
    "/": ["00001", "00010", "00100", "01000", "10000", "00000"],
    "(": ["00010", "00100", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00100", "01000"],
    "'": ["00100", "00100", "00000", "00000", "00000", "00000"],
    '"': ["01010", "01010", "00000", "00000", "00000", "00000"],
    "×": ["00000", "10001", "01010", "00100", "01010", "10001"],
    "∞": ["00000", "01010", "10101", "10101", "01010", "00000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "11111"],
    "%": ["11001", "11010", "00100", "01011", "10011", "00000"],
    "<": ["00010", "00100", "01000", "00100", "00010", "00000"],
    ">": ["01000", "00100", "00010", "00100", "01000", "00000"],
    "*": ["00000", "10101", "01110", "10101", "00000", "00000"],
    "#": ["01010", "11111", "01010", "01010", "11111", "01010"],
    "[": ["01100", "01000", "01000", "01000", "01000", "01100"],
    "]": ["00110", "00010", "00010", "00010", "00010", "00110"],
}
ACCENT = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N", "Ü": "U"}
ACCENT_ROW = {"Á": "00010", "É": "00010", "Í": "00010", "Ó": "00010", "Ú": "00010", "Ñ": "01010", "Ü": "01010"}


def build_font(out_dir: Path, name: str = "pixel5x7"):
    """Fuente bitmap blanca con contorno oscuro de 1 px (legible sobre cualquier fondo a 1x)."""
    chars = {}
    for ch, rows in GLYPHS.items():
        chars[ch] = ["00000"] + rows
        if ch.isalpha():
            chars[ch.lower()] = ["00000"] + rows
    for ch, base in ACCENT.items():
        chars[ch] = [ACCENT_ROW[ch]] + GLYPHS[base]
        chars[ch.lower()] = chars[ch]
    cell_w, cell_h = 7, 9  # 5×7 + contorno
    cols = 16
    rows_n = (len(chars) + cols - 1) // cols
    img = np.zeros((rows_n * cell_h, cols * cell_w, 4), np.uint8)
    entries = []
    for i, (ch, rows) in enumerate(sorted(chars.items(), key=lambda kv: ord(kv[0]))):
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_w if False else (i // cols) * cell_h
        glyph = np.zeros((cell_h, cell_w), bool)
        for y, row in enumerate(rows):
            for x, bit in enumerate(row):
                if bit == "1":
                    glyph[y + 1, x + 1] = True
        # contorno
        outline = np.zeros_like(glyph)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                outline |= np.roll(np.roll(glyph, dy, 0), dx, 1)
        outline &= ~glyph
        tile = img[cy:cy + cell_h, cx:cx + cell_w]
        tile[outline] = (20, 16, 24, 255)
        tile[glyph] = (255, 255, 255, 255)
        entries.append((ord(ch), cx, cy))
    png = out_dir / f"{name}.png"
    save(png, img)
    lines = [
        f'info face="{name}" size=8 bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=0 aa=1 padding=0,0,0,0 spacing=0,0 outline=0',
        f"common lineHeight=10 base=8 scaleW={img.shape[1]} scaleH={img.shape[0]} pages=1 packed=0 alphaChnl=0 redChnl=4 greenChnl=4 blueChnl=4",
        f'page id=0 file="{png.name}"',
        f"chars count={len(entries)}",
    ]
    for code, cx, cy in entries:
        lines.append(f"char id={code} x={cx} y={cy} width={cell_w} height={cell_h} xoffset=-1 yoffset=-1 xadvance=6 page=0 chnl=15")
    (out_dir / f"{name}.fnt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(entries)


# ----------------------------------------------------------------------------------------------
# Tiles y fondos de cueva
# ----------------------------------------------------------------------------------------------
def value_noise(h, w, scale, rng):
    gh, gw = h // scale + 2, w // scale + 2
    g = rng.random((gh, gw))
    ys, xs = np.mgrid[0:h, 0:w] / scale
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = ys - y0, xs - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


ROCK = [(38, 28, 30), (74, 52, 44), (110, 78, 58), (150, 110, 78), (196, 150, 104)]   # ocre/terracota (piso 1)


def rock_tile(rng, variant: int, top: bool = False, platform: bool = False):
    n = value_noise(16, 16, 5, rng) * 0.7 + value_noise(16, 16, 2, rng) * 0.3
    idx = np.clip((n * 3.2).astype(int), 0, 3)
    img = np.zeros((16, 16, 4), np.uint8)
    for i in range(4):
        img[idx == i, :3] = ROCK[i]
    img[..., 3] = 255
    # grietas
    for _ in range(2 + variant % 2):
        x, y = rng.integers(0, 16), rng.integers(0, 16)
        for _ in range(rng.integers(3, 7)):
            img[y % 16, x % 16, :3] = ROCK[0]
            x += rng.integers(-1, 2)
            y += 1
    if top:
        img[0, :, :3] = ROCK[4]
        img[1, :, :3] = ROCK[3]
        img[2, rng.random(16) < 0.5, :3] = ROCK[3]
    if platform:
        img[:] = 0
        img[0, :, :3] = ROCK[4]; img[0, :, 3] = 255
        img[1, :, :3] = ROCK[2]; img[1, :, 3] = 255
        img[2, :, :3] = ROCK[1]; img[2, :, 3] = 255
        img[3, 1:15, :3] = ROCK[0]; img[3, 1:15, 3] = 255
    return img


def build_tileset(path: Path):
    rng = np.random.default_rng(3)
    tiles = [
        rock_tile(rng, 0), rock_tile(rng, 1), rock_tile(rng, 2),            # 0-2 roca interior
        rock_tile(rng, 0, top=True), rock_tile(rng, 1, top=True),           # 3-4 roca con superficie
        rock_tile(rng, 0, platform=True),                                   # 5 plataforma atravesable
        rock_tile(rng, 3), rock_tile(rng, 4),                               # 6-7 variantes
    ]
    atlas = np.zeros((16, 16 * len(tiles), 4), np.uint8)
    for i, t in enumerate(tiles):
        atlas[:, i * 16:(i + 1) * 16] = t
    save(path, atlas)
    return len(tiles)


def build_backgrounds(folder: Path):
    rng = np.random.default_rng(11)
    W, H = 320, 224
    # lejano: degradado oscuro con pared de cueva (ruido) y vetas
    far = np.zeros((H, W, 4), np.uint8)
    n = value_noise(H, W, 40, rng) * 0.6 + value_noise(H, W, 12, rng) * 0.4
    depth = np.linspace(0.0, 1.0, H)[:, None]
    v = np.clip((n * 0.5 + depth * 0.5) * 3, 0, 2.99).astype(int)
    shades = [(22, 16, 22), (34, 24, 28), (48, 34, 34)]
    for i, c in enumerate(shades):
        far[v == i, :3] = c
    far[..., 3] = 255
    save(folder / "cave_far.png", far)
    # medio: estalactitas y columnas en silueta (transparente entre ellas)
    mid = np.zeros((H, W, 4), np.uint8)
    for x in range(0, W, 24):
        h = int(20 + rng.random() * 50)
        w = 6 + rng.integers(0, 10)
        for yy in range(h):
            half = max(1, int(w * (1 - yy / h) / 2))
            cx = x + 12
            mid[yy, max(0, cx - half):min(W, cx + half), :3] = (52, 38, 40)
            mid[yy, max(0, cx - half):min(W, cx + half), 3] = 255
    for x in range(0, W, 56):
        w = 10 + rng.integers(0, 8)
        mid[H - 90:, x:x + w, :3] = (46, 34, 36)
        mid[H - 90:, x:x + w, 3] = 255
    save(folder / "cave_mid.png", mid)
    # cercano: suelo rocoso oscuro de primer plano (franja inferior)
    near = np.zeros((48, W, 4), np.uint8)
    n2 = value_noise(48, W, 10, rng)
    top = (n2[0] * 10).astype(int)
    for x in range(W):
        near[8 + top[x]:, x, :3] = (26, 18, 22)
        near[8 + top[x]:, x, 3] = 255
    save(folder / "cave_near.png", near)


# ----------------------------------------------------------------------------------------------
# SFX sintetizados
# ----------------------------------------------------------------------------------------------
SR = 22050


def env(n, a=0.002, d=0.12):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1.0) * np.exp(-t / d)


def tone(freq, n, kind="square"):
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(np.full(n, freq) if np.isscalar(freq) else freq) / SR
    if kind == "square":
        return np.sign(np.sin(ph))
    if kind == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    return np.sin(ph)


def noise(n, rng):
    return rng.uniform(-1, 1, n)


def write_wav(path: Path, data: np.ndarray, gain: float = 0.6):
    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.clip(data * gain, -1, 1)
    pcm = (x * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def build_sfx(folder: Path):
    rng = np.random.default_rng(5)
    def N(sec):
        return int(SR * sec)
    n = N(0.18)
    write_wav(folder / "shot_pistol.wav", noise(n, rng) * env(n, 0.001, 0.03) + tone(np.linspace(900, 200, n), n, "saw") * env(n, 0.001, 0.05) * 0.5)
    n = N(0.45)
    write_wav(folder / "shot_shotgun.wav", noise(n, rng) * env(n, 0.001, 0.12) * 1.2 + tone(np.linspace(300, 60, n), n, "sine") * env(n, 0.002, 0.2) * 0.8, 0.7)
    n = N(0.09)
    write_wav(folder / "shot_hmg.wav", noise(n, rng) * env(n, 0.0005, 0.02) + tone(np.linspace(1400, 300, n), n, "square") * env(n, 0.0005, 0.03) * 0.4)
    n = N(0.12)
    write_wav(folder / "hit.wav", tone(np.linspace(600, 180, n), n, "square") * env(n, 0.001, 0.05) + noise(n, rng) * env(n, 0.001, 0.02) * 0.4)
    n = N(0.5)
    write_wav(folder / "enemy_die.wav", noise(n, rng) * env(n, 0.002, 0.18) * 0.8 + tone(np.linspace(220, 40, n), n, "saw") * env(n, 0.002, 0.25) * 0.6)
    n = N(0.22)
    write_wav(folder / "jump.wav", tone(np.linspace(300, 700, n), n, "square") * env(n, 0.002, 0.12) * 0.5)
    n = N(0.15)
    write_wav(folder / "land.wav", tone(np.linspace(160, 60, n), n, "sine") * env(n, 0.001, 0.08) + noise(n, rng) * env(n, 0.001, 0.03) * 0.5)
    n = N(0.5)
    arp = np.concatenate([tone(f, N(0.12), "square") * env(N(0.12), 0.002, 0.1) for f in (523, 659, 784, 1047)])
    write_wav(folder / "pickup.wav", arp[:n] if len(arp) >= n else np.pad(arp, (0, n - len(arp))), 0.5)
    n = N(1.0)
    seq = np.concatenate([tone(f, N(0.25), "square") * env(N(0.25), 0.002, 0.2) for f in (440, 349, 277, 196)])
    write_wav(folder / "player_die.wav", seq, 0.5)
    n = N(0.6)
    write_wav(folder / "gate_lock.wav", tone(np.linspace(110, 90, n), n, "saw") * env(n, 0.01, 0.4) * 0.7)
    n = N(0.7)
    write_wav(folder / "wave_clear.wav", np.concatenate([tone(f, N(0.14), "square") * env(N(0.14), 0.002, 0.12) for f in (392, 523, 659, 784, 1047)]), 0.5)
    n = N(0.35)
    write_wav(folder / "ui_move.wav", tone(880, n, "square") * env(n, 0.001, 0.05) * 0.4)
    write_wav(folder / "ui_confirm.wav", np.concatenate([tone(660, N(0.1), "square") * env(N(0.1), 0.001, 0.08), tone(990, N(0.2), "square") * env(N(0.2), 0.001, 0.15)]), 0.5)
    n = N(0.4)
    write_wav(folder / "tremor.wav", noise(n, rng) * env(n, 0.05, 0.3) * 0.5 + tone(np.linspace(55, 40, n), n, "sine") * env(n, 0.05, 0.3))
    n = N(0.3)
    write_wav(folder / "roar.wav", tone(np.linspace(140, 70, n), n, "saw") * env(n, 0.01, 0.2) + noise(n, rng) * env(n, 0.01, 0.15) * 0.6, 0.7)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", required=True, help="raíz del proyecto Godot (donde está project.godot)")
    args = p.parse_args(argv)
    root = Path(args.root)
    vfx = root / "assets/sprites/vfx"
    for name, frames in VFX.items():
        save(vfx / f"{name}.png", sheet([grid_to_rgba(f) for f in frames]))
    save(vfx / "puff.png", sheet(puff_frames()))
    ui = root / "assets/sprites/ui"
    for name, rows in ICONS.items():
        save(ui / f"{name}.png", grid_to_rgba(rows))
    pal, ix = weapons.extend_palette(np.zeros((0, 3), np.uint8))
    for w in ("shotgun", "hmg"):
        g, _ = weapons.sprite(w, ix)
        rgba = np.zeros(g.shape + (4,), np.uint8)
        m = g >= 0
        rgba[m, :3] = pal[g[m]]
        rgba[m, 3] = 255
        save(ui / f"icon_{w}.png", rgba)
        save(root / "assets/sprites/pickups" / f"crate_{w}.png", crate(w, ix))
    n_glyphs = build_font(root / "assets/fonts")
    n_tiles = build_tileset(root / "assets/tilesets/cave.png")
    build_backgrounds(root / "assets/backgrounds")
    build_sfx(root / "assets/audio/sfx")
    print(f"props: {len(VFX) + 1} vfx, {len(ICONS) + 2} iconos, 2 cajas, fuente de {n_glyphs} glifos, {n_tiles} tiles, 3 fondos, SFX")
    return 0


if __name__ == "__main__":
    sys.exit(main())
