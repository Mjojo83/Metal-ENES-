extends Node2D
## Fase 0, paso 0.7 — tabla de direcciones de apuntado por estado. Prueba directa de
## get_aim_direction() forzando phys_state y simulando Input, sin necesidad de física real.

@onready var player: CharacterBody2D = $Player

var all_ok := true


func _ok(label: String, cond: bool, detail: String = "") -> void:
	if not cond:
		all_ok = false
	print("%s -> %s %s" % [label, "OK" if cond else "FALLO", detail])


func _press_only(actions: Array[String]) -> void:
	for a in ["move_left", "move_right", "aim_up", "aim_down"]:
		if a in actions:
			Input.action_press(a)
		else:
			Input.action_release(a)


func _check(label: String, phys_state, facing: int, actions: Array[String], expected: Vector2) -> void:
	player.phys_state = phys_state
	player.facing = facing
	_press_only(actions)
	var got: Vector2 = player.get_aim_direction()
	_ok(label, got.is_equal_approx(expected), "obtuvo=%s esperado=%s" % [got, expected])


func _ready() -> void:
	var S = player.PhysState

	# De pie, quieto: horizontal (facing) o arriba si se sostiene aim_up.
	_check("0.7 de pie quieto, sin input -> horizontal (facing der.)", S.GROUND, 1, [], Vector2(1, 0))
	_check("0.7 de pie quieto, sin input -> horizontal (facing izq.)", S.GROUND, -1, [], Vector2(-1, 0))
	_check("0.7 de pie quieto + aim_up -> arriba", S.GROUND, 1, ["aim_up"], Vector2(0, -1))

	# Corriendo: solo horizontal, incluso si se sostiene aim_up (no se puede apuntar arriba corriendo).
	_check("0.7 corriendo -> horizontal, ignora aim_up", S.GROUND, 1, ["move_right", "aim_up"], Vector2(1, 0))
	_check("0.7 corriendo izq. -> horizontal (facing izq.)", S.GROUND, -1, ["move_left"], Vector2(-1, 0))

	# Agachado: horizontal solamente.
	_check("0.7 agachado -> horizontal", S.CROUCH, 1, ["aim_up", "aim_down"], Vector2(1, 0))

	# Boca abajo: horizontal solamente.
	_check("0.7 boca abajo -> horizontal", S.PRONE, -1, [], Vector2(-1, 0))

	# En el aire: 8 direcciones.
	_check("0.7 aire, sin input -> horizontal (facing)", S.AIR, 1, [], Vector2(1, 0))
	_check("0.7 aire + aim_up, sin horizontal -> arriba puro", S.AIR, 1, ["aim_up"], Vector2(0, -1))
	_check("0.7 aire + aim_down, sin horizontal -> abajo puro", S.AIR, 1, ["aim_down"], Vector2(0, 1))
	_check("0.7 aire + move_right + aim_up -> diagonal arriba-der.", S.AIR, 1, ["move_right", "aim_up"], Vector2(1, -1).normalized())
	_check("0.7 aire + move_left + aim_down -> diagonal abajo-izq.", S.AIR, -1, ["move_left", "aim_down"], Vector2(-1, 1).normalized())
	_check("0.7 aire + move_right -> horizontal", S.AIR, 1, ["move_right"], Vector2(1, 0))

	for a in ["move_left", "move_right", "aim_up", "aim_down"]:
		Input.action_release(a)

	print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
	get_tree().quit()
