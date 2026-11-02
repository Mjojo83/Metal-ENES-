extends CharacterBody2D
## Jugador (fases 0 y 1). Movimiento y salto con game feel (0.5-0.6), apuntado discreto por estado
## (0.7), armas como Resource (1.5) y componentes de daño (1.2). El estado físico sigue en un enum
## (PhysState) porque disparar no es un estado: se superpone a cualquier estado.

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

const RESPAWN_DELAY := 1.0
const RESPAWN_GRACE := 1.5
const SHOOT_ANIM_TIME := 0.15
const WALL_MARGIN := 8.0

# id del arma -> sufijo de las hojas de sprites (make_players.py)
const WEAPON_SUFFIX := {&"pistol": "pistol", &"shotgun": "shotgun", &"heavy_machine_gun": "hmg"}

enum PhysState { GROUND, AIR, CROUCH, PRONE }

@export var character: CharacterData

@onready var collision: CollisionShape2D = $Collision
@onready var sprite: AnimatedSprite2D = $Sprite
@onready var hurtbox: HurtboxComponent = $Hurtbox
@onready var hurt_shape: CollisionShape2D = $Hurtbox/Shape
@onready var health: HealthComponent = $Health
@onready var weapon: WeaponComponent = $Weapon
@onready var input: PlayerInput = $Input

var phys_state: PhysState = PhysState.GROUND
var facing: int = 1
var coyote_timer: float = 0.0
var jump_buffer_timer: float = 0.0
var current_height: float = STAND_HEIGHT
var is_dead: bool = false
var spawn_position: Vector2
var state_name: String = "idle"
var bounds: Vector2 = Vector2(-INF, INF)   # muro invisible del camera gate (x mín, x máx)
var shoot_anim_timer: float = 0.0
var recoil: float = 0.0
var _was_on_floor: bool = true
var _body_shape: RectangleShape2D
var _current_anim: String = ""
var _blink_t: float = 0.0


func _ready() -> void:
	add_to_group("player")
	spawn_position = global_position
	_body_shape = (collision.shape as RectangleShape2D).duplicate()
	collision.shape = _body_shape
	health.died.connect(_on_health_died)
	hurtbox.hit_received.connect(_on_hit_received)
	weapon.weapon_changed.connect(_on_weapon_changed)
	weapon.ammo_changed.connect(func(ammo: int) -> void: Events.ammo_changed.emit(ammo))
	weapon.fired.connect(_on_weapon_fired)
	sprite.animation_finished.connect(_on_animation_finished)
	Events.debug_give_weapon.connect(_on_debug_give_weapon)
	Events.checkpoint_reached.connect(func(pos: Vector2) -> void: spawn_position = pos)
	if character == null and Game.selected_character != null:
		character = Game.selected_character
	if character != null:
		apply_character(character)
	if weapon.weapon != null:
		_on_weapon_changed(weapon.weapon, weapon.ammo)
	_refresh_animation(true)


func apply_character(data: CharacterData) -> void:
	character = data
	if data.sprite_frames != null:
		sprite.sprite_frames = data.sprite_frames
	var shape := (hurt_shape.shape as RectangleShape2D).duplicate() as RectangleShape2D
	shape.size = data.hurtbox_size
	hurt_shape.shape = shape
	_current_anim = ""
	_refresh_animation(true)


func _physics_process(delta: float) -> void:
	hurtbox.invulnerable = Debug.invincible
	_blink(delta)
	if is_dead:
		return

	input.poll(self)
	var h_input := input.move_axis
	if h_input != 0.0:
		facing = 1 if h_input > 0.0 else -1
	var down_held := input.down_held
	var on_floor := is_on_floor()

	coyote_timer = COYOTE_TIME if on_floor else maxf(coyote_timer - delta, 0.0)
	jump_buffer_timer = JUMP_BUFFER_TIME if input.jump_pressed else maxf(jump_buffer_timer - delta, 0.0)

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
		AudioManager.play(&"jump", -8.0)

	if input.jump_released and velocity.y < 0.0:
		velocity.y *= JUMP_CUT_MULTIPLIER

	if not is_on_floor():
		var gravity := GRAVITY_DOWN if velocity.y > 0.0 else GRAVITY_UP
		velocity.y += gravity * delta

	var target_speed := h_input * MOVE_SPEED
	if phys_state == PhysState.PRONE:
		target_speed *= 0.5
	var accel := ACCEL_GROUND if on_floor else ACCEL_AIR
	var friction := FRICTION_GROUND if on_floor else FRICTION_AIR
	if h_input != 0.0:
		velocity.x = move_toward(velocity.x, target_speed, accel * delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, friction * delta)

	move_and_slide()
	_clamp_to_bounds()

	if is_on_floor() and not _was_on_floor:
		AudioManager.play(&"land", -10.0)
	_was_on_floor = is_on_floor()

	_update_shape()
	_handle_shooting()
	shoot_anim_timer = maxf(shoot_anim_timer - delta, 0.0)
	_refresh_animation(false)


