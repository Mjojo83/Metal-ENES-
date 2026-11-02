extends Node2D
## Fase 0, paso 0.5 — movimiento horizontal: acelera hasta MOVE_SPEED, frena rápido pero no
## de golpe al soltar, y cruza la pantalla (320px) en ~3.2s (320 / 100 px/s).

@onready var player: CharacterBody2D = $Player

var frame := 0
var stage := 0
var stage_frame := 0
var all_ok := true
var start_x: float
var reached_top_speed := false
var speed_after_release_1_frame := 0.0
var cross_frames := -1


func _ok(label: String, cond: bool, detail: String = "") -> void:
	if not cond:
		all_ok = false
	print("%s -> %s %s" % [label, "OK" if cond else "FALLO", detail])


func _ready() -> void:
	start_x = player.global_position.x


func _physics_process(_delta: float) -> void:
	frame += 1
	stage_frame += 1

	match stage:
		0:  # aceleracion: sostener move_right y medir cuanto tarda en llegar a MOVE_SPEED
			if stage_frame == 1:
				Input.action_press("move_right")
			if player.velocity.x >= player.MOVE_SPEED - 1.0:
				reached_top_speed = true
			if stage_frame == 20:
				_ok("0.5 alcanza MOVE_SPEED (~100px/s) sosteniendo move_right", reached_top_speed, "velocity.x=%.1f" % player.velocity.x)
				stage = 1
				stage_frame = 0

		1:  # frenado: soltar y verificar que NO es instantaneo pero SI es rapido
			if stage_frame == 1:
				Input.action_release("move_right")
				speed_after_release_1_frame = player.velocity.x
			if stage_frame == 2:
				var not_instant := player.velocity.x > 1.0  # todavia se mueve un frame despues
				_ok("0.5 no se detiene instantáneamente al soltar", not_instant, "velocity.x=%.1f" % player.velocity.x)
			if stage_frame == 8:  # a 1600 px/s^2 de friccion, desde 100px/s tarda ~0.0625s (~4 ticks)
				var stopped: bool = abs(player.velocity.x) < 5.0
				_ok("0.5 se detiene rápido (dentro de ~8 frames)", stopped, "velocity.x=%.1f" % player.velocity.x)
				player.global_position.x = start_x
				player.velocity = Vector2.ZERO
				stage = 2
				stage_frame = 0

		2:  # cruzar la pantalla (320px) en ~3.2s (~192 ticks a 60hz)
			if stage_frame == 1:
				Input.action_press("move_right")
			if player.global_position.x - start_x >= 320.0 and cross_frames == -1:
				cross_frames = stage_frame
			if cross_frames != -1 or stage_frame >= 250:
				Input.action_release("move_right")
				var expected: float = 320.0 / player.MOVE_SPEED * 60.0  # ~192 ticks
				var within_range: bool = cross_frames != -1 and abs(cross_frames - expected) < expected * 0.15
				_ok("0.5 cruza 320px en ~3.2s (~192 frames)", within_range, "frames=%d esperado=%.0f" % [cross_frames, expected])
				stage = 3
				stage_frame = 0

		3:
			print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
			get_tree().quit()
