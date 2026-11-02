#!/usr/bin/env python3
"""pixel_lab: pixelizador de sprites para Catástrofe en la Biblioteca.

Toma imágenes grandes (render de Blender, salida de IA, boceto) y las convierte en frames de pixel
art listos para retocar en Aseprite y meter a Godot: rejilla real, paleta corta compartida,
contorno, lienzo fijo por actor y origen en la planta de los pies (paso 2.2 de
01_Arquitectura_Tecnica). Ver tools/pixel_lab/README.md.

    python tools/pixel_lab/pixel_lab.py renders/run/ --actor player --name run \\
        --align source --out assets/sprites/player
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aseprite  # noqa: E402
import export  # noqa: E402
from pixelize import (SourceFrame, add_outline, cleanup, fit_palette, pixelize_frame,  # noqa: E402
                      placements, remove_background, scale_for_height, to_rgba)

# Lienzo del paso 2.2 de 01_Arquitectura_Tecnica (v1.1): las medidas reales de los sprites del Laboratorio de
# sprites, que es la referencia de tamaño (protagonista 47 px de alto, enemigos 31-38, Angiosperma 57, Tiranosaurio 85).
# La altura es solo un punto de partida para la primera animación del actor; ajústala con --height.
ACTORS = {
    "player": ((64, 64), 46),
    "enemy": ((48, 48), 36),
    "enemy_big": ((80, 80), 58),
    "boss": ((176, 112), 88),
    "projectile": ((16, 16), 12),
}
MANIFEST = "pixel_lab.json"
PALETTE_FILE = "palette.gpl"
TRES_FILE = "sprite_frames.tres"
PREVIEW_DIR = "_preview"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tga", ".tif", ".tiff"}


class LabError(Exception):
    pass


# --- Argumentos ------------------------------------------------------------------------------

def _size(text: str):
    m = re.fullmatch(r"(\d+)[xX×](\d+)", text.strip())
    if not m:
        raise argparse.ArgumentTypeError(f"usa ANCHOxALTO, por ejemplo 48x48 (no '{text}')")
    return int(m[1]), int(m[2])


def _color(text: str):
    h = text.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise argparse.ArgumentTypeError(f"usa un color como #1a1420 (no '{text}')")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _name(text: str):
    if not re.fullmatch(r"[a-z0-9_]+", text):
        raise argparse.ArgumentTypeError("el nombre va en minúsculas, números y _ (ej. run, shoot_up)")
    return text


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="pixel_lab",
        description="Convierte renders o imágenes de IA en sprites de pixel art para Godot/Aseprite.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Ejemplos en tools/pixel_lab/README.md")
    p.add_argument("inputs", nargs="+", help="imágenes, carpetas (orden natural) o patrones como renders/run_*.png")
    p.add_argument("--out", required=True, help="carpeta del actor (ej. assets/sprites/player)")
    p.add_argument("--name", required=True, type=_name, help="nombre de la animación (ej. run)")

    g = p.add_argument_group("lienzo y escala")
    g.add_argument("--actor", choices=sorted(ACTORS), help="tipo de actor: fija el lienzo del paso 2.2")
    g.add_argument("--cell", type=_size, help="lienzo a mano, ej. 48x48 (en vez de --actor)")
    g.add_argument("--height", type=int, help="alto en px del frame más alto, contorno incluido")
    g.add_argument("--scale", type=float, help="píxeles de la fuente por píxel del juego (en vez de --height)")
    g.add_argument("--align", choices=("feet", "source"), default="feet",
                   help="feet: cada frame se apoya en su píxel más bajo (tiras de IA). "
                        "source: mismo origen para todos (renders con cámara fija)")
    g.add_argument("--ground", type=float, help="con --align source: y de la fuente donde está el piso")
    g.add_argument("--anchor-x", type=float, help="x de la fuente que va al centro del lienzo")

    g = p.add_argument_group("entrada")
    g.add_argument("--strip", type=int, metavar="N", help="cada imagen es una tira de N frames en fila")
    g.add_argument("--grid", type=_size, metavar="CxR", help="cada imagen es una cuadrícula de C columnas y R filas")
    g.add_argument("--step", type=int, default=1, help="usar 1 de cada N frames (renders a 24/60 fps)")
    g.add_argument("--bg", default="auto",
                   help="auto (alfa si hay, si no el color del borde), alpha, o un color #RRGGBB")
    g.add_argument("--tol", type=float, default=40.0, help="tolerancia del color de fondo (0-441)")
    g.add_argument("--bg-everywhere", action="store_true",
                   help="borrar el color de fondo también dentro del personaje")

    g = p.add_argument_group("paleta y limpieza")
    g.add_argument("--colors", type=int, default=15,
                   help="colores opacos, contorno incluido (15 + transparente = 16, como el Neo Geo)")
    g.add_argument("--palette", help="paleta fija: .gpl, .hex, .txt o imagen")
    g.add_argument("--new-palette", action="store_true", help="recalcular la paleta del actor")
    g.add_argument("--outline", default="auto", help="auto, none, o un color #RRGGBB")
    g.add_argument("--method", choices=("mode", "mean"), default="mode",
                   help="mode: color más repetido del bloque (bordes limpios). mean: color promedio (más detalle)")
    g.add_argument("--coverage", type=float, default=0.5, help="fracción del bloque que debe cubrir el personaje")
    g.add_argument("--min-island", type=int, default=3, help="borrar islas sueltas de menos de N px")
    g.add_argument("--despeckle", type=float, default=0.12,
                   help="unificar píxeles solitarios de color parecido (distancia OKLab; 0 = no)")

    g = p.add_argument_group("salida")
    g.add_argument("--fps", type=float, default=12.0, help="velocidad de la animación")
    g.add_argument("--no-loop", action="store_true", help="la animación se reproduce una vez")
    g.add_argument("--preview-scale", type=int, default=4, help="aumento de las vistas previas")
    g.add_argument("--no-aseprite", action="store_true", help="no escribir el .aseprite")
    g.add_argument("--no-tres", action="store_true", help="no escribir el SpriteFrames de Godot")
    g.add_argument("--force", action="store_true", help="sobrescribir archivos editados a mano")
    args = p.parse_args(argv)

    if args.strip and args.grid:
        p.error("usa --strip o --grid, no los dos")
    if args.step < 1:
        p.error("--step debe ser 1 o más")
    if args.bg not in ("auto", "alpha"):
        args.bg = _color(args.bg)
    if args.outline not in ("auto", "none"):
        args.outline = _color(args.outline)
    return args


# --- Entrada ---------------------------------------------------------------------------------

def natural_key(path):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(path))]


def expand_inputs(inputs):
    paths = []
    for item in inputs:
        p = Path(item)
        if any(ch in item for ch in "*?["):
            found = sorted((Path(x) for x in glob.glob(item)), key=natural_key)
        elif p.is_dir():
            found = sorted((x for x in p.iterdir() if x.suffix.lower() in IMAGE_EXTS), key=natural_key)
        elif p.is_file():
            found = [p]
        else:
            raise LabError(f"no existe: {item}")
        if not found:
            raise LabError(f"no hay imágenes en: {item}")
        paths.extend(found)
    return paths


def load_sources(paths, strip=None, grid=None, step=1, warnings=None):
    cols, rows = (strip, 1) if strip else (grid or (1, 1))
    out = []
    for path in paths:
        with Image.open(path) as im:
            n = getattr(im, "n_frames", 1)
            for i in range(n):
                im.seek(i)
                rgba = np.array(im.convert("RGBA"))
                base = path.stem if n == 1 else f"{path.stem}#{i}"
                h, w = rgba.shape[:2]
                if (w % cols or h % rows) and warnings is not None:
                    warnings.append(f"{path.name}: {w}×{h} no se divide exacto en {cols}×{rows}; "
                                    "se ignoran los píxeles sobrantes")
                cw, ch = w // cols, h // rows
                for r in range(rows):
                    for c in range(cols):
                        name = base if cols * rows == 1 else f"{base}[{r * cols + c}]"
                        out.append((name, rgba[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw].copy()))
    return out[::step]


# --- Manifiesto y protección contra sobrescritura ---------------------------------------------

def load_manifest(out: Path) -> dict:
    p = out / MANIFEST
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"tool": "pixel_lab", "version": 1, "files": {}, "animations": {}}


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def can_overwrite(path: Path, out: Path, manifest: dict) -> bool:
    """Solo se sobrescribe lo que pixel_lab escribió y nadie tocó después. Si alguien retocó la
    hoja o el .aseprite, el hash ya no cuadra y hace falta --force."""
    if not path.exists():
        return True
    return manifest["files"].get(path.relative_to(out).as_posix()) == sha1(path)


def _rel_or_abs(path: Path, base: Path) -> str:
    try:
        return Path(os.path.relpath(path, base)).as_posix()
    except ValueError:  # otra unidad en Windows
        return path.as_posix()


# --- Flujo principal -------------------------------------------------------------------------

def resolve_cell(args, manifest, warnings):
    if args.cell:
        cell = tuple(args.cell)
    elif args.actor:
        cell = ACTORS[args.actor][0]
    elif manifest.get("cell"):
        cell = tuple(manifest["cell"])
    else:
        raise LabError("falta el lienzo: usa --actor (" + ", ".join(sorted(ACTORS)) + ") o --cell 48x48")
    if manifest.get("cell") and tuple(manifest["cell"]) != cell and not args.force:
        raise LabError(f"este actor ya usa un lienzo de {manifest['cell'][0]}×{manifest['cell'][1]} "
                       "y todas sus animaciones deben compartirlo (paso 2.2). Usa --force si de "
                       "verdad quieres cambiarlo; las animaciones anteriores habría que regenerarlas.")
    if cell[0] % 2:
        warnings.append(f"lienzo de ancho impar ({cell[0]}): el centro cae a mitad de píxel")
    return cell


def resolve_scale(args, manifest, frames, cell, outline, warnings):
    stored = manifest.get("scale")
    if args.scale:
        scale, why = args.scale, "--scale"
    elif args.height:
        scale, why = scale_for_height(frames, args.height, outline), f"--height {args.height}"
    elif stored:
        return stored, "la del actor (pixel_lab.json)"
    else:
        height = ACTORS[args.actor][1] if args.actor else round(cell[1] * 0.83)
        scale, why = scale_for_height(frames, height, outline), f"altura inicial {height} px"
    if stored and abs(scale - stored) / stored > 0.01:
        warnings.append(f"cambiaste la escala del actor ({stored:.2f} → {scale:.2f}); las animaciones "
                        "que ya tenía siguen a la escala anterior y se verán de otro tamaño")
    return scale, why


def resolve_palette(args, manifest, frames, scale, outline, out):
    """Devuelve (paleta, ruta guardada en el manifiesto, ¿hay que escribir palette.gpl?)."""
    if args.palette:
        path = Path(args.palette).resolve()
        palette = export.read_palette(path)
        ref, new = _rel_or_abs(path, out), False
    elif manifest.get("palette") and not args.new_palette:
        path = (out / manifest["palette"]).resolve()
        if not path.exists():
            raise LabError(f"el actor usa la paleta {manifest['palette']} y no existe; "
                           "usa --palette o --new-palette")
        palette = export.read_palette(path)
        ref, new = manifest["palette"], False
    else:
        erode = int(min(8, max(1, scale * 0.25)))
        palette = fit_palette(frames, args.colors, outline=outline, erode=erode)
        if isinstance(args.outline, tuple):
            palette.colors[palette.outline] = args.outline
        return palette, PALETTE_FILE, True

    if outline:
        if isinstance(args.outline, tuple):
            hit = np.nonzero((palette.colors == np.array(args.outline, np.uint8)).all(1))[0]
            if not len(hit):
                raise LabError("el color de --outline no está en la paleta; agrégalo a la paleta primero")
            palette.outline = int(hit[0])
        elif palette.outline is None:
            palette.outline = palette.darkest()
    return palette, ref, new


def run(args) -> int:
    warnings = []
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(out)
    outline = args.outline != "none"

    paths = expand_inputs(args.inputs)
    frames = []
    for name, rgba in load_sources(paths, args.strip, args.grid, args.step, warnings):
        f = SourceFrame(name, rgba, remove_background(rgba, args.bg, args.tol, args.bg_everywhere))
        if f.bbox() is None:
            warnings.append(f"{name}: quedó vacío al quitar el fondo; se omite")
            continue
        frames.append(f)
    if not frames:
        raise LabError("ningún frame tiene contenido después de quitar el fondo (revisa --bg y --tol)")

    cell = resolve_cell(args, manifest, warnings)
    scale, scale_why = resolve_scale(args, manifest, frames, cell, outline, warnings)
    palette, palette_ref, palette_new = resolve_palette(args, manifest, frames, scale, outline, out)

    results, rgba_frames = [], []
    for f, place in zip(frames, placements(frames, scale, args.align, args.ground, args.anchor_x)):
        pf = pixelize_frame(f, palette, place, cell, outline, args.method, args.coverage)
        idx = cleanup(pf.index, palette, args.min_island, args.despeckle)
        if outline:
            idx = add_outline(idx, palette.outline)
        if pf.overflow:
            warnings.append(f"{f.name}: el personaje se sale del lienzo por {', '.join(pf.overflow)} "
                            "(baja --height o usa un lienzo más grande)")
        if not (idx >= 0).any():
            warnings.append(f"{f.name}: quedó vacío al pixelizar")
        results.append(pf)
        rgba_frames.append(to_rgba(idx, palette))

    # Qué se va a escribir. Se revisa todo antes de tocar nada.
    godot_root = None if args.no_tres else export.find_godot_root(out)
    targets = [out / f"{args.name}.png"]
    if not args.no_aseprite:
        targets.append(out / f"{args.name}.aseprite")
    if palette_new:
        targets.append(out / PALETTE_FILE)
    if godot_root:
        targets.append(out / TRES_FILE)
    blocked = [t for t in targets if not can_overwrite(t, out, manifest)]
    if blocked and not args.force:
        raise LabError("estos archivos se editaron después de generarlos (o no los creó pixel_lab) y "
                       "no se van a sobrescribir: " + ", ".join(t.name for t in blocked)
                       + ". Usa otro --name, muévelos, o --force si de verdad quieres reemplazarlos.")

    written = []

    def record(path: Path):
        manifest["files"][path.relative_to(out).as_posix()] = sha1(path)
        written.append(path.name)

    sheet = out / f"{args.name}.png"
    export.write_sheet(sheet, rgba_frames)
    record(sheet)
    if palette_new:
        export.write_gpl(out / PALETTE_FILE, palette, out.name)
        record(out / PALETTE_FILE)
    if not args.no_aseprite:
        ase = out / f"{args.name}.aseprite"
        aseprite.write_aseprite(ase, rgba_frames, [round(1000 / args.fps)] * len(rgba_frames),
                                palette.colors.tolist(),
                                tags=[(args.name, 0, len(rgba_frames) - 1, 1 if args.no_loop else 0)],
                                reference=[r.reference for r in results])
        record(ase)

    preview = out / PREVIEW_DIR
    preview.mkdir(exist_ok=True)
    (preview / ".gdignore").touch()
    sources = []
    for f in frames:
        s = f.rgba.copy()
        s[..., 3] = np.round(f.alpha * 255).astype(np.uint8)
        sources.append(s)
    export.write_gif(preview / f"{args.name}.gif", rgba_frames, args.fps, args.preview_scale)
    export.write_compare(preview / f"{args.name}_compare.png", sources,
                         [r.source_box for r in results], rgba_frames, args.preview_scale)

    manifest.update(cell=list(cell), scale=scale, palette=palette_ref)
    manifest["animations"][args.name] = {
        "sheet": sheet.name, "frames": len(rgba_frames), "fps": args.fps, "loop": not args.no_loop,
        "align": args.align, "method": args.method, "outline": outline,
        "sources": [_rel_or_abs(p, out) for p in paths],
        "args": args.argv,
    }
    if godot_root:
        anims = []
        for name, a in sorted(manifest["animations"].items()):
            path = out / a["sheet"]
            if not path.exists():
                warnings.append(f"{a['sheet']} no existe; la animación '{name}' no va en el .tres")
                continue
            anims.append({"name": name, "res": export.res_path(path, godot_root), "frames": a["frames"],
                          "cell": cell, "fps": a["fps"], "loop": a["loop"]})
        export.write_tres(out / TRES_FILE, anims)
        record(out / TRES_FILE)
    (out / MANIFEST).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    heights = [int(np.ptp(np.nonzero(fr[..., 3])[0])) + 1 for fr in rgba_frames if fr[..., 3].any()]
    used = {tuple(c) for fr in rgba_frames for c in fr[fr[..., 3] > 0][:, :3].tolist()}
    W, H = cell
    print(f"pixel_lab: {len(rgba_frames)} frames -> '{args.name}' en {out}")
    print(f"  lienzo {W}×{H}, escala {scale:.2f} px de fuente por px ({scale_why}), "
          f"alto {min(heights)}-{max(heights)} px")
    print(f"  paleta: {len(palette.colors)} colores ({palette_ref}{', nueva' if palette_new else ''}), "
          f"usados {len(used)}")
    print(f"  escrito: {', '.join(written + [MANIFEST])}")
    print(f"  vista previa: {PREVIEW_DIR}/{args.name}.gif, {PREVIEW_DIR}/{args.name}_compare.png")
    if godot_root:
        print(f"  Godot: AnimatedSprite2D con sprite_frames = {export.res_path(out / TRES_FILE, godot_root)}, "
              f"centered = false, offset = Vector2({-W // 2}, {-H}) -> los pies quedan en el origen")
    else:
        print("  (la carpeta no está dentro de un proyecto de Godot: no se escribió .tres)")
    for w in warnings:
        print(f"  AVISO: {w}")
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    args.argv = list(sys.argv[1:] if argv is None else argv)
    try:
        return run(args)
    except (LabError, ValueError) as e:
        print(f"pixel_lab: error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
