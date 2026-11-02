extends Node
## Paso 1.4 (pools) + datos: 80 balas precargadas, prestar/devolver sin crear nodos nuevos;
## los tres CharacterData cargan con sus SpriteFrames y animaciones mínimas; los 14 EnemyData
## cargan y apuntan a SpriteFrames con idle/move/attack/die. (Requiere haber importado el proyecto:
## `--headless --import` una vez, para que existan los PNG importados.)

var all_ok := true


func _ok(label: String, cond: bool, detail: String = "") -> void:
	if not cond:
		all_ok = false
	print("%s -> %s %s" % [label, "OK" if cond else "FALLO", detail])


func _ready() -> void:
	_ok("1.4 pool de balas precargado (≥ 80)", Pools.free_count(&"bullet") >= 80, "libres=%d" % Pools.free_count(&"bullet"))
	var nodes_before := Performance.get_monitor(Performance.OBJECT_NODE_COUNT)
	var taken: Array[Node] = []
	for i in 60:
		taken.append(Pools.acquire(&"bullet"))
	_ok("1.4 prestar 60 balas -> active_count 60", Pools.active_count(&"bullet") == 60, "activas=%d" % Pools.active_count(&"bullet"))
	for b in taken:
		Pools.release(b)
	Pools.release(taken[0])  # doble devolución: no debe romper la cuenta
	_ok("1.4 devolver todas -> active_count 0 (doble release ignorado)", Pools.active_count(&"bullet") == 0, "activas=%d" % Pools.active_count(&"bullet"))
	var nodes_after := Performance.get_monitor(Performance.OBJECT_NODE_COUNT)
	_ok("1.4 el conteo de nodos no crece al reciclar", nodes_after == nodes_before, "antes=%d después=%d" % [nodes_before, nodes_after])

	var required := ["idle__pistol", "run__pistol", "jump__pistol", "fall__pistol", "crouch__pistol", "die__pistol",
		"shoot__shotgun", "aim_up__hmg", "aim_diag_up__pistol", "crouch_shoot__hmg"]
	for id in ["homi", "mariana", "oscar"]:
		var data := load("res://data/characters/%s.tres" % id) as CharacterData
		var ok := data != null and data.sprite_frames != null
		var missing: Array[String] = []
		if ok:
			for a in required:
				if not data.sprite_frames.has_animation(a):
					missing.append(a)
		_ok("4 CharacterData %s con sprites y animaciones" % id, ok and missing.is_empty(), "faltan=%s" % [missing])
	_ok("4 Game cargó los tres personajes", Game.characters.size() == 3, "n=%d" % Game.characters.size())

	var dir := DirAccess.open("res://data/enemies")
	var n := 0
	var bad: Array[String] = []
	if dir != null:
		for f in dir.get_files():
			if not f.ends_with(".tres"):
				continue
			var e := load("res://data/enemies/" + f) as EnemyData
			n += 1
			if e == null or e.sprite_frames == null:
				bad.append(f)
				continue
			for a in ["idle", "move", "attack", "die"]:
				if not e.sprite_frames.has_animation(a):
					bad.append(f + ":" + a)
	_ok("1.9 14 EnemyData cargan con idle/move/attack/die", n == 14 and bad.is_empty(), "n=%d problemas=%s" % [n, bad])
	print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
	get_tree().quit()
