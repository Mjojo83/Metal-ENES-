class_name PlayerInput
extends Node
## Lee las acciones abstractas del InputMap y las publica para el jugador (el actor nunca toca
## Input directamente). También decide si manda el ratón: "auto" = el último dispositivo que
## generó entrada; el ratón solo apunta, el movimiento siempre es teclado o mando.

var move_axis: float = 0.0
var up_held: bool = false
var down_held: bool = false
var jump_pressed: bool = false
var jump_released: bool = false
var shoot_held: bool = false
var shoot_pressed: bool = false
var grenade_pressed: bool = false
var pause_pressed: bool = false
var mouse_active: bool = false
var mouse_world: Vector2 = Vector2.ZERO
var enabled: bool = true

var _last_mouse_ms: int = -100000
var _last_other_ms: int = 0


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion or event is InputEventMouseButton:
		_last_mouse_ms = Time.get_ticks_msec()
	elif event is InputEventKey or event is InputEventJoypadButton:
		_last_other_ms = Time.get_ticks_msec()
	elif event is InputEventJoypadMotion and absf((event as InputEventJoypadMotion).axis_value) > 0.5:
		_last_other_ms = Time.get_ticks_msec()


func poll(owner_node: Node2D) -> void:
	if not enabled:
		move_axis = 0.0
		up_held = false
		down_held = false
		jump_pressed = false
		jump_released = false
		shoot_held = false
		shoot_pressed = false
		grenade_pressed = false
		mouse_active = false
		return
	move_axis = Input.get_axis("move_left", "move_right")
	up_held = Input.is_action_pressed("aim_up")
	down_held = Input.is_action_pressed("aim_down")
	jump_pressed = Input.is_action_just_pressed("jump")
	jump_released = Input.is_action_just_released("jump")
	shoot_held = Input.is_action_pressed("shoot")
	shoot_pressed = Input.is_action_just_pressed("shoot")
	grenade_pressed = Input.is_action_just_pressed("grenade")
	pause_pressed = Input.is_action_just_pressed("pause")
	mouse_active = _mouse_mode_active()
	if mouse_active and owner_node != null and owner_node.is_inside_tree():
		mouse_world = owner_node.get_global_mouse_position()


func _mouse_mode_active() -> bool:
	var mode := String(Game.settings.get("mouse_aim", "auto"))
	if mode == "off":
		return false
	if mode == "on":
		return true
	return _last_mouse_ms > _last_other_ms and Time.get_ticks_msec() - _last_mouse_ms < 2000
