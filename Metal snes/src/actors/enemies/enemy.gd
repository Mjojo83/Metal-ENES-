class_name Enemy
extends CharacterBody2D
## Enemigo genérico orientado a datos (paso 1.9): un EnemyData elige el perfil de IA y sus
## números; la escena ensambla Hurtbox + Hitbox (contacto) + Health. Todas las hojas de sprites
## miran a la izquierda; `facing` = +1 mira a la derecha (flip_h).

const GRAVITY := 1200.0
const ATTACK_TIME := 0.35

enum State { IDLE, MOVE, TELEGRAPH, ATTACK, RECOVER, HIDDEN, DEAD }

@export var data: EnemyData

@onready var sprite: AnimatedSprite2D = $Sprite
@onready var collision: CollisionShape2D = $Collision
@onready var hurtbox: HurtboxComponent = $Hurtbox
@onready var hurt_shape: CollisionShape2D = $Hurtbox/Shape
@onready var hitbox: HitboxComponent = $Hitbox
@onready var hit_shape: CollisionShape2D = $Hitbox/Shape
@onready var health: HealthComponent = $Health

var state: State = State.IDLE
var facing: int = -1
var wave_id: StringName = &""
var state_timer: float = 0.0
var attack_timer: float = 0.5
var jump_timer: float = 0.4
var time_alive: float = 0.0
var attack_dir: Vector2 = Vector2.LEFT
var _player: Node2D = null
var _ready_done: bool = false


func _ready() -> void:
	add_to_group("enemies")
	health.died.connect(_on_died)
	hurtbox.hit_received.connect(_on_hit_received)
	_ready_done = true
	if data != null:
		setup(data)


func setup(new_data: EnemyData) -> void:
	data = new_data
	if not _ready_done:
		return
	if data.sprite_frames != null:
		sprite.sprite_frames = data.sprite_frames
	sprite.centered = false
	sprite.offset = Vector2(-data.sprite_cell.x / 2.0, -float(data.sprite_cell.y))
	var body := RectangleShape2D.new()
	body.size = data.body_size
	collision.shape = body
	collision.position = Vector2(0.0, -data.body_size.y / 2.0)
	var hurt := RectangleShape2D.new()
	hurt.size = data.hurtbox_size
	hurt_shape.shape = hurt
	hurt_shape.position = Vector2(0.0, -data.hurtbox_size.y / 2.0)
	var hit := RectangleShape2D.new()
	hit.size = data.hurtbox_size * 0.9
	hit_shape.shape = hit
	hit_shape.position = hurt_shape.position
	hitbox.damage = data.contact_damage
	health.max_health = data.max_health
	health.reset()
	attack_timer = data.attack_cooldown * 0.5
	state = State.HIDDEN if data.profile == EnemyData.Profile.AMBUSH else State.IDLE
	if state == State.HIDDEN:
		visible = false
		hitbox.active = false
	_play("idle")


func take_damage(amount: int) -> void:
	## Compatibilidad con balas sueltas de la fase 0.
	hurtbox.receive_hit(amount, global_position)


func _physics_process(delta: float) -> void:
	if state == State.DEAD or data == null:
		return
	time_alive += delta
	attack_timer = maxf(attack_timer - delta, 0.0)
	_player = get_tree().get_first_node_in_group("player") as Node2D
	var to_player := Vector2.ZERO
	if _player != null:
		to_player = _player.global_position - global_position
	var player_alive := _player != null and not bool(_player.get("is_dead"))

	match data.profile:
		EnemyData.Profile.ADVANCER, EnemyData.Profile.BOSS:
			_ground_ai(delta, to_player, player_alive)
		EnemyData.Profile.AMBUSH:
			if state == State.HIDDEN:
				if player_alive and absf(to_player.x) < data.detect_range:
					state = State.IDLE
					visible = true
					hitbox.active = true
				_apply_gravity(delta)
			else:
				_ground_ai(delta, to_player, player_alive)
		EnemyData.Profile.STATIC:
			_static_ai(delta, to_player, player_alive)
		EnemyData.Profile.JUMPER:
			_jumper_ai(delta, to_player, player_alive)
		EnemyData.Profile.FLIER:
			_flier_ai(delta, to_player, player_alive)
	move_and_slide()
	sprite.flip_h = facing > 0


