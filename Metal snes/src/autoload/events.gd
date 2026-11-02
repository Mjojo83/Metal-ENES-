extends Node
## Bus de señales global. Solo señales, cero lógica — ver docs/01_Arquitectura_Tecnica.docx,
## paso 0.4. Úsalo solo para eventos que le interesan a tres o más sistemas distintos; para
## comunicación padre-hijo, usa señales normales del nodo.

signal player_died
signal player_respawned
signal enemy_killed(enemy_type: StringName, position: Vector2)
signal boss_phase_changed(phase: int)
signal wave_started(wave_id: StringName)
signal wave_cleared(wave_id: StringName)
signal camera_lock_requested(left: float, right: float)
signal camera_unlock_requested
signal weapon_picked_up(weapon_id: StringName)
signal hostage_rescued(hostage_id: StringName)
signal score_changed(new_score: int)

# Fase 1 (sistemas core)
signal weapon_changed(weapon: WeaponData, ammo: int)
signal ammo_changed(ammo: int)
signal lives_changed(lives: int, continues: int)
signal player_hit
signal boss_health_changed(current: int, max_health: int)
signal checkpoint_reached(position: Vector2)
signal level_cleared
signal game_over
signal tremor_started(intensity: float)
signal screenshake_requested(amount: float)
signal hitstop_requested(frames: int)
signal debug_give_weapon
signal debug_spawn_enemy(position: Vector2)
