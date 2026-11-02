class_name EnemyBullet
extends Area2D
## Proyectil enemigo (esporas de Calamites, etc.). Capa enemy_hitbox, pega a la hurtbox del jugador
## y al terreno. Pooled.

var direction: Vector2 = Vector2.LEFT
var speed: float = 120.0
var damage: int = 1
var life: float = 0.0
var max_life: float = 4.0
var _anim_t: float = 0.0

@onready var sprite: Sprite2D = $Sprite


func _ready() -> void:
	area_entered.connect(_on_area_entered)
	body_entered.connect(_on_body_entered)


func launch(origin: Vector2, dir: Vector2, bullet_speed: float, bullet_damage: int = 1) -> void:
	global_position = origin
	direction = dir.normalized()
	speed = bullet_speed
	damage = bullet_damage
	life = 0.0
	_anim_t = 0.0


func _physics_process(delta: float) -> void:
	global_position += direction * speed * delta
	life += delta
	_anim_t += delta
	sprite.frame = int(_anim_t * 8.0) % maxi(sprite.hframes, 1)
	if life > max_life:
		_despawn()


func _on_area_entered(area: Area2D) -> void:
	var hurtbox := area as HurtboxComponent
	if hurtbox != null and hurtbox.receive_hit(damage, global_position):
		_despawn()


func _on_body_entered(_body: Node) -> void:
	_despawn()


func _despawn() -> void:
	if has_meta("pool_key"):
		Pools.release(self)
	else:
		queue_free()