func _apply_gravity(delta: float) -> void:
	if not data.flying and not is_on_floor():
		velocity.y += GRAVITY * delta


func _face(to_player: Vector2) -> void:
	if absf(to_player.x) > 2.0:
		facing = 1 if to_player.x > 0.0 else -1


func _ground_ai(delta: float, to_player: Vector2, player_alive: bool) -> void:
	_apply_gravity(delta)
	match state:
		State.IDLE, State.MOVE:
			if player_alive and absf(to_player.x) < data.detect_range * 2.0:
				_face(to_player)
			var far := absf(to_player.x) > data.stop_distance + 2.0
			if player_alive and far and is_on_floor():
				velocity.x = move_toward(velocity.x, facing * data.speed, 600.0 * delta)
				_set_state(State.MOVE, "move")
			else:
				velocity.x = move_toward(velocity.x, 0.0, 800.0 * delta)
				_set_state(State.IDLE, "idle")
			if player_alive and attack_timer <= 0.0 and absf(to_player.x) <= data.attack_range and absf(to_player.y) < 48.0:
				_begin_telegraph()
		State.TELEGRAPH:
			velocity.x = move_toward(velocity.x, 0.0, 800.0 * delta)
			state_timer -= delta
			if state_timer <= 0.0:
				state = State.ATTACK
				state_timer = ATTACK_TIME
				velocity.x = facing * data.lunge_speed
				_play("attack")
				if data.profile == EnemyData.Profile.BOSS:
					AudioManager.play(&"roar")
		State.ATTACK:
			state_timer -= delta
			if state_timer <= 0.0:
				_set_state(State.RECOVER, "idle")
				state_timer = data.recover_time
				attack_timer = data.attack_cooldown
		State.RECOVER:
			velocity.x = move_toward(velocity.x, 0.0, 800.0 * delta)
			state_timer -= delta
			if state_timer <= 0.0:
				_set_state(State.IDLE, "idle")


func _static_ai(delta: float, to_player: Vector2, player_alive: bool) -> void:
	_apply_gravity(delta)
	velocity.x = 0.0
	match state:
		State.IDLE, State.MOVE:
			_set_state(State.IDLE, "idle")
			if player_alive and absf(to_player.x) < data.detect_range:
				_face(to_player)
				if attack_timer <= 0.0:
					_begin_telegraph()
		State.TELEGRAPH:
			state_timer -= delta
			if state_timer <= 0.0:
				state = State.ATTACK
				state_timer = ATTACK_TIME
				_play("attack")
				if data.ranged:
					_shoot(to_player)
		State.ATTACK:
			state_timer -= delta
			if state_timer <= 0.0:
				_set_state(State.RECOVER, "idle")
				state_timer = data.recover_time
				attack_timer = data.attack_cooldown
		State.RECOVER:
			state_timer -= delta
			if state_timer <= 0.0:
				_set_state(State.IDLE, "idle")


func _jumper_ai(delta: float, to_player: Vector2, player_alive: bool) -> void:
	_apply_gravity(delta)
	if is_on_floor():
		velocity.x = move_toward(velocity.x, 0.0, 900.0 * delta)
		jump_timer -= delta
		_set_state(State.IDLE, "idle")
		if player_alive and jump_timer <= 0.0 and absf(to_player.x) < data.detect_range:
			_face(to_player)
			velocity.y = data.jump_velocity
			velocity.x = facing * data.speed
			jump_timer = data.jump_interval
			_set_state(State.MOVE, "move")
	else:
		_set_state(State.MOVE, "move")


