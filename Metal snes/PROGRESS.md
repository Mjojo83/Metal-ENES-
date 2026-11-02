# Progreso de construcción

Registro corto de qué está hecho, cómo se comprobó, y qué falta. Sigue el orden de
`docs/01_Arquitectura_Tecnica.docx`. Si algo falla más adelante, este archivo dice qué se tocó
por última vez y cómo se había verificado.

## Fase 0 — Prototipo gris

### Paso 0.1 — Crear y configurar el proyecto — ✅ hecho
- `project.godot`: resolución interna 320×224, ventana 1280×896, stretch mode `viewport`,
  aspect `keep`, filtro de textura `Nearest` (0), física a 60 ticks/s, máx. 8 pasos/frame.
- Escena principal: `src/levels/main.tscn` (fondo de color + un `Sprite2D` de prueba
  `assets/sprites/ui/debug_nearest_test.png`, un checkerboard de 16×16 para comprobar a ojo que
  el filtro Nearest está activo — bordes duros, no borroso).
- **Comprobado:** `src/debug/check_project_settings.gd` corrido headless — `RESULTADO: PASS`
  (los 7 valores clave coinciden con la especificación). El proyecto importa y corre 10 frames
  headless sin errores. Pendiente: que alguien lo vea correr en pantalla con F5 y confirme el
  letterboxing al redimensionar la ventana.
- El sprite de prueba (`debug_nearest_test.png`) ya cumplió su función y se quitó de
  `main.tscn` al llegar el jugador/piso/enemigo reales del paso 0.5 en adelante; el archivo
  sigue en `assets/sprites/ui/` por si hace falta repetir la prueba visual del filtro Nearest.

### Paso 0.2 — Estructura de carpetas y Git — ✅ hecho
- Árbol completo de `res://` creado según la sección 2.1 del documento de arquitectura.
- Repo Git inicializado, `.gitignore` con las reglas de Godot (`.godot/`, `export.cfg`,
  `export_presets.cfg`, `*.translation`, `builds/`, `*.tmp`).
- **Comprobado:** `git status` limpio tras cada commit (varios ya hechos). Pendiente: confirmar
  que `.godot/` se regenera sola sin errores al borrarla.

### Paso 0.3 — InputMap — ✅ hecho
- 10 acciones registradas (las 8 de la tabla + `move_left`/`move_right`/`aim_up`/`aim_down`
  cubren tanto teclado como stick izquierdo y D-pad): `move_left`, `move_right`, `aim_up`,
  `aim_down`, `jump`, `shoot`, `grenade`, `melee`, `pause`, `debug_toggle`.
- Configuradas por código (`ProjectSettings.set_setting` + `save()`) en vez de a mano en el
  editor, para no arriesgar un typo en el formato del recurso `InputEventKey`/`InputEventJoypad*`.
- **Comprobado:** `src/debug/check_input_map.gd` (headless) confirma que las 10 acciones tienen
  exactamente las teclas, ejes y botones esperados — `RESULTADO: PASS`. Falta la prueba manual
  con un control físico conectado (el script no puede simular hardware real).

### Paso 0.4 — Autoloads — ✅ hecho
- `src/autoload/events.gd` — bus de señales (11 señales, sin lógica).
- `src/autoload/game.gd` — vidas, créditos, puntaje, piso actual, pausa. `lose_life()` consume
  un continue y resetea vidas a 3 cuando corresponde.
- `src/autoload/pools.gd`, `audio_manager.gd`, `debug.gd` — registrados como placeholders; su
  lógica real llega en Fase 1 paso 1.4, Fase 3 paso 3.5 y Fase 1 paso 1.10 respectivamente.
- Registrados en `project.godot` en el orden Events → Game → Pools → AudioManager → Debug.
- **Comprobado:** `src/debug/check_autoloads.tscn` (headless) confirma que los cinco autoloads
  existen en orden, que `Events.player_died` emitido desde un nodo llega a un receptor sin
  relación directa, y que `Game.add_score`/`lose_life` mantienen el estado correcto —
  `RESULTADO: PASS`.

### Paso 0.5 — Player: movimiento horizontal — ✅ hecho
- `src/actors/player/player.tscn` + `player.gd`: `CharacterBody2D` con `CollisionShape2D`
  (16×28) y un `ColorRect` blanco como cuerpo temporal. Constantes exactas del documento
  (`MOVE_SPEED=100`, `ACCEL_GROUND=1200`, `FRICTION_GROUND=1600`, `ACCEL_AIR=700`,
  `FRICTION_AIR=300`). Todavía sin StateMachine formal (eso es la fase 1.3): el estado vive en
  un enum simple (`PhysState`) dentro del mismo script.
- **Comprobado:** `src/debug/check_player_movement.gd/.tscn` (headless, física real a 60 Hz):
  llega a `MOVE_SPEED` sosteniendo `move_right`, no se detiene de golpe al soltar (frena en
  ~8 frames), y cruza 320px en 196 frames (~3.27s, esperado ~192f/3.2s) — `RESULTADO: PASS`.

