class_name HitboxComponent
extends Area2D
## Causa daño a las HurtboxComponent con las que se solapa (paso 1.2). Para contacto de
## enemigos, melee y proyectiles enemigos. Se registra en el grupo "hitboxes" para Debug (F2).

signal hit_landed(hurtbox: HurtboxComponent)

@export var damage: int = 1
@export var knockback: float = 0.0
@export var one_shot: bool = false
@export var active: bool = true


func _ready() -> void:
	add_to_group("hitboxes")
	area_entered.connect(_on_area_entered)


func _on_area_entered(area: Area2D) -> void:
	if not active:
		return
	var hurtbox := area as HurtboxComponent
	if hurtbox == null:
		return
	if hurtbox.receive_hit(damage, global_position):
		hit_landed.emit(hurtbox)
		if one_shot:
			set_deferred("monitoring", false)


func pulse() -> void:
	## Vuelve a comprobar solapes ya existentes (un enemigo quieto encima del jugador que reaparece).
	if not monitoring:
		return
	for area in get_overlapping_areas():
		_on_area_entered(area)
