import pygame


MAP_THEME = {
	"easy": {
		"wall": (72, 154, 116),
		"floor_overlay": (8, 34, 24, 38),
	},
	"medium": {
		"wall": (76, 110, 188),
		"floor_overlay": (10, 20, 44, 40),
	},
	"hard": {
		"wall": (150, 86, 132),
		"floor_overlay": (34, 10, 26, 50),
	},
}


def draw_map(screen_surface, map_data, tile_size, difficulty="medium"):
	theme = MAP_THEME.get(difficulty, MAP_THEME["medium"])
	width = len(map_data[0]) * tile_size
	height = len(map_data) * tile_size
	overlay = pygame.Surface((width, height), pygame.SRCALPHA)
	overlay.fill(theme["floor_overlay"])
	screen_surface.blit(overlay, (0, 0))

	for row_index, row in enumerate(map_data):
		for col_index, cell in enumerate(row):
			if cell == "X":
				pygame.draw.rect(
					screen_surface,
					theme["wall"],
					(col_index * tile_size, row_index * tile_size, tile_size, tile_size),
				)


def is_walkable(map_data, cell):
	row_index, col_index = cell
	return 0 <= row_index < len(map_data) and 0 <= col_index < len(map_data[0]) and map_data[row_index][col_index] != "X"