func _clamp_to_bounds() -> void:
	if bounds.x > -INF or bounds.y < INF:
		var clamped := clampf(global_position.x, bounds.x + WALL_MARGIN, bounds.y - WALL_MARGIN)
		if clamped != global_position.x:
			global_position.x = clamped
			velocity.x = 0.0


func _update_shape() -> void:
	current_height = CROUCH_HEIGHT if (phys_state == PhysState.CROUCH or phys_state == PhysState.PRONE) else STAND_HEIGHT
	_body_shape.size = Vector2(STAND_WIDTH, current_height)
	collision.position = Vector2(0.0, -current_height / 2.0)
	hurt_shape.position = Vector2(0.0, -current_height / 2.0)


## Tabla de direcciones de apuntado por estado — ver 01_Arquitectura_Tecnica.docx, paso 0.7.
## Acepta teclado/mando (h, v discretos) y ratón (cuantizado al mismo conjunto por estado).
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

	if input.mouse_active:
		var m := _mouse_dpad()
		if h == 0:
			h = m.x
		if v == 0:
			v = m.y
		if phys_state == PhysState.GROUND and Input.get_axis("move_left", "move_right") == 0.0 and m.x != 0:
			facing = m.x

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
				return Vector2(0.0, float(signi(v)))
			return Vector2(float(h), float(v)).normalized()
	return Vector2(float(facing), 0.0)


func _mouse_dpad() -> Vector2i:
	## Convierte el ángulo del cursor en la misma entrada discreta (h, v) que el teclado.
	var origin := global_position + Vector2(0.0, -current_height / 2.0)
	var d := input.mouse_world - origin
	if d.length() < 6.0:
		return Vector2i.ZERO
	var elevation := rad_to_deg(atan2(-d.y, absf(d.x)))
	var side := 1 if d.x >= 0.0 else -1
	if elevation > 60.0:
		return Vector2i(0, -1)
	if elevation < -60.0:
		return Vector2i(0, 1)
	if elevation > 22.5:
		return Vector2i(side, -1)
	if elevation < -22.5:
		return Vector2i(side, 1)
	return Vector2i(side, 0)


func muzzle_position(dir: Vector2) -> Vector2:
	var crouched := phys_state == PhysState.CROUCH or phys_state == PhysState.PRONE
	var local: Vector2
	if dir.y < -0.9:
		local = Vector2(6.0, -46.0)
	elif dir.y > 0.9:
		local = Vector2(4.0, -2.0)
	elif dir.y < -0.3:
		local = Vector2(17.0, -36.0)
	elif dir.y > 0.3:
		local = Vector2(17.0, -12.0)
	elif crouched:
		local = Vector2(22.0, -16.0)
	else:
		local = Vector2(22.0, -25.0)
	local.x *= facing
	return global_position + local


func _handle_shooting() -> void:
	var wants := input.shoot_pressed or (input.shoot_held and weapon.weapon != null and weapon.weapon.auto_fire)
	if not wants:
		return
	var dir := get_aim_direction()
	weapon.try_fire(muzzle_position(dir), dir, self)


func _on_weapon_fired(data: WeaponData, dir: Vector2) -> void:
	shoot_anim_timer = SHOOT_ANIM_TIME
	recoil = data.recoil_px
	AudioManager.play(data.fire_sound, -4.0)
	var vfx := Pools.acquire(&"vfx")
	if vfx != null and vfx.has_method("play_effect"):
		vfx.play_effect(&"muzzle_flash", muzzle_position(dir) + dir * 3.0, facing < 0)
	if data.screenshake > 0.0:
		Events.screenshake_requested.emit(data.screenshake)
	if data.hitstop_frames > 0:
		Events.hitstop_requested.emit(data.hitstop_frames)
	# los disparos reinician la animación de disparo para que se vea cada tiro
	var anim := _anim_name_for_state()
	if sprite.sprite_frames != null and sprite.sprite_frames.has_animation(anim) and anim.begins_with("shoot"):
		sprite.play(anim)
		_current_anim = anim


