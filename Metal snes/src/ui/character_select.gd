extends Control
## Selección de personaje: tres tarjetas con el sprite animado (la resaltada corre), nombre,
## licenciatura y una línea. Mando, teclado y ratón; confirmar en menos de 5 segundos.

const CARD_W := 96
const CARD_H := 160
const CARD_Y := 24
const CARD_XS := [16, 112, 208]

var cards: Array[Control] = []
var sprites: Array[AnimatedSprite2D] = []
var selected: int = 0
var confirmed: bool = false


func _ready() -> void:
	var bg := ColorRect.new()
	bg.size = Vector2(320, 224)
	bg.color = Color(0.09, 0.06, 0.08)
	add_child(bg)
	var title := Label.new()
	title.text = "ELIGE A TU ESTUDIANTE"
	title.position = Vector2(0, 8)
	title.size = Vector2(320, 10)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.modulate = Color(1.0, 0.9, 0.5)
	add_child(title)
	selected = maxi(Game.selected_index(), 0)
	for i in Game.characters.size():
		_make_card(i, Game.characters[i])
	var hint := Label.new()
	hint.text = "IZQ/DER ELEGIR · ENTER/A/CLIC CONFIRMAR · ESC VOLVER"
	hint.position = Vector2(0, 204)
	hint.size = Vector2(320, 10)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.modulate = Color(0.5, 0.5, 0.6)
	add_child(hint)
	_refresh()


func _make_card(i: int, data: CharacterData) -> void:
	var card := Control.new()
	card.position = Vector2(CARD_XS[i % CARD_XS.size()], CARD_Y)
	card.size = Vector2(CARD_W, CARD_H)
	add_child(card)
	var frame := ColorRect.new()
	frame.size = card.size
	frame.color = Color(0.16, 0.12, 0.16)
	card.add_child(frame)
	var sprite := AnimatedSprite2D.new()
	sprite.sprite_frames = data.sprite_frames
	sprite.centered = false
	sprite.offset = Vector2(-32, -64)
	sprite.position = Vector2(CARD_W / 2.0, 96)
	if data.sprite_frames != null and data.sprite_frames.has_animation("idle__pistol"):
		sprite.play("idle__pistol")
	card.add_child(sprite)
	var name_label := Label.new()
	name_label.text = data.display_name.to_upper()
	name_label.position = Vector2(0, 8)
	name_label.size = Vector2(CARD_W, 10)
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	card.add_child(name_label)
	var carrera := Label.new()
	carrera.text = data.carrera.to_upper()
	carrera.position = Vector2(0, 108)
	carrera.size = Vector2(CARD_W, 10)
	carrera.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	carrera.modulate = Color(0.8, 0.7, 0.55)
	carrera.autowrap_mode = TextServer.AUTOWRAP_WORD
	card.add_child(carrera)
	var tag := Label.new()
	tag.text = data.tagline
	tag.position = Vector2(2, 130)
	tag.size = Vector2(CARD_W - 4, 24)
	tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tag.autowrap_mode = TextServer.AUTOWRAP_WORD
	tag.modulate = Color(0.7, 0.7, 0.8)
	card.add_child(tag)
	cards.append(card)
	sprites.append(sprite)


func _refresh() -> void:
	for i in cards.size():
		var frame := cards[i].get_child(0) as ColorRect
		var data := Game.characters[i]
		var on := i == selected
		frame.color = Color(0.26, 0.2, 0.26) if on else Color(0.16, 0.12, 0.16)
		frame.modulate = Color.WHITE if on else Color(0.6, 0.6, 0.6)
		var sprite := sprites[i]
		sprite.modulate = Color.WHITE if on else Color(0.5, 0.5, 0.5)
		if data.sprite_frames == null:
			continue
		var anim := "run__pistol" if on else "idle__pistol"
		if data.sprite_frames.has_animation(anim) and sprite.animation != anim:
			sprite.play(anim)


func _move(delta: int) -> void:
	if cards.is_empty():
		return
	selected = wrapi(selected + delta, 0, cards.size())
	AudioManager.play(&"ui_move")
	_refresh()


func _confirm() -> void:
	if confirmed or cards.is_empty():
		return
	confirmed = true
	Game.select_character(selected)
	Game.reset_run()
	AudioManager.play(&"ui_confirm")
	get_tree().create_timer(0.5).timeout.connect(func() -> void: Game.go_to(Game.SCENE_LEVEL))


func _unhandled_input(event: InputEvent) -> void:
	if confirmed:
		return
	if event.is_action_pressed("ui_left") or event.is_action_pressed("move_left"):
		_move(-1)
	elif event.is_action_pressed("ui_right") or event.is_action_pressed("move_right"):
		_move(1)
	elif event.is_action_pressed("ui_accept") or event.is_action_pressed("shoot") or event.is_action_pressed("jump"):
		_confirm()
	elif event.is_action_pressed("ui_cancel") or event.is_action_pressed("pause"):
		Game.go_to(Game.SCENE_TITLE)
	elif event is InputEventMouseMotion:
		var i := _card_at((event as InputEventMouseMotion).position)
		if i >= 0 and i != selected:
			selected = i
			_refresh()
	elif event is InputEventMouseButton and (event as InputEventMouseButton).pressed:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_RIGHT:
			Game.go_to(Game.SCENE_TITLE)
			return
		var i := _card_at(mb.position)
		if i >= 0:
			selected = i
			_refresh()
			_confirm()


func _card_at(pos: Vector2) -> int:
	for i in cards.size():
		if Rect2(cards[i].position, cards[i].size).has_point(pos):
			return i
	return -1
