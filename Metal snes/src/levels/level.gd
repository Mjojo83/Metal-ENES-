class_name Level
extends Node2D
## Plantilla de nivel (paso 2.5) construida desde datos: data/levels/<id>.json trae el mapa ASCII
## (16 px por celda), los puntos de aparición, los gates, las cajas de armas y la ruta de las
## oleadas. Duplicar un nivel = escribir otro JSON, cero código.

const PICKUP_SCENE := preload("res://src/pickups/weapon_pickup.tscn")
const GATE_SCRIPT := preload("res://src/levels/camera_gate.gd")
const END_DELAY := 4.0

@export var level_path: String = "res://data/levels/deep_fall_01.json"

@onready var terrain: TileMapLayer = $Terrain
@onready var colliders: Node2D = $Colliders
@onready var gates: Node2D = $Gates
@onready var actors: Node2D = $Actors
@onready var pickups: Node2D = $Pickups
@onready var signs: Node2D = $Signs
@onready var player: CharacterBody2D = $Player
@onready var camera: GameCamera = $GameCamera
@onready var spawner: WaveSpawner = $WaveSpawner
@onready var reticle: Sprite2D = $Reticle

var data: Dictionary = {}
var tile_size: int = 16
var boss_id: StringName = &""
var tremor_period: float = 0.0
var tremor_timer: float = 0.0
var finished: bool = false
var level_height: int = 224


func _ready() -> void:
	data = load_json(level_path)
	if data.is_empty():
		push_error("Level: no se pudo cargar %s" % level_path)
		return
	tile_size = int(data.get("tile_size", 16))
	var rows: Array = data.get("map", [])
	level_height = rows.size() * tile_size
	_build_terrain(rows)
	var spawn := _vec(data.get("player_spawn", [48, 192]))
	player.global_position = spawn
	player.spawn_position = spawn
	var lim: Array = data.get("camera_limits", [0, 0, 320, 224])
	camera.set_level_limits(Rect2(float(lim[0]), float(lim[1]), float(lim[2]) - float(lim[0]), float(lim[3]) - float(lim[1])))
	camera.global_position = spawn + Vector2(0, -16)
	spawner.actors_parent = actors
	spawner.spawn_points = _points(data.get("spawn_points", {}))
	var waves_path := String(data.get("waves", ""))
	if waves_path != "":
		spawner.load_waves(waves_path)
	_build_gates(data.get("gates", []))
	_build_pickups(data.get("pickups", []))
	_build_signs(data.get("signs", []))
	boss_id = StringName(String(data.get("boss_id", "")))
	tremor_period = float(data.get("tremor_period", 0.0))
	tremor_timer = tremor_period
	Events.enemy_killed.connect(_on_enemy_killed)
	Events.game_over.connect(_on_game_over)
	Events.debug_spawn_enemy.connect(_on_debug_spawn)


static func load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed = JSON.parse_string(file.get_as_text())
	file.close()
	if typeof(parsed) != TYPE_DICTIONARY:
		return {}
	return parsed


func _vec(a) -> Vector2:
	if typeof(a) == TYPE_ARRAY and (a as Array).size() >= 2:
		return Vector2(float(a[0]), float(a[1]))
	return Vector2.ZERO


func _points(raw: Dictionary) -> Dictionary:
	var out := {}
	for key in raw.keys():
		out[String(key)] = _vec(raw[key])
	return out


# --- terreno ------------------------------------------------------------------------------

func _build_terrain(rows: Array) -> void:
	if rows.is_empty():
		return
	var tileset_path := String(data.get("tileset", ""))
	var texture: Texture2D = load(tileset_path) if tileset_path != "" and ResourceLoader.exists(tileset_path) else null
	var source_id := -1
	if texture != null:
		var ts := TileSet.new()
		ts.tile_size = Vector2i(tile_size, tile_size)
		var src := TileSetAtlasSource.new()
		src.texture = texture
		src.texture_region_size = Vector2i(tile_size, tile_size)
		var n := int(texture.get_width() / tile_size)
		for i in n:
			src.create_tile(Vector2i(i, 0))
		source_id = ts.add_source(src)
		terrain.tile_set = ts
	var h := rows.size()
	var w := String(rows[0]).length()
	for y in h:
		var row := String(rows[y])
		for x in w:
			var ch := row[x]
			if source_id < 0:
				continue
			if ch == "#":
				var above_air := y == 0 or String(rows[y - 1])[x] != "#"
				var variant := (3 + ((x * 7 + y * 3) % 2)) if above_air else [0, 1, 2, 6, 7][(x * 5 + y * 11) % 5]
				terrain.set_cell(Vector2i(x, y), source_id, Vector2i(variant, 0))
			elif ch == "=":
				terrain.set_cell(Vector2i(x, y), source_id, Vector2i(5, 0))
	_build_colliders(rows, w, h)


