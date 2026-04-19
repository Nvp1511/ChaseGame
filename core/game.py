import sys

import pygame

from config.settings import FPS, HEIGHT, WIDTH
from core.state_manager import StateManager
from states.difficulty_state import run as run_difficulty
from states.game_over_state import run as run_game_over
from states.instruction_state import run as run_instruction
from states.main_menu import run as run_main_menu
from states.play_pve import run as run_play_pve
from states.play_pvp import run as run_play_pvp
from states.settings_state import run as run_settings


def run():
	pygame.init()

	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Chase Game")
	clock = pygame.time.Clock()

	manager = StateManager("menu")
	manager.register("menu", run_main_menu)
	manager.register("difficulty", run_difficulty)
	manager.register("instructions", run_instruction)
	manager.register("settings", run_settings)
	manager.register("game", run_play_pve)
	manager.register("result", run_game_over)
	manager.register("pvp_placeholder", run_play_pvp)
	manager.register("quit", lambda _s, _c, _p: ("quit", None))

	while manager.state != "quit":
		manager.step(screen, clock)

	pygame.quit()
	sys.exit()
