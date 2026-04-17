import pygame

from states.main_menu import draw_torn_background, draw_panel, draw_button, PANEL, TITLE, ACCENT, NEUTRAL, get_font


def run(screen, clock, _payload=None):
	width, height = screen.get_size()
	title_font = get_font(40, bold=True)
	body_font = get_font(24, bold=True)
	button_font = get_font(20, bold=True)

	panel_rect = pygame.Rect(90, 65, width - 180, height - 130)
	back_rect = pygame.Rect(width // 2 - 90, height - 122, 180, 48)

	volume = 0.8
	slider_rect = pygame.Rect(panel_rect.left + 120, panel_rect.top + 175, panel_rect.width - 240, 12)
	knob_radius = 16

	while True:
		mouse_pos = pygame.mouse.get_pos()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return "quit", None
			if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				return "menu", None
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				if back_rect.collidepoint(event.pos):
					return "menu", None
				if slider_rect.inflate(0, 28).collidepoint(event.pos):
					volume = max(0.0, min(1.0, (event.pos[0] - slider_rect.left) / slider_rect.width))
			if event.type == pygame.MOUSEMOTION and event.buttons[0]:
				if slider_rect.inflate(20, 28).collidepoint(event.pos):
					volume = max(0.0, min(1.0, (event.pos[0] - slider_rect.left) / slider_rect.width))

		draw_torn_background(screen)
		draw_panel(screen, panel_rect, border_color=ACCENT, fill_color=PANEL)

		title = title_font.render("CÀI ĐẶT", True, (255, 171, 29))
		screen.blit(title, title.get_rect(center=(width // 2, panel_rect.top + 58)))

		volume_label = body_font.render(f"Âm thanh: {int(volume * 100)}%", True, (245, 247, 250))
		screen.blit(volume_label, (slider_rect.left - 20, slider_rect.top - 58))

		pygame.draw.rect(screen, (64, 74, 96), slider_rect, border_radius=8)
		filled_width = max(0, int(slider_rect.width * volume))
		filled_rect = pygame.Rect(slider_rect.left, slider_rect.top, filled_width, slider_rect.height)
		pygame.draw.rect(screen, (255, 167, 31), filled_rect, border_radius=8)

		knob_x = slider_rect.left + filled_width
		knob_center = (knob_x, slider_rect.centery)
		pygame.draw.circle(screen, (250, 250, 250), knob_center, knob_radius)
		pygame.draw.circle(screen, (34, 42, 64), knob_center, knob_radius, 2)

		draw_button(screen, back_rect, "Quay Lại", NEUTRAL, button_font, hover=back_rect.collidepoint(mouse_pos))

		pygame.display.flip()
		clock.tick(60)
