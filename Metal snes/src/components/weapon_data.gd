class_name WeaponData
extends Resource
## Arma como Resource (paso 1.5). Balancear = abrir el .tres y cambiar un número. La munición
## actual NO vive aquí (el Resource es compartido): vive en WeaponComponent.

@export var id: StringName = &"pistol"
@export var display_name: String = "Pistola"
@export var shout: String = "¡DE CAJÓN!"
@export var projectile_key: StringName = &"bullet"
@export var bullet_texture: Texture2D
@export var damage: int = 1
@export var fire_rate: float = 8.0          # disparos por segundo
@export var projectiles_per_shot: int = 1
@export var spread_degrees: float = 0.0
@export var projectile_speed: float = 350.0
@export var projectile_range: float = 400.0
@export var max_ammo: int = 200
@export var is_default: bool = false        # la pistola infinita
@export var auto_fire: bool = true          # mantener disparo = seguir disparando
@export var icon: Texture2D
@export var pickup_texture: Texture2D
@export var fire_sound: StringName = &"shot_pistol"
@export var recoil_px: float = 1.0
@export var screenshake: float = 0.0
@export var hitstop_frames: int = 0
@export var muzzle_frames: int = 1
