import pygame
import os

from utils.runtime_paths import resource_path


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
FOOTER_HOVER_TEXT = (255, 255, 255)
FOOTER_ICON_SIZE = 22
FOOTER_ICON_GAP = 8

_ICON_CACHE = {}
_TINT_CACHE = {}


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


def _safe_load_icon(path):
	if path in _ICON_CACHE:
		return _ICON_CACHE[path]

	if not os.path.exists(path):
		_ICON_CACHE[path] = None
		return None

	try:
		loaded = pygame.image.load(path).convert_alpha()
		_ICON_CACHE[path] = loaded
		return loaded
	except pygame.error:
		_ICON_CACHE[path] = None
		return None


def _load_first_available_icon(base_dir, filenames):
	for filename in filenames:
		icon = _safe_load_icon(os.path.join(base_dir, filename))
		if icon is not None:
			return icon
	return None


def _tint_icon(source, tint_color, size=FOOTER_ICON_SIZE):
	cache_key = (id(source), size, tint_color)
	if cache_key in _TINT_CACHE:
		return _TINT_CACHE[cache_key]

	icon = pygame.transform.smoothscale(source, (size, size)).convert_alpha()
	tinted = pygame.Surface((size, size), pygame.SRCALPHA)
	r, g, b = tint_color

	# Keep original alpha edges but force RGB to UI tint color.
	for y in range(size):
		for x in range(size):
			alpha = icon.get_at((x, y)).a
			if alpha:
				# Normalize thin/dim source icons so both footer icons render with equal brightness.
				normalized_alpha = max(170, min(255, int(alpha * 1.8)))
				tinted.set_at((x, y), (r, g, b, normalized_alpha))

	_TINT_CACHE[cache_key] = tinted
	return tinted


def draw_footer_link(screen, text, x, baseline_y, font, align_right=False, hover=False, icon_surface=None):
	color = FOOTER_HOVER_TEXT if hover else SMALL_TEXT
	text_surface = font.render(text, True, color)
	text_height = text_surface.get_height()
	text_y = baseline_y - text_height

	icon_width = FOOTER_ICON_SIZE if icon_surface is not None else 0
	gap = FOOTER_ICON_GAP if icon_surface is not None else 0
	total_width = text_surface.get_width() + icon_width + gap

	if align_right:
		left_x = x - total_width
	else:
		left_x = x

	text_x = left_x + icon_width + gap

	if icon_surface is not None:
		icon_y = text_y + (text_height - FOOTER_ICON_SIZE) // 2
		screen.blit(_tint_icon(icon_surface, color), (left_x, icon_y))

	draw_text(screen, text, font, color, (text_x, text_y), centered=False, shadow=True)

	return pygame.Rect(left_x - 6, text_y - 4, total_width + 12, text_height + 8)


def get_footer_link_rect(text, x, baseline_y, font, align_right=False, has_icon=False):
	text_surface = font.render(text, True, SMALL_TEXT)
	text_height = text_surface.get_height()
	text_y = baseline_y - text_height

	icon_width = FOOTER_ICON_SIZE if has_icon else 0
	gap = FOOTER_ICON_GAP if has_icon else 0
	total_width = text_surface.get_width() + icon_width + gap

	left_x = x - total_width if align_right else x
	return pygame.Rect(left_x - 6, text_y - 4, total_width + 12, text_height + 8)


def run(screen, clock, _payload=None):
	width, height = screen.get_size()
	title_font = get_font(72 if width >= 1100 else 68 if width >= 950 else 64, bold=True)
	button_font = get_font(22, bold=True)
	footer_font = get_font(19, bold=True)

	title_pos = (width // 2, int(height * 0.16))

	button_width = min(340, max(280, int(width * 0.35)))
	button_height = 58
	button_gap = 14
	start_y = int(height * 0.40)
	center_x = width // 2

	pvp_rect = pygame.Rect(center_x - button_width // 2, start_y, button_width, button_height)
	pve_rect = pygame.Rect(center_x - button_width // 2, start_y + button_height + button_gap, button_width, button_height)
	quit_rect = pygame.Rect(center_x - button_width // 2, start_y + (button_height + button_gap) * 2, button_width, button_height)

	footer_y = height - 14
	guide_x = 8
	settings_x = width - 8

	assets_dir = resource_path("assets", "images")
	help_icon = _load_first_available_icon(assets_dir, ["icon_help.png", "question.png", "help.png"])
	settings_icon = _load_first_available_icon(assets_dir, ["icon_settings.png", "icon_setting.png", "settings.png"])

	while True:
		mouse_pos = pygame.mouse.get_pos()
		guide_rect = get_footer_link_rect("Hướng Dẫn", guide_x, footer_y, footer_font, has_icon=help_icon is not None)
		settings_rect = get_footer_link_rect("Cài Đặt", settings_x, footer_y, footer_font, align_right=True, has_icon=settings_icon is not None)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return "quit", None

			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				if pvp_rect.collidepoint(event.pos):
					return "pvp_placeholder", None
				if pve_rect.collidepoint(event.pos):
					return "difficulty", None
				if quit_rect.collidepoint(event.pos):
					return "quit", None
				if guide_rect.collidepoint(event.pos):
					return "instructions", None
				if settings_rect.collidepoint(event.pos):
					return "settings", None

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_h:
					return "instructions", None
				if event.key == pygame.K_s:
					return "settings", None

		screen.fill(MENU_BG)
		draw_text(screen, "CHASE GAME", title_font, TITLE, title_pos, centered=True, shadow=True)

		draw_button(screen, pvp_rect, "Chơi 2 Người (PvP)", PRIMARY, button_font, hover=pvp_rect.collidepoint(mouse_pos))
		draw_button(screen, pve_rect, "Người vs AI (PvE)", SECONDARY, button_font, hover=pve_rect.collidepoint(mouse_pos))
		draw_button(screen, quit_rect, "Thoát Game", NEUTRAL, button_font, hover=quit_rect.collidepoint(mouse_pos))

		guide_rect = draw_footer_link(
			screen,
			"Hướng Dẫn",
			guide_x,
			footer_y,
			footer_font,
			hover=guide_rect.collidepoint(mouse_pos),
			icon_surface=help_icon,
		)
		settings_rect = draw_footer_link(
			screen,
			"Cài Đặt",
			settings_x,
			footer_y,
			footer_font,
			align_right=True,
			hover=settings_rect.collidepoint(mouse_pos),
			icon_surface=settings_icon,
		)

		pygame.display.flip()
		clock.tick(60)