func _flier_ai(delta: float, to_player: Vector2, player_alive: bool) -> void:
	var bob := sin(time_alive * 4.0) * 12.0
	match state:
		State.IDLE, State.MOVE:
			if player_alive:
				_face(to_player)
				var target_y := to_player.y - data.fly_height
				velocity.y = clampf((target_y + bob) * 2.0, -data.speed, data.speed)
				velocity.x = facing * data.speed * (0.9 if absf(to_player.x) > 24.0 else 0.0)
				_set_state(State.MOVE, "move")
				if attack_timer <= 0.0 and absf(to_player.x) < data.attack_range * 2.0 and to_player.y > 16.0:
					_begin_telegraph()
			else:
				velocity = Vector2(0.0, bob)
				_set_state(State.IDLE, "idle")
		State.TELEGRAPH:
			velocity = velocity.move_toward(Vector2.ZERO, 400.0 * delta)
			state_timer -= delta
			if state_timer <= 0.0:
				state = State.ATTACK
				state_timer = 0.5
				attack_dir = to_player.normalized() if to_player.length() > 1.0 else Vector2.DOWN
				velocity = attack_dir * data.lunge_speed
				_play("attack")
		State.ATTACK:
			state_timer -= delta
			if state_timer <= 0.0 or is_on_wall() or is_on_floor():
				_set_state(State.RECOVER, "move")
				state_timer = data.recover_time
				attack_timer = data.attack_cooldown
				velocity = Vector2(facing * 20.0, -data.speed)
		State.RECOVER:
			state_timer -= delta
			if state_timer <= 0.0:
				_set_state(State.IDLE, "move")


func _begin_telegraph() -> void:
	state = State.TELEGRAPH
	state_timer = data.telegraph_time
	_play("telegraph")


func _shoot(to_player: Vector2) -> void:
	var bullet := Pools.acquire(&"enemy_bullet")
	if bullet == null or not bullet.has_method("launch"):
		return
	var origin := global_position + Vector2(facing * 6.0, -data.hurtbox_size.y * 0.7)
	var dir := to_player.normalized() if to_player.length() > 1.0 else Vector2(facing, 0.0)
	bullet.launch(origin, dir, data.projectile_speed, data.contact_damage)


func _set_state(new_state: State, anim: String) -> void:
	if state != new_state:
		state = new_state
		_play(anim)


func _play(anim: String) -> void:
	if sprite.sprite_frames == null or not sprite.sprite_frames.has_animation(anim):
		return
	if sprite.animation != anim or not sprite.is_playing():
		sprite.play(anim)


func _on_hit_received(_damage: int, _source: Vector2) -> void:
	AudioManager.play(data.hit_sound if data != null else &"hit", -6.0)
	sprite.modulate = Color(3, 3, 3)
	var tween := create_tween()
	tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.1)
	if data != null and data.profile == EnemyData.Profile.BOSS:
		Events.boss_health_changed.emit(health.health, health.max_health)


func _on_died() -> void:
	if state == State.DEAD:
		return
	state = State.DEAD
	velocity = Vector2.ZERO
	collision.set_deferred("disabled", true)
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	hitbox.set_deferred("monitoring", false)
	hitbox.active = false
	var vfx := Pools.acquire(&"vfx")
	if vfx != null and vfx.has_method("play_effect"):
		vfx.play_effect(&"puff", global_position + Vector2(0.0, -data.hurtbox_size.y / 2.0))
	AudioManager.play(data.die_sound if data != null else &"enemy_die", -4.0)
	if data != null:
		Game.add_score(data.score)
		Events.enemy_killed.emit(data.id, global_position)
	_play("die")
	# sin await: si WaveSpawner libera este nodo antes, la conexión muere con él
	get_tree().create_timer(0.45).timeout.connect(queue_free)
