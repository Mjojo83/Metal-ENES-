extends Node2D
## Paso 1.2: Hurtbox/Hitbox/Health. Una hitbox enemiga mata al jugador una vez; una hurtbox
## invulnerable no recibe daño; una bala del jugador pega al enemigo de componentes y no al jugador.

@onready var player: CharacterBody2D = $Player
@onready var enemy: CharacterBody2D = $EnemyDebugBox

var all_ok := true
var stage := 0
var stage_frame := 0
var died := 0
var hits := 0


func _ok(label: String, cond: bool, detail: String = "") -> void:
	if not cond:
		all_ok = false
	print("%s -> %s %s" % [label, "OK" if cond else "FALLO", detail])


func _ready() -> void:
	Events.player_died.connect(func() -> void: died += 1)
	enemy.hurtbox.hit_received.connect(func(_d: int, _p: Vector2) -> void: hits += 1)
	player.input.enabled = false
	enemy.global_position = Vector2(-500, -500)


func _physics_process(_delta: float) -> void:
	stage_frame += 1
	match stage:
		0:  # hurtbox invulnerable: tocar al jugador no lo mata
			if stage_frame == 3:
				player.hurtbox.invulnerable = true
				enemy.global_position = player.global_position
			if stage_frame == 10:
				_ok("1.2 hurtbox invulnerable ignora la hitbox enemiga", died == 0 and not player.is_dead)
				enemy.global_position = Vector2(-500, -500)
				player.hurtbox.invulnerable = false
				stage = 1
				stage_frame = 0
		1:  # hitbox enemiga mata al jugador exactamente una vez aunque siga encima
			if stage_frame == 3:
				enemy.global_position = player.global_position
			if stage_frame == 15:
				_ok("1.2 hitbox enemiga -> hurtbox jugador -> Health.died una vez", died == 1 and player.is_dead, "died=%d" % died)
				enemy.global_position = Vector2(-500, -500)
				stage = 2
				stage_frame = 0
		2:  # tras reaparecer, i-frames: tocar al jugador no lo mata de inmediato
			if stage_frame == 70:
				_ok("1.2 reaparece con i-frames activos", not player.is_dead and player.health.is_invulnerable())
				enemy.global_position = player.global_position
			if stage_frame == 80:
				_ok("1.2 durante los i-frames no muere", died == 1 and not player.is_dead, "died=%d" % died)
				enemy.global_position = Vector2(player.global_position.x + 60, player.global_position.y)
				stage = 3
				stage_frame = 0
		3:  # la bala del jugador pega al enemigo por su hurtbox, no por el cuerpo
			if stage_frame == 1:
				player.facing = 1
			if stage_frame in [2, 12, 22]:
				player.weapon.cooldown = 0.0
				player.weapon.try_fire(player.global_position + Vector2(12, -10), Vector2.RIGHT, player)
			if stage_frame == 60:
				_ok("1.2 tres balas -> tres golpes en la hurtbox enemiga y muere", hits == 3 and not is_instance_valid(enemy), "hits=%d" % hits)
				stage = 4
		4:
			print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
			get_tree().quit()
