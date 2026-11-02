# Catástrofe en la Biblioteca

Run-and-gun 2D estilo Metal Slug. Godot **4.5.1 stable** (verificado localmente el 2026-09-15 — no
actualizar de versión mayor a mitad de fase; solo entre hitos, con el repo limpio y etiquetado).

## Documentación

Antes de tocar código, lee esto en orden:

1. [`docs/02_Documentacion_Proyecto.docx`](docs/02_Documentacion_Proyecto.docx) — la idea, el diseño,
   las decisiones (ADRs) y las reglas de tono/legales. Se actualiza según evoluciona el proyecto.
2. [`docs/01_Arquitectura_Tecnica.docx`](docs/01_Arquitectura_Tecnica.docx) — el orden de construcción
   paso a paso, con su comprobación. Es la fuente de verdad de "qué sigue".
3. [`docs/ideas/Ideas.docx`](docs/ideas/Ideas.docx) — notas sueltas de brainstorming, sin desarrollar.

**Alcance:** tres pisos, uno por uno: Ciencias de la Tierra (en producción), Órtesis y Prótesis, y Neurociencias (ADR-012).

**Estado actual:** Fase 0 (prototipo gris) terminada y comprobada; sigue la Fase 1 (sistemas core). Ver `PROGRESS.md` para el detalle paso a paso.

**Arte:** sale del Laboratorio de sprites y de su editor PixelForja (`O:\Programas\ANIMACIONES\Ortesis o protesis`), que
importan, alinean, retocan y prueban sprites y escenarios antes de traerlos aquí (ADR-011). El material de Metal Slug que hay
allá es solo referencia y nunca entra a este repo (ADR-013).

## Cómo correr el proyecto

```
"O:\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64.exe" --path "O:\Programas\Metal ENES" --editor
```

O abre `project.godot` con el editor de Godot 4.5.x.

## Cómo correr las comprobaciones automatizadas

Cada paso de la Fase 0 en adelante que se pueda verificar sin abrir el editor tiene un script en
`src/debug/`. Ejemplo:

```
"O:\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe" --headless --path "O:\Programas\Metal ENES" --script "res://src/debug/check_project_settings.gd"
```

Debe imprimir `RESULTADO: PASS`. Esto no reemplaza jugar el juego a mano — solo atrapa regresiones de
configuración rápido, sin abrir el editor.

## Teclas de depuración

Ver el documento de arquitectura, paso 1.10, para la lista completa (F1 overlay, F2 hitboxes, F3
invencibilidad, F4 frame-step, F5 warp, F6 dar arma, F7 spawn). Se van agregando conforme se
implementan; el estado real está en `PROGRESS.md`.

## Regla de proceso

Cualquier mecánica de juego nueva se propone y confirma con el responsable del proyecto antes de
implementarse. Ver la nota al final de la sección 1 de `02_Documentacion_Proyecto.docx`.
