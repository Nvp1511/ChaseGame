import pygame

from config.settings import FPS
from states.main_menu import draw_button, draw_panel, draw_torn_background, get_font


def run(screen_surface, game_clock, _payload=None):
	width, height = screen_surface.get_size()
	title_font = get_font(42, bold=True)
	body_font = get_font(22, bold=True)
	button_font = get_font(20, bold=True)

	card_rect = pygame.Rect(90, 75, width - 180, height - 150)
	back_rect = pygame.Rect(width // 2 - 100, height - 112, 200, 48)

	description_lines = [
		"Phần logic PvP sẽ do thành viên khác của nhóm hoàn thiện.",
		"Màn này là khung giao diện để test và ghép đúng thiết kế.",
		"Bạn có thể quay lại menu và tiếp tục hoàn thiện UI.",
	]

	while True:
		mouse_pos = pygame.mouse.get_pos()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return "quit", None
			if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				return "menu", None
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and back_rect.collidepoint(event.pos):
				return "menu", None

		draw_torn_background(screen_surface)
		draw_panel(screen_surface, card_rect)

		title_surface = title_font.render("Chế độ 2 Người", True, (255, 255, 255))
		screen_surface.blit(title_surface, title_surface.get_rect(center=(width // 2, card_rect.top + 66)))

		current_y = card_rect.top + 145
		for line in description_lines:
			line_surface = body_font.render(line, True, (240, 244, 250))
			screen_surface.blit(line_surface, line_surface.get_rect(center=(width // 2, current_y)))
			current_y += 38

		draw_button(screen_surface, back_rect, "Quay Lại", (96, 106, 126), button_font, hover=back_rect.collidepoint(mouse_pos))

		pygame.display.flip()
		game_clock.tick(FPS)
