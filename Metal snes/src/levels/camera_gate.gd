class_name CameraGate
extends Area2D
## Camera gate (paso 1.7): al cruzarlo el jugador la cámara se encierra en [lock_left, lock_right]
## y arranca la oleada. Al limpiarse, se sueltan los límites y se fija un checkpoint. Si el jugador
## muere a media oleada, el gate se rearma (vuelve a disparar al cruzarlo otra vez).

@export var gate_id: StringName = &"gate"
@export var lock_left: float = 0.0
@export var lock_right: float = 320.0
@export var wave_id: StringName = &""
@export var checkpoint: Vector2 = Vector2.ZERO

var triggered: bool = false
var cleared: bool = false


func _ready() -> void:
	add_to_group("gates")
	collision_layer = Layers.TRIGGERS
	collision_mask = Layers.PLAYER_BODY
	body_entered.connect(_on_body_entered)
	Events.wave_cleared.connect(_on_wave_cleared)
	Events.player_died.connect(_on_player_died)


func _on_body_entered(body: Node) -> void:
	if triggered or cleared or not body.is_in_group("player"):
		return
	triggered = true
	Events.camera_lock_requested.emit(lock_left, lock_right)
	if wave_id != &"":
		Events.wave_started.emit(wave_id)
	else:
		_clear()


func _on_wave_cleared(id: StringName) -> void:
	if triggered and not cleared and id == wave_id:
		_clear()


func _clear() -> void:
	cleared = true
	Events.camera_unlock_requested.emit()
	if checkpoint != Vector2.ZERO:
		Events.checkpoint_reached.emit(checkpoint)
	AudioManager.play(&"wave_clear", -4.0)


func _on_player_died() -> void:
	if triggered and not cleared:
		triggered = false
		Events.camera_unlock_requested.emit()
