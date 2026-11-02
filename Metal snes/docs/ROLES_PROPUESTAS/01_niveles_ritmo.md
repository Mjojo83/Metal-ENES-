# Piso 1 «DEEP FALL» — Niveles y ritmo (PROPUESTA)

Todo lo de aquí es propuesta: nada se programa sin confirmación explícita (regla del doc 02). Fuentes: doc 02 §3.1/§5, arquitectura pasos 1.7–1.9 y 3.2, PROGRESS.md. Base: jugador 47 px, salto ≈47 px, carrera 100 px/s, pantalla 320×224, temblor cada 20–25 s. Las carpetas de criaturas son fotos de referencia; los tamaños se fijan en la pestaña Tamaños del laboratorio (ADR-011).

## 1. Estructura del descenso

Idea rectora: cuanto más abajo, más antiguo. Cretácico arriba, Cámbrico al fondo: la estratigrafía es correcta y eso es el chiste («exageración de lo real»). Cada gate dura 25–40 s para que le toque **un** temblor y un checkpoint (§5.2: uno cada 30–40 s).

**Tramo 1 — Cretácico, «La bocamina»** (horizontal; luz de entrada, vigas, cajas de núcleos).
- G1.1 *Vestíbulo*: 3 Velociraptor escalonados por la derecha + 1 Nipponites en repisa. Enseña: disparar en movimiento y saltar un proyectil lento.
- G1.2 *Puente de vigas*: Quetzalcoatlus en picada + raptors, uno por la **izquierda**. A mitad cae el primer temblor y el centro del puente se desprende (permanente). Enseña: leer la sombra, apuntar arriba, voltear.
- G1.3 *Galería TR-001*: mini-jefe T-Rex (§4). Su derrota abre el pozo: la transición al tramo 2 **es** la caída.

**Tramo 2 — Carbonífero, «El bosque de carbón»** (vertical → horizontal; Calamites como columnas, carbón negro sobre ocre).
- G2.1 *Fondo del pozo*: 2 Pulmonoscorpius emergen del carbón + 2 Meganeura en senoidal. Enseña: emboscada telegrafiada (polvo antes de salir) y que lo bajo se dispara agachado.
- G2.2 *Calamites*: 2 Calamites lanzan esporas que caen con sombra; 1 Arthropleura avanza como muro. Enseña: priorizar (Calamites primero) y saltar al enemigo largo para dispararle la espalda.
- G2.3 *La grieta*: techo bajo; Megarachne cuelgan, Eryops saltan desde charcos. Enseña: la amenaza viene de arriba, no te quedes parado. Termina con agua filtrándose.

**Tramo 3 — Cámbrico, «El lago de abajo»** (lago bioluminiscente azul-verde: contraste con los ocres).
- G3.1 *Orilla*: Trilobites en fila + Hallucigenia en pared y techo, algunas al revés (nadie sabe cuál lado es arriba, y es verdad). Enseña: disparo agachado con timing y leer abanicos.
- G3.2 *Lago*: enjambres de Marrella + Anomalocaris emergiendo; el agua sube con cada temblor (§3). Enseña: todo junto bajo reloj suave. Desemboca en el jefe del piso (sismógrafo gigante, doc 02; fuera de esta entrega).

## 2. Criaturas

Tamaño en px alto×largo, aproximado.

| Criatura | Perfil | Tamaño vs 47 px | Ataque y telegrafía | Ritmo |
|---|---|---|---|---|
| Velociraptor | Avanzador rápido (120 px/s en ráfagas, para a 60 px) | 40×70 (0.85×) | Zarpazo corto; se agacha 0.3 s y sacude la cola | Presión frontal; tropa |
| Nipponites | Estático (repisa/pared) | 36×36 (0.75×) | Burbuja de tinta en arco (60 px/s, 20 px); la concha gira 0.5 s | Enseña a saltar proyectiles |
| Quetzalcoatlus | Volador (patrulla alta, picada) | 40 alto, 100 envergadura | Picada a 45° al punto donde estabas; su sombra crece 0.6 s | Verticalidad; obliga `aim_up` |
| T-Rex | Mini-jefe | 110×180 (2.3×) | Ver §4 | Cierre del tramo 1 |
| Arthropleura | Avanzador lento (30 px/s), mucha vida | 20×160 | Embestida de 40 px; alza 3 segmentos 0.4 s | Bloqueo: muro andante, se salta |
| Calamites | Estático (planta) | 100×24 | 3 esporas que caen con sombra 1.0 s después (reusa escombros) | Zona negada; prioridad |
| Eryops | Saltador | 30×60 (0.65×) | Salto en arco desde charco; hincha la garganta 0.4 s | Te saca del sitio |
| Meganeura | Volador senoidal (amplitud 40 px) | 20×50 | Contacto; 1 HP, en pares | Presión aérea |
| Megarachne | Emboscada (techo) → Avanzador | 40×40 (0.85×) | Cae de un hilo 0.5 s después de que brilla | Amenaza cenital |
| Pulmonoscorpius | Emboscada (carbón) → Avanzador | 30×70 | Aguijonazo en arco de 24 px; cola se enrosca, punta brilla 0.5 s | Niega la distancia corta |
| Anomalocaris | Emboscada (agua) | 40×90 (1.9×) | Salta en arco por la pantalla; ondas y aleta avanzan 0.8 s | Metrónomo del tramo 3 |
| Hallucigenia | Estático (pared/techo) | 24×30 (0.5×) | Abanico de 3 espinas lentas; brillan 0.4 s | Torreta de carril: agacharse o saltar |
| Marrella | Volador, enjambre de 5 | 16×16 (0.35×) | Contacto; 1 HP | Relleno para escopeta; densidad |
| Trilobites | Avanzador bajo (40 px/s) | 20×36 (0.4×) | Al recibir tiro se enrolla 1 s (invulnerable) y rueda a 80 px/s | Disparo agachado con timing; «piedras que ruedan» del backlog |

