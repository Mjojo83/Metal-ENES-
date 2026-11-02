class_name CharacterData
extends Resource
## Personaje jugable (sección 4 de 02_Documentacion_Proyecto): mismas constantes de movimiento
## para todos; se distinguen por sprites, paleta y detalles cosméticos.

@export var id: StringName = &"homi"
@export var display_name: String = "Homi"
@export var carrera: String = "Neurociencias"
@export var tagline: String = ""
@export var sprite_frames: SpriteFrames
@export var portrait: Texture2D
@export var hurtbox_size: Vector2 = Vector2(10, 22)
@export var accent_color: Color = Color.WHITE
