extends Node
## Herramientas de depuración (paso 1.10). Solo existen en builds de depuración:
## F1 overlay, F2 hitboxes, F3 invencibilidad, F6 dar arma, F7 spawn enemigo bajo el jugador.

var enabled: bool = false
var show_overlay: bool = false
var show_hitboxes: bool = false
var invincible: bool = false

var _layer: CanvasLayer
var _label: Label
var _drawer: Node2D
var _player: Node = null


func _ready() -> void:
	enabled = OS.is_debug_build()
	if not enabled:
		set_process(false)
		set_process_unhandled_input(false)
		return
	_layer = CanvasLayer.new()
	_layer.layer = 100
	add_child(_layer)
	_label = Label.new()
	_label.position = Vector2(4, 30)
	_label.add_theme_font_size_override("font_size", 8)
	_label.visible = false
	_layer.add_child(_label)
	_drawer = Node2D.new()
	_drawer.z_index = 50
	_drawer.draw.connect(_draw_boxes)
	add_child(_drawer)


func _unhandled_input(event: InputEvent) -> void:
	if not enabled:
		return
	if event.is_action_pressed("debug_toggle"):
		show_overlay = not show_overlay
		_label.visible = show_overlay
	elif event.is_action_pressed("debug_hitboxes"):
		show_hitboxes = not show_hitboxes
	elif event.is_action_pressed("debug_invincible"):
		invincible = not invincible
	elif event.is_action_pressed("debug_weapon"):
		Events.debug_give_weapon.emit()
	elif event.is_action_pressed("debug_spawn"):
		var player := get_tree().get_first_node_in_group("player") as Node2D
		if player != null:
			Events.debug_spawn_enemy.emit(player.global_position + Vector2(96, -8))


func _process(_delta: float) -> void:
	_drawer.queue_redraw()
	if not show_overlay:
		return
	var player := get_tree().get_first_node_in_group("player")
	var text := "FPS %d  nodos %d  balas %d" % [Engine.get_frames_per_second(),
		Performance.get_monitor(Performance.OBJECT_NODE_COUNT), Pools.active_count(&"bullet")]
	if player != null:
		text += "\n%s  pos %s  vel %s" % [player.get("state_name"), (player as Node2D).global_position.round(), player.get("velocity")]
	text += "\nenemigos %d  invencible %s  hitboxes %s" % [get_tree().get_nodes_in_group("enemies").size(), invincible, show_hitboxes]
	_label.text = text


func _draw_boxes() -> void:
	if not show_hitboxes:
		return
	var tree := get_tree()
	if tree == null:
		return
	for area in tree.get_nodes_in_group("hurtboxes"):
		_draw_area(area as Area2D, Color(0.2, 1.0, 0.3, 0.9))
	for area in tree.get_nodes_in_group("hitboxes"):
		_draw_area(area as Area2D, Color(1.0, 0.2, 0.2, 0.9))


func _draw_area(area: Area2D, color: Color) -> void:
	if area == null or not area.is_inside_tree() or not area.monitoring:
		return
	for child in area.get_children():
		var shape_node := child as CollisionShape2D
		if shape_node == null or shape_node.shape == null or shape_node.disabled:
			continue
		var rect := shape_node.shape.get_rect()
		var xform := _drawer.get_global_transform().affine_inverse() * shape_node.get_global_transform()
		_drawer.draw_set_transform_matrix(xform)
		_drawer.draw_rect(rect, color, false, 1.0)
	_drawer.draw_set_transform_matrix(Transform2D.IDENTITY)