Recorte: el doc pide máx. 3 enemigos nuevos por piso. Si se respeta al pie, el núcleo es Velociraptor, Quetzalcoatlus y Trilobites (los tres perfiles del paso 3.2) + T-Rex; los demás comparten perfil y entran como variantes si el arte alcanza.

## 3. Gimmicks de entorno (baratos, ligados a los temblores)

1. **Sismógrafo de pared como reloj diegético.** Un tambor en el fondo de cada gate; su aguja (Line2D que lee el timer del temblor) crece los últimos 3 s. Se aprende a mirar el fondo sin HUD. Costo: un nodo.
2. **Los bichos también sienten el temblor.** Señal `tremor_warning` 1.5 s antes: los perfiles de suelo entran en «agacharse» (Trilobites se enrollan, raptors se agachan, Eryops al charco); los voladores no. Compás pausa → sacudida → reanudar; el aire es la amenaza durante la sacudida. Costo: un estado más por perfil. Chiste: en la cueva todos saben cuándo va a temblar menos el estudiante.
3. **El lago sube un tile por temblor (tramo 3).** El agua (Area2D) sube 8 px por temblor y no baja. Sin física nueva: solo es de donde sale Anomalocaris y donde ya no se puede disparar agachado. Reloj suave sin contador. Costo: mover un Area2D al recibir la señal.

## 4. Mini-jefe: T-Rex «TR-001»

Arena plana de una pantalla con dos cajas de núcleos destructibles. Lleva colgada la etiqueta de la litoteca («Réplica — NO TOCAR»): comedia de registro, sin burlarse de nadie. Vida por fase 60/60/60 (≈70 s con pistola).

- **Fase 1 — Pisotón.** Alza la pata 0.6 s con polvo bajo el pie. Pisotón → onda por el suelo (16 px, 140 px/s): se salta. **Castigo:** 1.2 s con la cabeza baja (hurtbox a 30 px, alcanzable de pie). Enseña la fase 1 del jefe del piso.
- **Fase 2 — Mordida.** Se suma: abre las fauces 0.6 s con brillo de dientes y lanza la cabeza a ras de suelo 90 px (hitbox 30 px alto: se salta). **Castigo:** muerde una caja y queda trabado 1.5 s; escopeta a bocajarro aquí. Pisotones siguen, más lentos. Dos saltos con telegrafías distintas: ahí está la lectura.
- **Fase 3 — Rugido.** Inhala 1.0 s (pecho crece, vibra el borde de pantalla) y ruge: temblor completo (3 escombros con sombra, del sistema del piso) + onda doble separada 0.5 s (dos saltos seguidos). **Castigo:** 1.5 s con la garganta expuesta, justo bajo los escombros: riesgo/recompensa. Al morir, el último pisotón abre el pozo y caen los dos; abajo se le ve de fondo, atorado, con la etiqueta ondeando.

## 5. Oleada de ejemplo — `data/waves/piso1_cret_gate02.json`

```json
{
  "id": "piso1_cret_gate02",
  "clear_condition": "all_dead",
  "spawns": [
    { "enemy": "velociraptor", "point": "right_ground", "delay": 0.0, "count": 2, "interval": 0.6 },
    { "enemy": "nipponites", "point": "ledge_right_high", "delay": 1.0, "count": 1 },
    { "enemy": "quetzalcoatlus", "point": "ceiling_mid", "delay": 3.5, "count": 1 },
    { "enemy": "velociraptor", "point": "left_ground", "delay": 7.0, "count": 1 },
    { "enemy": "quetzalcoatlus", "point": "ceiling_right", "delay": 12.0, "count": 1 }
  ]
}
```

Ids en inglés (ADR-010); puntos = Marker2D de SpawnPoints. El temblor llega por su propio timer; forzarlo a mitad del gate pediría un campo nuevo (p. ej. `"tremor_at": 9.0`) que no existe y habría que confirmar.
