extends Control
## Pantalla de título (paso 5.1). Cualquier botón de acción lleva a la selección de personaje.

var _prompt: Label
var _t: float = 0.0


func _ready() -> void:
	var bg := ColorRect.new()
	bg.size = Vector2(320, 224)
	bg.color = Color(0.09, 0.06, 0.08)
	add_child(bg)
	_center("CATÁSTROFE EN LA", 56, Color(1.0, 0.9, 0.5))
	_center("BIBLIOTECA", 68, Color(1.0, 0.9, 0.5))
	_center("DEEP FALL · PISO 1: CIENCIAS DE LA TIERRA", 90, Color(0.8, 0.7, 0.55))
	_prompt = _center("PRESIONA ENTER, START O CLIC", 130, Color.WHITE)
	_center("MEJOR PUNTAJE %08d" % Game.high_score, 150, Color(0.7, 0.7, 0.8))
	_center("WASD/FLECHAS MOVER · ESPACIO SALTAR · J/CLIC DISPARAR", 196, Color(0.5, 0.5, 0.6))
	_center("MANDO: STICK · A SALTAR · X/RT DISPARAR", 206, Color(0.5, 0.5, 0.6))


func _center(text: String, y: float, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.position = Vector2(0, y)
	l.size = Vector2(320, 10)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.modulate = color
	add_child(l)
	return l


func _process(delta: float) -> void:
	_t += delta
	_prompt.visible = int(_t * 2.0) % 2 == 0


func _unhandled_input(event: InputEvent) -> void:
	var go := event.is_action_pressed("ui_accept") or event.is_action_pressed("shoot") \
		or event.is_action_pressed("jump") or event.is_action_pressed("pause")
	if event is InputEventMouseButton and (event as InputEventMouseButton).pressed:
		go = true
	if go:
		AudioManager.play(&"ui_confirm")
		Game.go_to(Game.SCENE_SELECT)
		get_viewport().set_input_as_handled()
