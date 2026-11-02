class_name GameCamera
extends Camera2D
## Cámara del paso 1.6 (deadzone + lookahead + límites) y los camera gates del 1.7 (lock/unlock).
## Mientras está bloqueada, empuja al jugador un muro invisible (Player.bounds).

const DEADZONE := Vector2(40.0, 24.0)
const LOOKAHEAD := 32.0
const LOOK_SMOOTH := 4.0
const VERTICAL_OFFSET := -16.0

var target: Node2D = null
var level_limits: Rect2 = Rect2(0, 0, 320, 224)
var locked: bool = false
var look: float = 0.0
var shake_amount: float = 0.0
var _rng := RandomNumberGenerator.new()
var _center: Vector2 = Vector2.ZERO
var _hitstop_until_ms: int = 0


func _ready() -> void:
	add_to_group("game_camera")
	position_smoothing_enabled = false
	Events.camera_lock_requested.connect(lock)
	Events.camera_unlock_requested.connect(unlock)
	Events.screenshake_requested.connect(shake)
	Events.hitstop_requested.connect(hitstop)
	set_level_limits(level_limits)
	_center = global_position


func set_level_limits(rect: Rect2) -> void:
	level_limits = rect
	if not locked:
		_apply_limits(rect.position.x, rect.end.x)
	limit_top = int(rect.position.y)
	limit_bottom = int(rect.end.y)


func _apply_limits(left: float, right: float) -> void:
	limit_left = int(left)
	limit_right = int(right)
	var player := get_tree().get_first_node_in_group("player") if is_inside_tree() else null
	if player != null:
		player.set("bounds", Vector2(left, right))


func lock(left: float, right: float) -> void:
	locked = true
	_apply_limits(left, right)
	AudioManager.play(&"gate_lock", -6.0)


func unlock() -> void:
	locked = false
	_apply_limits(level_limits.position.x, level_limits.end.x)


func shake(amount: float) -> void:
	if not bool(Game.settings.get("screenshake", true)):
		return
	shake_amount = maxf(shake_amount, minf(amount, 4.0))


func hitstop(frames: int) -> void:
	## Pausa casi total de 'frames' cuadros (a 60 Hz) medida en tiempo real, porque con
	## time_scale bajo los ticks de física casi no corren y un contador de ticks nunca llegaría.
	_hitstop_until_ms = maxi(_hitstop_until_ms, Time.get_ticks_msec() + frames * 16)


func _process(_delta: float) -> void:
	if Time.get_ticks_msec() < _hitstop_until_ms:
		Engine.time_scale = 0.05
	elif Engine.time_scale != 1.0:
		Engine.time_scale = 1.0


func _physics_process(delta: float) -> void:
	if target == null or not is_instance_valid(target):
		target = get_tree().get_first_node_in_group("player") as Node2D
		if target == null:
			return
		_center = target.global_position + Vector2(0.0, VERTICAL_OFFSET)
	var goal := target.global_position + Vector2(0.0, VERTICAL_OFFSET)
	var dx := goal.x - _center.x
	if absf(dx) > DEADZONE.x / 2.0:
		_center.x += dx - signf(dx) * DEADZONE.x / 2.0
	var dy := goal.y - _center.y
	if absf(dy) > DEADZONE.y / 2.0:
		_center.y += dy - signf(dy) * DEADZONE.y / 2.0
	var facing := int(target.get("facing")) if target.get("facing") != null else 1
	var moving := absf(float((target.get("velocity") as Vector2).x)) > 10.0 if target.get("velocity") != null else false
	look = lerpf(look, (facing * LOOKAHEAD) if moving else look, minf(LOOK_SMOOTH * delta, 1.0))
	var pos := _center + Vector2(look, 0.0)
	# clamp manual (además de los límites de Camera2D) para que el lookahead no asome fuera
	var half := get_viewport_rect().size / 2.0
	pos.x = clampf(pos.x, limit_left + half.x, maxf(limit_right - half.x, limit_left + half.x))
	pos.y = clampf(pos.y, limit_top + half.y, maxf(limit_bottom - half.y, limit_top + half.y))
	global_position = pos.round()
	if shake_amount > 0.05:
		offset = Vector2(_rng.randf_range(-1.0, 1.0), _rng.randf_range(-1.0, 1.0)).round() * shake_amount
		shake_amount *= 0.82
	else:
		shake_amount = 0.0
		offset = Vector2.ZERO
