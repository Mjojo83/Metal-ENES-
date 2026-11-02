#!/usr/bin/env python3
"""Genera data/levels/deep_fall_01.json y data/waves/deep_fall_01.json (piso 1, DEEP FALL).

El nivel es un mapa ASCII de 16 px por celda: '#' roca sólida, '=' plataforma atravesable, '.' aire.
Dos corredores: el Cretácico arriba, un pozo de caída y abajo el Carbonífero → Cámbrico → jefe.
Los gates, puntos de aparición, cajas de armas y oleadas van como datos, no como código (ADR-005).

    python tools/level_gen/deep_fall_01.py --root .
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

COLS, ROWS = 176, 28
TILE = 16
UPPER_GROUND = 12       # fila de la superficie del corredor de arriba (y = 192)
UPPER_ROCK_END = 16     # roca de 12..15
LOWER_GROUND = 26       # superficie del corredor de abajo (y = 416)
SHAFT = (72, 77)        # columnas del pozo (sin suelo arriba)
LOWER_START = 60        # el corredor de abajo empieza aquí (a la izquierda, roca)
UPPER_WALL = 77         # desde aquí el corredor de arriba está cerrado


def build_map():
    grid = [["." for _ in range(COLS)] for _ in range(ROWS)]
    for c in range(COLS):
        # corredor de arriba
        if c < UPPER_WALL:
            if not (SHAFT[0] <= c < SHAFT[1]):
                for r in range(UPPER_GROUND, UPPER_ROCK_END):
                    grid[r][c] = "#"
        else:
            for r in range(0, UPPER_ROCK_END):
                grid[r][c] = "#"
        # relleno entre corredores donde abajo aún no hay corredor
        if c < LOWER_START:
            for r in range(UPPER_ROCK_END, ROWS):
                grid[r][c] = "#"
        # suelo de abajo
        for r in range(LOWER_GROUND, ROWS):
            grid[r][c] = "#"
    # muros de los extremos
    for r in range(ROWS):
        grid[r][0] = "#"
        grid[r][COLS - 1] = "#"
    # techo bajo en el corredor de arriba (estalactitas de roca) para que se sienta cueva
    for c in range(0, UPPER_WALL):
        grid[0][c] = "#"
        if c % 9 in (3, 4):
            grid[1][c] = "#"
    # plataformas atravesables arriba (saltos y disparo hacia arriba)
    for (c0, c1, r) in [(12, 16, 9), (28, 32, 8), (36, 39, 6), (54, 58, 8), (64, 68, 9)]:
        for c in range(c0, c1):
            grid[r][c] = "="
    # escalones de roca en el corredor de abajo y plataformas
    for (c0, c1, r) in [(96, 100, 23), (104, 107, 21), (128, 132, 23), (140, 143, 21), (150, 153, 23)]:
        for c in range(c0, c1):
            grid[r][c] = "="
    for (c0, c1) in [(84, 86), (118, 120), (166, 168)]:
        for c in range(c0, c1):
            grid[LOWER_GROUND - 1][c] = "#"
    # un hueco letal no: el género castiga con enemigos, no con pozos (sección 3.5); el pozo baja
    return ["".join(row) for row in grid]


def px(c: float, r: float) -> list:
    return [int(c * TILE), int(r * TILE)]


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    args = p.parse_args(argv)
    root = Path(args.root)
    ug, lg = UPPER_GROUND, LOWER_GROUND
    level = {
        "id": "deep_fall_01",
        "name": "DEEP FALL — Piso 1: Ciencias de la Tierra",
        "tile_size": TILE,
        "tileset": "res://assets/tilesets/cave.png",
        "map": build_map(),
        "player_spawn": px(3, ug),
        "camera_limits": [0, 0, COLS * TILE, ROWS * TILE],
        "waves": "res://data/waves/deep_fall_01.json",
        "boss_id": "trex",
        "tremor_period": 24.0,
        "parallax": {
            "far": "res://assets/backgrounds/cave_far.png",
            "mid": "res://assets/backgrounds/cave_mid.png",
        },
        "spawn_points": {
            # Cretácico (arriba)
            "cret1_right": px(41, ug), "cret1_left": px(19, ug), "cret1_sky": px(38, 3),
            "cret2_right": px(71, ug), "cret2_left": px(49, ug), "cret2_sky": px(66, 3),
            # Carbonífero (abajo)
            "carb_right": px(106, lg), "carb_left": px(84, lg), "carb_sky": px(100, 18),
            "carb_plant_a": px(90, lg), "carb_plant_b": px(101, lg),
            # Cámbrico
            "camb_right": px(141, lg), "camb_left": px(119, lg), "camb_sky": px(133, 18),
            "camb_mid": px(131, lg),
            # Jefe
            "boss_right": px(176 - 2, lg), "boss_left": px(156, lg),
        },
        "gates": [
            {"id": "gate_cret_1", "x": 400, "lock_left": 320, "lock_right": 640, "wave": "cret_01",
             "checkpoint": px(37, ug)},
            {"id": "gate_cret_2", "x": 880, "lock_left": 800, "lock_right": 1120, "wave": "cret_02",
             "checkpoint": px(67, ug)},
            {"id": "gate_carb", "x": 1440, "lock_left": 1360, "lock_right": 1680, "wave": "carb_01",
             "checkpoint": px(102, lg)},
            {"id": "gate_camb", "x": 2000, "lock_left": 1920, "lock_right": 2240, "wave": "camb_01",
             "checkpoint": px(137, lg)},
            {"id": "gate_boss", "x": 2560, "lock_left": 2496, "lock_right": 2816, "wave": "boss_01",
             "checkpoint": px(170, lg)},
        ],
        "pickups": [
            {"weapon": "shotgun", "pos": px(44, ug)},
            {"weapon": "heavy_machine_gun", "pos": px(80, lg)},
            {"weapon": "shotgun", "pos": px(146, lg)},
            {"weapon": "heavy_machine_gun", "pos": px(152, lg)},
        ],
        "signs": [
            {"text": "CRETÁCICO  -66 MA", "pos": px(8, ug - 4)},
            {"text": "CARBONÍFERO  -300 MA", "pos": px(82, lg - 4)},
            {"text": "CÁMBRICO  -505 MA", "pos": px(122, lg - 4)},
        ],
    }
    waves = {
        "waves": {
            "cret_01": {"clear_condition": "all_dead", "spawns": [
                {"enemy": "velociraptor", "point": "cret1_right", "delay": 0.5, "count": 3, "interval": 0.9},
                {"enemy": "nipponites", "point": "cret1_sky", "delay": 2.0, "count": 2, "interval": 1.2},
            ]},
            "cret_02": {"clear_condition": "all_dead", "spawns": [
                {"enemy": "velociraptor", "point": "cret2_right", "delay": 0.3, "count": 2, "interval": 0.9},
                {"enemy": "velociraptor", "point": "cret2_left", "delay": 2.5, "count": 1},
                {"enemy": "quetzalcoatlus", "point": "cret2_right", "delay": 4.0, "count": 1},
                {"enemy": "nipponites", "point": "cret2_sky", "delay": 5.0, "count": 2, "interval": 1.2},
            ]},
            "carb_01": {"clear_condition": "all_dead", "spawns": [
                {"enemy": "calamites", "point": "carb_plant_a", "delay": 0.0, "count": 1},
                {"enemy": "calamites", "point": "carb_plant_b", "delay": 0.0, "count": 1},
                {"enemy": "eryops", "point": "carb_right", "delay": 1.0, "count": 2, "interval": 1.5},
                {"enemy": "meganeura", "point": "carb_sky", "delay": 2.0, "count": 3, "interval": 1.0},
                {"enemy": "pulmonoscorpius", "point": "carb_left", "delay": 4.0, "count": 1},
                {"enemy": "arthropleura", "point": "carb_right", "delay": 6.0, "count": 1},
            ]},
            "camb_01": {"clear_condition": "all_dead", "spawns": [
                {"enemy": "megarachne", "point": "camb_mid", "delay": 0.0, "count": 1},
                {"enemy": "trilobites", "point": "camb_right", "delay": 0.3, "count": 4, "interval": 0.7},
                {"enemy": "marrella", "point": "camb_left", "delay": 2.0, "count": 3, "interval": 0.6},
                {"enemy": "anomalocaris", "point": "camb_sky", "delay": 3.0, "count": 2, "interval": 1.5},
                {"enemy": "hallucigenia", "point": "camb_right", "delay": 4.0, "count": 3, "interval": 0.8},
            ]},
            "boss_01": {"clear_condition": "all_dead", "spawns": [
                {"enemy": "trex", "point": "boss_right", "delay": 1.0, "count": 1},
                {"enemy": "velociraptor", "point": "boss_left", "delay": 12.0, "count": 2, "interval": 1.0},
            ]},
        }
    }
    (root / "data/levels").mkdir(parents=True, exist_ok=True)
    (root / "data/waves").mkdir(parents=True, exist_ok=True)
    (root / "data/levels/deep_fall_01.json").write_text(json.dumps(level, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "data/waves/deep_fall_01.json").write_text(json.dumps(waves, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("nivel %d×%d celdas, %d gates, %d oleadas" % (COLS, ROWS, len(level["gates"]), len(waves["waves"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