func pick_weapon(data: WeaponData) -> void:
	weapon.equip(data)


func _on_weapon_changed(data: WeaponData, ammo: int) -> void:
	Events.weapon_changed.emit(data, ammo)
	_current_anim = ""
	_refresh_animation(true)


func _on_debug_give_weapon() -> void:
	var ids := [&"pistol", &"shotgun", &"heavy_machine_gun"]
	var current := ids.find(weapon.weapon.id) if weapon.weapon != null else -1
	var next_id: StringName = ids[(current + 1) % ids.size()]
	var path := "res://data/weapons/%s.tres" % next_id
	if ResourceLoader.exists(path):
		weapon.equip(load(path) as WeaponData)


# --- animación --------------------------------------------------------------------------------

func _weapon_suffix() -> String:
	if weapon.weapon == null:
		return "pistol"
	return String(WEAPON_SUFFIX.get(weapon.weapon.id, "pistol"))


func _anim_name_for_state() -> String:
	var base := "idle"
	var shooting := shoot_anim_timer > 0.0
	if is_dead:
		base = "die"
	elif phys_state == PhysState.CROUCH or phys_state == PhysState.PRONE:
		base = "crouch_shoot" if shooting else "crouch"
	elif phys_state == PhysState.AIR:
		var dir := get_aim_direction()
		if dir.y < -0.9:
			base = "aim_up"
		elif dir.y > 0.9:
			base = "aim_down"
		elif dir.y < -0.3:
			base = "aim_diag_up"
		elif dir.y > 0.3:
			base = "aim_diag_down"
		else:
			base = "jump" if velocity.y < 0.0 else "fall"
	else:
		if absf(velocity.x) > 5.0:
			base = "run"
		else:
			var dir := get_aim_direction()
			if dir.y < -0.9:
				base = "shoot_up" if shooting else "aim_up"
			else:
				base = "shoot" if shooting else "idle"
	state_name = base
	return base + "__" + _weapon_suffix()


func _refresh_animation(force: bool) -> void:
	if sprite.sprite_frames == null:
		return
	sprite.flip_h = facing < 0
	var anim := _anim_name_for_state()
	if not sprite.sprite_frames.has_animation(anim):
		anim = "idle__pistol"
		if not sprite.sprite_frames.has_animation(anim):
			return
	if force or anim != _current_anim:
		_current_anim = anim
		sprite.play(anim)
	# retroceso del arma: 1-3 px contra la dirección del disparo, un solo tick
	var cell_w := 64.0
	sprite.offset = Vector2(-cell_w / 2.0 - recoil * facing, -cell_w)
	recoil = 0.0


func _on_animation_finished() -> void:
	if _current_anim.begins_with("shoot") or _current_anim.begins_with("crouch_shoot"):
		_current_anim = ""
		_refresh_animation(true)


func _blink(delta: float) -> void:
	## Parpadeo durante los i-frames tras reaparecer; muerto, el sprite se queda como esté.
	if health.is_invulnerable() and not is_dead:
		_blink_t += delta
		sprite.visible = int(_blink_t * 16.0) % 2 == 0
	elif not is_dead:
		_blink_t = 0.0
		sprite.visible = true


# --- daño y muerte ----------------------------------------------------------------------------

func _on_hit_received(_damage: int, _source: Vector2) -> void:
	Events.player_hit.emit()


func _on_health_died() -> void:
	_die()


func _die() -> void:
	if is_dead:
		return
	is_dead = true
	velocity = Vector2.ZERO
	collision.set_deferred("disabled", true)
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	health.dead = true
	_current_anim = ""
	_refresh_animation(true)
	Events.player_died.emit()
	AudioManager.play(&"player_die")
	var alive := Game.lose_life()
	await get_tree().create_timer(RESPAWN_DELAY).timeout
	if not is_inside_tree():
		return
	if not alive:
		sprite.visible = false
		Events.game_over.emit()
		return
	_respawn()


func _respawn() -> void:
	global_position = spawn_position
	velocity = Vector2.ZERO
	is_dead = false
	phys_state = PhysState.GROUND
	health.reset(RESPAWN_GRACE)
	collision.set_deferred("disabled", false)
	hurtbox.set_deferred("monitoring", true)
	hurtbox.set_deferred("monitorable", true)
	sprite.visible = true
	_current_anim = ""
	_refresh_animation(true)
	Events.player_respawned.emit()
