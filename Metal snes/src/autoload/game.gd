extends Node
## Estado de partida: vidas, créditos, puntaje, piso actual, pausa.
## No debe conocer nodos concretos de la escena — solo datos y contadores.

var lives: int = 3
var continues: int = 3
var score: int = 0
var current_floor: int = 1
var paused: bool = false

func reset_run() -> void:
	lives = 3
	continues = 3
	score = 0
	current_floor = 1
	paused = false

func add_score(amount: int) -> void:
	score += amount
	Events.score_changed.emit(score)

func lose_life() -> bool:
	## Devuelve true si todavía queda al menos un continue disponible tras perder la vida.
	lives -= 1
	if lives > 0:
		return true
	if continues > 0:
		continues -= 1
		lives = 3
		return true
	return false
