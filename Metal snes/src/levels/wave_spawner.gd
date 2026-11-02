class_name WaveSpawner
extends Node
## Oleadas desde JSON (paso 1.8). Los retardos se cuentan en segundos de física, nunca en frames.
## Formato: {"waves": {"id": {"clear_condition": "all_dead", "spawns": [{"enemy", "point",
## "delay", "count", "interval"}]}}}. Los puntos de aparición los inyecta el nivel.

const ENEMY_SCENE := preload("res://src/actors/enemies/enemy.tscn")
const ENEMY_DATA_DIR := "res://data/enemies/"

var waves: Dictionary = {}
var spawn_points: Dictionary = {}
var actors_parent: Node = null
var current_wave: StringName = &""
var pending: Array[Dictionary] = []   # {"time": float, "enemy": String, "point": String}
var alive: Array[Node] = []
var total_spawned: int = 0
var enemy_data_override: Dictionary = {}   # id -> EnemyData (pruebas headless sin texturas)


func _ready() -> void:
	Events.wave_started.connect(start_wave)
	Events.player_died.connect(abort)


func load_waves(path: String) -> bool:
	waves.clear()
	if not FileAccess.file_exists(path):
		push_error("WaveSpawner: no existe %s" % path)
		return false
	var file := FileAccess.open(path, FileAccess.READ)
	var parsed = JSON.parse_string(file.get_as_text())
	file.close()
	if typeof(parsed) != TYPE_DICTIONARY or not (parsed as Dictionary).has("waves"):
		push_error("WaveSpawner: JSON de oleadas inválido en %s" % path)
		return false
	waves = (parsed as Dictionary)["waves"]
	return true


func start_wave(id: StringName) -> void:
	if not waves.has(String(id)):
		push_warning("WaveSpawner: oleada desconocida '%s'" % id)
		Events.wave_cleared.emit(id)
		return
	abort()
	current_wave = id
	total_spawned = 0
	var wave: Dictionary = waves[String(id)]
	for spawn in wave.get("spawns", []):
		var s: Dictionary = spawn
		var count := int(s.get("count", 1))
		var delay := float(s.get("delay", 0.0))
		var interval := float(s.get("interval", 0.0))
		for i in count:
			pending.append({"time": delay + interval * i, "enemy": String(s.get("enemy", "")),
				"point": String(s.get("point", ""))})
	pending.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["time"] < b["time"])


func abort() -> void:
	pending.clear()
	for e in alive:
		if is_instance_valid(e):
			e.queue_free()
	alive.clear()
	current_wave = &""


func _physics_process(delta: float) -> void:
	if current_wave == &"":
		return
	var i := 0
	while i < pending.size():
		pending[i]["time"] = float(pending[i]["time"]) - delta
		if float(pending[i]["time"]) <= 0.0:
			var s: Dictionary = pending[i]
			pending.remove_at(i)
			_spawn(s["enemy"], s["point"])
		else:
			i += 1
	alive = alive.filter(func(e: Node) -> bool: return is_instance_valid(e) and e.is_inside_tree())
	if pending.is_empty() and alive.is_empty():
		var id := current_wave
		current_wave = &""
		Events.wave_cleared.emit(id)


func _spawn(enemy_id: String, point: String) -> Node:
	var data: EnemyData = enemy_data_override.get(enemy_id, null)
	if data == null:
		var path := ENEMY_DATA_DIR + enemy_id + ".tres"
		if not ResourceLoader.exists(path):
			push_warning("WaveSpawner: no hay datos para el enemigo '%s'" % enemy_id)
			return null
		data = load(path) as EnemyData
	var enemy := ENEMY_SCENE.instantiate() as Enemy
	var parent := actors_parent if actors_parent != null else get_parent()
	parent.add_child(enemy)
	var pos: Vector2 = spawn_points.get(point, Vector2.ZERO)
	enemy.global_position = pos
	enemy.setup(data)
	enemy.wave_id = current_wave
	alive.append(enemy)
	total_spawned += 1
	return enemy


func spawn_now(enemy_id: String, position: Vector2) -> Node:
	## Para la tecla de depuración F7 y para props estáticos del nivel.
	spawn_points["__debug"] = position
	var saved := current_wave
	var enemy := _spawn(enemy_id, "__debug")
	if saved == &"" and enemy != null:
		alive.erase(enemy)
	return enemy
