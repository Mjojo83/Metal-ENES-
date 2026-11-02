# Dirección de arte pixel — «Catástrofe en la Biblioteca», piso 1 (DEEP FALL)

Base: ADR-002 (320×224), arq. 2.2 (ancla en pies), 3.1 (62 frames), 3.2 (silueta), ADR-008/011/013 y §8.4. Cifras en OKLab (L claridad, C croma, ΔE distancia) medidas sobre las referencias y las salidas actuales del pipeline (`out/chars/*_1x.png`).

## 1. Paleta maestra

Principio: la capa jugable del fondo vive en L 0.30–0.65 y C ≤ 0.10; cada era tiene **un** acento saturado; cada jugador tiene un matiz **reservado** que ninguna era usa.

| Era | Sombra → luz · acentos |
|---|---|
| Cretácico (cuevas secas) | `#1f1512` `#4a2d20` `#8c5a32` `#b8864c` `#dcc088` · `#5e5a52` roca · `#4f7a5a` helecho frío · `#b8382a` rojo sismógrafo, solo peligros |
| Carbonífero (pantano, carbón) | `#0f1a16` `#1b3a30` `#2f6b56` `#5a9a74` `#a8cc8a` · `#4a3a2e` turba · `#8a6a44` madera · `#e0a03a` ámbar (lámparas, ojos, Meganeura) |
| Cámbrico (lecho marino) | `#141026` `#2b2a4e` `#1f5f66` `#3f9a94` `#8fe0cf` aqua · `#7a4a6e` `#b07a9a` malvas de criatura · `#ece3d2` hueso. Verdes a teal, sombras a violeta: dejan libre el azul |
| UI | `#f4efe6` texto · `#1a1410` sombra · `#2a2420` panel · `#ffd23f` munición · `#ff4f3a` daño · `#3fd0ff` recogibles. C 0.14–0.22, más que cualquier era (≤ 0.14) |

Contraste con los jugadores (ΔE mínimo contra Cretácico / Carbonífero / Cámbrico):

- **Homi**: el salmón `#e46c6c` queda a 0.11 de la arenisca. Magenta `#e85a8a` → 0.16 / 0.20 / 0.11; matiz reservado.
- **Mariana**: el marino `#243c6c` (L 0.26–0.36) se funde con el Cámbrico (0.07) y con cualquier cueva. Base `#3d6bb3` (L 0.53), marino solo en sombra → ≥ 0.13. El azul puro es su matiz reservado.
- **Óscar**: el caqui (h≈108°) cae entre ocre y verde; ningún caqui pasa de 0.10. Se resuelve por **valor y acento**: gorro `#c8b878` (L 0.75), chamarra `#9aa040`, pantalón `#3c3c24`, acento azul reservado `#4aa8e0` (martillo de geólogo) → ≥ 0.17.

## 2. Reglas para que lo automático parezca hecho a mano

1. **Contorno** exterior de 1 px, nunca negro puro: el tono más oscuro de cada material (L 0.20–0.25); `#1a1410` solo en el contacto con el suelo. Interior **selectivo**: solo entre formas superpuestas (brazo sobre torso, pierna delantera sobre trasera), nunca dentro de una pieza.
2. **Tres bandas** por material (sombra/base/luz) + contorno; cuatro solo en jefes. ΔL ≥ 0.10 entre bandas; sombra corrida 15–25° hacia azul, luz hacia amarillo. Luz cenital-frontal igual en todos: el espejo no la delata.
3. **Dithering**: cero en actores; en fondos, tablero 50 % en franjas ≥ 4 px.
4. **Clústeres**: isla mínima 3 px (base) y 2 px (luz); píxeles sueltos solo ojo, metal, gotas, máximo 4 por sprite. Aceptación: islas < 3 px ≤ 10 %. Hoy: 285–373 islas por personaje, 72–75 % menores de 3 px; ese es el «aspecto de filtro».
5. **Highlights**: una banda por material en planos que miran arriba, ≤ 25 % de su área, nunca sobre el contorno.
6. **Ojos**: 2×1 o 2×2 px (pupila + 1 px claro) en jugadores; en enemigos un píxel del acento de la era sobre cabeza oscura; jefes 3×3. Lentes de Homi 3×2 px, opacos.
7. **Armas**: pieza aparte dibujada a mano a 1x (pistola 9×5, 3 grises azulados + 1 px de boca), cañón en fila recta, contorno solo abajo y atrás; fogonazo propio de 16×16.
8. **Líneas y presupuesto**: pasada pixel-perfect (sin esquinas en L ni dobles en diagonal), escalones monótonos (1-1-1, 2-2-2, 1-2-1-2); ≤ 16 colores por actor; contorno con |ΔL| ≥ 0.20 frente al suelo.
9. **Re-rejilla**: las referencias IA no están en rejilla exacta (celda 13–14 px con deriva): detectar la retícula en vez de reducir, y recortar la sombra de suelo (en `homi_1x` entró al sprite).

## 3. Vistas y animaciones mínimas

Solo vista lateral; izquierda/derecha por espejo X: nada asimétrico en pecho ni cara, el arma siempre en «la mano de adelante», coleta/mochila/cola en el eje. El jugador se parte en **mitad superior e inferior** (corte a 22 px de los pies) combinadas en tiempo real: correr + disparar sale gratis.

