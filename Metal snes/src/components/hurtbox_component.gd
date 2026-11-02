class_name HurtboxComponent
extends Area2D
## Dónde te pueden herir (paso 1.2). No sabe de capas: eso lo decide la escena que lo contiene.
## Se registra en el grupo "hurtboxes" para que Debug (F2) pueda dibujarlo.

signal hit_received(damage: int, source_position: Vector2)

@export var health_component: HealthComponent
@export var invulnerable: bool = false


func _ready() -> void:
	add_to_group("hurtboxes")
	if health_component == null:
		for child in get_parent().get_children():
			if child is HealthComponent:
				health_component = child
				break


func receive_hit(damage: int, source_position: Vector2) -> bool:
	if invulnerable or health_component == null:
		return false
	if not health_component.take_damage(damage):
		return false
	hit_received.emit(damage, source_position)
	return true
