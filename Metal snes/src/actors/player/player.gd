extends CharacterBody2D
## Jugador, fase 0 (pasos 0.5-0.8 y 0.10). Todavía sin StateMachine formal —eso es fase 1.3—,
## así que el estado vive en un enum simple dentro de este mismo script.

const MOVE_SPEED := 100.0
const ACCEL_GROUND := 1200.0
const FRICTION_GROUND := 1600.0
const ACCEL_AIR := 700.0
const FRICTION_AIR := 300.0

const GRAVITY_UP := 900.0
const GRAVITY_DOWN := 1400.0
const JUMP_VELOCITY := -290.0
const JUMP_CUT_MULTIPLIER := 0.5
const COYOTE_TIME := 0.1
const JUMP_BUFFER_TIME := 0.1

const STAND_WIDTH := 16.0
const STAND_HEIGHT := 28.0
const CROUCH_HEIGHT := 14.0

const FIRE_INTERVAL := 1.0 / 8.0
const BULLET_SPEED := 350.0

enum PhysState { GROUND, AIR, CROUCH, PRONE }

@onready var collision: CollisionShape2D = $Collision
@onready var body_visual: ColorRect = $Body
@onready var hurt_area: Area2D = $HurtAreaTmp
@onready var bullet_scene: PackedScene = preload("res://src/projectiles/bullet.tscn")

var phys_state: PhysState = PhysState.GROUND
var facing: int = 1
var coyote_timer: float = 0.0
var jump_buffer_timer: float = 0.0
var fire_cooldown: float = 0.0
var current_height: float = STAND_HEIGHT
var is_dead: bool = false
var spawn_position: Vector2


func _ready() -> void:
	spawn_position = global_position
	hurt_area.body_entered.connect(_on_hurt_area_body_entered)


func _physics_process(delta: float) -> void:
	if is_dead:
		return

	var h_input := Input.get_axis("move_left", "move_right")
	if h_input != 0.0:
		facing = 1 if h_input > 0.0 else -1
	var down_held := Input.is_action_pressed("aim_down")
	var on_floor := is_on_floor()

	coyote_timer = COYOTE_TIME if on_floor else max(coyote_timer - delta, 0.0)
	jump_buffer_timer = JUMP_BUFFER_TIME if Input.is_action_just_pressed("jump") else max(jump_buffer_timer - delta, 0.0)

	if on_floor:
		if down_held:
			phys_state = PhysState.PRONE if h_input != 0.0 else PhysState.CROUCH
		else:
			phys_state = PhysState.GROUND
	else:
		phys_state = PhysState.AIR

	if jump_buffer_timer > 0.0 and coyote_timer > 0.0:
		velocity.y = JUMP_VELOCITY
		jump_buffer_timer = 0.0
		coyote_timer = 0.0
		phys_state = PhysState.AIR

	if Input.is_action_just_released("jump") and velocity.y < 0.0:
		velocity.y *= JUMP_CUT_MULTIPLIER

	if not is_on_floor():
		var gravity := GRAVITY_DOWN if velocity.y > 0.0 else GRAVITY_UP
		velocity.y += gravity * delta

	var target_speed := h_input * MOVE_SPEED
	var accel := ACCEL_GROUND if on_floor else ACCEL_AIR
	var friction := FRICTION_GROUND if on_floor else FRICTION_AIR
	if h_input != 0.0:
		velocity.x = move_toward(velocity.x, target_speed, accel * delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, friction * delta)

	move_and_slide()

	_update_shape()
	fire_cooldown = max(fire_cooldown - delta, 0.0)
	if Input.is_action_pressed("shoot"):
		_try_shoot()


func _update_shape() -> void:
	current_height = CROUCH_HEIGHT if (phys_state == PhysState.CROUCH or phys_state == PhysState.PRONE) else STAND_HEIGHT
	var shape: RectangleShape2D = collision.shape
	shape.size = Vector2(STAND_WIDTH, current_height)
	collision.position = Vector2(0.0, -current_height / 2.0)
	body_visual.size = Vector2(STAND_WIDTH, current_height)
	body_visual.position = Vector2(-STAND_WIDTH / 2.0, -current_height)


## Tabla de direcciones de apuntado por estado — ver 01_Arquitectura_Tecnica.docx, paso 0.7.
func get_aim_direction() -> Vector2:
	var h := 0
	if Input.is_action_pressed("move_left"):
		h -= 1
	if Input.is_action_pressed("move_right"):
		h += 1
	var v := 0
	if Input.is_action_pressed("aim_up"):
		v -= 1
	if Input.is_action_pressed("aim_down"):
		v += 1

	match phys_state:
		PhysState.GROUND:
			if h == 0:
				return Vector2(0.0, -1.0) if v < 0 else Vector2(float(facing), 0.0)
			return Vector2(float(facing), 0.0)
		PhysState.CROUCH, PhysState.PRONE:
			return Vector2(float(facing), 0.0)
		PhysState.AIR:
			if h == 0 and v == 0:
				return Vector2(float(facing), 0.0)
			if h == 0:
				return Vector2(0.0, float(sign(v)))
			return Vector2(float(h), float(v)).normalized()
	return Vector2(float(facing), 0.0)


func _try_shoot() -> void:
	if fire_cooldown > 0.0:
		return
	fire_cooldown = FIRE_INTERVAL
	var dir := get_aim_direction()
	var bullet := bullet_scene.instantiate()
	get_parent().add_child(bullet)
	bullet.global_position = global_position + Vector2(0.0, -current_height / 2.0) + dir * 10.0
	bullet.setup(dir, BULLET_SPEED)


func _on_hurt_area_body_entered(body: Node) -> void:
	if is_dead or not body.is_in_group("enemies"):
		return
	_die()


func _die() -> void:
	is_dead = true
	visible = false
	collision.set_deferred("disabled", true)
	hurt_area.set_deferred("monitoring", false)
	velocity = Vector2.ZERO
	Events.player_died.emit()
	await get_tree().create_timer(1.0).timeout
	global_position = spawn_position
	is_dead = false
	visible = true
	collision.set_deferred("disabled", false)
	hurt_area.set_deferred("monitoring", true)
	Events.player_respawned.emit()
