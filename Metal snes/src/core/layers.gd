class_name Layers
## Capas de colisión 2D del paso 1.1 (01_Arquitectura_Tecnica). Bit = 1 << (capa - 1).
## Los nombres también están en project.godot ([layer_names]); aquí viven los valores para código.

const TERRAIN := 1 << 0          # 1  suelo, paredes, techos
const PLAYER_BODY := 1 << 1      # 2
const ONE_WAY := 1 << 2          # 3  plataformas atravesables
const ENEMY_BODY := 1 << 3       # 4
const PLAYER_HURTBOX := 1 << 4   # 5
const PLAYER_HITBOX := 1 << 5    # 6  balas y melee del jugador
const ENEMY_HURTBOX := 1 << 6    # 7
const ENEMY_HITBOX := 1 << 7     # 8  balas y melee enemigos
const PICKUPS := 1 << 8          # 9
const HAZARDS := 1 << 9          # 10
const DESTRUCTIBLES := 1 << 10   # 11
const TRIGGERS := 1 << 11        # 12
