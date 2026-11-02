extends Node
## Reproduce SFX con un pool de reproductores y límite de voces (paso 3.5, versión mínima).
## Los clips se cargan bajo demanda desde assets/audio/sfx/<nombre>.wav (síntesis propia, sin
## derechos). Nunca carga assets del nivel ni conoce nodos del juego.

const SFX_DIR := "res://assets/audio/sfx/"
const MAX_VOICES := 12

var _players: Array[AudioStreamPlayer] = []
var _streams: Dictionary = {}
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	for i in MAX_VOICES:
		var p := AudioStreamPlayer.new()
		p.bus = &"Master"
		add_child(p)
		_players.append(p)


func play(name: StringName, volume_db: float = 0.0, pitch_variation: float = 0.05) -> void:
	var stream := _get_stream(name)
	if stream == null:
		return
	var player := _free_player()
	if player == null:
		return
	player.stream = stream
	player.volume_db = volume_db
	player.pitch_scale = 1.0 + _rng.randf_range(-pitch_variation, pitch_variation)
	player.play()


func _get_stream(name: StringName) -> AudioStream:
	if _streams.has(name):
		return _streams[name]
	var path := SFX_DIR + String(name) + ".wav"
	var stream: AudioStream = null
	if ResourceLoader.exists(path):
		stream = load(path) as AudioStream
	_streams[name] = stream
	return stream


func _free_player() -> AudioStreamPlayer:
	for p in _players:
		if not p.playing:
			return p
	# todas ocupadas: se roba la más antigua (prioridad simple)
	return _players[0]
