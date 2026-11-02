extends Node2D
## Paso 1.5: las tres armas cargan como WeaponData; cadencia, dispersión y munición reales con el
## jugador disparando 5 s con cada una; vuelta a la pistola al acabarse la munición.

@onready var player: CharacterBody2D = $Player

var all_ok := true
var stage := 0
var stage_frame := 0
var fired := 0
var weapons: Array[WeaponData] = []
var names := ["pistol", "shotgun", "heavy_machine_gun"]
var expected_shots := [40.0, 10.0, 75.0]
var changes := 0


func _ok(label: String, cond: bool, detail: String = "") -> void:
	if not cond:
		all_ok = false
	print("%s -> %s %s" % [label, "OK" if cond else "FALLO", detail])


func _ready() -> void:
	for n in names:
		var w := load("res://data/weapons/%s.tres" % n) as WeaponData
		_ok("1.5 carga %s.tres como WeaponData" % n, w != null and w.id == StringName(n))
		weapons.append(w)
	player.weapon.fired.connect(func(_w: WeaponData, _d: Vector2) -> void: fired += 1)
	player.weapon.weapon_changed.connect(func(_w: WeaponData, _a: int) -> void: changes += 1)
	player.input.enabled = false   # el disparo se dispara directo al componente, sin Input


func _physics_process(_delta: float) -> void:
	stage_frame += 1
	if stage < 3:
		var w := weapons[stage]
		if stage_frame == 1:
			player.weapon.equip(w)
			fired = 0
		if stage_frame <= 300:
			player.weapon.try_fire(player.global_position + Vector2(10, -20), Vector2.RIGHT, player)
		if stage_frame == 40 and stage == 1:
			# dispersión: ángulos de los perdigones vivos ≈ 25°
			var angles: Array[float] = []
			for node in Pools.get_children():
				if node is Bullet and node.process_mode != Node.PROCESS_MODE_DISABLED:
					angles.append(rad_to_deg((node as Bullet).direction.angle()))
			if angles.size() >= 2:
				var spread: float = angles.max() - angles.min()
				_ok("1.5 escopeta dispersa ~25° (%d perdigones)" % angles.size(), absf(spread - 25.0) < 6.0, "medido %.1f°" % spread)
			else:
				_ok("1.5 escopeta tiene perdigones vivos", false)
		if stage_frame == 301:
			var expected: float = expected_shots[stage]
			_ok("1.5 %s: ~%d disparos en 5 s" % [w.id, int(expected)], absf(float(fired) - expected) <= expected * 0.2, "disparos=%d" % fired)
			if w.is_default:
				_ok("1.5 pistola infinita", player.weapon.ammo == -1 and player.weapon.weapon.id == &"pistol")
			else:
				var still := player.weapon.weapon.id == w.id
				_ok("1.5 %s descuenta munición" % w.id, (not still) or player.weapon.ammo == w.max_ammo - fired, "ammo=%d" % player.weapon.ammo)
			Pools.release_all(&"bullet")
			stage += 1
			stage_frame = 0
	elif stage == 3:
		# vuelta a la pistola: escopeta con 3 cartuchos, 4 intentos
		if stage_frame == 1:
			player.weapon.equip(weapons[1])
			player.weapon.ammo = 3
			changes = 0
		if stage_frame in [2, 40, 80, 120]:
			player.weapon.cooldown = 0.0
			player.weapon.try_fire(player.global_position, Vector2.RIGHT, player)
		if stage_frame == 130:
			_ok("5.3 al acabarse la munición vuelve a la pistola", player.weapon.weapon.id == &"pistol" and player.weapon.ammo == -1, "arma=%s cambios=%d" % [player.weapon.weapon.id, changes])
			_ok("5.3 la señal weapon_changed se emite una vez al volver", changes == 1, "cambios=%d" % changes)
			stage = 4
	else:
		print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
		get_tree().quit()
