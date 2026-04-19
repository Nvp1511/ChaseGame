import pygame

from states.main_menu import MENU_BG, draw_button, draw_panel, get_font


def run(screen_surface, game_clock, _payload=None):
	width, height = screen_surface.get_size()
	title_font = get_font(44, bold=True)
	subtitle_font = get_font(22, bold=True)
	button_font = get_font(22, bold=True)
	hint_font = get_font(17, bold=False)

	panel_width = min(640, max(470, int(width * 0.62)))
	panel_height = min(500, max(420, int(height * 0.72)))
	panel_rect = pygame.Rect(width // 2 - panel_width // 2, height // 2 - panel_height // 2, panel_width, panel_height)

	button_width = min(420, panel_rect.width - 120)
	button_height = 58
	button_gap = 16
	button_x = width // 2 - button_width // 2
	start_y = panel_rect.top + 148

	easy_rect = pygame.Rect(button_x, start_y, button_width, button_height)
	medium_rect = pygame.Rect(button_x, start_y + (button_height + button_gap), button_width, button_height)
	hard_rect = pygame.Rect(button_x, start_y + (button_height + button_gap) * 2, button_width, button_height)
	back_rect = pygame.Rect(width // 2 - 110, panel_rect.bottom - 78, 220, 48)

	while True:
		mouse_pos = pygame.mouse.get_pos()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return "quit", None
			if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				return "menu", None

			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				if easy_rect.collidepoint(event.pos):
					return "game", {"difficulty": "easy"}
				if medium_rect.collidepoint(event.pos):
					return "game", {"difficulty": "medium"}
				if hard_rect.collidepoint(event.pos):
					return "game", {"difficulty": "hard"}
				if back_rect.collidepoint(event.pos):
					return "menu", None

		screen_surface.fill(MENU_BG)
		draw_panel(screen_surface, panel_rect, border_color=(255, 121, 130))

		title = title_font.render("CHỌN ĐỘ KHÓ", True, (255, 171, 29))
		screen_surface.blit(title, title.get_rect(center=(width // 2, panel_rect.top + 56)))

		subtitle = subtitle_font.render("Chọn mức độ thử thách trước khi chơi", True, (240, 244, 250))
		screen_surface.blit(subtitle, subtitle.get_rect(center=(width // 2, panel_rect.top + 102)))

		draw_button(screen_surface, easy_rect, "Dễ", (41, 174, 112), button_font, hover=easy_rect.collidepoint(mouse_pos))
		draw_button(screen_surface, medium_rect, "Trung Bình", (236, 158, 23), button_font, hover=medium_rect.collidepoint(mouse_pos))
		draw_button(screen_surface, hard_rect, "Khó", (226, 92, 92), button_font, hover=hard_rect.collidepoint(mouse_pos))
		draw_button(screen_surface, back_rect, "Quay Lại", (90, 104, 128), get_font(20, bold=True), hover=back_rect.collidepoint(mouse_pos))

		hint = hint_font.render("Nhấn ESC để quay lại menu", True, (189, 198, 216))
		screen_surface.blit(hint, hint.get_rect(center=(width // 2, panel_rect.bottom - 20)))

		pygame.display.flip()
		game_clock.tick(60)
