# Corre todas las comprobaciones headless y resume. Uso (PowerShell, en la carpeta del proyecto):
#   .\run_all_checks.ps1 -Godot "O:\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe"
param([string]$Godot = "godot")
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Importando recursos (primera vez tarda)..."
& $Godot --headless --path $here --import 2>&1 | Out-Null
$scripts = @("check_project_settings.gd", "check_input_map.gd", "check_collision_layers.gd")
$scenes = @("check_autoloads.tscn", "check_player_movement.tscn", "check_player_jump.tscn", "check_aim_directions.tscn",
    "check_shooting_and_enemy.tscn", "check_death_respawn.tscn", "check_damage_components.tscn", "check_weapons.tscn",
    "check_camera_gate_wave.tscn", "check_enemy_profiles.tscn", "check_pools_and_data.tscn")
$fail = 0
foreach ($s in $scripts) {
    $out = & $Godot --headless --path $here --script "res://src/debug/$s" 2>&1 | Out-String
    $ok = $out -match "RESULTADO: PASS"
    if (-not $ok) { $fail++ }
    Write-Host ("{0,-34} {1}" -f $s, $(if ($ok) { "PASS" } else { "FAIL" }))
    if (-not $ok) { Write-Host $out }
}
foreach ($s in $scenes) {
    $out = & $Godot --headless --path $here "res://src/debug/$s" 2>&1 | Out-String
    $ok = $out -match "RESULTADO: PASS"
    if (-not $ok) { $fail++ }
    Write-Host ("{0,-34} {1}" -f $s, $(if ($ok) { "PASS" } else { "FAIL" }))
    if (-not $ok) { Write-Host $out }
}
Write-Host ("`n{0} comprobaciones, {1} fallaron" -f ($scripts.Count + $scenes.Count), $fail)
exit $fail
