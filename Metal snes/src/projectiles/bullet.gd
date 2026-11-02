class_name Bullet
extends Area2D
## Bala del jugador (paso 0.8 + 1.4). Vive en el pool: `launch()` la activa y `Pools.release()`
## la guarda. Pega a HurtboxComponent (capa enemy_hurtbox) y al terreno; muere por distancia
## recorrida, no por el viewport (con Camera2D el viewport ya no es el mundo).

const DEFAULT_RANGE := 400.0

var direction: Vector2 = Vector2.RIGHT
var speed: float = 350.0
var damage: int = 1
var max_distance: float = DEFAULT_RANGE
var travelled: float = 0.0
var shooter: Node2D = null

@onready var sprite: Sprite2D = $Sprite


func _ready() -> void:
	area_entered.connect(_on_area_entered)
	body_entered.connect(_on_body_entered)


func launch(origin: Vector2, dir: Vector2, weapon: WeaponData, from: Node2D = null) -> void:
	global_position = origin
	direction = dir.normalized()
	speed = weapon.projectile_speed
	damage = weapon.damage
	max_distance = weapon.projectile_range
	travelled = 0.0
	shooter = from
	rotation = direction.angle()
	if weapon.bullet_texture != null:
		sprite.texture = weapon.bullet_texture


func setup(dir: Vector2, bullet_speed: float, bullet_damage: int = 1) -> void:
	## Compatibilidad con la fase 0: bala suelta sin WeaponData.
	direction = dir.normalized()
	speed = bullet_speed
	damage = bullet_damage
	max_distance = DEFAULT_RANGE
	travelled = 0.0
	rotation = direction.angle()


func _physics_process(delta: float) -> void:
	var step := direction * speed * delta
	global_position += step
	travelled += step.length()
	if travelled > max_distance:
		_despawn()


func _on_area_entered(area: Area2D) -> void:
	var hurtbox := area as HurtboxComponent
	if hurtbox == null:
		return
	if hurtbox.receive_hit(damage, global_position):
		_impact(true)


func _on_body_entered(body: Node) -> void:
	# compatibilidad fase 0: cuerpos del grupo "enemies" con take_damage() y sin hurtbox
	if body.is_in_group("enemies") and body.has_method("take_damage") and not _has_hurtbox(body):
		body.take_damage(damage)
	_impact(false)


func _has_hurtbox(node: Node) -> bool:
	for child in node.get_children():
		if child is HurtboxComponent:
			return true
	return false


func _impact(hit_enemy: bool) -> void:
	var vfx := Pools.acquire(&"vfx")
	if vfx != null and vfx.has_method("play_effect"):
		vfx.play_effect(&"hit_spark", global_position)
	if hit_enemy:
		AudioManager.play(&"hit", -6.0)
	_despawn()


func _despawn() -> void:
	if has_meta("pool_key"):
		Pools.release(self)
	else:
		queue_free()
