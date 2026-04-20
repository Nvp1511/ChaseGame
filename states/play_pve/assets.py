import os

import pygame

from config.settings import TILE
from entities.player import Player

from .constants import BASE_DIR


def load_scaled_image(path, size):
	image = pygame.image.load(path)
	return pygame.transform.scale(image, size)


def reset_game_objects():
	player_img = load_scaled_image(os.path.join(BASE_DIR, "assets", "images", "blue.png"), (TILE, TILE))
	enemy_img = load_scaled_image(os.path.join(BASE_DIR, "assets", "images", "ghost_20.png"), (TILE, TILE))
	return Player(player_img), enemy_img
