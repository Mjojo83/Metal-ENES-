#!/usr/bin/env python3
"""make_players: genera los sprites de los tres personajes jugables a partir de las referencias.

Flujo por personaje:
  referencia (falso pixel art) → regrid (rejilla real, paleta corta) → piezas (cabeza, torso,
  antebrazo+arma, piernas) → cuadros por operaciones que preservan el pixel (puppet) → lienzo fijo
  64×64 con los pies en la misma línea → hojas PNG por animación + SpriteFrames (.tres) + vistas
  previas. Las tres armas (pistola, escopeta, ametralladora) se intercambian en la mano.

    python tools/pixel_lab/make_players.py --refs "enemigos y personajes/personajes" --out assets/sprites/player
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export  # noqa: E402
import puppet as P  # noqa: E402
import weapons  # noqa: E402
from pixelize import Palette, cleanup  # noqa: E402
from regrid import regrid  # noqa: E402

CELL = (64, 64)
PAD_BOTTOM = 1

# Esqueleto de cada personaje en coordenadas del sprite re-cuadriculado (mirando a la derecha).
#   legs: banda de piernas (filas, columnas), columna que separa pierna trasera/delantera,
#         centro del espejo (×2 para permitir medio pixel) y cuánto se cierran las piernas.
#   arm:  filas del brazo; el antebrazo con el arma empieza en elbow_x y gira sobre pivot.
#   gun:  caja que ocupa la pistola dibujada (se vacía al cambiar de arma) y ancla de la mano.
#   crouch_rows: filas que se comprimen al agacharse.
RIGS = {
    "homi": dict(
        file="homi.jpeg", period=14.0, display="Homi", carrera="Neurociencias",
        erase_boxes=[(0, 41, 42, 43), (8, 39, 21, 41), (0, 40, 2, 41), (29, 39, 32, 41)],
        erase_color_boxes=[(9, 34, 22, 39, (215, 179, 162), 40)],
        legs=dict(rows=(34, 41), cols=(2, 30), split_x=15, center_x2=31, close=(3, 6)),
        arm=dict(rows=(13, 24), elbow_x=22, pivot=(22, 19)),
        gun=dict(box=(30, 13, 42, 18), anchor=(29, 20), grip_box=(30, 18, 36, 23)), skin=[(188, 120, 99), (215, 179, 162)],
        crouch_rows=(23, 41), hip_row=34,
    ),
    "mariana": dict(
        file="Mariana.jpeg", period=14.0, display="Mariana", carrera="Órtesis y Prótesis",
        erase_boxes=[], erase_color_boxes=[],
        legs=dict(rows=(29, 43), cols=(0, 29), split_x=14, center_x2=28, close=(2, 5)),
        arm=dict(rows=(14, 24), elbow_x=22, pivot=(22, 20)),
        gun=dict(box=(28, 14, 41, 19), anchor=(29, 21), grip_box=(30, 19, 37, 24)), skin=[(125, 73, 47), (166, 104, 69)],
        crouch_rows=(26, 43), hip_row=29,
    ),
    "oscar": dict(
        file="Oscar.jpeg", period=13.0, display="Óscar", carrera="Ciencias de la Tierra",
        erase_boxes=[], erase_color_boxes=[],
        legs=dict(rows=(37, 47), cols=(4, 31), split_x=17, center_x2=34, close=(2, 5)),
        arm=dict(rows=(14, 27), elbow_x=23, pivot=(23, 19)),
        gun=dict(box=(30, 14, 40, 18), anchor=(29, 21), grip_box=(31, 18, 36, 24)), skin=[(175, 104, 79), (208, 139, 104), (241, 187, 151)],
        crouch_rows=(33, 47), hip_row=37,
    ),
}

WEAPONS = ("pistol", "shotgun", "hmg")


PAD = 52  # margen de trabajo alrededor del sprite para que girar o tender no recorte nada


def _pad_rig(rig: dict, pad: int) -> dict:
    """Traslada todas las coordenadas del esqueleto al lienzo de trabajo acolchado."""
    r = dict(rig)
    lg = dict(rig["legs"])
    lg["rows"] = (lg["rows"][0] + pad, lg["rows"][1] + pad)
    lg["cols"] = (lg["cols"][0] + pad, lg["cols"][1] + pad)
    lg["split_x"] += pad
    lg["center_x2"] += 2 * pad
    r["legs"] = lg
    a = dict(rig["arm"])
    a["rows"] = (a["rows"][0] + pad, a["rows"][1] + pad)
    a["elbow_x"] += pad
    a["pivot"] = (a["pivot"][0] + pad, a["pivot"][1] + pad)
    r["arm"] = a
    g = dict(rig["gun"])
    for key in ("box", "grip_box"):
        x0, y0, x1, y1 = g[key]
        g[key] = (x0 + pad, y0 + pad, x1 + pad, y1 + pad)
    g["anchor"] = (g["anchor"][0] + pad, g["anchor"][1] + pad)
    r["gun"] = g
    r["crouch_rows"] = (rig["crouch_rows"][0] + pad, rig["crouch_rows"][1] + pad)
    r["hip_row"] = rig["hip_row"] + pad
    return r


class Actor:
    def __init__(self, idx: np.ndarray, palette: np.ndarray, rig: dict):
        self.rig = _pad_rig(rig, PAD)
        # paleta del personaje + colores de armas compartidos
        self.palette, self.weapon_index = weapons.extend_palette(palette)
        self.outline = int(np.argmin(self.palette.astype(int).sum(1)))
        pal = self.palette.astype(int)
        self.skin_index = [int(np.argmin(((pal - np.array(c)) ** 2).sum(1))) for c in rig.get("skin", [])]
        self.base = np.pad(idx, PAD, constant_values=P.TRANSPARENT).astype(np.int16)
        self.h, self.w = self.base.shape
        self.feet_y = PAD + idx.shape[0] - 1
        b = P.bbox(idx)
        self.center_x = PAD + ((b[0] + b[2]) / 2 if b else idx.shape[1] / 2)

    # --- piezas --------------------------------------------------------------------------
    def with_weapon(self, weapon: str) -> np.ndarray:
        idx = self.base.copy()
        if weapon == "pistol":
            return idx
        g = self.rig["gun"]
        x0, y0, x1, y1 = g["box"]
        idx[y0:y1, x0:x1] = P.TRANSPARENT
        # en la empuñadura se borra lo que no sea piel (quedan los dedos, se va el resto de la pistola)
        x0, y0, x1, y1 = g["grip_box"]
        sub = idx[y0:y1, x0:x1]
        keep = np.isin(sub, self.skin_index) | (sub < 0)
        sub[~keep] = P.TRANSPARENT
        ax, ay = g["anchor"]
        sprite, (gx, gy) = weapons.sprite(weapon, self.weapon_index)
        return P.paste(idx, sprite, ax - gx, ay - gy)

    def split_arm(self, idx):
        a = self.rig["arm"]
        mask = P.region_mask(idx.shape, rows=a["rows"], cols=(a["elbow_x"], idx.shape[1]))
        return P.take(idx, mask)  # (antebrazo+arma, resto)

    def split_legs(self, idx):
        lg = self.rig["legs"]
        mask = P.region_mask(idx.shape, rows=lg["rows"], cols=lg["cols"])
        return P.take(idx, mask)

    # --- poses ---------------------------------------------------------------------------
    def legs_pose(self, idx, mirrored: bool, close: int, lift_back: bool):
        legs, rest = self.split_legs(idx)
        lg = self.rig["legs"]
        if mirrored:
            legs = P.mirror_x(legs, lg["center_x2"])
        if close:
            lmask = P.region_mask(idx.shape, rows=lg["rows"], cols=(0, lg["split_x"]))
            back, front = P.take(legs, lmask)
            back = P.shift(back, close, -1 if lift_back else 0)
            front = P.shift(front, -close, 0)
            legs = P.paste(back, front, 0, 0)
        return P.paste(rest, legs, 0, 0, under=True)

    def bob(self, idx, dy: int = -1):
        """Sube torso y cabeza dy px y estira la última fila del torso para no dejar hueco."""
        hip = self.rig["hip_row"]
        upper = P.region_mask(idx.shape, rows=(0, hip))
        top, rest = P.take(idx, upper)
        out = P.paste(rest, P.shift(top, 0, dy), 0, 0)
        for r in range(hip + dy, hip):
            row = idx[hip - 1]
            m = (row >= 0) & (out[r] < 0)
            out[r, m] = row[m]
        return out

    def arm_pose(self, idx, angle: float, recoil: int = 0):
        """Gira el antebrazo (con el arma) sobre el codo; recoil desplaza el arma hacia atrás a lo
        largo del cañón (1 px)."""
        fore, rest = self.split_arm(idx)
        a = self.rig["arm"]
        if recoil:
            fore = P.shift(fore, -recoil, 0)
        if angle:
            fore = P.rotate_free(fore, angle, a["pivot"])
        return P.paste(rest, fore, 0, 0)

    def crouch(self, idx, scale_y: float = 0.5):
        r0, r1 = self.rig["crouch_rows"]
        mask = P.region_mask(idx.shape, rows=(r0, r1))
        low, top = P.take(idx, mask)
        low_s = P.scale_nearest(low, 1.0, scale_y, anchor=(0.0, 1.0))
        b_old, b_new = P.bbox(low), P.bbox(low_s)
        drop = b_new[1] - b_old[1]      # cuánto bajó el borde superior de la parte comprimida
        top = P.shift(top, 0, drop)
        out = P.paste(low_s, top, 0, 0)
        return out

    # --- animaciones -------------------------------------------------------------------
    def animations(self, weapon: str) -> dict:
        base = self.with_weapon(weapon)
        lg = self.rig["legs"]
        k1, k2 = lg["close"]
        anims = {}
        anims["idle"] = (6.0, True, [base, base, self.bob(base, -1), self.bob(base, -1)])
        run = [
            self.legs_pose(base, False, 0, False),
            self.bob(self.legs_pose(base, False, k1, False), -1),
            self.bob(self.legs_pose(base, False, k2, True), -1),
            self.legs_pose(base, True, 0, False),
            self.bob(self.legs_pose(base, True, k1, False), -1),
            self.bob(self.legs_pose(base, True, k2, True), -1),
        ]
        anims["run"] = (12.0, True, run)
        anims["jump"] = (8.0, False, [P.shift(self.legs_pose(base, False, k2, True), 0, 0)])
        anims["fall"] = (8.0, False, [self.legs_pose(base, True, 0, False)])
        anims["shoot"] = (16.0, False, [self.arm_pose(base, 0, 1), base])
        anims["aim_up"] = (8.0, False, [self.arm_pose(base, 90)])
        anims["shoot_up"] = (16.0, False, [self.arm_pose(self.bob(base, 1), 90), self.arm_pose(base, 90)])
        anims["aim_diag_up"] = (8.0, False, [self.arm_pose(base, 45)])
        anims["aim_diag_down"] = (8.0, False, [self.arm_pose(base, -45)])
        anims["aim_down"] = (8.0, False, [self.arm_pose(base, -90)])
        crouch = self.crouch(base)
        anims["crouch"] = (8.0, False, [crouch])
        anims["crouch_shoot"] = (16.0, False, [self.arm_pose_crouch(base, 1), crouch])
        # muerte: cae de espaldas (gira antihorario sobre el talón trasero) y queda tendido
        heel = (lg["cols"][0] + 2, self.feet_y)
        die = [
            self.bob(base, -2),
            P.rotate_free(base, 25, heel),
            P.rotate_free(base, 55, heel),
            P.rot90(base, 1, heel),
            P.rot90(base, 1, heel),
        ]
        anims["die"] = (8.0, False, die)
        return anims

    def arm_pose_crouch(self, base, recoil):
        return self.crouch(self.arm_pose(base, 0, recoil))

    def frame(self, idx: np.ndarray, recenter: bool = False) -> np.ndarray:
        """Acabado + lienzo fijo con los pies en la misma línea y el torso centrado. recenter=True
        (muerte) centra el bbox en el lienzo para que el cuerpo tendido no se salga."""
        idx = P.finish(idx, self.outline)
        b = P.bbox(idx)
        cx = (b[0] + b[2]) / 2 if (recenter and b) else self.center_x
        fy = (b[3] - 1) if (recenter and b) else self.feet_y
        # la fila de apoyo es la del sprite base: así saltar o agacharse no mueve el ancla
        return P.to_canvas(idx, CELL, feet_y=fy, center_x=cx, pad_bottom=PAD_BOTTOM)


def write_actor(name: str, rig: dict, refs: Path, out: Path, preview_scale: int = 3):
    idx, palette, info = regrid(refs / rig["file"], rig["period"], erase_boxes=rig["erase_boxes"],
                                erase_color_boxes=rig["erase_color_boxes"])
    pal_obj = Palette(palette, [f"c{i:02d}" for i in range(len(palette))])
    idx = cleanup(idx, pal_obj, min_island=1, despeckle=rig.get("despeckle", 0.10))
    actor = Actor(idx, palette, rig)
    folder = out / name
    folder.mkdir(parents=True, exist_ok=True)
    pal = Palette(actor.palette, [f"c{i:02d}" for i in range(len(actor.palette))], actor.outline)
    pal.names[actor.outline] = "outline"
    export.write_gpl(folder / "palette.gpl", pal, name)
    Image.fromarray(P.to_rgba(idx, actor.palette), "RGBA").save(folder / "portrait.png")

    tres_anims = []
    previews = []
    for weapon in WEAPONS:
        for anim, (fps, loop, frames) in actor.animations(weapon).items():
            rgba = [P.to_rgba(actor.frame(f, recenter=(anim == "die")), actor.palette) for f in frames]
            sheet = folder / f"{anim}__{weapon}.png"
            export.write_sheet(sheet, rgba)
            tres_anims.append({"name": f"{anim}__{weapon}", "res": None, "path": sheet,
                               "frames": len(rgba), "cell": CELL, "fps": fps, "loop": loop})
            if weapon == "pistol" or anim in ("idle", "shoot", "aim_up"):
                previews.append((f"{anim}__{weapon}", rgba))
    godot_root = export.find_godot_root(folder)
    for a in tres_anims:
        a["res"] = export.res_path(a["path"], godot_root) if godot_root else a["path"].name
    export.write_tres(folder / "sprite_frames.tres", tres_anims)

    prev = folder / "_preview"
    prev.mkdir(exist_ok=True)
    (prev / ".gdignore").touch()
    for anim, rgba in previews:
        export.write_gif(prev / f"{anim}.gif", rgba, 8.0, preview_scale)
    write_contact(prev / "contact.png", previews, preview_scale)
    print(f"{name}: sprite {idx.shape[1]}×{idx.shape[0]} px, rejilla {info['period'][0]:.2f} px, "
          f"paleta {len(actor.palette)} colores, {len(tres_anims)} animaciones → {folder}")
    return actor


def write_contact(path: Path, previews, scale: int):
    W, H = CELL
    rows = []
    for name, frames in previews:
        row = Image.new("RGB", (len(frames) * (W + 2) * scale, (H + 10) * scale), (38, 38, 50))
        for i, fr in enumerate(frames):
            im = Image.fromarray(fr, "RGBA").resize((W * scale, H * scale), Image.NEAREST)
            row.paste(im, (i * (W + 2) * scale, 8 * scale), im)
        rows.append((name, row))
    total_h = sum(r.height for _, r in rows)
    max_w = max(r.width for _, r in rows)
    sheet = Image.new("RGB", (max_w, total_h), (38, 38, 50))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    y = 0
    for name, row in rows:
        sheet.paste(row, (0, y))
        d.text((2, y + 2), name, fill=(230, 230, 230))
        y += row.height
    sheet.save(path)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--refs", required=True, help="carpeta con homi.jpeg, Mariana.jpeg, Oscar.jpeg")
    p.add_argument("--out", required=True, help="carpeta assets/sprites/player del proyecto")
    p.add_argument("--only", nargs="*", choices=sorted(RIGS), help="solo estos personajes")
    args = p.parse_args(argv)
    for name, rig in RIGS.items():
        if args.only and name not in args.only:
            continue
        write_actor(name, rig, Path(args.refs), Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
