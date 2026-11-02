class_name EnemyData
extends Resource
## Enemigo orientado a datos (ADR-005 + paso 1.9): un perfil de IA parametrizado, sus sprites y
## sus números. Crear un enemigo nuevo = crear un .tres, cero código.

enum Profile { ADVANCER, STATIC, AMBUSH, JUMPER, FLIER, BOSS }

@export var id: StringName = &"velociraptor"
@export var display_name: String = "Velociraptor"
@export var era: String = "cretacico"
@export var sprite_frames: SpriteFrames
@export var profile: Profile = Profile.ADVANCER
@export var max_health: int = 3
@export var speed: float = 60.0
@export var score: int = 100
@export var contact_damage: int = 1
@export var hurtbox_size: Vector2 = Vector2(20, 20)
@export var body_size: Vector2 = Vector2(16, 16)
@export var sprite_cell: Vector2i = Vector2i(48, 48)
@export var flying: bool = false
@export var fly_height: float = 48.0          # altura sobre el suelo a la que patrulla (voladores)
@export var detect_range: float = 160.0
@export var stop_distance: float = 0.0
@export var attack_range: float = 24.0
@export var attack_cooldown: float = 1.4
@export var telegraph_time: float = 0.4
@export var recover_time: float = 0.6
@export var lunge_speed: float = 120.0
@export var jump_velocity: float = -220.0
@export var jump_interval: float = 1.2
@export var ranged: bool = false
@export var projectile_speed: float = 120.0
@export var hit_sound: StringName = &"hit"
@export var die_sound: StringName = &"enemy_die"
