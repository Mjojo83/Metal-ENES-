# Catástrofe en la Biblioteca

Run-and-gun 2D estilo Metal Slug ambientado en la biblioteca de la ENES Juriquilla. Godot **4.5.1
stable** (no actualizar de versión mayor a mitad de fase; solo entre hitos, con el repo limpio y
etiquetado). PC, con mando Xbox o teclado y ratón.

**Estado (noviembre 2026):** Fase 0 cerrada y comprobada; **Fase 1 (sistemas core) construida** y
Fase 2/3 adelantadas en lo mínimo para que el piso 1 "DEEP FALL" sea jugable de principio a jefe:
tres personajes con sprites reales, pistola/escopeta/ametralladora, 14 criaturas, camera gates,
oleadas, HUD, selección de personaje. Ver `PROGRESS.md` para el detalle y lo que falta verificar.

## Documentación

Antes de tocar código, lee esto en orden:

1. [`docs/02_Documentacion_Proyecto.docx`](docs/02_Documentacion_Proyecto.docx) — idea, diseño, ADRs y reglas de tono/legales.
2. [`docs/01_Arquitectura_Tecnica.docx`](docs/01_Arquitectura_Tecnica.docx) — orden de construcción paso a paso, con su comprobación.
3. [`docs/PIPELINE_ARTE.md`](docs/PIPELINE_ARTE.md) — cómo se generan y regeneran todos los sprites, tiles, fuente y SFX.
4. [`docs/ROLES_PROPUESTAS/`](docs/ROLES_PROPUESTAS/README.md) — cinco revisiones por rol (niveles, arte, controles, narrativa/audio, producción/QA). **Son propuestas**, no decisiones.
5. [`docs/REFERENCIAS_Y_LICENCIAS.md`](docs/REFERENCIAS_Y_LICENCIAS.md) — qué hay que resolver antes de publicar.
6. [`docs/ideas/Ideas.docx`](docs/ideas/Ideas.docx) — notas sueltas.

**Alcance:** tres pisos, uno por uno: Ciencias de la Tierra (en producción como descenso "DEEP FALL"),
Órtesis y Prótesis, y Neurociencias (ADR-012).

## Cómo correr el juego

```
"O:\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64.exe" --path "O:\Programas\Metal ENES" --editor
```

O abre `project.godot` con Godot 4.5.x y presiona F5. La escena principal es `src/ui/title.tscn`:
título → selección de personaje → `src/levels/deep_fall.tscn` → game over / piso despejado → título.

La primera vez, deja que el editor importe los assets (o corre `--headless --import`).

## Controles

| Acción | Teclado | Ratón | Mando Xbox |
|---|---|---|---|
| Mover / apuntar | WASD o flechas | el cursor apunta (ver abajo) | stick izquierdo, D-pad |
| Saltar | Espacio / Z | — | A |
| Disparar | J / X | botón izquierdo | X o gatillo derecho |
| Granada (reservado) | K / C | botón derecho | B o LB |
| Melee (reservado) | L / V | botón central | Y o RB |
| Agacharse / arrastrarse | abajo / abajo + dirección | — | abajo |
| Pausa | Esc | — | Start |

El ratón **no** apunta en 360°: su ángulo se cuantiza a las direcciones de Metal Slug según el estado
(de pie: horizontal o arriba; corriendo/agachado: horizontal; en el aire: 8 direcciones) y aparece una
retícula en la dirección real. Manda el último dispositivo usado (`Game.settings.mouse_aim`:
`auto`/`on`/`off`). Al acabarse la munición se vuelve a la pistola; recoger una caja reemplaza el arma.

Teclas de depuración (solo en builds de depuración): **F1** overlay, **F2** hitboxes, **F3**
invencibilidad, **F6** ciclar armas, **F7** invocar un enemigo. (F4 frame-step y F5 warp: pendientes.)

## Cómo correr las comprobaciones automatizadas

Cada sistema tiene un script en `src/debug/` que imprime `RESULTADO: PASS`. Para correrlos todos:

```
.\run_all_checks.ps1 -Godot "O:\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe"
```

(o `./run_all_checks.sh /ruta/godot` en Linux/macOS). Importa el proyecto primero y luego corre 3
scripts (`--script`) y 11 escenas. Uno suelto:

```
"...\Godot_v4.5.1-stable_win64_console.exe" --headless --path . --script "res://src/debug/check_project_settings.gd"
"...\Godot_v4.5.1-stable_win64_console.exe" --headless --path . "res://src/debug/check_weapons.tscn"
```

Las escenas (`.tscn`) necesitan autoloads; `extends SceneTree` + `--script` no los tiene.

## Estructura

```
src/autoload/      Events, Game, Pools, AudioManager, Debug
src/components/    Health, Hurtbox, Hitbox, WeaponData/WeaponComponent, CharacterData, EnemyData
src/actors/        player (+ player_input), enemies (enemy.gd = perfiles de IA por datos)
src/levels/        level.gd (nivel desde JSON), game_camera, camera_gate, wave_spawner, deep_fall.tscn
src/ui/            title, character_select, hud
src/projectiles/   bullet (jugador, pooled), enemy_bullet
src/pickups/       weapon_pickup
data/              weapons/*.tres, characters/*.tres, enemies/*.tres, levels/*.json, waves/*.json
assets/            sprites generados, tileset, fondos, fuente bitmap, SFX (todo regenerable)
tools/             pixel_lab (arte), level_gen (nivel/oleadas/datos), mockup (maquetas 320×224)
```

## Arte

Sale de `tools/pixel_lab/` a partir de `../enemigos y personajes/` (ver `docs/PIPELINE_ARTE.md`).
Las referencias de criaturas son de terceros y solo sirven de referencia (ADR-008/013); lo que
entra a `res://` son los sprites derivados, que hay que sustituir por referencias propias o
libres antes de publicar (`docs/REFERENCIAS_Y_LICENCIAS.md`). El material de Metal Slug nunca
entra al repo.

## Regla de proceso

Cualquier mecánica de juego nueva se propone y confirma con el responsable del proyecto antes de
implementarse. Ver la nota al final de la sección 1 de `02_Documentacion_Proyecto.docx`.
