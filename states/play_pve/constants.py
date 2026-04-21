import pygame

from config.settings import TIME_LIMIT

PLAYER_STEP_MS = 110
PLAYER_ANIM_MS = 90
ENEMY_STEP_MS = 110
ENEMY_ANIM_MS = 90

DIFFICULTY_CONFIG = {
	"easy": {
		"time_limit": 35,
		"enemy_step_ms": ENEMY_STEP_MS ,
		"algorithms": ("vision", "vision", "vision"),
	},
	"medium": {
		"time_limit": TIME_LIMIT + 10,
		"enemy_step_ms": ENEMY_STEP_MS + 5,
		"algorithms": ("vision", "vision", "bfs"),
	},
	"hard": {
		"time_limit": TIME_LIMIT ,
		"enemy_step_ms": ENEMY_STEP_MS - 5,
		"algorithms": ("bfs", "bfs", "astar"),
	},
}

DIFFICULTY_LABELS = {
	"easy": "Dễ",
	"medium": "Trung bình",
	"hard": "Khó",
}

OBJECTIVE_TARGETS = {
	"easy": 5,
	"medium": 5,
	"hard": 5,
}

POWERUP_DURATION_MS = 4200
POWERUP_RESPAWN_RANGE_MS = (2200, 5200)
POWERUP_ON_MAP_CAP = 2
OBJECTIVE_RELOCATE_MS = 6600
POWERUP_LIFETIME_MS = 6500
POWERUP_PLAYER_STEP_BONUS = 34
DANGER_DISTANCE_THRESHOLD = 8

KEY_TO_DIR = {
	pygame.K_w: (-1, 0),
	pygame.K_s: (1, 0),
	pygame.K_a: (0, -1),
	pygame.K_d: (0, 1),
}
