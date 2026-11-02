extends CharacterBody2D
## Enemigo "caja que muere" de la fase 0 (paso 0.9). Sin IA todavía —los perfiles llegan en la
## fase 1.9— y sin HurtboxComponent/HitboxComponent —esos llegan en la fase 1.2—, así que la
## vida vive directamente en este script como placeholder.

@export var max_health: int = 3

var health: int

@onready var body_visual: ColorRect = $Body


func _ready() -> void:
	health = max_health
	add_to_group("enemies")


func take_damage(amount: int) -> void:
	health -= amount
	_flash()
	if health <= 0:
		Events.enemy_killed.emit(&"debug_box", global_position)
		queue_free()


func _flash() -> void:
	body_visual.modulate = Color(3, 3, 3)
	var tween := create_tween()
	tween.tween_property(body_visual, "modulate", Color(1, 1, 1), 0.1)
