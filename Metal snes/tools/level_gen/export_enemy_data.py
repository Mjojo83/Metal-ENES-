#!/usr/bin/env python3
"""Escribe data/enemies/<id>.tres (EnemyData) a partir de assets/sprites/enemies/<id>/enemy.json.

Los números de IA por criatura viven aquí (son datos de diseño, no de arte); el JSON aporta el
lienzo, la hurtbox y la ruta del SpriteFrames que generó make_enemies.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROFILE = {"advancer": 0, "static": 1, "ambush": 2, "jumper": 3, "flier": 4, "boss": 5}

# ajustes de diseño por criatura (propuesta del rol de niveles; se balancea jugando)
TUNING = {
    "velociraptor": dict(display="Velociraptor", attack_range=28, lunge_speed=170, telegraph=0.35, cooldown=1.3, detect=200),
    "trex": dict(display="Tiranosaurio TR-001", attack_range=64, lunge_speed=90, telegraph=0.6, recover=1.5, cooldown=2.6, detect=400, speed=28),
    "quetzalcoatlus": dict(display="Quetzalcoatlus", jump_velocity=-300, jump_interval=1.6, detect=220),
    "nipponites": dict(display="Nipponites", fly_height=40, attack_range=30, lunge_speed=110, cooldown=2.2, detect=200),
    "arthropleura": dict(display="Arthropleura", attack_range=34, lunge_speed=60, telegraph=0.5, cooldown=2.0, detect=220),
    "calamites": dict(display="Calamites", ranged=True, projectile_speed=95, cooldown=2.4, telegraph=0.5, detect=200),
    "eryops": dict(display="Eryops", attack_range=40, lunge_speed=130, telegraph=0.4, cooldown=1.8, detect=200),
    "meganeura": dict(display="Meganeura", fly_height=56, attack_range=28, lunge_speed=190, cooldown=1.8, detect=240),
    "megarachne": dict(display="Megarachne", detect=110, attack_range=34, lunge_speed=150, cooldown=1.4),
    "pulmonoscorpius": dict(display="Pulmonoscorpius", attack_range=32, lunge_speed=120, telegraph=0.45, cooldown=1.8, detect=200),
    "anomalocaris": dict(display="Anomalocaris", fly_height=28, attack_range=40, lunge_speed=140, cooldown=2.0, detect=200),
    "hallucigenia": dict(display="Hallucigenia", jump_velocity=-190, jump_interval=0.9, detect=180),
    "marrella": dict(display="Marrella", attack_range=20, lunge_speed=150, telegraph=0.3, cooldown=1.2, detect=220),
    "trilobites": dict(display="Trilobites", attack_range=22, lunge_speed=80, telegraph=0.4, cooldown=1.6, detect=180),
}


def tres(d: dict, t: dict) -> str:
    profile = PROFILE[d["ai_profile"]]
    hw, hh = d["hurtbox"]
    flying = d["ai_profile"] == "flier"
    body_w = max(8, int(hw * 0.6))
    body_h = max(8, int(hh * (0.9 if flying else 1.0)))
    lines = [
        '[gd_resource type="Resource" script_class="EnemyData" load_steps=3 format=3]',
        '',
        '[ext_resource type="Script" path="res://src/components/enemy_data.gd" id="1_script"]',
        '[ext_resource type="SpriteFrames" path="%s" id="2_frames"]' % d["sprite_frames"],
        '',
        '[resource]',
        'script = ExtResource("1_script")',
        'id = &"%s"' % d["id"],
        'display_name = "%s"' % t.get("display", d["display_name"]),
        'era = "%s"' % d["era"],
        'sprite_frames = ExtResource("2_frames")',
        'profile = %d' % profile,
        'max_health = %d' % d["health"],
        'speed = %.1f' % float(t.get("speed", d["speed"])),
        'score = %d' % d["score"],
        'contact_damage = %d' % d["damage"],
        'hurtbox_size = Vector2(%d, %d)' % (hw, hh),
        'body_size = Vector2(%d, %d)' % (body_w, body_h),
        'sprite_cell = Vector2i(%d, %d)' % tuple(d["cell"]),
        'flying = %s' % ("true" if flying else "false"),
        'fly_height = %.1f' % float(t.get("fly_height", 48)),
        'detect_range = %.1f' % float(t.get("detect", 180)),
        'stop_distance = %.1f' % float(t.get("stop_distance", 0)),
        'attack_range = %.1f' % float(t.get("attack_range", hw / 2 + 14)),
        'attack_cooldown = %.2f' % float(t.get("cooldown", 1.6)),
        'telegraph_time = %.2f' % float(t.get("telegraph", 0.4)),
        'recover_time = %.2f' % float(t.get("recover", 0.6)),
        'lunge_speed = %.1f' % float(t.get("lunge_speed", float(d["speed"]) * 2)),
        'jump_velocity = %.1f' % float(t.get("jump_velocity", -220)),
        'jump_interval = %.2f' % float(t.get("jump_interval", 1.2)),
        'ranged = %s' % ("true" if t.get("ranged") else "false"),
        'projectile_speed = %.1f' % float(t.get("projectile_speed", 120)),
        'hit_sound = &"hit"',
        'die_sound = &"%s"' % ("roar" if d["id"] == "trex" else "enemy_die"),
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    args = p.parse_args(argv)
    root = Path(args.root)
    out = root / "data/enemies"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for js in sorted((root / "assets/sprites/enemies").glob("*/enemy.json")):
        d = json.loads(js.read_text(encoding="utf-8"))
        (out / f"{d['id']}.tres").write_text(tres(d, TUNING.get(d["id"], {})), encoding="utf-8")
        n += 1
    print(f"{n} EnemyData escritos en {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
