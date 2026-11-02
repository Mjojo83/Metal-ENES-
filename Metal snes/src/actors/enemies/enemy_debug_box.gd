extends CharacterBody2D
## Enemigo "caja que muere" de la fase 0 (paso 0.9), ahora ensamblado con los componentes de la
## fase 1.2 (Hurtbox + Hitbox + Health) sin lógica propia más que el parpadeo y la señal.

@export var max_health: int = 3

@onready var body_visual: ColorRect = $Body
@onready var health: HealthComponent = $Health
@onready var hurtbox: HurtboxComponent = $Hurtbox


func _ready() -> void:
	add_to_group("enemies")
	health.max_health = max_health
	health.reset()
	health.died.connect(_on_died)
	hurtbox.hit_received.connect(func(_d: int, _p: Vector2) -> void: _flash())


func take_damage(amount: int) -> void:
	hurtbox.receive_hit(amount, global_position)


func _flash() -> void:
	body_visual.modulate = Color(3, 3, 3)
	var tween := create_tween()
	tween.tween_property(body_visual, "modulate", Color(1, 1, 1), 0.1)


func _on_died() -> void:
	Events.enemy_killed.emit(&"debug_box", global_position)
	queue_free()
