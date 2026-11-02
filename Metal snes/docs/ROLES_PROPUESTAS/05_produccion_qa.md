# 05 · Producción técnica y QA — iteración "jugable"

Revisado: `src/`, `project.godot`, docs 01/02, `tools/pixel_lab/`. Ojo: `enemigos y personajes/` tiene **3 JPEG de un solo pose** y referencias web de criaturas, no hojas de sprites.

## 1. Revisión crítica del código actual

| # | Dónde | Problema | Arreglo |
|---|---|---|---|
| 1 | `player.gd:51-58, 93, 109-117` | `Input.*` leído dentro del actor: no sirve para 3 personajes, IA ni pruebas | `PlayerInputComponent` que publica `move_axis`, `aim_v`, `jump_*`, `shoot_held`; el player nunca toca `Input` |
| 2 | `player.gd:141` | `get_parent().add_child(bullet)` acopla al padre | `Pools.spawn(&"bullet_player", pos, dir)` bajo `Level/Projectiles` |
| 3 | `player.gd:99-100`, `player.tscn:5-6` | Muta `collision.shape.size` de un `RectangleShape2D` **compartido** entre instancias | `resource_local_to_scene = true` o `shape.duplicate()` en `_ready` |
| 4 | `player.gd:152-165` | `_die()` reentrante: dos llamadas en un frame → doble respawn y doble señal; tras el `await` no comprueba que el nodo siga vivo | `if is_dead: return`; `Timer.one_shot` o `await` + `if not is_inside_tree(): return` |
| 5 | `bullet.gd:29-32` | Culling contra `get_viewport_rect()` (mundo 0–320): con `Camera2D` las balas lejanas mueren al nacer | `VisibleOnScreenNotifier2D.screen_exited` → devolver al pool |
| 6 | `bullet.gd:36`, `bullet.tscn:10` | Duck-typing y `body_entered` contra `enemy_body` (máscara 8); con hurtboxes es `area_entered` en capa 7 | `HitboxComponent`: layer 6, mask 1+64+1024 (terrain, enemy_hurtbox, destructibles); `area is HurtboxComponent` |
| 7 | `project.godot` | Sin `[layer_names]`; `[physics]` ausente (el check pasa por defaults); sin ratón ni F2–F7 | 12 nombres del paso 1.1; `physics/common/*` explícitos; `shoot`=LMB, `grenade`=RMB, `melee`=MMB; `debug_f2..f7`; `character_next` |
| 8 | `check_shooting_and_enemy.gd:35-44`; repo | Cuenta balas por `node_added`/`has_method("setup")`: con pooling → falso FAIL. El git visible: un commit, sin tags ni `.gitignore`, contra `PROGRESS.md` | `Pools.active_count()`; tag `v0.1-hito0` y `.gitignore` antes de la primera línea nueva |

Menores: `player.gd:30` `@onready`+`preload` → `const`; `player.gd:57-58` `max()` es Variant → `maxf`; `enemy_debug_box.gd:15` grupo en `_ready` → `groups=["enemies"]` en el `.tscn`.

## 2. Orden de construcción

1. **Cimientos**: `[layer_names]`, `src/core/layers.gd` con bits, InputMap completo (mando, ratón, F1–F7), `.gitignore`, tag.
2. **Componentes de daño** (1.2) y migración de bullet/enemy/player.
3. **WeaponData + WeaponComponent** (1.5): `pistol/shotgun/hmg.tres`; munición en el componente, no en el Resource; vuelta a pistola.
4. **Pools** (1.4) solo balas; reescribir el check 0.8.
5. **PlayerInputComponent + `CharacterData.tres` ×3** (nombre, `SpriteFrames`, paleta; cero stats distintos, doc 02 §4) + selección con 3 tarjetas.
6. **Cámara** deadzone+límites (1.6), **gates** (1.7), **oleadas JSON** (1.8), `Level.tscn` mínimo con `StaticBody2D` grises.
7. **IA**: Avanzador, Estático, Volador, Saltador en un `EnemyBrain` con `@export var profile`.
8. **HUD** + **Debug** F1/F2/F3/F6/F7.
9. **Sprites** al final: `AnimatedSprite2D` sustituye al `ColorRect`; el gris sigue jugable si el arte se retrasa.

Recortable sin perder "jugable": Emboscada; lookahead; F4/F5; granada y melee (mapeados, sin lógica); StateMachine formal; tiles/parallax; audio; rehenes; retratos en la selección.

## 3. Pruebas headless nuevas (`src/debug/`)

Lo que toca autoloads va como `.tscn` (ruta de escena posicional, no `--script`). `run_all_checks.ps1` exige `RESULTADO: PASS` en todos.

