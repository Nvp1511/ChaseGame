import pygame

from states.main_menu import draw_button, draw_panel, draw_torn_background, get_font


def draw_center_card(screen_surface, border_color, title_text, title_color, body_text):
	width, height = screen_surface.get_size()
	draw_torn_background(screen_surface)

	card_rect = pygame.Rect(width // 2 - 190, height // 2 - 210, 380, 420)
	draw_panel(screen_surface, card_rect, border_color=border_color)

	title_font = get_font(46, bold=True)
	body_font = get_font(22, bold=True)

	title_surface = title_font.render(title_text, True, title_color)
	screen_surface.blit(title_surface, title_surface.get_rect(center=(width // 2, card_rect.top + 68)))

	body_surface = body_font.render(body_text, True, (245, 247, 250))
	screen_surface.blit(body_surface, body_surface.get_rect(center=(width // 2, card_rect.top + 125)))

	return card_rect


def run(screen_surface, game_clock, result_type=None):
	width, _height = screen_surface.get_size()
	button_font = get_font(22, bold=True)

	result_type = result_type or "lose"
	border_color = (92, 232, 137) if result_type == "win" else (255, 109, 109)
	title_text = "You Win!" if result_type == "win" else "You Lose!"
	title_color = (83, 232, 143) if result_type == "win" else (255, 125, 125)

	card_rect = draw_center_card(screen_surface, border_color, title_text, title_color, "Kết quả trận đấu đã được xác định")

	button_width = 300
	button_height = 56
	start_y = card_rect.top + 140
	button_gap = 18
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
					return "game", None
				if restart_rect.collidepoint(event.pos):
					return "game", None
				if menu_rect.collidepoint(event.pos):
					return "menu", None

		draw_center_card(screen_surface, border_color, title_text, title_color, "Kết quả trận đấu đã được xác định")

		draw_button(screen_surface, continue_rect, "Tiếp Tục", (30, 147, 184), button_font, hover=continue_rect.collidepoint(mouse_pos))
		draw_button(screen_surface, restart_rect, "Chơi Lại (Restart)", (232, 134, 10), button_font, hover=restart_rect.collidepoint(mouse_pos))
		draw_button(screen_surface, menu_rect, "Về Menu", (92, 104, 124), button_font, hover=menu_rect.collidepoint(mouse_pos))

		pygame.display.flip()
		game_clock.tick(60)
