# Referencias y licencias — pendientes antes de publicar

Resumen de lo que los roles de arte y narrativa señalaron (noviembre 2026). Nada de esto bloquea el
desarrollo; sí bloquea la publicación (secciones 8.2-8.4 de `02_Documentacion_Proyecto.docx`,
ADR-008 y ADR-013).

| Material | Situación | Qué hacer |
|---|---|---|
| `enemigos y personajes/personajes/*.jpeg` | Tres imágenes de aspecto generado por IA. | Declararlas en la divulgación de IA de itch.io; conservar el prompt/herramienta si se sabe. |
| `enemigos y personajes/dino/*` | Paleoarte descargado de terceros (capturas de navegador, Britannica, museos, un archivo con marca de agua `_wm`). Los sprites de `assets/sprites/enemies/` son obra derivada. | Mantener la carpeta solo como referencia (como los rips de Metal Slug, ADR-013). Antes de publicar: sustituir por reconstrucciones propias, CC0/CC-BY (Wikimedia Commons con atribución) o con permiso, y regenerar con `make_enemies.py` (son 14 entradas en `CREATURES`). |
| Audio `assets/audio/sfx/*.wav` | Síntesis propia (`make_props.py`). | Libre. Las voces de armas (¡DE CAJÓN!, etc.) se graban con gente del campus. |
| Fuente `assets/fonts/pixel5x7` | Dibujada aquí, glifo por glifo. | Libre. |
| Tiles y fondos | Generados por ruido en `make_props.py`. | Libre; son bloqueo, el arte final del piso es tarea de la fase 3. |
| Sprite de Óscar | Hojas de cannabis (gorro, mochila) y cigarro en la referencia. | Decisión del dueño: a 47 px no se leen, pero son un riesgo frente a la identidad UNAM y la clasificación de edad. Se puede borrar en `RIGS["oscar"]["erase_color_boxes"]` o retocar el PNG. |
| Nombre de carpeta `Metal snes` | Zona gris 8.3 si aparece en algo público. | Renombrar a `catastrofe` (o el título que se elija) cuando convenga; el proyecto se llama "Catástrofe en la Biblioteca". |
