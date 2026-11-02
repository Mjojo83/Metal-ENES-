"""Salidas del pixelizador: hoja PNG, paleta .gpl, vistas previas y SpriteFrames de Godot."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image

from pixelize import Palette

PREVIEW_BG = (38, 38, 50)


# --- Paletas ---------------------------------------------------------------------------------

def read_palette(path) -> Palette:
    """Lee .gpl (GIMP/Aseprite), .hex (Lospec), .txt (Paint.NET) o una imagen (sus colores
    opacos, en orden de aparición). Si un color se llama "outline", ese es el del contorno."""
    path = Path(path)
    ext = path.suffix.lower()
    colors, names = [], []
    if ext in (".png", ".gif", ".bmp", ".webp"):
        rgba = np.array(Image.open(path).convert("RGBA")).reshape(-1, 4)
        opaque = rgba[rgba[:, 3] > 0][:, :3]
        if len(opaque):
            _, first = np.unique(opaque, axis=0, return_index=True)
            colors = [tuple(int(v) for v in c) for c in opaque[np.sort(first)]]
            names = [f"c{i:02d}" for i in range(len(colors))]
    else:
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = raw.split()
            if ext == ".gpl":
                if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
                    colors.append(tuple(int(p) for p in parts[:3]))
                    names.append(" ".join(parts[3:]) or f"c{len(names):02d}")
            elif parts and re.fullmatch(r"#?([0-9a-fA-F]{2})?[0-9a-fA-F]{6}", parts[0]):
                h = parts[0].lstrip("#")[-6:]  # Paint.NET usa AARRGGBB
                colors.append(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
                names.append(f"c{len(names):02d}")
    if not colors:
        raise ValueError(f"la paleta {path} no tiene colores")
    if len(colors) > 256:
        raise ValueError(f"la paleta {path} tiene {len(colors)} colores (máximo 256)")
    outline = next((i for i, n in enumerate(names) if n.strip().lower() == "outline"), None)
    return Palette(np.array(colors, np.uint8), names, outline)


def write_gpl(path, palette: Palette, title: str) -> None:
    lines = ["GIMP Palette", f"Name: {title}", "Columns: 8",
             '# pixel_lab: paleta compartida del actor. "outline" = color del contorno.']
    for (r, g, b), name in zip(palette.colors.tolist(), palette.names):
        lines.append(f"{r:3d} {g:3d} {b:3d}\t{name}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- Imágenes --------------------------------------------------------------------------------

def write_sheet(path, frames) -> None:
    """Tira horizontal, un frame por celda, sin recortes (el ancla no se mueve)."""
    Image.fromarray(np.concatenate(frames, axis=1), "RGBA").save(path)


def _on_bg(rgba: np.ndarray) -> Image.Image:
    im = Image.new("RGB", (rgba.shape[1], rgba.shape[0]), PREVIEW_BG)
    src = Image.fromarray(rgba, "RGBA")
    im.paste(src, (0, 0), src)
    return im


def write_gif(path, frames, fps: float, scale: int) -> None:
    imgs = [_on_bg(f).resize((f.shape[1] * scale, f.shape[0] * scale), Image.NEAREST)
            for f in frames]
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=round(1000 / fps),
                 loop=0, disposal=2)


def write_compare(path, sources, boxes, frames, scale: int, max_frames: int = 8) -> None:
    """Arriba lo que vio el pixelizador (la fuente ya sin fondo, recortada al lienzo); abajo el
    resultado. Para juzgar de un vistazo si la escala, el ancla y la paleta están bien."""
    n = min(len(frames), max_frames)
    h, w = frames[0].shape[:2]
    W, H, gap = w * scale, h * scale, 4
    sheet = Image.new("RGB", (n * W + (n + 1) * gap, 2 * H + 3 * gap), (20, 20, 26))
    for i in range(n):
        src = Image.fromarray(sources[i], "RGBA")
        crop = src.crop(tuple(int(round(v)) for v in boxes[i])).resize((W, H), Image.LANCZOS)
        top = Image.new("RGB", (W, H), PREVIEW_BG)
        top.paste(crop, (0, 0), crop)
        x = gap + i * (W + gap)
        sheet.paste(top, (x, gap))
        sheet.paste(_on_bg(frames[i]).resize((W, H), Image.NEAREST), (x, 2 * gap + H))
    sheet.save(path)


# --- Godot -----------------------------------------------------------------------------------

def find_godot_root(path):
    path = Path(path).resolve()
    for d in (path, *path.parents):
        if (d / "project.godot").exists():
            return d
    return None


def res_path(file, root) -> str:
    return "res://" + Path(file).resolve().relative_to(root).as_posix()


def write_tres(path, animations) -> None:
    """SpriteFrames de Godot 4 con una animación por hoja.
    animations: [{"name", "res", "frames", "cell": (w, h), "fps", "loop"}]"""
    ext, sub, anims = [], [], []
    for i, a in enumerate(animations, 1):
        eid = f"{i}_{a['name']}"
        ext.append(f'[ext_resource type="Texture2D" path="{a["res"]}" id="{eid}"]')
        w, h = a["cell"]
        frames = []
        for j in range(a["frames"]):
            sid = f"AtlasTexture_{a['name']}_{j}"
            sub.append(f'[sub_resource type="AtlasTexture" id="{sid}"]\n'
                       f'atlas = ExtResource("{eid}")\n'
                       f'region = Rect2({j * w}, 0, {w}, {h})')
            frames.append('{\n"duration": 1.0,\n"texture": SubResource("%s")\n}' % sid)
        anims.append('{\n"frames": [%s],\n"loop": %s,\n"name": &"%s",\n"speed": %r\n}'
                     % (", ".join(frames), "true" if a["loop"] else "false", a["name"],
                        float(a["fps"])))
    text = ('[gd_resource type="SpriteFrames" format=3]\n\n' + "\n".join(ext) + "\n\n"
            + "\n\n".join(sub) + "\n\n[resource]\nanimations = [" + ", ".join(anims) + "]\n")
    Path(path).write_text(text, encoding="utf-8")
