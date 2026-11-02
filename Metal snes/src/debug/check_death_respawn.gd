extends Node2D
## Fase 0, paso 0.10 — muerte y respawn. Primero un ciclo real (el enemigo toca al jugador de
## verdad, vía HurtAreaTmp), después cinco ciclos rápidos seguidos para probar que no hay
## fugas ni estados corruptos (criterio de cierre del Hito 0).

@onready var player: CharacterBody2D = $Player

var frame := 0
var stage := 0
var stage_frame := 0
var all_ok := true

var enemy: CharacterBody2D
var enemy_scene: PackedScene = preload("res://src/actors/enemies/enemy_debug_box.tscn")

var died_count := 0
var respawned_count := 0
var rapid_cycle := 0
var waiting_for_respawn := false


func _ok(label: String, cond: bool, detail: String = "") -> void:
	if not cond:
		all_ok = false
	print("%s -> %s %s" % [label, "OK" if cond else "FALLO", detail])


func _ready() -> void:
	Events.player_died.connect(func(): died_count += 1)
	Events.player_respawned.connect(func(): respawned_count += 1)
	enemy = enemy_scene.instantiate()
	add_child(enemy)
	enemy.global_position = Vector2(-1000, -1000)  # lejos, no toca al jugador todavía


func _physics_process(_delta: float) -> void:
	frame += 1
	stage_frame += 1

	match stage:
		0:  # asentarse
			if stage_frame >= 3:
				stage = 1
				stage_frame = 0

		1:  # ciclo real: el enemigo se mueve encima del jugador -> debe morir
			if stage_frame == 1:
				enemy.global_position = player.global_position
			if stage_frame == 5:
				_ok("0.10 tocar a un enemigo mata al jugador", player.is_dead and player.collision.disabled, "is_dead=%s collision.disabled=%s" % [player.is_dead, player.collision.disabled])
				_ok("0.10 Events.player_died se emite", died_count == 1, "died_count=%d" % died_count)
				enemy.global_position = Vector2(-1000, -1000)  # lo quitamos del camino
			if stage_frame == 75:  # ~1s de espera de respawn + margen
				_ok("0.10 respawnea ~1s después, en el punto de spawn", not player.is_dead and not player.collision.disabled and player.global_position.is_equal_approx(player.spawn_position), "pos=%s spawn=%s" % [player.global_position, player.spawn_position])
				_ok("0.10 Events.player_respawned se emite", respawned_count == 1, "respawned_count=%d" % respawned_count)
				stage = 2
				stage_frame = 0

		2:  # cinco ciclos rapidos seguidos (llamada directa a _die(), la ruta de deteccion
			# por colision ya quedó comprobada en la etapa 1)
			if not waiting_for_respawn and rapid_cycle < 5:
				player._die()
				rapid_cycle += 1
				waiting_for_respawn = true
			if waiting_for_respawn and not player.is_dead and respawned_count == rapid_cycle + 1:
				waiting_for_respawn = false
			if rapid_cycle >= 5 and not waiting_for_respawn:
				var players_in_scene := 0
				for child in get_children():
					if child == player or (is_instance_valid(child) and child.has_method("get_aim_direction")):
						players_in_scene += 1
				_ok("0.10 cinco muertes rápidas: sin crash, sigue habiendo un solo jugador", is_instance_valid(player) and players_in_scene == 1, "jugadores=%d" % players_in_scene)
				_ok("0.10 cinco muertes rápidas: terminó en estado consistente", not player.is_dead and not player.collision.disabled)
				_ok("0.10 cinco muertes rápidas: respawnea siempre en spawn_position", player.global_position.is_equal_approx(player.spawn_position))
				stage = 3
				stage_frame = 0

		3:
			print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
			get_tree().quit()
