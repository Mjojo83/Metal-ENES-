extends SceneTree
## Paso 1.1: los doce nombres de capa y los bits de Layers coinciden con la tabla del documento.

func _initialize() -> void:
	var names := ["terrain", "player_body", "one_way", "enemy_body", "player_hurtbox", "player_hitbox",
		"enemy_hurtbox", "enemy_hitbox", "pickups", "hazards", "destructibles", "triggers"]
	var all_ok := true
	for i in names.size():
		var key := "layer_names/2d_physics/layer_%d" % (i + 1)
		var actual := String(ProjectSettings.get_setting(key, ""))
		var ok := actual == names[i]
		all_ok = all_ok and ok
		print("%s -> '%s' %s" % [key, actual, "OK" if ok else "FALLO (esperado %s)" % names[i]])
	var bits := {"terrain": Layers.TERRAIN, "player_body": Layers.PLAYER_BODY, "one_way": Layers.ONE_WAY,
		"enemy_body": Layers.ENEMY_BODY, "player_hurtbox": Layers.PLAYER_HURTBOX, "player_hitbox": Layers.PLAYER_HITBOX,
		"enemy_hurtbox": Layers.ENEMY_HURTBOX, "enemy_hitbox": Layers.ENEMY_HITBOX, "pickups": Layers.PICKUPS,
		"hazards": Layers.HAZARDS, "destructibles": Layers.DESTRUCTIBLES, "triggers": Layers.TRIGGERS}
	for i in names.size():
		var ok: bool = int(bits[names[i]]) == (1 << i)
		all_ok = all_ok and ok
		print("Layers.%s = %d %s" % [names[i].to_upper(), bits[names[i]], "OK" if ok else "FALLO"])
	# escenas: la bala del jugador pega a enemy_hurtbox + terreno, nunca al jugador
	var bullet: PackedScene = load("res://src/projectiles/bullet.tscn")
	var b := bullet.instantiate() as Area2D
	var bullet_ok := b.collision_layer == Layers.PLAYER_HITBOX and (b.collision_mask & Layers.ENEMY_HURTBOX) != 0 \
		and (b.collision_mask & Layers.TERRAIN) != 0 and (b.collision_mask & Layers.PLAYER_HURTBOX) == 0
	print("bullet.tscn capa=%d mascara=%d %s" % [b.collision_layer, b.collision_mask, "OK" if bullet_ok else "FALLO"])
	all_ok = all_ok and bullet_ok
	b.free()
	print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
	quit()
