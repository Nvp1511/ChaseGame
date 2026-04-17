import pygame
import math


SCREEN_LEFT = (250, 237, 214)
SCREEN_RIGHT = (240, 214, 177)
SEAM = (246, 230, 201)
PANEL = (20, 27, 49)
PANEL_SHADOW = (9, 12, 24)
TITLE = (255, 255, 255)
ACCENT = (255, 93, 93)
PRIMARY = (248, 163, 18)
SECONDARY = (51, 183, 88)
NEUTRAL = (97, 109, 130)
SMALL_TEXT = (255, 248, 235)
MENU_BG = (30, 29, 111)
TEXT_SHADOW = (8, 12, 28)


def get_font(size, bold=False):
	for family in ("tahoma", "segoeui", "arial", "dejavusans"):
		font_path = pygame.font.match_font(family, bold=bold)
		if font_path:
			return pygame.font.Font(font_path, size)
	return pygame.font.SysFont("arial", size, bold=bold)


def draw_text(screen, text, font, color, pos, centered=False, shadow=True):
	label = font.render(text, True, color)
	if centered:
		rect = label.get_rect(center=pos)
	else:
		rect = label.get_rect(topleft=pos)

	if shadow:
		shadow_label = font.render(text, True, TEXT_SHADOW)
		screen.blit(shadow_label, rect.move(0, 1))

	screen.blit(label, rect)
	return rect


def lighten(color, amount):
	return tuple(min(255, channel + amount) for channel in color)


def draw_torn_background(screen):
	width, height = screen.get_size()
	seam_width = max(42, width // 18)
	center = width // 2

	left_points = [(0, 0)]
	right_points = [(width, 0)]
	seam_left = []
	seam_right = []

	step = max(34, height // 12)
	for index, y in enumerate(range(0, height + step, step)):
		offset = 8 if index % 2 == 0 else -8
		seam_left.append((center - seam_width // 2 + offset, min(y, height)))
		seam_right.append((center + seam_width // 2 + offset, min(y, height)))

	left_points.extend(seam_left)
	left_points.extend([(0, height)])

	right_points.extend(seam_right)
	right_points.extend([(width, height)])

	screen.fill(SCREEN_LEFT)
	pygame.draw.polygon(screen, SCREEN_RIGHT, right_points)
	pygame.draw.polygon(screen, SEAM, seam_left + list(reversed(seam_right)))


def draw_panel(screen, rect, border_color=ACCENT, fill_color=PANEL, shadow_offset=(7, 8)):
	shadow_rect = rect.move(*shadow_offset)
	pygame.draw.rect(screen, PANEL_SHADOW, shadow_rect, border_radius=18)
	pygame.draw.rect(screen, fill_color, rect, border_radius=18)
	pygame.draw.rect(screen, border_color, rect, width=4, border_radius=18)


def draw_button(screen, rect, text, fill_color, font, text_color=(255, 255, 255), hover=False):
	shadow_rect = rect.move(0, 6)
	pygame.draw.rect(screen, (6, 11, 36), shadow_rect, border_radius=14)

	color = lighten(fill_color, 8) if hover else fill_color
	pygame.draw.rect(screen, color, rect, border_radius=14)
	pygame.draw.rect(screen, (16, 20, 34), rect, width=2, border_radius=14)

	draw_text(screen, text, font, text_color, rect.center, centered=True, shadow=True)


def draw_footer_text(screen, text, position, font, color=SMALL_TEXT):
	draw_text(screen, text, font, color, position, centered=False, shadow=True)


def draw_settings_icon(screen, center, color=SMALL_TEXT, radius=8):
	cx, cy = center
	teeth = 8
	outer_r = radius + 5
	inner_r = radius + 2
	points = []

	for i in range(teeth * 2):
		angle = (math.pi * i) / teeth
		r = outer_r if i % 2 == 0 else inner_r
		points.append((cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle))))

	pygame.draw.polygon(screen, color, points)
	pygame.draw.circle(screen, MENU_BG, (cx, cy), max(2, radius - 2))
	pygame.draw.circle(screen, color, (cx, cy), max(2, radius - 2), 2)


def run(screen, clock, _payload=None):
	width, height = screen.get_size()
	title_font = get_font(72 if width >= 1100 else 68 if width >= 950 else 64, bold=True)
	button_font = get_font(22, bold=True)
	footer_font = get_font(18, bold=True)

	title_pos = (width // 2, int(height * 0.16))

	button_width = min(340, max(280, int(width * 0.35)))
	button_height = 58
	button_gap = 14
	start_y = int(height * 0.40)
	center_x = width // 2

	pvp_rect = pygame.Rect(center_x - button_width // 2, start_y, button_width, button_height)
	pve_rect = pygame.Rect(center_x - button_width // 2, start_y + button_height + button_gap, button_width, button_height)
	quit_rect = pygame.Rect(center_x - button_width // 2, start_y + (button_height + button_gap) * 2, button_width, button_height)

	guide_rect = pygame.Rect(8, height - 40, 165, 32)
	settings_rect = pygame.Rect(width - 184, height - 40, 176, 32)

	while True:
		mouse_pos = pygame.mouse.get_pos()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return "quit", None

			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				if pvp_rect.collidepoint(event.pos):
					return "pvp_placeholder", None
				if pve_rect.collidepoint(event.pos):
					return "game", None
				if quit_rect.collidepoint(event.pos):
					return "quit", None
				if guide_rect.collidepoint(event.pos):
					return "instructions", None
				if settings_rect.collidepoint(event.pos):
					return "settings", None

		screen.fill(MENU_BG)
		draw_text(screen, "CHASE GAME", title_font, TITLE, title_pos, centered=True, shadow=True)

		draw_button(screen, pvp_rect, "Chơi 2 Người (PvP)", PRIMARY, button_font, hover=pvp_rect.collidepoint(mouse_pos))
		draw_button(screen, pve_rect, "Người vs AI (PvE)", SECONDARY, button_font, hover=pve_rect.collidepoint(mouse_pos))
		draw_button(screen, quit_rect, "Thoát Game", NEUTRAL, button_font, hover=quit_rect.collidepoint(mouse_pos))

		draw_footer_text(screen, "Hướng Dẫn", (8, height - 33), footer_font)
		draw_settings_icon(screen, (width - 98, height - 22), SMALL_TEXT, radius=7)
		draw_footer_text(screen, "Cài Đặt", (width - 74, height - 33), footer_font)

		pygame.display.flip()
		clock.tick(60)