| Actor | Frames | Qué se mueve |
|---|---|---|
| Jugador, inferior | idle 1, correr 8, salto 3, caída 2, aterrizar 2, agacharse 2 | dos piernas, cadera ±1 px |
| Jugador, superior | idle 6, disparo horizontal 3, arriba 3, diagonal 3, lanzar 4, melee 5; morir 8 (entero) | brazo armado como pieza única, torso ±1 px; accesorio (coleta, mochila, faldón) con 1 frame de retraso |
| Bípedo (Velociraptor, T-Rex) | idle 4, andar 6, mordida 4, morir 5; jefe + rugido 4, pisotón 4, morir 8 | piernas, cuello +3 px, mandíbula 2 px, cola en contrafase |
| Reptante (Arthropleura, Eryops, Trilobites, Hallucigenia, Pulmonoscorpius, Megarachne) | andar 4, ataque 3–4, morir 4 | solo la fila de patas (onda 1 px/frame); Arthropleura = cabeza + segmento repetido + cola; muerte = se enrolla |
| Volador (Meganeura, Quetzalcoatlus) | aleteo 4, picada 2, morir 3 | alas 1 pieza por lado; Meganeura con dos pares desfasados |
| Flotante (Nipponites, Anomalocaris, Marrella) | idle 2, ataque 3, morir 3 | vaivén ±2 px por código; aletas/tentáculos como piezas desplazadas |
| Planta (Calamites, Angiosperma) | idle 2, ataque 3, morir 4 | balanceo por shader de cizalla |

Apuntar arriba/diagonal: solo cambia la mitad superior; el pipeline rota la pieza «brazo armado» 45°/90°, limpia, y se corrigen a mano sus ~12 px; los ojos suben 1 px. Daño = paleta a blanco 2 frames.

## 4. Prueba de silueta (14 criaturas + 3 jugadores)

Tamaño y gancho (an×al px): T-Rex 150×145 masa + mandíbula · Velociraptor 48×30 cuerpo horizontal, cola rígida · Quetzalcoatlus 96×64 en vuelo / 40×72 en zancos · Nipponites 28×28 nudo + 3 tentáculos · Arthropleura 112×16 tren bajo con antenas · Calamites 24×90 tallo con nudos · Eryops 64×22 cabeza ancha, patas en X · Meganeura 56×24 cuatro alas · Megarachne 32×24 colgada de un hilo (Emboscada) · Pulmonoscorpius 40×28 cola arqueada encima · Anomalocaris 72×28 apéndices curvos, aletas en sierra · Hallucigenia 40×24 peine de 7 espinas · Marrella 20×16 corona de 4 espinas · Trilobites 24×12 óvalo que se enrolla · jugadores ~24×46.

Riesgos:

- **Largos y bajos** (Arthropleura, Trilobites, Hallucigenia, Eryops): separar por longitud y altura del eje del cuerpo (Eryops 8 px vs Velociraptor 20 px). Espinas de Hallucigenia de 2 px.
- **Arácnidos**: el escorpión lleva la cola encima; Megarachne nunca toca el suelo. Su reconstrucción moderna (euriptérido) se confundiría con el escorpión: usar a propósito la forma de araña.
- **Flotantes con puntas** (Anomalocaris, Marrella, Meganeura): tamaño, altura de vuelo y color (malva / malva / alas claras).
- **Jugadores** (`ad_tmp/silhouettes_players.png`): Mariana lee perfecto (coleta + hueco entre piernas). Homi es una campana: faldón y sombra tapan las piernas; acortar el abrigo a la cadera. La mochila de Óscar compite con la coleta: mantenerla bajo los hombros.

Protocolo: los 17 en negro sobre `#808080` a 1x en 320×224; mirar 0.25 s, desenfocar 1 px, espejear. Si dos se confunden, se rediseña el de menor jerarquía.

## 5. Críticas a las referencias y nota ética

Las tres son chibis IA con cabeza de 12–13 px (28 % de la altura) y proporciones distintas (Óscar 47 px, los otros 43): unificar a un cuerpo compartido de 46 px (doc §4) y diferenciar solo cabeza, paleta y un accesorio-pieza.

- **Homi**: el moteado del abrigo es la fuente principal de ruido; abrigo en 2 tonos planos. Pantalón, cinturón y botas negros colapsan en bloque: pantalón ciruela `#3a2a3a`, botas más claras. Pistola café contra pelo café: metal gris azulado. Conservar pelo redondo + lentes.
- **Mariana**: hebras grises de 1 px en el pelo = ruido; 2 tonos. Zapatos del mismo L que el pantalón. Brazos extendidos fundidos: línea interior selectiva. Quitar la nariz.
- **Óscar**: oliva sin estructura de valor (receta del §1). Cuerda, mosquetones, parches y acanalado del gorro son detalles de 1–2 px: mochila en 2 tonos + correa, gorro liso. El cigarro y las hojas de cannabis no se leen y son un pasivo para un proyecto con identidad UNAM (§8.2): sustituir por martillo de geólogo.

**Ética/legal.** `dino/` mezcla paleoarte con copyright identificable (Britannica, fossilguy.com, Mark Witton, prehistoric-wildlife.com, el T-Rex), fotos de maquetas, capturas de navegador e imágenes IA. Mirarlas para anatomía es referencia legítima; pasarlas por el pipeline (recorte → rejilla → paleta) produce una **obra derivada**, lo que ADR-008 prohíbe aunque el resultado «se vea distinto». Regla: el pipeline solo consume una carpeta `propios/` (dibujo propio, IA declarada, CC0 o dominio público verificado, CC BY con atribución; CC BY-SA no). Las referencias de personajes son IA: registrar hoy herramienta y licencia, declararlo en itch.io (§8.4). `dino/` queda fuera del repo como los rips de Metal Slug (ADR-013), con un `CREDITS_referencias.md` de fuente y licencia por archivo.
