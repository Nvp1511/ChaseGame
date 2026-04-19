import pygame

from states.main_menu import draw_button, draw_panel, draw_torn_background, get_font


def draw_center_card(screen_surface, result_type):
	width, height = screen_surface.get_size()
	draw_torn_background(screen_surface)

	card_width = min(760, max(420, int(width * 0.46)))
	card_height = min(620, max(500, int(height * 0.80)))
	card_rect = pygame.Rect(width // 2 - card_width // 2, height // 2 - card_height // 2, card_width, card_height)

	if result_type == "win":
		border_color = (92, 232, 137)
		title_text = "You Win!"
		title_color = (83, 232, 143)
	else:
		border_color = (255, 109, 109)
		title_text = "You Lose!"
		title_color = (255, 125, 125)

	draw_panel(screen_surface, card_rect, border_color=border_color)

	title_font = get_font(80 if width >= 1100 else 68 if width >= 950 else 58, bold=True)

	title_surface = title_font.render(title_text, True, title_color)
	screen_surface.blit(title_surface, title_surface.get_rect(center=(width // 2, card_rect.top + 102)))

	return card_rect


def run(screen_surface, game_clock, payload=None):
	width, _height = screen_surface.get_size()
	button_font = get_font(28 if width >= 1100 else 24, bold=True)

	if isinstance(payload, dict):
		result_type = payload.get("result", "lose")
		selected_difficulty = payload.get("difficulty", "medium")
	else:
		result_type = payload or "lose"
		selected_difficulty = "medium"

	card_rect = draw_center_card(screen_surface, result_type)

	button_width = min(560, max(380, card_rect.width - 120))
	button_height = 82
	start_y = card_rect.top + 190
	button_gap = 30
	center_x = width // 2

	continue_rect = pygame.Rect(center_x - button_width // 2, start_y, button_width, button_height)
	restart_rect = pygame.Rect(center_x - button_width // 2, start_y + button_height + button_gap, button_width, button_height)
	menu_rect = pygame.Rect(center_x - button_width // 2, start_y + (button_height + button_gap) * 2, button_width, button_height)

	while True:
		mouse_pos = pygame.mouse.get_pos()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return "quit", None
			if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				return "menu", None
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				if continue_rect.collidepoint(event.pos):
					return "game", {"difficulty": selected_difficulty}
				if restart_rect.collidepoint(event.pos):
					return "game", {"difficulty": selected_difficulty}
				if menu_rect.collidepoint(event.pos):
					return "menu", None

		draw_center_card(screen_surface, result_type)

		draw_button(screen_surface, continue_rect, "Tiếp Tục", (30, 155, 186), button_font, hover=continue_rect.collidepoint(mouse_pos))
		draw_button(screen_surface, restart_rect, "Chơi Lại (Restart)", (228, 131, 10), button_font, hover=restart_rect.collidepoint(mouse_pos))
		draw_button(screen_surface, menu_rect, "Về Menu", (88, 101, 122), button_font, hover=menu_rect.collidepoint(mouse_pos))

		pygame.display.flip()
		game_clock.tick(60)
