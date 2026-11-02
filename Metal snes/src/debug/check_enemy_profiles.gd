extends Node2D
## Paso 1.9: los perfiles de IA se configuran solo con EnemyData (@export), sin scripts nuevos.
## Avanzador camina hacia el jugador y se detiene a stop_distance; Estático no se mueve; Volador
## mantiene altura sin suelo; Saltador despega al menos dos veces en 3 s.

const ENEMY := preload("res://src/actors/enemies/enemy.tscn")

@onready var player: CharacterBody2D = $Player

var all_ok := true
var frame := 0
var advancer: Enemy
var advancer_fast: Enemy
var static_e: Enemy
var flier: Enemy
var jumper: Enemy
var static_x := 0.0
var jumper_airborne := 0
var jumper_was_floor := true
var flier_min_y := INF
var flier_max_y := -INF


func _ok(label: String, cond: bool, detail: String = "") -> void:
	if not cond:
		all_ok = false
	print("%s -> %s %s" % [label, "OK" if cond else "FALLO", detail])


func _data(profile: int, speed: float, extra: Dictionary = {}) -> EnemyData:
	var d := EnemyData.new()
	d.profile = profile as EnemyData.Profile
	d.speed = speed
	d.max_health = 99
	d.hurtbox_size = Vector2(12, 12)
	d.body_size = Vector2(10, 12)
	d.sprite_cell = Vector2i(32, 32)
	d.detect_range = 400.0
	d.attack_range = 0.0        # sin ataques en esta prueba
	d.contact_damage = 0
	for k in extra.keys():
		d.set(k, extra[k])
	return d


func _make(data: EnemyData, pos: Vector2) -> Enemy:
	var e := ENEMY.instantiate() as Enemy
	add_child(e)
	e.global_position = pos
	e.setup(data)
	e.hitbox.active = false
	return e


func _ready() -> void:
	player.input.enabled = false
	player.hurtbox.invulnerable = true
	advancer = _make(_data(EnemyData.Profile.ADVANCER, 40.0, {"stop_distance": 48.0}), Vector2(300, 200))
	advancer_fast = _make(_data(EnemyData.Profile.ADVANCER, 90.0, {"stop_distance": 48.0}), Vector2(420, 200))
	static_e = _make(_data(EnemyData.Profile.STATIC, 60.0), Vector2(250, 200))
	flier = _make(_data(EnemyData.Profile.FLIER, 50.0, {"flying": true, "fly_height": 60.0}), Vector2(200, 140))
	jumper = _make(_data(EnemyData.Profile.JUMPER, 60.0, {"jump_velocity": -220.0, "jump_interval": 0.8}), Vector2(500, 200))
	static_x = static_e.global_position.x


func _physics_process(_delta: float) -> void:
	frame += 1
	if jumper != null:
		var on_floor := jumper.is_on_floor()
		if jumper_was_floor and not on_floor:
			jumper_airborne += 1
		jumper_was_floor = on_floor
	if flier != null and frame > 60:
		flier_min_y = minf(flier_min_y, flier.global_position.y)
		flier_max_y = maxf(flier_max_y, flier.global_position.y)
	if frame == 60:
		_ok("1.9 Avanzador rápido avanzó más que el lento en 1 s", (420.0 - advancer_fast.global_position.x) > (300.0 - advancer.global_position.x) + 10.0,
			"lento=%.1f rápido=%.1f" % [advancer.global_position.x, advancer_fast.global_position.x])
	if frame == 240:
		var px := player.global_position.x
		_ok("1.9 Avanzador se detiene a stop_distance (48±6 px)", absf(absf(advancer.global_position.x - px) - 48.0) <= 6.0, "dist=%.1f" % absf(advancer.global_position.x - px))
		_ok("1.9 Avanzador rápido también (misma lógica, otro número)", absf(absf(advancer_fast.global_position.x - px) - 48.0) <= 6.0, "dist=%.1f" % absf(advancer_fast.global_position.x - px))
		_ok("1.9 Estático no se mueve en x", absf(static_e.global_position.x - static_x) < 0.5, "dx=%.2f" % (static_e.global_position.x - static_x))
		_ok("1.9 Volador se queda en el aire (nunca toca el suelo y=200)", flier_max_y < 190.0, "y en [%.0f, %.0f]" % [flier_min_y, flier_max_y])
		_ok("1.9 Saltador despega ≥ 2 veces en 3 s", jumper_airborne >= 2, "despegues=%d" % jumper_airborne)
		print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
		get_tree().quit()
