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
