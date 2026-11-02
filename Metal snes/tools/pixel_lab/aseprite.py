"""Escritura de archivos .aseprite (y lectura, para las pruebas).

Formato: https://github.com/aseprite/aseprite/blob/main/docs/ase-file-specs.md
Solo lo que necesita el pixelizador: modo RGBA, capas normales, cels comprimidos, paleta y tags.

Capas que escribe, con la convención del paso 2.1 de 01_Arquitectura_Tecnica:
    sprite      el personaje pixelizado (lo que se retoca y llega al juego)
    _ref_pose   la fuente promediada a la misma rejilla, al 50 % y marcada como capa de
                referencia: Aseprite no la exporta y Aseprite Wizard la filtra con ^_
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

import numpy as np

FLAG_VISIBLE = 1
FLAG_EDITABLE = 2
FLAG_REFERENCE = 64

CHUNK_OLD_PALETTE = 0x0004
CHUNK_LAYER = 0x2004
CHUNK_CEL = 0x2005
CHUNK_COLOR_PROFILE = 0x2007
CHUNK_TAGS = 0x2018
CHUNK_PALETTE = 0x2019

HEADER_MAGIC = 0xA5E0
FRAME_MAGIC = 0xF1FA


def _string(s: str) -> bytes:
    b = s.encode("utf-8")
    return struct.pack("<H", len(b)) + b


def _chunk(kind: int, data: bytes) -> bytes:
    return struct.pack("<IH", len(data) + 6, kind) + data


def _color_profile() -> bytes:
    return _chunk(CHUNK_COLOR_PROFILE, struct.pack("<HHI8x", 1, 0, 0))  # sRGB


def _palette(colors) -> bytes:
    n = len(colors)
    data = struct.pack("<III8x", n, 0, n - 1)
    for r, g, b in colors:
        data += struct.pack("<H4B", 0, r, g, b, 255)
    return _chunk(CHUNK_PALETTE, data)


def _old_palette(colors) -> bytes:
    # Aseprite lo sigue escribiendo para que lo lean versiones viejas (y LibreSprite).
    n = len(colors)
    data = struct.pack("<HBB", 1, 0, n % 256) + bytes(v for rgb in colors for v in rgb)
    return _chunk(CHUNK_OLD_PALETTE, data)


def _layer(name: str, flags: int, opacity: int) -> bytes:
    return _chunk(CHUNK_LAYER, struct.pack("<6HB3x", flags, 0, 0, 0, 0, 0, opacity) + _string(name))


def _cel(layer: int, rgba: np.ndarray) -> bytes:
    h, w = rgba.shape[:2]
    pixels = zlib.compress(np.ascontiguousarray(rgba, dtype=np.uint8).tobytes())
    return _chunk(CHUNK_CEL, struct.pack("<HhhBHh5x", layer, 0, 0, 255, 2, 0)
                  + struct.pack("<HH", w, h) + pixels)


def _tags(tags) -> bytes:
    data = struct.pack("<H8x", len(tags))
    for name, first, last, repeat in tags:
        data += struct.pack("<HHBH6x3Bx", first, last, 0, repeat, 0, 0, 0) + _string(name)
    return _chunk(CHUNK_TAGS, data)


def _frame(chunks, duration_ms: int) -> bytes:
    body = b"".join(chunks)
    n = len(chunks)
    return struct.pack("<IHHH2xI", 16 + len(body), FRAME_MAGIC, min(n, 0xFFFF), duration_ms, n) + body


def write_aseprite(path, frames, durations_ms, palette_colors, tags=(), reference=None,
                   reference_opacity: int = 128) -> None:
    """frames y reference: listas de arreglos (H, W, 4) uint8 del mismo tamaño.
    tags: [(nombre, primer_frame, último_frame, repeticiones)], 0 repeticiones = en bucle."""
    h, w = frames[0].shape[:2]
    palette_colors = [tuple(int(v) for v in c) for c in palette_colors]
    layers = []
    if reference is not None:
        layers.append(("_ref_pose", FLAG_VISIBLE | FLAG_REFERENCE, reference_opacity))
    layers.append(("sprite", FLAG_VISIBLE | FLAG_EDITABLE, 255))
    sprite_layer = len(layers) - 1

    body = b""
    for i, img in enumerate(frames):
        chunks = []
        if i == 0:
            chunks += [_color_profile(), _palette(palette_colors), _old_palette(palette_colors)]
            chunks += [_layer(*layer) for layer in layers]
        if reference is not None:
            chunks.append(_cel(0, reference[i]))
        chunks.append(_cel(sprite_layer, img))
        if i == 0 and tags:
            chunks.append(_tags(tags))
        body += _frame(chunks, int(durations_ms[i]))

    header = struct.pack(
        "<IHHHHHIHIIB3xHBBhhHH84x",
        128 + len(body), HEADER_MAGIC, len(frames), w, h,
        32,                     # bits por píxel: RGBA
        1,                      # la opacidad de las capas es válida
        int(durations_ms[0]),   # "speed" (obsoleto, Aseprite lo sigue llenando)
        0, 0,
        0,                      # índice transparente (solo modo indexado)
        len(palette_colors),
        1, 1,                   # proporción de píxel 1:1
        0, 0, 16, 16)           # rejilla
    Path(path).write_bytes(header + body)


def read_aseprite(path) -> dict:
    """Lector estricto, para comprobar lo que escribe write_aseprite. Falla con AssertionError
    si un tamaño declarado no cuadra con lo que hay en el archivo."""
    data = Path(path).read_bytes()
    size, magic, n_frames, w, h, depth, flags, speed = struct.unpack_from("<IHHHHHIH", data, 0)
    assert magic == HEADER_MAGIC, "no es un archivo .aseprite"
    assert size == len(data), f"tamaño declarado {size} != real {len(data)}"
    assert depth == 32, "solo se lee modo RGBA"
    n_colors = struct.unpack_from("<H", data, 32)[0]
    out = {"width": w, "height": h, "n_colors": n_colors, "layers": [], "frames": [],
           "tags": [], "palette": None}
    pos = 128
    for _ in range(n_frames):
        fsize, fmagic, old_n, duration, new_n = struct.unpack_from("<IHHH2xI", data, pos)
        assert fmagic == FRAME_MAGIC, f"frame sin firma en el byte {pos}"
        n = new_n or old_n
        cpos, end = pos + 16, pos + fsize
        cels = {}
        for _ in range(n):
            csize, kind = struct.unpack_from("<IH", data, cpos)
            body = data[cpos + 6:cpos + csize]
            if kind == CHUNK_LAYER:
                lflags, ltype, child, _, _, blend, opacity = struct.unpack_from("<6HB", body)
                nlen = struct.unpack_from("<H", body, 16)[0]
                out["layers"].append({"name": body[18:18 + nlen].decode("utf-8"),
                                      "flags": lflags, "type": ltype, "opacity": opacity})
            elif kind == CHUNK_CEL:
                layer, x, y, opacity, ctype, z = struct.unpack_from("<HhhBHh", body)
                assert ctype == 2, "solo cels comprimidos"
                cw, ch = struct.unpack_from("<HH", body, 16)
                px = np.frombuffer(zlib.decompress(body[20:]), np.uint8).reshape(ch, cw, 4)
                cels[layer] = {"x": x, "y": y, "pixels": px}
            elif kind == CHUNK_TAGS:
                (count,) = struct.unpack_from("<H", body)
                tpos = 10
                for _ in range(count):
                    first, last, direction, repeat = struct.unpack_from("<HHBH", body, tpos)
                    nlen = struct.unpack_from("<H", body, tpos + 17)[0]
                    name = body[tpos + 19:tpos + 19 + nlen].decode("utf-8")
                    out["tags"].append({"name": name, "from": first, "to": last,
                                        "direction": direction, "repeat": repeat})
                    tpos += 19 + nlen
                assert tpos == len(body), "chunk de tags con bytes de sobra"
            elif kind == CHUNK_PALETTE:
                total, first, last = struct.unpack_from("<III", body)
                entries, ppos = [], 20
                for _ in range(last - first + 1):
                    eflags, r, g, b, a = struct.unpack_from("<H4B", body, ppos)
                    entries.append((r, g, b, a))
                    ppos += 6
                    if eflags & 1:
                        ppos += 2 + struct.unpack_from("<H", body, ppos)[0]
                out["palette"] = entries
            cpos += csize
        assert cpos == end, f"el frame declara {fsize} bytes pero sus chunks suman {cpos - pos}"
        out["frames"].append({"duration": duration, "cels": cels})
        pos = end
    assert pos == len(data), "bytes de sobra al final del archivo"
    return out