func _build_colliders(rows: Array, w: int, h: int) -> void:
	## Rectángulos fusionados: una caja por bloque sólido (menos costuras donde atorarse).
	var active := {}   # (x0, x1) -> fila de inicio
	for y in range(h + 1):
		var runs := {}
		if y < h:
			var row := String(rows[y])
			var x := 0
			while x < w:
				if row[x] == "#":
					var x0 := x
					while x < w and row[x] == "#":
						x += 1
					runs[Vector2i(x0, x)] = true
				else:
					x += 1
		for key in active.keys():
			if not runs.has(key):
				_add_solid(key.x, int(active[key]), key.y, y)
		for key in runs.keys():
			if not active.has(key):
				active[key] = y
		for key in active.keys():
			if not runs.has(key):
				active.erase(key)
		if y < h:
			var row2 := String(rows[y])
			var x2 := 0
			while x2 < w:
				if row2[x2] == "=":
					var x0 := x2
					while x2 < w and row2[x2] == "=":
						x2 += 1
					_add_platform(x0, x2, y)
				else:
					x2 += 1


func _add_solid(x0: int, y0: int, x1: int, y1: int) -> void:
	var body := StaticBody2D.new()
	body.collision_layer = Layers.TERRAIN
	body.collision_mask = 0
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2((x1 - x0) * tile_size, (y1 - y0) * tile_size)
	shape.shape = rect
	body.position = Vector2((x0 + x1) * tile_size / 2.0, (y0 + y1) * tile_size / 2.0)
	body.add_child(shape)
	colliders.add_child(body)


func _add_platform(x0: int, x1: int, y: int) -> void:
	var body := StaticBody2D.new()
	body.collision_layer = Layers.ONE_WAY
	body.collision_mask = 0
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2((x1 - x0) * tile_size, 4.0)
	shape.shape = rect
	shape.one_way_collision = true
	shape.one_way_collision_margin = 4.0
	body.position = Vector2((x0 + x1) * tile_size / 2.0, y * tile_size + 2.0)
	body.add_child(shape)
	colliders.add_child(body)


# --- gates, cajas, letreros -------------------------------------------------------------------

func _build_gates(list: Array) -> void:
	for raw in list:
		var g: Dictionary = raw
		var gate := Area2D.new()
		gate.set_script(GATE_SCRIPT)
		gate.name = String(g.get("id", "gate"))
		gate.set("gate_id", StringName(String(g.get("id", "gate"))))
		gate.set("lock_left", float(g.get("lock_left", 0)))
		gate.set("lock_right", float(g.get("lock_right", 320)))
		gate.set("wave_id", StringName(String(g.get("wave", ""))))
		gate.set("checkpoint", _vec(g.get("checkpoint", [0, 0])))
		var shape := CollisionShape2D.new()
		var rect := RectangleShape2D.new()
		rect.size = Vector2(8.0, float(level_height))
		shape.shape = rect
		gate.add_child(shape)
		gate.position = Vector2(float(g.get("x", 0)), level_height / 2.0)
		gates.add_child(gate)


func _build_pickups(list: Array) -> void:
	for raw in list:
		var p: Dictionary = raw
		var path := "res://data/weapons/%s.tres" % String(p.get("weapon", "shotgun"))
		if not ResourceLoader.exists(path):
			continue
		var pickup := PICKUP_SCENE.instantiate()
		pickup.set("weapon", load(path))
		pickups.add_child(pickup)
		pickup.global_position = _vec(p.get("pos", [0, 0]))


func _build_signs(list: Array) -> void:
	for raw in list:
		var s: Dictionary = raw
		var label := Label.new()
		label.text = String(s.get("text", ""))
		label.modulate = Color(0.85, 0.75, 0.6, 0.9)
		label.position = _vec(s.get("pos", [0, 0]))
		label.z_index = -1
		signs.add_child(label)


# --- flujo -----------------------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	if finished:
		return
	if tremor_period > 0.0:
		tremor_timer -= delta
		if tremor_timer <= 0.0:
			tremor_timer = tremor_period
			Events.tremor_started.emit(1.0)
			Events.screenshake_requested.emit(3.0)
			AudioManager.play(&"tremor", -4.0)


func _process(_delta: float) -> void:
	var input: PlayerInput = player.get_node_or_null("Input")
	if input == null or player.is_dead or not input.mouse_active:
		reticle.visible = false
		return
	var dir: Vector2 = player.get_aim_direction()
	reticle.visible = true
	reticle.global_position = (player.muzzle_position(dir) + dir * 22.0).round()


func _on_enemy_killed(id: StringName, _pos: Vector2) -> void:
	if finished or boss_id == &"" or id != boss_id:
		return
	finished = true
	Game.add_score(1000)
	Events.level_cleared.emit()
	player.get_node("Input").set("enabled", false)
	get_tree().create_timer(END_DELAY).timeout.connect(_back_to_title)


func _on_game_over() -> void:
	if finished:
		return
	finished = true
	Game.save_game()
	get_tree().create_timer(3.0).timeout.connect(_back_to_title)


func _back_to_title() -> void:
	Game.go_to(Game.SCENE_TITLE)


func _on_debug_spawn(position: Vector2) -> void:
	var ids := ["velociraptor", "trilobites", "meganeura", "eryops", "hallucigenia"]
	var id: String = ids[randi() % ids.size()]
	spawner.spawn_now(id, Vector2(position.x, player.global_position.y))
