extends Node2D
## Pasos 1.6-1.8: cámara + camera gate + oleadas. Cruzar el gate traba la cámara y arranca la
## oleada (retardos en segundos: 0 y 2.0 s → frames 0±3 y 120±3); morir a media oleada rearma el
## gate, libera enemigos y restaura límites; limpiar la oleada suelta la cámara y fija checkpoint.

@onready var player: CharacterBody2D = $Player
@onready var camera: GameCamera = $GameCamera
@onready var spawner: WaveSpawner = $WaveSpawner
@onready var gate: CameraGate = $Gate

var all_ok := true
var stage := 0
var stage_frame := 0
var spawn_frames: Array[int] = []
var cleared := 0
var checkpoint := Vector2.ZERO
var wave_start_frame := -1


func _ok(label: String, cond: bool, detail: String = "") -> void:
	if not cond:
		all_ok = false
	print("%s -> %s %s" % [label, "OK" if cond else "FALLO", detail])


func _dummy(id: String) -> EnemyData:
	var d := EnemyData.new()
	d.id = StringName(id)
	d.profile = EnemyData.Profile.STATIC
	d.max_health = 1
	d.hurtbox_size = Vector2(16, 16)
	d.body_size = Vector2(12, 16)
	d.sprite_cell = Vector2i(32, 32)
	d.detect_range = 0.0
	return d


func _ready() -> void:
	player.input.enabled = false
	spawner.actors_parent = self
	spawner.spawn_points = {"right": Vector2(600, 200), "left": Vector2(340, 200)}
	spawner.waves = {"test": {"clear_condition": "all_dead", "spawns": [
		{"enemy": "dummy", "point": "right", "delay": 0.0, "count": 1},
		{"enemy": "dummy", "point": "left", "delay": 2.0, "count": 2, "interval": 0.5}]}}
	spawner.enemy_data_override = {"dummy": _dummy("dummy")}
	Events.wave_started.connect(func(_id: StringName) -> void: wave_start_frame = stage_frame)
	Events.wave_cleared.connect(func(_id: StringName) -> void: cleared += 1)
	Events.checkpoint_reached.connect(func(pos: Vector2) -> void: checkpoint = pos)
	get_tree().node_added.connect(func(n: Node) -> void:
		if n is Enemy and wave_start_frame >= 0:
			spawn_frames.append(stage_frame - wave_start_frame))
	# JSON roto no debe tumbar nada
	var bad := FileAccess.open("user://bad_waves.json", FileAccess.WRITE)
	bad.store_string("{ esto no es json")
	bad.close()
	var loaded := spawner.load_waves("user://bad_waves.json")
	_ok("1.8 JSON inválido -> false sin crash", loaded == false)
	spawner.waves = {"test": {"clear_condition": "all_dead", "spawns": [
		{"enemy": "dummy", "point": "right", "delay": 0.0, "count": 1},
		{"enemy": "dummy", "point": "left", "delay": 2.0, "count": 2, "interval": 0.5}]}}


func _physics_process(_delta: float) -> void:
	stage_frame += 1
	match stage:
		0:  # empujar al jugador a través del gate (x=400)
			player.velocity.x = 150.0
			player.global_position.x += 2.5
			if gate.triggered:
				_ok("1.7 cruzar el gate lo dispara", true)
				_ok("1.7 la cámara queda trabada en [320, 640]", camera.limit_left == 320 and camera.limit_right == 640, "limites=%d..%d" % [camera.limit_left, camera.limit_right])
				_ok("1.7 el jugador recibe el muro invisible", player.bounds == Vector2(320, 640), "bounds=%s" % player.bounds)
				stage = 1
				stage_frame = wave_start_frame if wave_start_frame >= 0 else 0
				wave_start_frame = 0
			elif stage_frame > 200:
				_ok("1.7 el gate se dispara al cruzarlo", false)
				stage = 9
		1:  # el jugador intenta seguir: choca con el muro
			player.global_position.x += 4.0
			if stage_frame == 60:
				_ok("1.7 no se puede pasar del límite derecho", player.global_position.x <= 640.0 - 7.0, "x=%.1f" % player.global_position.x)
			if stage_frame == 200:
				_ok("1.8 spawns en segundos: frames %s (esperado ~[0, 120, 150])" % [spawn_frames],
					spawn_frames.size() == 3 and absi(spawn_frames[0]) <= 3 and absi(spawn_frames[1] - 120) <= 4 and absi(spawn_frames[2] - 150) <= 4)
				_ok("1.8 tres enemigos vivos", spawner.alive.size() == 3, "vivos=%d" % spawner.alive.size())
				player._die()
				stage = 2
				stage_frame = 0
		2:  # morir a media oleada
			if stage_frame == 5:
				_ok("1.7 al morir: el gate se rearma", gate.triggered == false and gate.cleared == false)
				_ok("1.7 al morir: la cámara vuelve a los límites del nivel", camera.limit_right == 2000, "limit_right=%d" % camera.limit_right)
				_ok("1.8 al morir: la oleada se aborta y los enemigos se liberan", spawner.alive.is_empty() and spawner.current_wave == &"")
			if stage_frame == 70:
				_ok("0.10 reaparece en el spawn", not player.is_dead and player.global_position.x < 400.0, "x=%.1f" % player.global_position.x)
				spawn_frames.clear()
				wave_start_frame = -1
				stage = 3
				stage_frame = 0
		3:  # volver a cruzar: se dispara otra vez; matar a todos -> limpia y checkpoint
			player.global_position.x += 2.5
			if gate.triggered and stage == 3:
				stage = 4
				stage_frame = 0
			elif stage_frame > 200:
				_ok("1.7 el gate vuelve a dispararse tras morir", false)
				stage = 9
		4:
			if stage_frame == 200:
				_ok("1.7 segundo disparo del gate", gate.triggered)
				for e in spawner.alive.duplicate():
					if is_instance_valid(e):
						(e as Enemy).health.take_damage(99)
			if stage_frame == 260:
				_ok("1.8 wave_cleared al morir todos", cleared == 1, "cleared=%d" % cleared)
				_ok("1.7 al limpiar: gate cerrado y cámara libre", gate.cleared and camera.limit_right == 2000)
				_ok("1.7 checkpoint fijado y spawn del jugador actualizado", checkpoint == Vector2(600, 200) and player.spawn_position == checkpoint, "spawn=%s" % player.spawn_position)
				stage = 9
		9:
			print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
			get_tree().quit()
