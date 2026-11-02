# PROPUESTA — Controles, UX y accesibilidad

*Catástrofe en la Biblioteca · Godot 4.5 · 320×224. Todo es PROPUESTA: nada se implementa sin confirmación (regla de la sección 1 de `02_Documentacion_Proyecto`).*

Base: InputMap de `project.godot` (deadzone 0.5), `player.gd::get_aim_direction()` (tabla del paso 0.7), pasos 0.6, 1.10, 3.6, 5.3, 5.4, Apéndice A, sección 5 y ADR-004.

## 1. Mapa de controles

### Mando Xbox

| Acción | Principal | Alternativa | Por qué |
|---|---|---|---|
| move_left/right | `JOY_AXIS_LEFT_X`, `JOY_BUTTON_DPAD_LEFT/RIGHT` | — | Ya está; el D-pad es lo preciso para 8 direcciones. |
| aim_up/down | `JOY_AXIS_LEFT_Y`, `JOY_BUTTON_DPAD_UP/DOWN` | — | Abajo = agacharse (convención Contra/Metal Slug). |
| jump | `JOY_BUTTON_A` | — | Estándar Xbox. |
| shoot | `JOY_BUTTON_X` | `JOY_AXIS_TRIGGER_RIGHT` | X deja rodar el pulgar a A para saltar disparando; RT evita fatiga al mantener fuego. |
| grenade | `JOY_BUTTON_B` | `JOY_BUTTON_LEFT_SHOULDER` | Misma relación disparo/granada que el Neo Geo. |
| melee | `JOY_BUTTON_Y` | `JOY_BUTTON_RIGHT_SHOULDER` | Acción menos frecuente, botón más lejano. |
| pause | `JOY_BUTTON_START` | — | — |
| debug_toggle | — | `JOY_BUTTON_BACK` solo con `OS.is_debug_build()` | Probar con mando sin soltar el teclado. |

Deadzones: `move_*` 0.4; `aim_up/down` 0.6, para que un stick algo inclinado no apunte arriba ni agache sin querer. Stick derecho: sin uso por defecto (opción con la cuantización de 1.3).

### Teclado + ratón

| Acción | Default | Alternativo | Ratón |
|---|---|---|---|
| mover/apuntar | WASD | Flechas | — |
| jump | Espacio | Z | — |
| shoot | J | X | Botón izquierdo |
| grenade | K | C | Botón derecho |
| melee | L | V | Botón central / Shift |
| pause | Esc | Esc | — |

Ambas columnas activas a la vez; `physical_keycode` como ahora (independiente de distribución).

### 1.3 Ratón con apuntado discreto

El ratón **no** da 360°: su ángulo desde la boca del arma (coordenadas de mundo vía `Camera2D`) se **cuantiza al conjunto permitido por el estado**. `get_aim_direction()` recibe el vector de entrada (teclas o ratón) y aplica la misma tabla: una sola fuente de verdad y `check_aim_directions` sigue pasando.

- **De pie quieto:** >60° sobre la horizontal → arriba; si no, horizontal, y el lado del ratón fija `facing` (girarse sin caminar: la ventaja real).
- **Corriendo/agachado:** horizontal en la dirección de carrera; el ratón se ignora.
- **Aire:** 8 sectores de 45° con histéresis de 8°.
- Cursor del SO oculto; **retículo propio 5×5 px en la dirección cuantizada**. Enseña el sistema sin texto.

Pros: expectativa natural en PC, giro en seco, descubrible. Contras: tentación de apuntado libre; confusión al correr con el ratón detrás. Opción **«Apuntar con ratón: Automático / Sí / No»** (Automático = manda el último dispositivo que generó entrada).

## 2. Selección de personaje

Título → **Selección** → fundido 0.2 s → nivel. Jugador decidido: aparece 0.2 s + 0–2 pulsaciones + confirmación 0.6 s + fundido 0.3 s ≈ **1.5–3 s (< 5 s)**. Temporizador arcade de 15 s que autoconfirma el resaltado.

Tres tarjetas de 96×160 px en x = 16/112/208, y = 24: nombre (8 px), **sprite 1x en idle** (6 frames); la resaltada pasa a **carrera** (8 frames) sobre suelo que se desplaza; debajo, licenciatura ENES (por definir) y **una línea** ≤ 28 caracteres, p. ej. *Homi — «Entrego tarde, pero vivo»*. Sin estadísticas: las diferencias son cosméticas (sección 4).

Navegar: izquierda/derecha (stick, D-pad, A/D, flechas) con wrap; el ratón resalta al pasar y confirma con clic. Confirmar: `A`, `shoot`, Enter, clic izquierdo. Cancelar: `B`, Esc, clic derecho → Título. Al confirmar: flash 2 frames, pose «listo», voz del nombre, las otras al 50 % de brillo; `B` aún cancela durante esos 0.6 s. Se recuerda la última elección en `user://`.

## 3. HUD a 320×224