### Paso 0.6 — Player: salto con game feel — ✅ hecho (el paso más importante de la fase)
- Las cinco técnicas juntas en `player.gd`: gravedad asimétrica (900 subiendo / 1400 bajando),
  jump cut (corta la velocidad a la mitad al soltar mientras sube), coyote time (0.1s),
  buffer de salto (0.1s), velocidad inicial de salto (−290 px/s).
- **Comprobado:** `src/debug/check_player_jump.gd/.tscn` (headless, física real, sin mockear
  matemática aparte). Coyote time y buffer fuerzan las variables internas del jugador para
  aislar cada técnica de forma determinista, con ventanas de tolerancia de varios frames en
  vez de comparar frame exacto (documentado en el propio script). Resultado real medido:
  altura de salto 49.2px (esperado ~47px), subida 23 frames vs bajada 15 frames (la bajada es
  visiblemente más rápida, confirma la asimetría), jump cut reduce la altura a 18.9px, coyote
  time y buffer disparan el salto correctamente — `RESULTADO: PASS`.

### Paso 0.7 — Player: agacharse y direcciones de apuntado — ✅ hecho
- `get_aim_direction()` implementa la tabla exacta de los 5 estados (de pie quieto, corriendo,
  agachado, en el aire, boca abajo). Agacharse/boca abajo se activan sosteniendo `aim_down`
  en el suelo (quieto = agachado, moviéndose = boca abajo/arrastre) — no hay un botón de
  crouch dedicado en el InputMap, así que se resolvió con la convención estándar del género
  (Contra/Metal Slug: abajo para agacharse, abajo+dirección para arrastrarse).
- **Comprobado:** `src/debug/check_aim_directions.gd/.tscn` — 13 combinaciones de
  estado+input contra la tabla del documento, sin necesitar física (llamada directa a la
  función) — `RESULTADO: PASS`.

### Paso 0.8 — Disparo básico — ✅ hecho
- `src/projectiles/bullet.gd/.tscn`: `Area2D` de 4×2px, velocidad 350px/s, cadencia máxima
  8/s, se destruye al salir de pantalla (+32px de margen) o al impactar. Sin pooling todavía
  (llega en la fase 1.4): se usa `queue_free()` y se vigila que no haya fuga.
- **Comprobado:** `src/debug/check_shooting_and_enemy.gd/.tscn` — sosteniendo disparo 5s
  seguidos salieron 38 balas (esperado ~40), pico de 7 balas vivas simultáneas, y vuelve a 0
  nodos vivos al dejar de disparar y esperar — `RESULTADO: PASS`.

### Paso 0.9 — Enemigo caja que muere — ✅ hecho
- `src/actors/enemies/enemy_debug_box.gd/.tscn`: 3 de vida, parpadea al recibir daño (tween de
  modulate), emite `Events.enemy_killed` y se libera al llegar a 0. Sin perfiles de IA todavía
  (fase 1.9) ni HurtboxComponent/HitboxComponent (fase 1.2) — la vida vive directo en el script
  como placeholder documentado.
- **Comprobado:** mismo test que 0.8 — el enemigo muere exactamente al tercer impacto, se
  libera del árbol, y la señal llega con el tipo correcto — `RESULTADO: PASS`.

### Paso 0.10 — Muerte y reinicio del jugador — ✅ hecho
- El jugador tiene un `Area2D` temporal (`HurtAreaTmp`, capa `enemy_body`) que dispara la
  muerte al tocar cualquier nodo del grupo `enemies`. Muere → se oculta 1s → reaparece en
  `spawn_position`. Placeholder hasta que llegue el HurtboxComponent real (fase 1.2).
- **Bug encontrado y corregido durante la prueba:** `_die()` intentaba cambiar
  `hurt_area.monitoring` de forma síncrona *desde dentro* de la propia señal
  `body_entered` del Area2D — Godot lo bloquea con error
  (`Function blocked during in/out signal`). Se corrigió usando
  `set_deferred("monitoring", ...)`, igual que ya se hacía con `collision.disabled`.
- **Comprobado:** `src/debug/check_death_respawn.gd/.tscn` — un ciclo real (el enemigo toca al
  jugador de verdad) confirma muerte + señal + respawn en `spawn_position` a 1s; luego cinco
  ciclos rápidos seguidos confirman que no hay crash, no se duplica el jugador, y siempre
  termina en `spawn_position` con estado consistente — `RESULTADO: PASS`.

## Hito 0 — Estado

Todos los criterios de cierre de la Fase 0 (documento de arquitectura) están hechos y
comprobados por headless: movimiento, las cinco técnicas de salto, agacharse/apuntado por
estado, disparo sin fugas, enemigo que muere, muerte/respawn del jugador sin crashear. Antes de
etiquetar `v0.1-hito0` (en vez del actual `v0.1-hito0-wip`) falta:
- Confirmación visual humana en el editor (F5): letterboxing, que el juego "se sienta bien" a
  ojo, teclado y gamepad reales.
- El criterio "le diste el teclado a alguien sin explicarle nada" — inherentemente no
  automatizable.

## Convención de este archivo
- ✅ hecho y comprobado — ⏳ pendiente — ⚠️ hecho pero con algo por revisar (se explica por qué).
- Se actualiza en cada paso, no al final de la fase.
