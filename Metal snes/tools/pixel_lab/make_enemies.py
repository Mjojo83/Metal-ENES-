#!/usr/bin/env python3
"""make_enemies: criaturas del DEEP FALL a partir de las referencias de `enemigos y personajes/dino`.

Por criatura: referencia → mate → pixel art (photo2pixel) → esqueleto automático según el tipo
(bípedo, cuadrúpedo, reptante, volador, flotante, planta) → cuadros con puppet → lienzo fijo con
los pies en la misma línea → hojas PNG + SpriteFrames + datos para Godot. Todas miran a la IZQUIERDA
(vienen por la derecha); Godot espeja con flip_h cuando van a la derecha.

    python tools/pixel_lab/make_enemies.py --refs "enemigos y personajes/dino" --out assets/sprites/enemies
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export  # noqa: E402
import puppet as P  # noqa: E402
from cel import cel_pixelize  # noqa: E402
from photo2pixel import auto_levels, load_reference, smooth  # noqa: E402
from pixelize import Palette  # noqa: E402

# era, archivo, recorte (fracciones), mate, espejo (True si la referencia mira a la derecha),
# alto en px, colores, tipo de esqueleto, perfil de IA sugerido por los docs, vida, velocidad, puntos.
CREATURES = {
    # --- Cretácico (tramo 1) ---
    "velociraptor": dict(era="cretacico", materials=3, file="cretacico/Velociraptor/images (6).jfif", crop=(0, 0, 0.70, 1),
                         matte="rembg", flip=False, height=34, colors=10, rig="biped", levels=1.0,
                         ai="advancer", health=3, speed=70, score=200, damage=1, hurt=(22, 24)),
    "trex": dict(era="cretacico", materials=3, file="cretacico/T-Rex/brave_g24vDjBPQn.jpg", crop=None,
                 matte="rembg", flip=False, height=88, colors=11, rig="biped", levels=0.8, flatten=2,
                 ai="boss", health=60, speed=30, score=5000, damage=1, hurt=(60, 70)),
    "quetzalcoatlus": dict(era="cretacico", materials=3, file="cretacico/Quetzalcoatlus/brave_2ceCKOy6Pv.png", crop=None,
                           matte="border", flip=False, height=78, colors=10, rig="quad", levels=0.6, flatten=2,
                           ai="jumper", health=6, speed=50, score=600, damage=1, hurt=(28, 56)),
    "nipponites": dict(era="cretacico", materials=2, file="cretacico/Nipponites/Nipponites.webp", crop=(0, 0, 1, 0.9),
                       matte="border", flip=True, height=36, colors=10, rig="floater", levels=0.9,
                       ai="flier", health=2, speed=35, score=150, damage=1, hurt=(22, 22)),
    # --- Carbonífero (tramo 2) ---
    "arthropleura": dict(era="carbonifero", materials=2, file="Carbonífero/Arthropleura/images (6).jfif", crop=(0.0, 0.0, 0.56, 0.86),
                         matte="border", flip=False, rotate=90, height=22, colors=9, rig="crawler", levels=1.0,
                         ai="advancer", health=8, speed=25, score=400, damage=1, hurt=(16, 48)),
    "calamites": dict(era="carbonifero", materials=2, file="Carbonífero/Calamites/images (6)ll.jfif", crop=(0.0, 0.0, 0.5, 0.92),
                      matte="rembg", flip=False, height=90, colors=8, rig="plant", levels=0.6,
                      ai="static", health=4, speed=0, score=100, damage=1, hurt=(12, 80)),
    "eryops": dict(era="carbonifero", materials=3, file="Carbonífero/Eryops/Eryops-Carboniferous-Period.webp", crop=(0, 0, 0.78, 1),
                   matte="rembg", flip=False, height=30, colors=10, rig="quad", levels=0.7,
                   ai="advancer", health=5, speed=40, score=300, damage=1, hurt=(40, 22)),
    "meganeura": dict(era="carbonifero", materials=3, file="Carbonífero/Meganeura/d.jfif", crop=(0.3, 0.1, 1, 1),
                      matte="border", flip=True, height=40, colors=9, rig="flier", levels=0.4,
                      ai="flier", health=2, speed=90, score=250, damage=1, hurt=(24, 14)),
    "megarachne": dict(era="carbonifero", materials=2, file="Carbonífero/Megarachne/Megarachne-01.jpg", crop=None,
                       matte="rembg", flip=True, height=34, colors=9, rig="quad", levels=0.9,
                       ai="ambush", health=4, speed=60, score=350, damage=1, hurt=(40, 24)),
    "pulmonoscorpius": dict(era="carbonifero", materials=2, file="Carbonífero/Pulmonoscorpius/images (6)k.jfif", crop=None,
                            matte="rembg", flip=False, height=40, colors=10, rig="quad", levels=0.9,
                            ai="advancer", health=6, speed=35, score=450, damage=1, hurt=(36, 30)),
    # --- Cámbrico (tramo 3) ---
    "anomalocaris": dict(era="cambrico", materials=2, file="Cámbrico/Anomalocaris/20191203_Anomalocaris_canadensis.png", crop=None,
                         matte="border", flip=False, height=24, colors=9, rig="floater", levels=0.9,
                         ai="flier", health=3, speed=55, score=300, damage=1, hurt=(36, 16)),
    "hallucigenia": dict(era="cambrico", materials=2, file="Cámbrico/Hallucigenia/claude_I0tUs3AttT.png", crop=(0.34, 0.02, 0.66, 0.86),
                         matte="black", flip=False, height=26, colors=8, rig="crawler", levels=0.9,
                         ai="jumper", health=2, speed=45, score=150, damage=1, hurt=(20, 20)),
    "marrella": dict(era="cambrico", materials=3, file="Cámbrico/Marrella/Marrella.png", crop=None,
                     matte="border", flip=False, height=22, colors=9, rig="crawler", levels=0.9,
                     ai="advancer", health=2, speed=80, score=120, damage=1, hurt=(22, 16)),
    "trilobites": dict(era="cambrico", materials=2, file="Cámbrico/Trilobites/Olenoides_serratus_3d.jpg", crop=None,
                       matte="border", flip=False, height=20, colors=8, rig="crawler", levels=1.0,
                       ai="advancer", health=4, speed=30, score=100, damage=1, hurt=(26, 12)),
}

PAD = 24


def canvas_for(idx: np.ndarray):
    """Lienzo fijo por actor: múltiplo de 16 con margen para los cuadros girados/estirados."""
    h, w = idx.shape
    W = int(np.ceil((w + 8) / 16) * 16)
    H = int(np.ceil((h + 6) / 16) * 16)
    return (W, H)


# --- esqueletos automáticos ----------------------------------------------------------------

def leg_band(idx: np.ndarray):
    """Detecta la banda de piernas: filas inferiores donde la silueta se parte en ≥2 trozos."""
    H, W = idx.shape
    opaque = idx >= 0
    rows = np.nonzero(opaque.any(1))[0]
    y0, y1 = rows.min(), rows.max()
    widths = opaque.sum(1)
    body_w = np.percentile(widths[y0:y1 + 1], 85)
    hip = y1
    for r in range(y1, y0, -1):
        from scipy import ndimage
        n = ndimage.label(opaque[r])[1]
        if n >= 2 and widths[r] < body_w * 0.8:
            hip = r
        else:
            if y1 - r > 2:
                break
    hip = max(hip, y0 + int((y1 - y0) * 0.55))
    xs = np.nonzero(opaque[hip:y1 + 1].any(0))[0]
    cols = (int(xs.min()), int(xs.max()) + 1)
    # columna de separación: el hueco más grande en la fila de los pies
    foot = opaque[y1 - 1] | opaque[y1]
    gaps, start = [], None
    for x in range(cols[0], cols[1]):
        if not foot[x] and start is None:
            start = x
        if foot[x] and start is not None:
            gaps.append((x - start, start, x))
            start = None
    split = (cols[0] + cols[1]) // 2
    if gaps:
        g = max(gaps)
        split = (g[1] + g[2]) // 2
    return dict(rows=(int(hip), int(y1) + 1), cols=cols, split_x=int(split), center_x2=cols[0] + cols[1] - 1)


class Creature:
    def __init__(self, name: str, cfg: dict, idx: np.ndarray, palette):
        self.name, self.cfg = name, cfg
        self.base = np.pad(idx, PAD, constant_values=P.TRANSPARENT).astype(np.int16)
        self.palette = palette.colors
        self.outline = palette.outline if palette.outline is not None else 0
        b = P.bbox(self.base)
        self.feet_y = b[3] - 1
        self.center_x = (b[0] + b[2]) / 2
        self.cell = canvas_for(idx)
        self.legs = leg_band(self.base) if cfg["rig"] in ("biped", "quad") else None

    # --- piezas -------------------------------------------------------------------------
    def legs_pose(self, idx, mirrored: bool, close: int, lift: bool):
        lg = self.legs
        mask = P.region_mask(idx.shape, rows=lg["rows"], cols=lg["cols"])
        legs, rest = P.take(idx, mask)
        if mirrored:
            legs = P.mirror_x(legs, lg["center_x2"])
        if close:
            lmask = P.region_mask(idx.shape, rows=lg["rows"], cols=(0, lg["split_x"]))
            back, front = P.take(legs, lmask)
            back = P.shift(back, close, -1 if lift else 0)
            front = P.shift(front, -close, 0)
            legs = P.paste(back, front, 0, 0)
        return P.paste(rest, legs, 0, 0, under=True)

    def bob(self, idx, dy: int):
        hip = self.legs["rows"][0] if self.legs else self.feet_y
        top, rest = P.take(idx, P.region_mask(idx.shape, rows=(0, hip)))
        out = P.paste(rest, P.shift(top, 0, dy), 0, 0)
        if dy < 0:
            for r in range(hip + dy, hip):
                row = idx[hip - 1]
                m = (row >= 0) & (out[r] < 0)
                out[r, m] = row[m]
        return out

    def wave(self, idx, amp: float, wavelength: float, phase: float, rows=None):
        """Ondulación vertical por columnas (reptantes, tentáculos)."""
        H, W = idx.shape
        out = P.empty(H, W)
        r0, r1 = (0, H) if rows is None else rows
        static = idx.copy()
        static[r0:r1] = P.TRANSPARENT
        band = P.empty(H, W)
        band[r0:r1] = idx[r0:r1]
        for x in range(W):
            dy = int(round(amp * np.sin(2 * np.pi * x / wavelength + phase)))
            col = band[:, x]
            if dy == 0:
                out[:, x] = col
            elif dy > 0:
                out[dy:, x] = col[:-dy]
            else:
                out[:dy, x] = col[-dy:]
        return P.paste(static, out, 0, 0, under=False)

    def shear(self, idx, px_top: int):
        """Inclinación: las filas de arriba se corren px_top, las de abajo nada (plantas)."""
        H, W = idx.shape
        b = P.bbox(idx)
        out = P.empty(H, W)
        for r in range(H):
            t = (b[3] - 1 - r) / max(1, (b[3] - 1 - b[1]))
            dx = int(round(px_top * t))
            row = idx[r]
            if dx > 0:
                out[r, dx:] = row[:-dx]
            elif dx < 0:
                out[r, :dx] = row[-dx:]
            else:
                out[r] = row
        return out

    def squash(self, idx, sy: float):
        return P.scale_nearest(idx, 1.0, sy, anchor=(0.5, 1.0))

    def head_dip(self, idx, angle: float):
        """Cabeza/frente (tercio izquierdo, mitad superior) gira hacia abajo para morder."""
        b = P.bbox(idx)
        w = b[2] - b[0]
        h = b[3] - b[1]
        mask = P.region_mask(idx.shape, rows=(b[1], b[1] + int(h * 0.55)), cols=(b[0], b[0] + int(w * 0.42)))
        head, rest = P.take(idx, mask)
        pivot = (b[0] + int(w * 0.42), b[1] + int(h * 0.45))
        head = P.rotate_free(head, angle, pivot)
        return P.paste(rest, head, 0, 0)

    # --- animaciones --------------------------------------------------------------------
    def animations(self) -> dict:
        base = self.base
        rig = self.cfg["rig"]
        a = {}
        if rig in ("biped", "quad"):
            lg = self.legs
            gap = max(2, (lg["cols"][1] - lg["cols"][0]) // 8)
            k1, k2 = max(1, gap // 2), gap
            a["idle"] = (4.0, True, [base, self.bob(base, -1)])
            a["move"] = (10.0, True, [
                self.legs_pose(base, False, 0, False),
                self.bob(self.legs_pose(base, False, k1, False), -1),
                self.bob(self.legs_pose(base, False, k2, True), -1),
                self.legs_pose(base, True, 0, False),
                self.bob(self.legs_pose(base, True, k1, False), -1),
                self.bob(self.legs_pose(base, True, k2, True), -1),
            ])
            bite = self.head_dip(base, -18)
            a["attack"] = (8.0, False, [self.bob(base, -2), bite, bite, base])
            a["telegraph"] = (6.0, False, [self.bob(base, -1), self.bob(base, -2)])
        elif rig == "crawler":
            b = P.bbox(base)
            lam = max(8.0, (b[2] - b[0]) / 1.5)
            a["idle"] = (6.0, True, [base, self.wave(base, 1, lam, 0.0)])
            a["move"] = (10.0, True, [self.wave(base, 1, lam, ph) for ph in (0, 1.57, 3.14, 4.71)])
            a["attack"] = (8.0, False, [self.bob(base, -2), P.shift(base, -2, 0), base])
            a["telegraph"] = (6.0, False, [self.squash(base, 0.85), self.squash(base, 0.75)])
        elif rig == "flier":
            b = P.bbox(base)
            body_row = b[1] + int((b[3] - b[1]) * 0.55)
            wings, body = P.take(base, P.region_mask(base.shape, rows=(0, body_row)))
            mid = P.paste(body, P.scale_nearest(wings, 1.0, 0.5, anchor=(0.5, 1.0)), 0, 0)
            down_w = P.empty(*base.shape)
            # alas abajo: espejo vertical de las alas alrededor de la línea del cuerpo
            for r in range(b[1], body_row):
                nr = 2 * body_row - r - 1
                if 0 <= nr < base.shape[0]:
                    row = wings[r]
                    m = row >= 0
                    down_w[nr, m] = row[m]
            down = P.paste(down_w, body, 0, 0)
            a["idle"] = (10.0, True, [base, mid, down, mid])
            a["move"] = (12.0, True, [base, mid, down, mid])
            a["attack"] = (10.0, False, [P.shift(mid, -2, 1), P.shift(down, -3, 2), mid])
            a["telegraph"] = (8.0, False, [P.shift(base, 0, -2), P.shift(base, 0, -3)])
        elif rig == "floater":
            b = P.bbox(base)
            lam = max(8.0, (b[2] - b[0]) / 1.2)
            a["idle"] = (6.0, True, [base, P.shift(self.wave(base, 1, lam, 1.0), 0, -1),
                                      self.wave(base, 1, lam, 2.0), P.shift(self.wave(base, 1, lam, 3.0), 0, 1)])
            a["move"] = a["idle"]
            a["attack"] = (8.0, False, [P.shift(base, -2, 0), P.shift(base, -4, 0), base])
            a["telegraph"] = (6.0, False, [self.squash(base, 0.9), self.squash(base, 0.8)])
        else:  # plant
            a["idle"] = (4.0, True, [self.shear(base, -1), base, self.shear(base, 1), base])
            a["move"] = a["idle"]
            a["attack"] = (8.0, False, [self.shear(base, -3), self.shear(base, 3), self.shear(base, -1), base])
            a["telegraph"] = (6.0, False, [self.shear(base, 2), self.shear(base, -2)])
        a["die"] = (10.0, False, [self.bob(base, -2) if self.legs else P.shift(base, 0, -2),
                                   self.squash(base, 0.7), self.squash(base, 0.45), self.squash(base, 0.3)])
        return a

    def frame(self, idx: np.ndarray) -> np.ndarray:
        idx = P.finish(idx, self.outline)
        return P.to_canvas(idx, self.cell, feet_y=self.feet_y, center_x=self.center_x, pad_bottom=1)


def write_creature(name: str, cfg: dict, refs: Path, out: Path, preview_scale: int = 3):
    rgba, alpha = load_reference(refs / cfg["file"], cfg.get("crop"), cfg["matte"], flip=cfg.get("flip", False),
                                 rotate=cfg.get("rotate", 0))
    # estilo cel (como los personajes): materiales planos, 3 tonos, tinta negra, acentos
    work = auto_levels(rgba, alpha, lo=0.25, hi=0.90, strength=cfg.get("levels", 0.9))
    work = smooth(work, cfg.get("smooth", 12), 28)
    idx, colors, ink = cel_pixelize(work, alpha, cfg["height"], n_materials=cfg.get("materials", 3),
                                    **cfg.get("cel", {}))
    names = [f"c{i:02d}" for i in range(len(colors))]
    names[ink] = "outline"
    pal = Palette(colors, names, outline=ink)
    c = Creature(name, cfg, idx, pal)
    folder = out / name
    folder.mkdir(parents=True, exist_ok=True)
    export.write_gpl(folder / "palette.gpl", pal, name)
    Image.fromarray(P.to_rgba(idx, pal.colors), "RGBA").save(folder / "base.png")
    anims = c.animations()
    tres = []
    previews = []
    for anim, (fps, loop, frames) in anims.items():
        rgba_frames = [P.to_rgba(c.frame(f), pal.colors) for f in frames]
        sheet = folder / f"{anim}.png"
        export.write_sheet(sheet, rgba_frames)
        tres.append({"name": anim, "path": sheet, "frames": len(rgba_frames), "cell": c.cell, "fps": fps, "loop": loop})
        previews.append((anim, rgba_frames))
    root = export.find_godot_root(folder)
    for t in tres:
        t["res"] = export.res_path(t["path"], root) if root else t["path"].name
    export.write_tres(folder / "sprite_frames.tres", tres)
    W, H = c.cell
    data = {
        "id": name, "era": cfg["era"], "display_name": name.capitalize(), "ai_profile": cfg["ai"],
        "health": cfg["health"], "speed": cfg["speed"], "score": cfg["score"], "damage": cfg["damage"],
        "cell": [W, H], "sprite_size": [int(idx.shape[1]), int(idx.shape[0])],
        "hurtbox": list(cfg["hurt"]), "sprite_frames": (export.res_path(folder / "sprite_frames.tres", root) if root else None),
    }
    (folder / "enemy.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    prev = folder / "_preview"
    prev.mkdir(exist_ok=True)
    (prev / ".gdignore").touch()
    for anim, fr in previews:
        export.write_gif(prev / f"{anim}.gif", fr, anims[anim][0], preview_scale)
    print(f"{name}: {idx.shape[1]}×{idx.shape[0]} px, lienzo {W}×{H}, {len(pal.colors)} colores, "
          f"{sum(len(f) for _, _, f in anims.values())} cuadros")
    return c, previews


def write_contact(path: Path, items, scale: int = 2):
    tiles = []
    for name, cell, frames in items:
        W, H = cell
        n = len(frames)
        tile = Image.new("RGB", (n * (W + 2) * scale, (H + 10) * scale), (44, 48, 64))
        for i, fr in enumerate(frames):
            im = Image.fromarray(fr, "RGBA").resize((W * scale, H * scale), Image.NEAREST)
            tile.paste(im, (i * (W + 2) * scale, 8 * scale), im)
        ImageDraw.Draw(tile).text((2, 2), name, fill=(240, 240, 240))
        tiles.append(tile)
    sheet = Image.new("RGB", (max(t.width for t in tiles), sum(t.height for t in tiles)), (44, 48, 64))
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height
    sheet.save(path)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--refs", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--only", nargs="*", choices=sorted(CREATURES))
    p.add_argument("--contact", help="PNG de vista general (move de cada criatura)")
    args = p.parse_args(argv)
    items = []
    for name, cfg in CREATURES.items():
        if args.only and name not in args.only:
            continue
        c, previews = write_creature(name, cfg, Path(args.refs), Path(args.out))
        frames = dict(previews)
        items.append((name, c.cell, frames["move"] + frames["attack"][:2] + frames["die"][-1:]))
    if args.contact and items:
        write_contact(Path(args.contact), items)
    return 0


if __name__ == "__main__":
    sys.exit(main())
