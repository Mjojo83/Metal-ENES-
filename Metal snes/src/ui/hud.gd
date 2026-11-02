extends CanvasLayer
## HUD (paso 3.6): vidas, créditos, puntaje, arma + munición, grito del arma, barra del jefe y
## mensajes (PAUSA, GAME OVER, piso despejado). Fuente bitmap del tema del proyecto, legible a 1x.
## Sigue procesando en pausa para mostrar el menú y reaccionar a la tecla.

const SHOUT_TIME := 1.2
const MESSAGE_COLOR := Color(1.0, 0.9, 0.5)

var lives_label: Label
var credits_label: Label
var score_label: Label
var ammo_label: Label
var weapon_icon: TextureRect
var life_icon: TextureRect
var shout_label: Label
var message_label: Label
var sub_label: Label
var boss_bg: ColorRect
var boss_fill: ColorRect
var _shout_timer: float = 0.0
var _flash_timer: float = 0.0
var _infinity: Texture2D = preload("res://assets/sprites/ui/infinity.png")
var _state: String = "play"   # play | pause | over | cleared


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 10
	life_icon = _icon(preload("res://assets/sprites/ui/life.png"), Vector2(8, 6))
	lives_label = _label("×3", Vector2(17, 5))
	credits_label = _label("CRED 3", Vector2(8, 15))
	score_label = _label("00000000", Vector2(112, 5), 96, HORIZONTAL_ALIGNMENT_RIGHT)
	weapon_icon = _icon(null, Vector2(232, 6))
	ammo_label = _label("", Vector2(258, 5))
	shout_label = _label("", Vector2(0, 34), 320, HORIZONTAL_ALIGNMENT_CENTER)
	shout_label.modulate = MESSAGE_COLOR
	shout_label.visible = false
	message_label = _label("", Vector2(0, 92), 320, HORIZONTAL_ALIGNMENT_CENTER)
	message_label.modulate = MESSAGE_COLOR
	message_label.visible = false
	sub_label = _label("", Vector2(0, 106), 320, HORIZONTAL_ALIGNMENT_CENTER)
	sub_label.visible = false
	boss_bg = ColorRect.new()
	boss_bg.position = Vector2(80, 210)
	boss_bg.size = Vector2(160, 6)
	boss_bg.color = Color(0.1, 0.05, 0.08, 0.9)
	boss_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	boss_bg.visible = false
	add_child(boss_bg)
	boss_fill = ColorRect.new()
	boss_fill.position = Vector2(81, 211)
	boss_fill.size = Vector2(158, 4)
	boss_fill.color = Color(0.85, 0.2, 0.2)
	boss_fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	boss_bg.add_child(boss_fill)
	boss_fill.position = Vector2(1, 1)

	Events.lives_changed.connect(_on_lives_changed)
	Events.score_changed.connect(_on_score_changed)
	Events.weapon_changed.connect(_on_weapon_changed)
	Events.ammo_changed.connect(_on_ammo_changed)
	Events.boss_health_changed.connect(_on_boss_health)
	Events.game_over.connect(_on_game_over)
	Events.level_cleared.connect(_on_level_cleared)
	Events.tremor_started.connect(_on_tremor)
	Events.wave_started.connect(_on_wave_started)
	Events.enemy_killed.connect(_on_enemy_killed)
	_on_lives_changed(Game.lives, Game.continues)
	_on_score_changed(Game.score)
	# el jugador ya existe (es hermano anterior): leer su arma actual
	var player := get_tree().get_first_node_in_group("player")
	if player != null:
		var wc: WeaponComponent = player.get_node_or_null("Weapon")
		if wc != null and wc.weapon != null:
			_on_weapon_changed(wc.weapon, wc.ammo)
			shout_label.visible = false


func _label(text: String, pos: Vector2, width: float = 0.0, align: int = HORIZONTAL_ALIGNMENT_LEFT) -> Label:
	var l := Label.new()
	l.text = text
	l.position = pos
	if width > 0.0:
		l.size = Vector2(width, 10)
		l.horizontal_alignment = align as HorizontalAlignment
	add_child(l)
	return l


