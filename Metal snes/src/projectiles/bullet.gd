extends Area2D
## Bala genérica de jugador, fase 0 (paso 0.8). Sin pooling todavía —eso es fase 1.4—,
## así que se instancia y se libera con queue_free(); el conteo de nodos se vigila con el
## depurador para detectar fugas mientras tanto.

const OFFSCREEN_MARGIN := 32.0

var direction: Vector2 = Vector2.RIGHT
var speed: float = 350.0
var damage: int = 1


func setup(dir: Vector2, bullet_speed: float, bullet_damage: int = 1) -> void:
	direction = dir
	speed = bullet_speed
	damage = bullet_damage
	rotation = dir.angle()


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _physics_process(delta: float) -> void:
	global_position += direction * speed * delta

	# Fase 0: todavía no hay Camera2D (llega en 1.6), así que el límite de pantalla
	# es directamente el viewport interno de 320x224.
	var size := get_viewport_rect().size
	if global_position.x < -OFFSCREEN_MARGIN or global_position.x > size.x + OFFSCREEN_MARGIN \
			or global_position.y < -OFFSCREEN_MARGIN or global_position.y > size.y + OFFSCREEN_MARGIN:
		queue_free()


func _on_body_entered(body: Node) -> void:
	if body.is_in_group("enemies") and body.has_method("take_damage"):
		body.take_damage(damage)
	queue_free()
