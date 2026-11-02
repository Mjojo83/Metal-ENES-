extends Node2D
## Fase 0, paso 0.6 — comprobación automatizada de las cinco técnicas de salto.
## Corre como parte de un árbol de escena real (physics engine real, 60 Hz fijo), no como
## simulación matemática aparte. Coyote time y buffer fuerzan directamente variables internas
## del jugador para aislar cada técnica de forma determinista sin depender de la geometría
## exacta de una plataforma — mismo espíritu que un test unitario, con ventanas de tolerancia
## de varios frames en vez de comparar frame a frame exacto (is_on_floor() refleja el estado
## del último move_and_slide(), con un frame de desfase inherente).

@onready var player: CharacterBody2D = $Player

var frame := 0
var stage := 0
var stage_frame := 0
var all_ok := true
var start_y: float

var min_y_stage1 := 0.0
var apex_frame_stage1 := -1
var land_frame_stage1 := -1
var was_airborne_stage1 := false

var min_y_stage2 := 0.0

var jumped_stage3 := false
var jumped_immediately_stage4 := false
var jumped_eventually_stage4 := false


func _ready() -> void:
	start_y = player.global_position.y


func _ok(label: String, cond: bool, detail: String = "") -> void:
	if not cond:
		all_ok = false
	print("%s -> %s %s" % [label, "OK" if cond else "FALLO", detail])


func _reset_player() -> void:
	Input.action_release("jump")
	player.global_position = Vector2(player.global_position.x, start_y)
	player.velocity = Vector2.ZERO
	player.phys_state = player.PhysState.GROUND
	player.coyote_timer = 0.0
	player.jump_buffer_timer = 0.0


func _physics_process(_delta: float) -> void:
	frame += 1
	stage_frame += 1

	match stage:
		0:  # asentarse en el piso
			if stage_frame >= 5:
				min_y_stage1 = player.global_position.y
				stage = 1
				stage_frame = 0

		1:  # salto completo, sin soltar hasta bien despues del apice
			if stage_frame == 1:
				Input.action_press("jump")
			if stage_frame == 50:
				Input.action_release("jump")
			min_y_stage1 = min(min_y_stage1, player.global_position.y)
			if not player.is_on_floor():
				was_airborne_stage1 = true
			if was_airborne_stage1 and player.velocity.y >= 0.0 and apex_frame_stage1 == -1:
				apex_frame_stage1 = stage_frame
			if was_airborne_stage1 and player.is_on_floor() and land_frame_stage1 == -1 and stage_frame > 2:
				land_frame_stage1 = stage_frame
			if land_frame_stage1 != -1 and stage_frame >= land_frame_stage1 + 3:
				var height := start_y - min_y_stage1
				var rise_frames := apex_frame_stage1
				var fall_frames := land_frame_stage1 - apex_frame_stage1
				_ok("0.6a altura de salto completo (~47px)", height > 30.0 and height < 65.0, "altura=%.1fpx" % height)
				_ok("0.6d gravedad asimétrica (bajada más rápida que subida)", fall_frames < rise_frames, "subida=%df bajada=%df" % [rise_frames, fall_frames])
				_reset_player()
				stage = 2
				stage_frame = 0

		2:  # jump cut: soltar el boton casi de inmediato
			if stage_frame == 1:
				Input.action_press("jump")
				min_y_stage2 = player.global_position.y
			if stage_frame == 3:
				Input.action_release("jump")
			min_y_stage2 = min(min_y_stage2, player.global_position.y)
			if player.is_on_floor() and stage_frame > 12:
				var height_full := start_y - min_y_stage1
				var height_cut := start_y - min_y_stage2
				_ok("0.6b jump cut (soltar acorta el salto)", height_cut < height_full * 0.75, "completo=%.1fpx cortado=%.1fpx" % [height_full, height_cut])
				_reset_player()
				stage = 3
				stage_frame = 0

		3:  # coyote time: se fuerza al jugador al aire (como si acabara de dejar el suelo)
			# y se salta poco despues, dentro de la ventana de coyote time.
			if stage_frame == 1:
				player.global_position.y = start_y - 20.0
				player.velocity = Vector2.ZERO
			if stage_frame == 3:
				Input.action_press("jump")
			if stage_frame >= 4 and stage_frame <= 8 and player.velocity.y < -200.0:
				jumped_stage3 = true
			if stage_frame == 9:
				_ok("0.6c coyote time (saltar poco después de dejar el suelo)", jumped_stage3)
				_reset_player()
				stage = 4
				stage_frame = 0

		4:  # buffer de entrada: se presiona salto en el aire, bien despues de que expiro el
			# coyote time, y debe ejecutarse igual al aterrizar (no antes).
			if stage_frame == 1:
				player.global_position.y = start_y - 30.0
				player.velocity = Vector2.ZERO
			if stage_frame == 9:
				Input.action_press("jump")
			if stage_frame == 10 and player.velocity.y < -200.0:
				jumped_immediately_stage4 = true
			if stage_frame > 10 and stage_frame <= 30 and player.velocity.y < -200.0:
				jumped_eventually_stage4 = true
			if stage_frame == 30:
				_ok("0.6e buffer no dispara salto antes de tiempo (coyote ya expiró)", not jumped_immediately_stage4)
				_ok("0.6e buffer de entrada (salta al aterrizar, sin volver a presionar)", jumped_eventually_stage4)
				stage = 5
				stage_frame = 0

		5:
			print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
			get_tree().quit()
