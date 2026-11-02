#!/usr/bin/env python3
"""Maqueta 320×224 sin motor: fondo + tiles del nivel + sprites + HUD con la fuente bitmap.

Sirve para juzgar legibilidad, escala y silueta antes de abrir Godot (rol de producción, §5).
    python tools/mockup/compose_320.py --root . --out docs/mockups
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image

W, H = 320, 224


def load_font(root: Path):
    img = Image.open(root / "assets/fonts/pixel5x7.png").convert("RGBA")
    glyphs = {}
    for line in (root / "assets/fonts/pixel5x7.fnt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"char id=(\d+) x=(\d+) y=(\d+) width=(\d+) height=(\d+)", line)
        if m:
            i, x, y, w, h = map(int, m.groups())
            glyphs[chr(i)] = img.crop((x, y, x + w, y + h))
    return glyphs


def text(canvas, glyphs, s, x, y, tint=None):
    for ch in s:
        g = glyphs.get(ch) or glyphs.get(ch.upper())
        if g is None:
            x += 6
            continue
        if tint:
            g = g.copy()
            px = g.load()
            for yy in range(g.height):
                for xx in range(g.width):
                    r, gg, b, a = px[xx, yy]
                    if (r, gg, b) == (255, 255, 255):
                        px[xx, yy] = (*tint, a)
        canvas.alpha_composite(g, (x - 1, y - 1))
        x += 6


def frame_of(sheet_path: Path, cell_w: int, cell_h: int, index: int = 0):
    sheet = Image.open(sheet_path).convert("RGBA")
    return sheet.crop((index * cell_w, 0, (index + 1) * cell_w, cell_h))


def compose(root: Path, cam_x: int, cam_y: int, actors, hud: dict, glyphs) -> Image.Image:
    level = json.loads((root / "data/levels/deep_fall_01.json").read_text(encoding="utf-8"))
    tiles = Image.open(root / level["tileset"].replace("res://", "")).convert("RGBA")
    far = Image.open(root / "assets/backgrounds/cave_far.png").convert("RGBA")
    mid = Image.open(root / "assets/backgrounds/cave_mid.png").convert("RGBA")
    canvas = Image.new("RGBA", (W, H))
    # parallax
    fx = -int(cam_x * 0.1) % W
    for ox in (fx - W, fx):
        canvas.alpha_composite(far, (ox, 0))
    mx = -int(cam_x * 0.4) % W
    for ox in (mx - W, mx):
        canvas.alpha_composite(mid, (ox, -cam_y % 224 - 224))
        canvas.alpha_composite(mid, (ox, (-cam_y) % 224))
    # tiles
    rows = level["map"]
    ts = level["tile_size"]
    for ty, row in enumerate(rows):
        for tx, ch in enumerate(row):
            sx, sy = tx * ts - cam_x, ty * ts - cam_y
            if sx < -ts or sx > W or sy < -ts or sy > H:
                continue
            if ch == "#":
                above_air = ty == 0 or rows[ty - 1][tx] != "#"
                v = (3 + ((tx * 7 + ty * 3) % 2)) if above_air else [0, 1, 2, 6, 7][(tx * 5 + ty * 11) % 5]
            elif ch == "=":
                v = 5
            else:
                continue
            canvas.alpha_composite(tiles.crop((v * ts, 0, (v + 1) * ts, ts)), (sx, sy))
    # actores: (hoja, cell_w, cell_h, frame, x_pies, y_pies, flip)
    for sheet, cw, chh, idx, x, y, flip in actors:
        fr = frame_of(root / sheet, cw, chh, idx)
        if flip:
            fr = fr.transpose(Image.FLIP_LEFT_RIGHT)
        canvas.alpha_composite(fr, (x - cw // 2 - cam_x, y - chh + 1 - cam_y))
    # HUD
    text(canvas, glyphs, "×%d" % hud.get("lives", 3), 17, 6)
    canvas.alpha_composite(Image.open(root / "assets/sprites/ui/life.png").convert("RGBA"), (8, 6))
    text(canvas, glyphs, "CRED %d" % hud.get("credits", 3), 8, 16)
    text(canvas, glyphs, "%08d" % hud.get("score", 0), 160, 6)
    icon = Image.open(root / f"assets/sprites/ui/icon_{hud.get('weapon', 'pistol')}.png").convert("RGBA")
    canvas.alpha_composite(icon, (232, 6))
    ammo = hud.get("ammo")
    if ammo is None:
        canvas.alpha_composite(Image.open(root / "assets/sprites/ui/infinity.png").convert("RGBA"), (258, 7))
    else:
        text(canvas, glyphs, str(ammo), 258, 6)
    if hud.get("shout"):
        s = hud["shout"]
        text(canvas, glyphs, s, (W - len(s) * 6) // 2, 34, tint=(255, 230, 128))
    return canvas


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)
    root, out = Path(args.root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / ".gdignore").touch()
    glyphs = load_font(root)
    P = "assets/sprites/player"
    E = "assets/sprites/enemies"
    scenes = {
        "01_cretacico_gate1": (330, 0, [
            (f"{P}/mariana/run__pistol.png", 64, 64, 2, 400, 192, False),
            (f"{E}/velociraptor/move.png", 80, 48, 1, 560, 192, False),
            (f"{E}/velociraptor/move.png", 80, 48, 4, 610, 192, False),
            (f"{E}/nipponites/move.png", 48, 48, 0, 520, 120, False),
        ], {"lives": 3, "credits": 3, "score": 1200, "weapon": "pistol", "ammo": None, "shout": "¡OLEADA!"}),
        "02_carbonifero": (1380, 224, [
            (f"{P}/oscar/shoot__hmg.png", 64, 64, 0, 1440, 416, False),
            (f"{E}/eryops/move.png", 96, 48, 0, 1560, 416, False),
            (f"{E}/meganeura/move.png", 64, 48, 1, 1600, 330, False),
            (f"{E}/calamites/idle.png", 48, 96, 0, 1440, 416, False),
            (f"{E}/pulmonoscorpius/move.png", 48, 48, 2, 1510, 416, True),
            (f"{E}/arthropleura/move.png", 64, 32, 0, 1640, 416, False),
        ], {"lives": 2, "credits": 3, "score": 8450, "weapon": "hmg", "ammo": 143, "shout": "¡MATRACA!"}),
        "03_cambrico": (1940, 224, [
            (f"{P}/homi/aim_up__shotgun.png", 64, 64, 0, 2000, 416, False),
            (f"{E}/trilobites/move.png", 32, 32, 0, 2090, 416, False),
            (f"{E}/trilobites/move.png", 32, 32, 2, 2130, 416, False),
            (f"{E}/marrella/move.png", 48, 32, 1, 2160, 416, False),
            (f"{E}/hallucigenia/move.png", 32, 32, 0, 2190, 416, False),
            (f"{E}/anomalocaris/move.png", 64, 32, 1, 2080, 350, False),
            (f"{E}/megarachne/idle.png", 64, 48, 0, 2230, 416, False),
        ], {"lives": 3, "credits": 2, "score": 15320, "weapon": "shotgun", "ammo": 12, "shout": "¡ABANICO!"}),
        "04_jefe_trex": (2500, 224, [
            (f"{P}/mariana/shoot__hmg.png", 64, 64, 0, 2560, 416, False),
            (f"{E}/trex/telegraph.png", 128, 96, 1, 2700, 416, False),
            (f"{E}/velociraptor/move.png", 80, 48, 3, 2540, 416, True),
        ], {"lives": 1, "credits": 1, "score": 23100, "weapon": "hmg", "ammo": 61, "shout": "¡TR-001 SE ESCAPÓ DE LA LITOTECA!"}),
    }
    for name, (cx, cy, actors, hud) in scenes.items():
        img = compose(root, cx, cy, actors, hud, glyphs)
        img.save(out / f"{name}_1x.png")
        img.resize((W * 3, H * 3), Image.NEAREST).save(out / f"{name}_3x.png")
        print("maqueta", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
