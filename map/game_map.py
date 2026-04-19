import pygame


WALL_COLOR = (39, 66, 190)


def draw_map(screen_surface, map_data, tile_size):
	for row_index, row in enumerate(map_data):
		for col_index, cell in enumerate(row):
			if cell == "X":
				pygame.draw.rect(
					screen_surface,
					WALL_COLOR,
					(col_index * tile_size, row_index * tile_size, tile_size, tile_size),
				)


def is_walkable(map_data, cell):
	row_index, col_index = cell
	return 0 <= row_index < len(map_data) and 0 <= col_index < len(map_data[0]) and map_data[row_index][col_index] != "X"
