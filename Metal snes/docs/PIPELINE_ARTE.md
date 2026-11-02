# Pipeline de arte (noviembre 2026)

Todo el arte del juego sale de `tools/pixel_lab/` a partir de las referencias de
`../enemigos y personajes/`. Un pixel de la referencia procesada es un pixel del juego; Godot no
reescala nada (ADR-002/ADR-011). Regenerar todo tarda menos de un minuto:

```
cd "Metal snes"
python tools/pixel_lab/make_players.py --refs "../enemigos y personajes/personajes" --out assets/sprites/player
python tools/pixel_lab/make_enemies.py --refs "../enemigos y personajes/dino" --out assets/sprites/enemies
python tools/level_gen/export_enemy_data.py --root .      # data/enemies/*.tres
python tools/pixel_lab/make_props.py --root .              # balas, fogonazos, cajas, iconos, tiles, fondos, fuente, SFX
python tools/level_gen/deep_fall_01.py --root .            # data/levels + data/waves
python tools/mockup/compose_320.py --root . --out docs/mockups   # maquetas 320×224 sin motor
```

Dependencias: Python 3.11+, `pip install pillow numpy scipy opencv-python-headless rembg[cpu]`
(rembg descarga el modelo `isnet-general-use` la primera vez).

## Personajes (`make_players.py`)

Las tres referencias son pixel art generado por IA a ~14 px por "pixel" con rejilla irregular y JPEG.

1. `regrid.py` detecta el periodo y la fase de la rejilla por el gradiente, toma la mediana del
   interior de cada celda, quita el fondo por inundación y reduce la paleta en OKLab. Resultado:
   el sprite a su tamaño real (42×43 Homi, 41×43 Mariana, 40×47 Óscar) con 12-14 colores.
2. `puppet.py` anima por piezas con operaciones que **preservan el pixel**: espejo de la banda de
   piernas (la otra pierna adelante gratis), corrimientos para cerrar las piernas, estirado de una
   fila para el "bob", giros exactos de 90° (apuntar arriba/abajo) y giro tipo RotSprite (EPX ×8 +
   muestreo por votos) para las diagonales y la caída al morir. Luego `seal_outline` repara las
   costuras con el color de contorno sin engrosar la silueta.
3. `weapons.py` dibuja a mano la escopeta y la ametralladora (rejilla de letras) y las pone en la
   mano, borrando la pistola. Se generan las 13 animaciones × 3 armas = 39 hojas por personaje.
4. Lienzo fijo 64×64, pies en la fila 62, centrados: en Godot el `AnimatedSprite2D` lleva
   `centered = false` y `offset = (-32, -64)` para que el origen sea la planta de los pies (paso 2.2).

El esqueleto de cada personaje (filas de piernas, codo, caja de la pistola, piel) está en `RIGS`.
Para ajustar una pose, cambia ahí y regenera; para retocar a mano, edita el PNG de la animación y
no vuelvas a correr el generador sobre esa carpeta (o guarda tu copia).

## Criaturas (`make_enemies.py` + `cel.py`)

Las referencias son fotos/ilustraciones. Para que el resultado parezca dibujado y no "una imagen mal
hecha", el estilo imita el de los personajes:

1. Mate con `rembg` (o color del borde/negro), niveles automáticos y desplazamiento de medias.
2. `cel.py`: reducción por área a la altura objetivo → **materiales** (k-means en OKLab, se funden los
   parecidos) → **tres tonos por material** cortados sobre la luz suavizada (las bandas siguen la
   forma, no el grano) → paleta de 7-13 colores con sombra fría/saturada y luz cálida → contorno casi
   negro + **tinta interior** donde la referencia tiene un borde fuerte entre regiones → acentos
   (ojos/garras, máximo 2 colores) → un brillo → limpieza de motas.
3. Esqueleto automático según el tipo (`rig`): bípedo/cuadrúpedo (banda de piernas detectada por
   la silueta), reptante (ondulación por columnas), volador (alas arriba/medio/abajo), flotante,
   planta (inclinación). Animaciones: `idle`, `move`, `telegraph`, `attack`, `die` (aplastado).
4. Todas miran a la **izquierda** (vienen por la derecha); Godot espeja con `flip_h`.
5. `enemy.json` por criatura → `export_enemy_data.py` escribe `data/enemies/<id>.tres` (perfil de
   IA y números de diseño en `TUNING`).

Parámetros por criatura en `CREATURES`: referencia, recorte, mate, espejo/giro, altura en px,
materiales, tipo de esqueleto, perfil, vida, velocidad, puntos, hurtbox.

## Lo que falta para "a mano"

- Retoque de ojos y bocas (1-3 px) y de las poses de ataque en Aseprite/PixelForja: el generador
  escribe PNG planos; `pixel_lab.py` sabe escribir `.aseprite` si se quiere ese flujo.
- Idle cosmético por carrera (ver `docs/ROLES_PROPUESTAS/04_narrativa_audio.md`).
- Referencias propias o CC0 para publicar (ver `docs/REFERENCIAS_Y_LICENCIAS.md`).
