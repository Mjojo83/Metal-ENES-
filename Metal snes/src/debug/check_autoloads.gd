extends Node
## Fase 0, paso 0.4 — comprobación: emite Events.player_died y confirma que llega a un
## receptor sin relación directa (otro nodo cualquiera). Además confirma que los cinco
## autoloads existen, en orden, y que Game.gd mantiene estado básico.
##
## Se corre como escena (no como --script suelto): los autoloads solo se instancian cuando
## el árbol de escena arranca de verdad. Ver check_autoloads.tscn.

var received := false

func _on_player_died() -> void:
	received = true

func _ready() -> void:
	var all_ok := true

	var expected_order := ["Events", "Game", "Pools", "AudioManager", "Debug"]
	var root := get_tree().root
	for autoload_name in expected_order:
		if not root.has_node(autoload_name):
			print("FALTA autoload: %s" % autoload_name)
			all_ok = false
	print("Autoloads presentes: %s" % str(expected_order))

	var receiver := Node.new()
	add_child(receiver)
	Events.player_died.connect(_on_player_died)
	Events.player_died.emit()
	print("Events.player_died llegó al receptor: %s" % ("OK" if received else "FALLO"))
	if not received:
		all_ok = false

	Game.reset_run()
	var start_continues := Game.continues
	Game.add_score(150)
	var score_ok := Game.score == 150
	Game.lose_life()
	Game.lose_life()
	Game.lose_life()  # esta debería consumir un continue y resetear lives a 3
	var continue_ok := Game.continues == start_continues - 1 and Game.lives == 3
	print("Game.add_score -> score=%d %s" % [Game.score, "OK" if score_ok else "FALLO"])
	print("Game.lose_life x3 -> lives=%d continues=%d %s" % [Game.lives, Game.continues, "OK" if continue_ok else "FALLO"])
	if not score_ok or not continue_ok:
		all_ok = false

	print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
	get_tree().quit()