func _icon(tex: Texture2D, pos: Vector2) -> TextureRect:
	var t := TextureRect.new()
	t.texture = tex
	t.position = pos
	t.stretch_mode = TextureRect.STRETCH_KEEP
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(t)
	return t


func _process(delta: float) -> void:
	if _shout_timer > 0.0:
		_shout_timer -= delta
		if _shout_timer <= 0.0:
			shout_label.visible = false
	if _flash_timer > 0.0:
		_flash_timer -= delta
		ammo_label.modulate = Color(1, 0.4, 0.4) if int(_flash_timer * 12.0) % 2 == 0 else Color.WHITE
		if _flash_timer <= 0.0:
			ammo_label.modulate = Color.WHITE
	if _state == "pause":
		message_label.visible = int(Time.get_ticks_msec() / 400) % 2 == 0


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") and _state in ["play", "pause"]:
		Game.toggle_pause()
		_state = "pause" if Game.paused else "play"
		message_label.text = "PAUSA"
		message_label.visible = Game.paused
		sub_label.text = "ESC / START PARA SEGUIR"
		sub_label.visible = Game.paused
		get_viewport().set_input_as_handled()


func _on_lives_changed(lives: int, continues: int) -> void:
	lives_label.text = "×%d" % maxi(lives, 0)
	credits_label.text = "CRED %d" % continues


func _on_score_changed(score: int) -> void:
	score_label.text = "%08d" % score


func _on_weapon_changed(weapon: WeaponData, ammo: int) -> void:
	weapon_icon.texture = weapon.icon
	if weapon.is_default:
		ammo_label.text = ""
		if ammo_label.get_child_count() == 0:
			var inf := TextureRect.new()
			inf.texture = _infinity
			inf.stretch_mode = TextureRect.STRETCH_KEEP
			inf.position = Vector2(0, 2)
			ammo_label.add_child(inf)
		(ammo_label.get_child(0) as TextureRect).visible = true
	else:
		if ammo_label.get_child_count() > 0:
			(ammo_label.get_child(0) as TextureRect).visible = false
		ammo_label.text = str(ammo)
	shout_label.text = weapon.shout
	shout_label.visible = true
	_shout_timer = SHOUT_TIME


func _on_ammo_changed(ammo: int) -> void:
	ammo_label.text = str(maxi(ammo, 0))
	if ammo <= 10:
		_flash_timer = 0.3


func _on_boss_health(current: int, max_health: int) -> void:
	boss_bg.visible = current > 0
	boss_fill.size.x = 158.0 * float(current) / float(maxi(max_health, 1))


func _on_enemy_killed(id: StringName, _pos: Vector2) -> void:
	if id == &"trex":
		boss_bg.visible = false


func _on_wave_started(id: StringName) -> void:
	if id.begins_with("boss"):
		boss_bg.visible = true
		boss_fill.size.x = 158.0
		_show_shout("¡TR-001 SE ESCAPÓ DE LA LITOTECA!")
	else:
		_show_shout("¡OLEADA!")


func _on_tremor(_intensity: float) -> void:
	_show_shout("¡TEMBLOR!")


func _show_shout(text: String) -> void:
	shout_label.text = text
	shout_label.visible = true
	_shout_timer = SHOUT_TIME


func _on_game_over() -> void:
	_state = "over"
	message_label.text = "GAME OVER"
	message_label.visible = true
	sub_label.text = "PUNTAJE %d" % Game.score
	sub_label.visible = true


func _on_level_cleared() -> void:
	_state = "cleared"
	message_label.text = "¡PISO 1 DESPEJADO!"
	message_label.visible = true
	sub_label.text = "EL PROFESOR ESTÁ A SALVO · PUNTAJE %d" % Game.score
	sub_label.visible = true
