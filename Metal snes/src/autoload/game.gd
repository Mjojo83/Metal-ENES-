extends Node
## Estado de partida: vidas, créditos, puntaje, piso actual, pausa, personaje elegido y ajustes.
## No debe conocer nodos concretos de la escena — solo datos y contadores.

const SAVE_PATH := "user://catastrofe_save.json"
const CHARACTER_DIR := "res://data/characters/"
const SCENE_TITLE := "res://src/ui/title.tscn"
const SCENE_SELECT := "res://src/ui/character_select.tscn"
const SCENE_LEVEL := "res://src/levels/deep_fall.tscn"

var lives: int = 3
var continues: int = 3
var score: int = 0
var current_floor: int = 1
var paused: bool = false

var characters: Array[CharacterData] = []
var selected_character: CharacterData
var high_score: int = 0
var settings := {
	"mouse_aim": "auto",     # auto | on | off
	"screenshake": true,
	"shield": false,          # accesibilidad: chaleco de 2 impactos (propuesta, apagado)
}


func _ready() -> void:
	_load_characters()
	load_save()


func _load_characters() -> void:
	characters.clear()
	for id in ["homi", "mariana", "oscar"]:
		var path := CHARACTER_DIR + id + ".tres"
		if ResourceLoader.exists(path):
			var data := load(path) as CharacterData
			if data != null:
				characters.append(data)
	if not characters.is_empty() and selected_character == null:
		selected_character = characters[0]


func reset_run() -> void:
	lives = 3
	continues = 3
	score = 0
	current_floor = 1
	paused = false
	Events.lives_changed.emit(lives, continues)
	Events.score_changed.emit(score)


func add_score(amount: int) -> void:
	score += amount
	if score > high_score:
		high_score = score
	Events.score_changed.emit(score)


func lose_life() -> bool:
	## Devuelve true si todavía queda al menos un continue disponible tras perder la vida.
	lives -= 1
	var alive := true
	if lives <= 0:
		if continues > 0:
			continues -= 1
			lives = 3
		else:
			alive = false
	Events.lives_changed.emit(lives, continues)
	return alive


func select_character(index: int) -> void:
	if characters.is_empty():
		return
	selected_character = characters[wrapi(index, 0, characters.size())]
	save_game()


func selected_index() -> int:
	return characters.find(selected_character)


func go_to(scene_path: String) -> void:
	get_tree().paused = false
	paused = false
	get_tree().call_deferred("change_scene_to_file", scene_path)


func toggle_pause() -> void:
	paused = not paused
	get_tree().paused = paused


# --- guardado (paso 5.2: JSON en user://, tolerante a archivos rotos) ---------------------

func save_game() -> void:
	var data := {
		"version": 1,
		"high_score": high_score,
		"character": selected_character.id if selected_character != null else "",
		"settings": settings,
	}
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(data, "\t"))
		file.close()


func load_save() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed = JSON.parse_string(file.get_as_text())
	file.close()
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var data: Dictionary = parsed
	high_score = int(data.get("high_score", 0))
	var saved_settings = data.get("settings", {})
	if typeof(saved_settings) == TYPE_DICTIONARY:
		for key in settings.keys():
			if saved_settings.has(key):
				settings[key] = saved_settings[key]
	var char_id := String(data.get("character", ""))
	for c in characters:
		if String(c.id) == char_id:
			selected_character = c
