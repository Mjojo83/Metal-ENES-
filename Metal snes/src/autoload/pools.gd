extends Node
## Pools de objetos (paso 1.4). Precarga N instancias por escena reciclable y las presta y recibe
## en vez de crear y destruir. Cero lógica de gameplay: los nodos prestados se activan solos con
## su propio método `activate()` y se devuelven con `Pools.release(node)`.

const SCENES := {
	&"bullet": preload("res://src/projectiles/bullet.tscn"),
	&"enemy_bullet": preload("res://src/projectiles/enemy_bullet.tscn"),
	&"vfx": preload("res://src/vfx/vfx_sprite.tscn"),
}
const PRELOAD := {&"bullet": 80, &"enemy_bullet": 60, &"vfx": 48}

var _free: Dictionary = {}     # key -> Array[Node]
var _active: Dictionary = {}   # key -> int


func _ready() -> void:
	for key in SCENES.keys():
		_free[key] = []
		_active[key] = 0
		for i in int(PRELOAD.get(key, 16)):
			_park(_make(key))


func _make(key: StringName) -> Node:
	var node: Node = (SCENES[key] as PackedScene).instantiate()
	node.set_meta("pool_key", key)
	add_child(node)
	return node


func _park(node: Node) -> void:
	node.process_mode = Node.PROCESS_MODE_DISABLED
	if node is CanvasItem:
		(node as CanvasItem).visible = false
	if node is Area2D:
		var area := node as Area2D
		area.set_deferred("monitoring", false)
		area.set_deferred("monitorable", false)
	var key: StringName = node.get_meta("pool_key")
	(_free[key] as Array).append(node)


func acquire(key: StringName) -> Node:
	if not _free.has(key):
		push_error("Pools: no existe el pool '%s'" % key)
		return null
	var free: Array = _free[key]
	var node: Node = free.pop_back() if not free.is_empty() else _make(key)
	_active[key] = int(_active[key]) + 1
	node.set_meta("pooled_free", false)
	node.process_mode = Node.PROCESS_MODE_INHERIT
	if node is CanvasItem:
		(node as CanvasItem).visible = true
	if node is Area2D:
		var area := node as Area2D
		area.set_deferred("monitoring", true)
		area.set_deferred("monitorable", true)
	return node


func release(node: Node) -> void:
	if node == null or not node.has_meta("pool_key"):
		return
	var key: StringName = node.get_meta("pool_key")
	if node.has_meta("pooled_free") and node.get_meta("pooled_free"):
		return
	node.set_meta("pooled_free", true)
	_active[key] = maxi(int(_active[key]) - 1, 0)
	_park(node)


func mark_in_use(node: Node) -> void:
	node.set_meta("pooled_free", false)


func active_count(key: StringName) -> int:
	return int(_active.get(key, 0))


func free_count(key: StringName) -> int:
	return (_free.get(key, []) as Array).size()


func release_all(key: StringName) -> void:
	for child in get_children():
		if child.has_meta("pool_key") and child.get_meta("pool_key") == key:
			if not (child.has_meta("pooled_free") and child.get_meta("pooled_free")):
				release(child)
