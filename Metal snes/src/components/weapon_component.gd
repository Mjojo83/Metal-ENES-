class_name WeaponComponent
extends Node
## Dispara según un WeaponData (paso 1.5). Lleva la munición y la cadencia; al acabarse la
## munición vuelve al arma por defecto (nunca dejar al jugador sin poder disparar, sección 5.3).

signal fired(weapon: WeaponData, direction: Vector2)
signal weapon_changed(weapon: WeaponData, ammo: int)
signal ammo_changed(ammo: int)

@export var default_weapon: WeaponData

var weapon: WeaponData
var ammo: int = 0
var cooldown: float = 0.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 1234
	if default_weapon != null and weapon == null:
		equip(default_weapon)


func _physics_process(delta: float) -> void:
	if cooldown > 0.0:
		cooldown = maxf(cooldown - delta, 0.0)


func equip(data: WeaponData) -> void:
	weapon = data
	ammo = -1 if data.is_default else data.max_ammo
	cooldown = 0.0
	weapon_changed.emit(weapon, ammo)


func has_infinite_ammo() -> bool:
	return weapon != null and weapon.is_default


func can_fire() -> bool:
	return weapon != null and cooldown <= 0.0


func try_fire(origin: Vector2, direction: Vector2, shooter: Node2D = null) -> bool:
	if not can_fire():
		return false
	cooldown = 1.0 / maxf(weapon.fire_rate, 0.01)
	var n := maxi(weapon.projectiles_per_shot, 1)
	for i in n:
		var angle := 0.0
		if n > 1:
			angle = deg_to_rad(lerpf(-weapon.spread_degrees / 2.0, weapon.spread_degrees / 2.0, float(i) / float(n - 1)))
			angle += deg_to_rad(_rng.randf_range(-2.0, 2.0))
		elif weapon.spread_degrees > 0.0:
			angle = deg_to_rad(_rng.randf_range(-weapon.spread_degrees / 2.0, weapon.spread_degrees / 2.0))
		var dir := direction.normalized().rotated(angle)
		var bullet := Pools.acquire(weapon.projectile_key)
		if bullet != null and bullet.has_method("launch"):
			bullet.launch(origin, dir, weapon, shooter)
	fired.emit(weapon, direction)
	if not weapon.is_default:
		ammo -= 1
		ammo_changed.emit(ammo)
		if ammo <= 0 and default_weapon != null:
			equip(default_weapon)
	return true


func add_ammo(amount: int) -> void:
	if weapon == null or weapon.is_default:
		return
	ammo = mini(ammo + amount, weapon.max_ammo)
	ammo_changed.emit(ammo)
