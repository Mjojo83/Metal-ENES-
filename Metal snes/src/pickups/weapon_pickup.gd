class_name WeaponPickup
extends Area2D
## Caja de arma. Al tocarla el jugador la equipa (reemplaza la actual: nada de inventario,
## sección 5.3) y suena el grito del arma.

@export var weapon: WeaponData

@onready var sprite: Sprite2D = $Sprite

var _t: float = 0.0
var _base_y: float = 0.0


func _ready() -> void:
	add_to_group("pickups")
	collision_layer = Layers.PICKUPS
	collision_mask = Layers.PLAYER_BODY
	body_entered.connect(_on_body_entered)
	if weapon != null and weapon.pickup_texture != null:
		sprite.texture = weapon.pickup_texture
	_base_y = sprite.position.y


func _process(delta: float) -> void:
	_t += delta
	sprite.position.y = _base_y + roundf(sin(_t * 3.0) * 1.5)


func _on_body_entered(body: Node) -> void:
	if weapon == null or not body.is_in_group("player") or not body.has_method("pick_weapon"):
		return
	body.pick_weapon(weapon)
	Events.weapon_picked_up.emit(weapon.id)
	AudioManager.play(&"pickup")
	set_deferred("monitoring", false)
	queue_free()
