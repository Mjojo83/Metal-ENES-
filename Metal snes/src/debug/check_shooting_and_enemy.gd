extends Node2D
## Fase 0, pasos 0.8 y 0.9 — cadencia de disparo (~8/s, sin fugas de nodos) y enemigo caja que
## recibe daño y muere. Los daños se cuentan conectando Events.enemy_killed, y las balas se
## detectan por duck-typing (tienen el método setup()) al entrar al árbol.

@onready var player: CharacterBody2D = $Player

var frame := 0
var stage := 0
var stage_frame := 0
var all_ok := true

var total_fired := 0
var peak_alive := 0
var alive_bullets := 0

var enemy: CharacterBody2D
var enemy_scene: PackedScene = preload("res://src/actors/enemies/enemy_debug_box.tscn")
var enemy_killed_signal_ok := false
var enemy_freed := false


func _ok(label: String, cond: bool, detail: String = "") -> void:
	if not cond:
		all_ok = false
	print("%s -> %s %s" % [label, "OK" if cond else "FALLO", detail])


func _ready() -> void:
	get_tree().node_added.connect(_on_node_added)
	get_tree().node_removed.connect(_on_node_removed)
	Events.enemy_killed.connect(_on_enemy_killed)


func _on_node_added(node: Node) -> void:
	if node.has_method("setup"):  # bullet.gd
		total_fired += 1
		alive_bullets += 1
		peak_alive = max(peak_alive, alive_bullets)


func _on_node_removed(node: Node) -> void:
	if node.has_method("setup"):
		alive_bullets -= 1


func _on_enemy_killed(enemy_type: StringName, _pos: Vector2) -> void:
	enemy_killed_signal_ok = enemy_type == &"debug_box"


func _physics_process(_delta: float) -> void:
	frame += 1
	stage_frame += 1

	match stage:
		0:  # asentarse, sin enemigo en el camino todavia
			if stage_frame >= 3:
				stage = 1
				stage_frame = 0

		1:  # sostener disparo 5 segundos (300 ticks) hacia el vacío
			if stage_frame == 1:
				Input.action_press("shoot")
			if stage_frame == 300:
				Input.action_release("shoot")
			if stage_frame == 300:
				var expected := 8.0 * 5.0
				var within_range: bool = abs(total_fired - expected) < expected * 0.2
				_ok("0.8 cadencia ~8 balas/s sostenida (5s)", within_range, "disparadas=%d esperado=%.0f" % [total_fired, expected])
				stage = 2
				stage_frame = 0

		2:  # esperar a que las balas en vuelo salgan de pantalla y se liberen
			if stage_frame >= 60:
				_ok("0.8 sin fuga de nodos: balas vivas vuelven a 0", alive_bullets == 0, "vivas=%d pico=%d" % [alive_bullets, peak_alive])
				stage = 3
				stage_frame = 0

		3:  # aparece un enemigo en la linea de fuego y se le dispara hasta matarlo
			if stage_frame == 1:
				enemy = enemy_scene.instantiate()
				add_child(enemy)
				enemy.global_position = Vector2(player.global_position.x + 40.0, player.global_position.y)
			if stage_frame == 5:
				Input.action_press("shoot")
			if stage_frame == 60:
				Input.action_release("shoot")
				enemy_freed = not is_instance_valid(enemy) or enemy.is_queued_for_deletion()
				_ok("0.9 el enemigo muere tras 3 impactos y se libera", enemy_freed)
				_ok("0.9 Events.enemy_killed se emite con el tipo correcto", enemy_killed_signal_ok)
				stage = 4
				stage_frame = 0

		4:
			print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
			get_tree().quit()
