class_name HealthComponent
extends Node
## Lleva la cuenta de la vida (paso 1.2). Los i-frames se descuentan en el tick de física para que
## "60 frames" sea exactamente un segundo en cualquier máquina (ADR-007).

signal health_changed(current: int, max_health: int)
signal died

@export var max_health: int = 3
@export var iframe_duration: float = 0.0

var health: int = 0
var iframes: float = 0.0
var dead: bool = false


func _ready() -> void:
	health = max_health


func _physics_process(delta: float) -> void:
	if iframes > 0.0:
		iframes = maxf(iframes - delta, 0.0)


func is_invulnerable() -> bool:
	return iframes > 0.0


func take_damage(amount: int) -> bool:
	## Devuelve true si el daño se aplicó (no estaba muerto ni en i-frames).
	if dead or iframes > 0.0 or amount <= 0:
		return false
	health = maxi(health - amount, 0)
	iframes = iframe_duration
	health_changed.emit(health, max_health)
	if health == 0:
		dead = true
		died.emit()
	return true


func heal(amount: int) -> void:
	if dead:
		return
	health = mini(health + amount, max_health)
	health_changed.emit(health, max_health)


func reset(grace: float = 0.0) -> void:
	dead = false
	health = max_health
	iframes = grace
	health_changed.emit(health, max_health)
