#!/usr/bin/env python3
"""Comprobación automática de pixel_lab. Imprime RESULTADO: PASS o FAIL, como los scripts de
src/debug/.

Dibuja un personaje sintético (cero píxeles de terceros, ADR-008), corre la CLI completa como la
correría una persona y revisa: lienzo y ancla del paso 2.2, paleta, quitado del fondo, contorno,
el .aseprite leído de vuelta, la protección contra sobrescritura y, si encuentra Godot, que el
SpriteFrames cargue de verdad en el motor.

    python tools/pixel_lab/selftest.py [--keep] [--godot RUTA_AL_EXE_DE_CONSOLA]
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import aseprite  # noqa: E402
import export  # noqa: E402
from pixel_lab import natural_key  # noqa: E402

GODOT_DEFAULT = Path(r"O:\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe")
BG = (246, 244, 238)
H = W = 64

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(f"  [{'OK' if ok else 'FALLA'}] {name}" + (f" — {detail}" if detail else ""))


# --- Personaje sintético ---------------------------------------------------------------------

def draw_student(t: float, size: int = 384, crouch: bool = False, bob: bool = True) -> Image.Image:
    """Un estudiante con mochila y una engrapadora gigante, dibujado al doble y reducido con
    antialiasing para que tenga bordes suaves como un render o una imagen de IA."""
    S = size * 2
    k = S / 100
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    phase = 2 * math.pi * t
    swing = 0.55 * math.sin(phase)
    lift = abs(math.sin(phase)) * 2 * k if bob else 0
    leg = (24 if crouch else 34) * k
    hip = (50 * k, 90 * k - leg - lift)

    def limb(o, ang, length, width, color):
        ex, ey = o[0] + math.sin(ang) * length, o[1] + math.cos(ang) * length
        nx, ny = math.cos(ang) * width / 2, -math.sin(ang) * width / 2
        d.polygon([(o[0] - nx, o[1] - ny), (o[0] + nx, o[1] + ny),
                   (ex + nx, ey + ny), (ex - nx, ey - ny)], fill=color)
        return ex, ey

    def shoe(p, color):
        d.ellipse([p[0] - 4 * k, p[1] - 3 * k, p[0] + 7 * k, p[1] + 3 * k], fill=color)

    shoe(limb(hip, -swing, leg, 8 * k, (34, 40, 80)), (120, 24, 36))
    tx0, ty0, tx1, ty1 = hip[0] - 10 * k, hip[1] - 28 * k, hip[0] + 10 * k, hip[1] + 3 * k
    d.rounded_rectangle([hip[0] - 17 * k, ty0 + 3 * k, hip[0] - 8 * k, ty0 + 20 * k], radius=2 * k,
                        fill=(232, 122, 34))
    d.rounded_rectangle([tx0, ty0, tx1, ty1], radius=4 * k, fill=(28, 150, 146))
    d.rectangle([hip[0] + 3 * k, ty0 + 3 * k, tx1 - 1 * k, ty1 - 2 * k], fill=(18, 104, 108))
    hx0, hy0 = hip[0] - 9 * k, ty0 - 19 * k
    d.ellipse([hx0, hy0, hx0 + 18 * k, hy0 + 19 * k], fill=(238, 188, 148))
    d.pieslice([hx0 - 1 * k, hy0 - 1 * k, hx0 + 19 * k, hy0 + 16 * k], 180, 360, fill=(74, 42, 30))
    d.ellipse([hx0 + 12 * k, hy0 + 8 * k, hx0 + 14.5 * k, hy0 + 11 * k], fill=(20, 16, 24))
    hand = limb((hip[0] + 2 * k, ty0 + 9 * k), math.pi / 2 - 0.1, 14 * k, 6 * k, (238, 188, 148))
    d.rectangle([hand[0] - 2 * k, hand[1] - 4 * k, hand[0] + 12 * k, hand[1] + 1 * k], fill=(70, 72, 84))
    shoe(limb(hip, swing, leg, 8 * k, (48, 58, 112)), (150, 30, 44))
    return im.resize((size, size), Image.LANCZOS)


def make_ai_strip(path: Path, n: int = 6, size: int = 384) -> None:
    """Tira de frames sobre fondo claro con ruido y compresión JPEG, como sale de un generador."""
    strip = Image.new("RGB", (size * n, size), BG)
    for i in range(n):
        fr = draw_student(i / n, size)
        strip.paste(fr, (i * size, 0), fr)
    rng = np.random.default_rng(1)
    noisy = np.array(strip, np.int16) + rng.normal(0, 4, (size, size * n, 3)).round().astype(np.int16)
    Image.fromarray(np.clip(noisy, 0, 255).astype(np.uint8)).save(path, quality=82)


def make_render_sequence(folder: Path, n: int = 10, size: int = 384) -> None:
    """PNG con transparencia y cámara fija, como un render de Blender (caminando en el lugar)."""
    folder.mkdir(parents=True)
    for i in range(n):
        draw_student(i / n, size, crouch=True, bob=False).save(folder / f"crouch_{i + 1}.png")


# --- Utilidades ------------------------------------------------------------------------------

def lab(*args):
    cmd = [sys.executable, str(HERE / "pixel_lab.py"), *map(str, args)]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def frames_of(sheet_path: Path):
    sheet = np.array(Image.open(sheet_path).convert("RGBA"))
    return [sheet[:, i:i + W] for i in range(0, sheet.shape[1], W)], sheet


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def opaque_rows(fr):
    return np.nonzero(fr[..., 3].any(1))[0]


# --- Pruebas ---------------------------------------------------------------------------------

def test_ai_strip(tmp: Path, out: Path):
    print("Tira tipo IA (fondo claro con ruido JPEG, --align feet):")
    strip = tmp / "run_strip.jpg"
    make_ai_strip(strip)
    r = lab(strip, "--actor", "player", "--name", "run", "--strip", 6, "--out", out)
    check("la CLI termina bien", r.returncode == 0, r.stderr.strip()[-300:])
    if r.returncode:
        return
    frames, sheet = frames_of(out / "run.png")
    check("hoja de 6 frames de 64×64 sin recorte", sheet.shape == (H, W * 6, 4), str(sheet.shape))
    bottoms = [int(opaque_rows(f).max()) for f in frames]
    check("los pies de todos los frames tocan el último renglón", all(b == H - 1 for b in bottoms), str(bottoms))
    heights = [int(np.ptp(opaque_rows(f))) + 1 for f in frames]
    check("el frame más alto mide 46 px (altura inicial del jugador)", max(heights) == 46, str(heights))
    edges = np.concatenate([sheet[0, :, 3], sheet[:, 0, 3], sheet[:, -1, 3]])
    check("margen transparente arriba y a los lados", not edges.any())

    palette = export.read_palette(out / "palette.gpl")
    pal = {tuple(c) for c in palette.colors.tolist()}
    used = {tuple(c) for c in sheet[sheet[..., 3] > 0][:, :3].tolist()}
    check("15 colores o menos, todos de palette.gpl", len(used) <= 15 and used <= pal,
          f"{len(used)} usados, {len(pal)} en la paleta")
    check("todos los píxeles son opacos o transparentes del todo", set(np.unique(sheet[..., 3])) <= {0, 255})
    dist = np.sqrt(((sheet[..., :3].astype(float) - BG) ** 2).sum(-1))
    check("no quedó nada del fondo", not ((sheet[..., 3] > 0) & (dist < 40)).any())

    outline = tuple(palette.colors[palette.outline].tolist()) if palette.outline is not None else None
    ok = outline is not None
    for f in frames:
        opaque = f[..., 3] > 0
        boundary = opaque & ndimage.binary_dilation(~opaque, structure=ndimage.generate_binary_structure(2, 1))
        ok = ok and all(tuple(c) == outline for c in f[boundary][:, :3].tolist())
    check("la silueta está cerrada por el color 'outline'", ok, f"outline={outline}")

    centers = []
    for f in frames:
        rows = opaque_rows(f)
        top = f[rows.min():rows.min() + int(len(rows) * 0.6), :, 3] > 0
        centers.append(np.nonzero(top)[1].mean() + 0.5)
    check("el torso queda centrado en x = 24 (±2.5)", all(abs(c - W / 2) <= 2.5 for c in centers),
          ", ".join(f"{c:.1f}" for c in centers))

    ase = aseprite.read_aseprite(out / "run.aseprite")
    check(".aseprite: 6 frames de 64×64", len(ase["frames"]) == 6 and (ase["width"], ase["height"]) == (W, H))
    check(".aseprite: capas _ref_pose (referencia) y sprite",
          [l["name"] for l in ase["layers"]] == ["_ref_pose", "sprite"]
          and ase["layers"][0]["flags"] & aseprite.FLAG_REFERENCE)
    check(".aseprite: tag 'run' en bucle de 0 a 5",
          ase["tags"] == [{"name": "run", "from": 0, "to": 5, "direction": 0, "repeat": 0}], str(ase["tags"]))
    same = all(np.array_equal(fr["cels"][1]["pixels"], frames[i]) for i, fr in enumerate(ase["frames"]))
    check(".aseprite: la capa sprite es idéntica a la hoja PNG", same)
    check(".aseprite: paleta y duración (83 ms a 12 fps)",
          [list(c[:3]) for c in ase["palette"]] == palette.colors.tolist()
          and all(fr["duration"] == 83 for fr in ase["frames"]))


def test_render_sequence(tmp: Path, out: Path):
    print("Secuencia tipo render (PNG con alfa, --align source, misma escala y paleta del actor):")
    seq = tmp / "render_crouch"
    make_render_sequence(seq)
    before = sha1(out / "palette.gpl")
    r = lab(seq, "--name", "crouch", "--align", "source", "--step", 2, "--fps", 10, "--no-loop", "--out", out)
    check("la CLI termina bien", r.returncode == 0, r.stderr.strip()[-300:])
    if r.returncode:
        return
    frames, sheet = frames_of(out / "crouch.png")
    check("--step 2 sobre 10 renders deja 5 frames", sheet.shape == (H, W * 5, 4), str(sheet.shape))
    heights = [int(np.ptp(opaque_rows(f))) + 1 for f in frames]
    check("agachado sale más bajo que 46 px: reusa la escala del actor", 35 <= max(heights) <= 43, str(heights))
    check("reusa palette.gpl sin tocarla", sha1(out / "palette.gpl") == before)
    check("el frame más bajo toca el piso", any(f[H - 1, :, 3].any() for f in frames))
    top = int(min(opaque_rows(f).min() for f in frames))
    upper = slice(top, top + 14)
    check("con --align source el torso no se mueve entre frames",
          all(np.array_equal(f[upper], frames[0][upper]) for f in frames))
    ase = aseprite.read_aseprite(out / "crouch.aseprite")
    check(".aseprite: tag de una sola vuelta y 100 ms por frame",
          ase["tags"][0]["repeat"] == 1 and all(fr["duration"] == 100 for fr in ase["frames"]))
    tres = (out / "sprite_frames.tres").read_text(encoding="utf-8")
    check(".tres con las dos animaciones", '&"run"' in tres and '&"crouch"' in tres)


def test_guards(tmp: Path, out: Path):
    print("Protecciones:")
    sheet = out / "run.png"
    im = np.array(Image.open(sheet))
    im[0, 0] = (255, 0, 255, 255)  # "retoque" hecho a mano
    Image.fromarray(im).save(sheet)
    edited = sha1(sheet)
    r = lab(tmp / "run_strip.jpg", "--name", "run", "--strip", 6, "--out", out)
    check("no sobrescribe una hoja retocada a mano", r.returncode == 2 and sha1(sheet) == edited,
          r.stderr.strip()[-200:])
    r = lab(tmp / "run_strip.jpg", "--name", "run", "--strip", 6, "--out", out, "--force")
    check("con --force sí la regenera", r.returncode == 0 and sha1(sheet) != edited)
    r = lab(tmp / "run_strip.jpg", "--name", "run2", "--strip", 6, "--cell", "80x80", "--out", out)
    check("no deja cambiar el lienzo del actor", r.returncode == 2)
    r = lab(tmp / "run_strip.jpg", "--actor", "player", "--name", "big", "--strip", 6, "--height", 76,
            "--out", tmp / "proj" / "sprites" / "big")
    check("avisa si el personaje no cabe en el lienzo", r.returncode == 0 and "se sale del lienzo" in r.stdout)


def test_units(tmp: Path):
    print("Piezas sueltas:")
    names = sorted([Path("f10.png"), Path("f2.png"), Path("f1.png")], key=natural_key)
    check("orden natural de frames (f1, f2, f10)", [p.name for p in names] == ["f1.png", "f2.png", "f10.png"])
    hexfile = tmp / "p.hex"
    hexfile.write_text("1a1420\nff8800\n#00ff00\n", encoding="utf-8")
    p = export.read_palette(hexfile)
    check("lee paletas .hex", p.colors.tolist() == [[26, 20, 32], [255, 136, 0], [0, 255, 0]])
    p.names[0] = "outline"
    export.write_gpl(tmp / "p.gpl", p, "prueba")
    q = export.read_palette(tmp / "p.gpl")
    check("escribe y relee .gpl con su color de contorno", q.colors.tolist() == p.colors.tolist() and q.outline == 0)


def test_godot(proj: Path, exe: Path):
    print("Godot:")
    if not exe.exists():
        print(f"  (no encontré Godot en {exe}; se omite. Usa --godot RUTA)")
        return
    (proj / "_check.gd").write_text(
        "extends SceneTree\n\n"
        "func _init() -> void:\n"
        "\tvar sf := load(\"res://sprites/hero/sprite_frames.tres\") as SpriteFrames\n"
        "\tif sf == null:\n"
        "\t\tprint(\"CHECK_LOAD_FAIL\")\n"
        "\t\tquit(1)\n"
        "\t\treturn\n"
        "\tfor anim in sf.get_animation_names():\n"
        "\t\tvar tex := sf.get_frame_texture(anim, 0)\n"
        "\t\tprint(\"CHECK_ANIM %s %d %s %s %dx%d\" % [anim, sf.get_frame_count(anim), "
        "sf.get_animation_speed(anim), sf.get_animation_loop(anim), tex.get_width(), tex.get_height()])\n"
        "\tvar img := sf.get_frame_texture(&\"run\", 0).get_image()\n"
        "\tvar opaque := 0\n"
        "\tfor y in img.get_height():\n"
        "\t\tfor x in img.get_width():\n"
        "\t\t\tif img.get_pixel(x, y).a > 0.5:\n"
        "\t\t\t\topaque += 1\n"
        "\tprint(\"CHECK_OPAQUE %d\" % opaque)\n"
        "\tquit(0)\n", encoding="utf-8")
    subprocess.run([str(exe), "--headless", "--path", str(proj), "--import"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    r = subprocess.run([str(exe), "--headless", "--path", str(proj), "--script", "res://_check.gd"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    lines = [l for l in r.stdout.splitlines() if l.startswith("CHECK_")]
    anims = {m[1]: m for m in (re.match(r"CHECK_ANIM (\w+) (\d+) ([\d.]+) (\w+) (\d+)x(\d+)", l) for l in lines) if m}
    check("Godot carga el SpriteFrames", "run" in anims and "crouch" in anims,
          " | ".join(lines) or (r.stdout + r.stderr).strip()[-300:])
    if "run" in anims and "crouch" in anims:
        run, crouch = anims["run"], anims["crouch"]
        check("run: 6 frames, 12 fps, en bucle, 64×64",
              (run[2], float(run[3]), run[4], run[5], run[6]) == ("6", 12.0, "true", "64", "64"))
        check("crouch: 5 frames, 10 fps, sin bucle",
              (crouch[2], float(crouch[3]), crouch[4]) == ("5", 10.0, "false"))
        frames, _ = frames_of(proj / "sprites" / "hero" / "run.png")
        expected = int((frames[0][..., 3] > 0).sum())
        got = next((int(l.split()[1]) for l in lines if l.startswith("CHECK_OPAQUE")), -1)
        check("Godot ve los mismos píxeles que la hoja", got == expected, f"{got} vs {expected}")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="no borrar la carpeta temporal")
    ap.add_argument("--godot", type=Path, default=GODOT_DEFAULT)
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="pixel_lab_"))
    proj = tmp / "proj"
    out = proj / "sprites" / "hero"
    out.mkdir(parents=True)
    (proj / "project.godot").write_text(
        'config_version=5\n\n[application]\n\nconfig/name="pixel_lab_selftest"\n\n'
        "[rendering]\n\ntextures/canvas_textures/default_texture_filter=0\n", encoding="utf-8")
    try:
        test_units(tmp)
        test_ai_strip(tmp, out)
        if (out / "run.png").exists():
            test_render_sequence(tmp, out)
            test_godot(proj, args.godot)
            test_guards(tmp, out)
    finally:
        if args.keep:
            print(f"Archivos de la prueba en: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    passed = all(results) and len(results) > 0
    print(f"{sum(results)}/{len(results)} comprobaciones")
    print("RESULTADO: " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
