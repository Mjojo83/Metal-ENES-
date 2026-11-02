class_name VfxSprite
extends Node2D
## Efecto visual de un solo uso (fogonazo, chispa, humo). Pooled: `play_effect()` lo arranca y
## al terminar se devuelve solo al pool. Las hojas van en assets/sprites/vfx/<nombre>.png.

const EFFECTS := {
	&"muzzle_flash": {"frames": 2, "fps": 24.0, "size": 8},
	&"hit_spark": {"frames": 3, "fps": 24.0, "size": 8},
	&"puff": {"frames": 4, "fps": 14.0, "size": 24},
}

var _frames: int = 1
var _fps: float = 12.0
var _t: float = 0.0
var _textures: Dictionary = {}

@onready var sprite: Sprite2D = $Sprite


func play_effect(effect: StringName, at: Vector2, flip: bool = false) -> void:
	var info: Dictionary = EFFECTS.get(effect, {"frames": 1, "fps": 12.0, "size": 8})
	if not _textures.has(effect):
		_textures[effect] = load("res://assets/sprites/vfx/%s.png" % effect)
	sprite.texture = _textures[effect]
	sprite.hframes = int(info["frames"])
	sprite.frame = 0
	sprite.flip_h = flip
	_frames = int(info["frames"])
	_fps = float(info["fps"])
	_t = 0.0
	global_position = at


func _process(delta: float) -> void:
	_t += delta
	var frame := int(_t * _fps)
	if frame >= _frames:
		if has_meta("pool_key"):
			Pools.release(self)
		else:
			queue_free()
		return
	sprite.frame = frame
