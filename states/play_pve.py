import os
import time

import pygame

from ai.bfs import bfs
from config.settings import FPS, TILE, TIME_LIMIT
from entities.enemy import Enemy
from entities.player import Player
from map.map_data import map_data


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLAYER_STEP_MS = 110
PLAYER_ANIM_MS = 90
ENEMY_STEP_MS = 110
ENEMY_ANIM_MS = 90

KEY_TO_DIR = {
	pygame.K_w: (-1, 0),
	pygame.K_s: (1, 0),
	pygame.K_a: (0, -1),
	pygame.K_d: (0, 1),
}


def load_scaled_image(path, size):
	image = pygame.image.load(path)
	return pygame.transform.scale(image, size)


def draw_map(screen_surface):
	for row_index in range(len(map_data)):
		for col_index in range(len(map_data[0])):
			if map_data[row_index][col_index] == "X":
				pygame.draw.rect(
					screen_surface,
					(39, 66, 190),
					(col_index * TILE, row_index * TILE, TILE, TILE),
				)


def reset_game_objects():
	player_img = load_scaled_image(os.path.join(BASE_DIR, "assets", "images", "blue.png"), (TILE, TILE))
	enemy_img = load_scaled_image(os.path.join(BASE_DIR, "assets", "images", "ghost_20.png"), (TILE, TILE))
	return Player(player_img), Enemy(enemy_img)


def run(screen_surface, game_clock, _payload=None):
	player, enemy = reset_game_objects()

	start_time = time.time()
	last_player_step_ms = pygame.time.get_ticks()
	last_enemy_step_ms = pygame.time.get_ticks()

	active_dirs = []
	queued_turn = None

	while True:
		delta_ms = game_clock.tick(FPS)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return "quit", None

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					return "menu", None
				if event.key in KEY_TO_DIR:
					direction = KEY_TO_DIR[event.key]
					queued_turn = direction
					if direction in active_dirs:
						active_dirs.remove(direction)
					active_dirs.append(direction)

			if event.type == pygame.KEYUP and event.key in KEY_TO_DIR:
				direction = KEY_TO_DIR[event.key]
				if direction in active_dirs:
					active_dirs.remove(direction)

		now_ms = pygame.time.get_ticks()

		if now_ms - last_player_step_ms >= PLAYER_STEP_MS:
			moved = False
			used_dir = None

			if queued_turn and player.can_move(queued_turn):
				moved = player.move(queued_turn)
				used_dir = queued_turn
			else:
				for direction in reversed(active_dirs):
					if player.can_move(direction):
						moved = player.move(direction)
						used_dir = direction
						break

			if moved and queued_turn == used_dir:
				queued_turn = None

			last_player_step_ms = now_ms

		if now_ms - last_enemy_step_ms >= ENEMY_STEP_MS:
			path = bfs(enemy.pos, player.pos)
			enemy.update(path)
			last_enemy_step_ms = now_ms

		player.update_animation(delta_ms, PLAYER_ANIM_MS)
		enemy.update_animation(delta_ms, ENEMY_ANIM_MS)

		if player.pos == enemy.pos:
			return "result", "lose"

		if time.time() - start_time >= TIME_LIMIT:
			return "result", "win"

		screen_surface.fill((0, 0, 0))
		draw_map(screen_surface)
		player.draw(screen_surface, TILE)
		enemy.draw(screen_surface, TILE)

		pygame.display.flip()
