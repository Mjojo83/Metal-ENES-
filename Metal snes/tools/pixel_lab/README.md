# pixel_lab

Herramientas de arte del proyecto. Ver `docs/PIPELINE_ARTE.md` para el flujo completo.

| Archivo | Para qué |
|---|---|
| `pixel_lab.py`, `pixelize.py`, `export.py`, `aseprite.py`, `selftest.py` | Pixelizador original (tiras de IA / renders) con salida PNG, `.aseprite` y SpriteFrames. `python selftest.py` → 30 comprobaciones. |
| `regrid.py` | Recupera la rejilla real de "falso pixel art" (referencias de personajes). |
| `puppet.py` | Animación por piezas preservando el pixel (espejos, bandas, giros 90°, RotSprite). |
| `weapons.py` | Escopeta y ametralladora dibujadas a mano, y su paleta. |
| `make_players.py` | Homi, Mariana y Óscar: 39 hojas + `sprite_frames.tres` + vistas previas por personaje. |
| `photo2pixel.py`, `cel.py` | Foto/ilustración → sprite con sombreado cel (materiales, 3 tonos, tinta, acentos). |
| `make_enemies.py` | Las 14 criaturas: sprites, animaciones, `enemy.json`, `sprite_frames.tres`. |
| `make_props.py` | Balas, fogonazos, chispas, humo, esporas, cajas, iconos, fuente bitmap, tiles, fondos, SFX. |
