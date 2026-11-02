# Roles y propuestas (noviembre 2026)

Cinco "roles" revisaron el proyecto en paralelo, cada uno desde su oficio, con la instrucción de
proponer opciones no obvias y concretas. **Todo lo de esta carpeta es PROPUESTA**: según la regla de la
sección 1 de `02_Documentacion_Proyecto.docx`, ninguna mecánica nueva se implementa sin confirmación
explícita. Lo que ya se implementó en esta iteración está marcado en `PROGRESS.md`.

| Archivo | Rol | Lo más aprovechable |
|---|---|---|
| `01_niveles_ritmo.md` | Diseño de niveles y ritmo | Descenso en 3 tramos (Cretácico → Carbonífero → Cámbrico, orden estratigráfico real), tabla de las 14 criaturas con perfil de IA/tamaño/ataque, mini-jefe T-Rex "TR-001" en 3 fases, gimmicks de temblor baratos. |
| `02_direccion_arte.md` | Dirección de arte pixel | Paletas por era, reglas medibles para que el arte automático parezca a mano (islas, bandas, contorno), prueba de silueta, crítica de las tres referencias y nota legal sobre el paleoarte de terceros. |
| `03_controles_ux.md` | Controles, UX y accesibilidad | Mapa completo mando/teclado/ratón, ratón cuantizado a las direcciones de Metal Slug (implementado), selección de personaje, HUD a 320×224, game feel por arma, 6 opciones de accesibilidad, checklist de 10 pruebas. |
| `04_narrativa_audio.md` | Narrativa, humor y audio | Fichas de Homi/Mariana/Óscar, 8 gags "dato real → chiste jugable", gritos de armas originales (¡DE CAJÓN! ¡ABANICO! ¡MATRACA!), plan de 20 SFX sin derechos, títulos alternativos, checklist ético. |
| `05_produccion_qa.md` | Producción técnica y QA | Revisión del código de la fase 0, orden de construcción, 11 pruebas headless, 12 errores típicos de GDScript 4.5, plan de iteración visual sin motor, riesgos. |

Decisiones que estos roles piden al dueño del proyecto (no se tomaron por él):

1. **Óscar**: la referencia trae hojas de cannabis en gorro y mochila y un cigarro. A 47 px casi no se
   leen, pero son un pasivo frente a la identidad UNAM (sección 8.2). Se dejaron tal cual; decidir.
2. **Referencias de criaturas**: `enemigos y personajes/dino/` es paleoarte de terceros (Britannica,
   museos, artistas). Los sprites generados son obra derivada; para publicar hay que sustituir las
   referencias por propias/CC0 o pedir permiso, y declarar el uso de IA en las tres referencias de
   personajes (sección 8.4, ADR-008/013).
3. **Personajes jugables**: tres en vez de los dos que recomienda la sección 4. Comparten constantes;
   el costo extra de arte lo absorbe el generador (`make_players.py`), no el dibujo a mano.
4. **Vida**: se implementó muerte de un golpe + i-frames al reaparecer (recomendación de 5.2). El
   chaleco de 2 impactos de accesibilidad queda como ajuste apagado (`Game.settings.shield`).