Un `CanvasLayer`, banda superior de **28 px**; y 208–216 reservado a la barra del jefe.

| Elemento | (x, y) | Formato |
|---|---|---|
| Vidas | 8, 6 | Cabeza del personaje 8×8 + `×3` |
| Créditos | 8, 16 | `CRED 3` en 5×7 |
| Puntaje | 112–208, 6 | 8 dígitos de 8 px, a la derecha |
| Arma + munición | 240, 6 | Icono 16×8 + `200` o `∞` |
| Granadas · rehenes | 240, 16 | Icono 8×8 `×10` · icono 8×8 `×2` |

Fuente **bitmap** 8×8 para valores, 5×7 para etiquetas; trazo 1 px, blanco con contorno negro 1 px, nunca < 5 px ni con antialias; propia o CC0 verificada (ADR-008).

Cambio de arma (`Events.weapon_picked_up`): icono entra 6 px desde la derecha en 4 frames, número con flash 2 frames y rebote 2 px, nombre centrado en y = 32 durante 1 s con la voz. Munición ≤ 10: dígitos parpadean a 4 Hz **y** el icono tiembla 1 px (no solo color). **Vuelta a la pistola:** el `0` queda rojo 2 frames, «clic» seco, entra el icono de pistola con `∞`. Nunca un frame sin arma.

## 4. Game feel por arma

| | Pistola 8/s | Escopeta 2/s | Ametralladora 15/s |
|---|---|---|---|
| Retroceso sprite | 1 px, 2 frames | 3 px + 1 px vertical, 3 frames | 1 px + jitter ±1 px vertical por disparo |
| Screenshake | 0 | 2 px, 4 frames | 1 px continuo, **sin acumular** |
| Hitstop | 0 (2 frames al matar) | 3 frames, una vez por disparo | 0 (rompería la cadencia) |
| Casquillos | 3×2 px, vx −50 / vy −90 px/s, 1 rebote, 0.6 s | cartucho rojo 4×2, más lento | 1 por disparo, 0.5 s (≈8 vivos del pool de 40) |
| Fogonazo | 1 frame 6×6 | 2 frames 10×8 | 1 frame 6×6 |
| Sonido | «pak» 70 ms, pitch ±5 %, máx. 3 voces | «boom» 180 ms + bombeo a los 120 ms | «tat» 50 ms, pitch ±8 %, máx. 4 voces |
| Vibración | — | fuerte 0.6, 0.12 s | débil 0.3, refrescada cada 0.1 s |

Granada: shake 3 px / 6 frames, hitstop 4. Melee: hitstop 4, flash 2. Tope global de shake **3 px** (paso 5.3), vía `Camera2D.offset` redondeado a enteros.

## 5. Accesibilidad

| Opción | Qué hace | Costo |
|---|---|---|
| **Chaleco (escudo de 2 impactos)** | Base: un golpe mata (5.2). Con chaleco mueres al tercero; 1 s de invulnerabilidad parpadeante; se recarga en checkpoint; 2 iconos bajo las vidas. **No agranda la hurtbox** (ADR-004). La tabla de puntajes lo marca. | Medio |
| Remapeo completo | `InputMap.action_erase_events/add_event`, guardado en `user://`. | Medio |
| Shake / flashes / vibración | Deslizador 0–100 % y dos interruptores. | Bajo |
| Fuego mantenido / conmutado | Una pulsación enciende, otra apaga. Motricidad reducida. | Bajo |
| Ritmo: Arcade / Pausado 85 % / Con calma 70 % | `Engine.time_scale`; nunca se llama «fácil». Oleadas reducidas serían alto (JSON alternativos). | Bajo |
| Proyectiles enemigos en alto contraste + subtítulos | Contorno 1 px y tinte distinto (shader de un parámetro); texto de los gritos de arma. | Bajo–medio |

## 6. Checklist de usabilidad (10 min, sin explicar nada)

Solo se habla para hacer la pregunta indicada; anota ✔/✘ y tiempo.

1. **Moverse y saltar** en < 10 s (criterio del Hito 0).
2. **Disparar** en < 15 s. Anota la primera tecla probada; si es Enter/Ctrl/Z, añadir binding.
3. Ante una bala alta, ¿se **agacha** solo? ¿Se arrastra sin asustarse?
4. Enemigo volador: ¿**apunta arriba** en ≤ 2 intentos? Después: «¿a dónde creías que disparabas?».
5. Tres huecos de un tile: ≤ 1 caída (coyote/buffer).
6. Tras recoger un arma: «**¿qué arma traes?**» (4/5, paso 3.7).
7. Al acabarse la munición: «¿qué le pasó a tu arma?» → «volví a la pistola».
8. Tras la primera muerte: «**¿qué te mató?**». Si no sabe, falla la telegrafía.
9. Rehén: ¿lo libera? Si lo mata, ¿entiende y se ríe?
10. «Pausa» y «vuelve al menú» sin ayuda. Si tomó el ratón: «¿el disparo iba a donde apuntabas?».
