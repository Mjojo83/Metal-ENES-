#!/usr/bin/env bash
# Corre todas las comprobaciones headless (Linux/macOS). Uso: ./run_all_checks.sh /ruta/a/godot
set -u
GODOT="${1:-godot}"
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "Importando recursos (la primera vez tarda)..."
"$GODOT" --headless --path "$HERE" --import >/dev/null 2>&1
fail=0; total=0
run() {  # $1 = PASS/FAIL etiqueta, resto = comando
  local name="$1"; shift
  total=$((total+1))
  out="$("$@" 2>&1)"
  if grep -q "RESULTADO: PASS" <<<"$out"; then printf '%-34s PASS\n' "$name"; else printf '%-34s FAIL\n' "$name"; echo "$out"; fail=$((fail+1)); fi
}
for s in check_project_settings.gd check_input_map.gd check_collision_layers.gd; do
  run "$s" "$GODOT" --headless --path "$HERE" --script "res://src/debug/$s"
done
for s in check_autoloads.tscn check_player_movement.tscn check_player_jump.tscn check_aim_directions.tscn \
         check_shooting_and_enemy.tscn check_death_respawn.tscn check_damage_components.tscn check_weapons.tscn \
         check_camera_gate_wave.tscn check_enemy_profiles.tscn check_pools_and_data.tscn; do
  run "$s" "$GODOT" --headless --path "$HERE" "res://src/debug/$s"
done
echo; echo "$total comprobaciones, $fail fallaron"
exit $fail