| Archivo | Comprueba | PASS |
|---|---|---|
| `check_collision_layers.gd` | 12 `layer_names/2d_physics/layer_N`; layer/mask de cada componente | nombres exactos; máscaras = tabla 1.1 bit a bit |
| `check_weapon_resources.tscn` | 3 `.tres` cargan como `WeaponData`; 5 s de disparo con cada una | pistol 40±6; shotgun 10±2 ráfagas ×5; hmg 75±11; dispersión 25°±3; munición −1 por ráfaga |
| `check_ammo_fallback.tscn` | escopeta con 3 cartuchos; pistola 300 disparos | al 4.º intento `weapon.id == &"pistol"`, señal de cambio una vez; pistola nunca baja |
| `check_damage_components.tscn` | hitbox/hurtbox cruzados jugador↔enemigo; i-frames | daño solo en pares válidos; 2 golpes en 10 frames = 1; `invulnerable` bloquea; `died` una vez |
| `check_camera_gate.tscn` | cruzar, empujar, limpiar, recruzar, **morir a media oleada** | `limit_right` fijado; `x ≤ límite`; unlock con `wave_cleared`; sin 2.º disparo; tras respawn: gate rearmado, enemigos liberados, límites restaurados |
| `check_wave_spawner.tscn` | JSON con delays 0 / 2.0 / 4.5 s, `count` 3, `interval` 0.4 | spawns en frames 0±2, 120±3, 270±3; `wave_cleared` al morir todos; JSON roto → error, sin crash |
| `check_character_select.tscn` | 3 `CharacterData.tres`; jugador con cada uno | cada `SpriteFrames` tiene idle/run/jump/fall/crouch/die; constantes idénticas; `main` instancia el elegido |
| `check_pools.tscn` | 80 balas precargadas; 60 s con 30 enemigos disparando | `OBJECT_NODE_COUNT` plano (máx−mín últimos 30 s < 5); `active_count()==0`; `OBJECT_ORPHAN_NODE_COUNT==0` |
| `check_input_map.gd` (ampliar) | ≥1 tecla y ≥1 botón/eje por acción; `shoot/grenade/melee` con `InputEventMouseButton`; `debug_f1..f7` | todo presente; ninguna tecla repetida |
| `check_enemy_profiles.tscn` | 4 perfiles por `@export`; dos Avanzadores con velocidad distinta | para a `stop_distance`±4 px; Estático Δx=0; Volador Δy=0 sin suelo; Saltador despega ≥2 veces en 3 s |
| `check_hud_debug.tscn` | HUD en `CanvasLayer` reacciona a puntaje/vidas/arma; F3, F6, F7 | textos coinciden; con F3 un hitbox no mata; F6 cicla 3 armas; F7 instancia enemigo; `Debug.visible == OS.is_debug_build()` |

## 4. Doce errores fáciles de GDScript 4.5 sin ejecutar

1. `@onready var s := preload(...)` → `const BULLET := preload(...)`; `load()` solo para rutas dinámicas.
2. Los hijos entran en `_ready` **antes** que el padre: un componente no puede leer `@onready` del padre ahí → el padre inyecta con `setup()`.
3. Dentro de `body_entered/area_entered`: `set_deferred("monitoring", false)`, `set_deferred("disabled", true)`, `call_deferred("add_child", …)`.
4. `await` en `_die`: guarda de reentrada y, tras el `await`, `if not is_inside_tree(): return`. Mejor `Timer.one_shot`.
5. `StringName` vs `String`: ids `&"pistol"`; lo que llega de JSON es `String` → `StringName(d["enemy"])` en la frontera.
6. JSON: todo número es `float` → `int(d["count"])`; `JSON.parse_string()` devuelve `null` si falla.
7. `Array[WeaponData]` no acepta un `Array` sin tipo → `typed.assign(untyped)`.
8. `Callable`: `sig.connect(_on_x)` / `.bind(arg)`, nunca cadenas; una lambda captura **copias** de las locales.
9. `instantiate()` devuelve `Node`: `var b := BULLET.instantiate() as Bullet`; `add_child` antes de `global_position`.
10. Resource: `class_name WeaponData extends Resource`; el `.tres` lleva `type="Resource" script_class="WeaponData"` y `script = ExtResource(...)`. Es **compartido**: la munición vive en el componente.
11. Tipado: `max/min/sign` devuelven Variant → `maxf/mini/signf`; `1/8` es `0`; `var t := 0` fija `int`.
12. En `.tscn` va la **máscara** (`8` = capa 4); en código `set_collision_layer_value(4, true)`. Y `extends SceneTree` + `--script` **no tiene autoloads**.

Antes de la primera corrida: `--headless --path . --import`, luego `--check-only --script res://ruta.gd` por archivo (solo parsea, en segundos).

## 5. Iteración visual sin motor

1. **Maqueta 320×224** (`tools/mockup/compose_320.py` → `docs/mockups/`, con `.gdignore`): fondo ocre, suelo en y=216, los 3 personajes (lienzo 64×64, pies en y=216), enemigos 48×48 y 80×80, balas 4×2, HUD. A 1× y 4× `NEAREST`.
2. **Checklist**: silueta negra de los 4 actores (3.2); HUD legible a 1× (3.6); ≤16 colores (`identify -format %k`); hurtbox verde y hitbox rojo encima (= F2).
3. **Ancla**: `pixel_lab --align feet`; script que verifica que el píxel opaco inferior de cada frame cae en la misma fila.
4. **`.tres` estructural**: regex `AtlasTexture` = frames y `region` dentro de la hoja; el dueño confirma con `selftest.py --godot`.
5. **Arte mínimo** desde los 3 JPEG: idle (1–2 frames) + run (4) con `pixel_lab --actor player`; lo demás reutiliza idle. `dino/` es referencia web: nunca a `res://` (ADR-008/013).

## 6. Riesgos top-5

| Riesgo | Mitigación |
|---|---|
| Los "sprites reales" no existen aún | "Real" = idle+run pixelizados; el gris sigue funcionando; gate ADR-008 para todo PNG en `assets/` |
| ~30 archivos GDScript escritos a ciegas → errores de parse en cascada | Orden por capas (§2), `--check-only` por archivo, un check por capa |
| Gate + muerte a media oleada (donde el doc avisa que siempre está el bug) | `WaveSpawner.abort()` en `player_died`, gate rearmado, límites restaurados; `check_camera_gate` lo cubre |
| Pooling y hurtboxes rompen los 7 checks de Fase 0 | Actualizar checks viejos en el mismo commit; `run_all_checks.ps1` corre los 18 |
| Alcance de la iteración | Recortes de §2 acordados antes de empezar; tag y `.gitignore` primero |
