import math

import pygame

from config.settings import TILE
from states.main_menu import draw_button, draw_panel, get_font

from .constants import DANGER_DISTANCE_THRESHOLD


def draw_objectives(screen_surface, objective_cells):
	for row_index, col_index in objective_cells:
		center = (col_index * TILE + TILE // 2, row_index * TILE + TILE // 2)
		pygame.draw.circle(screen_surface, (255, 208, 76), center, max(4, TILE // 4))
		pygame.draw.circle(screen_surface, (255, 245, 210), center, max(2, TILE // 8))


def draw_powerups(screen_surface, powerup_cells):
	for row_index, col_index in powerup_cells:
		rect = pygame.Rect(col_index * TILE + 5, row_index * TILE + 5, TILE - 10, TILE - 10)
		pygame.draw.rect(screen_surface, (89, 232, 159), rect, border_radius=6)
		pygame.draw.rect(screen_surface, (212, 255, 232), rect, width=2, border_radius=6)


def draw_danger_feedback(screen_surface, danger_level, warning_font, critical_alert=False):
	danger_level = max(0.0, min(1.0, danger_level))
	if danger_level <= 0.01:
		return

	factor = danger_level
	alpha = min(48, max(8, int(52 * factor)))
	overlay = pygame.Surface(screen_surface.get_size(), pygame.SRCALPHA)
	overlay.fill((145, 26, 26, alpha))
	screen_surface.blit(overlay, (0, 0))

	# Keep warning movement subtle to avoid visual jitter while still feeling urgent.
	pulse = 0.84 + 0.16 * math.sin(pygame.time.get_ticks() * 0.004)
	border_alpha = min(175, max(72, int((85 + 70 * factor) * pulse)))
	border_width = max(2, int(2 + 5 * factor))

	border_layer = pygame.Surface(screen_surface.get_size(), pygame.SRCALPHA)
	pygame.draw.rect(
		border_layer,
		(255, 82, 82, border_alpha),
		border_layer.get_rect().inflate(-4, -4),
		width=border_width,
		border_radius=12,
	)
	screen_surface.blit(border_layer, (0, 0))

	if critical_alert:
		warning = warning_font.render("DANGER", True, (255, 244, 244))
		screen_surface.blit(warning, warning.get_rect(center=(screen_surface.get_width() // 2, 26)))


def draw_hud(
	screen_surface,
	elapsed_sec,
	time_limit,
	hud_font,
	objective_collected,
	objective_total,
	boost_remaining_sec,
	danger_alert=False,
):
	remaining = max(0, math.ceil(time_limit - elapsed_sec))
	boost_sec = max(0.0, boost_remaining_sec)
	# Quantize to 0.5s steps so the timer is easier to read and less jittery.
	display_boost_sec = math.floor(boost_sec * 2.0) / 2.0
	boost_text = "Tăng tốc 0s" if display_boost_sec <= 0.0 else f"Tăng tốc {display_boost_sec:.1f}s"

	# Keep in-match HUD minimal: only critical information needed while moving.
	hud_items = [
		f"Thời gian {remaining}s",
		f"Mục tiêu {objective_collected}/{objective_total}",
		boost_text,
	]

	text_surfaces = [hud_font.render(item, True, (242, 246, 255)) for item in hud_items]
	chip_pad_x = 8
	chip_pad_y = 4
	chip_gap = 8
	row_gap = 6
	left_margin = 8
	# Reserve a larger top safe zone so HUD never overlaps the centered DANGER warning.
	danger_safe_top = max(56, int(screen_surface.get_height() * 0.09))
	top_margin = danger_safe_top if danger_alert else 2
	max_row_width = screen_surface.get_width() - left_margin * 2

	def chip_width(surface):
		return surface.get_width() + chip_pad_x * 2

	rows = [[]]
	current_width = 0
	for surface in text_surfaces:
		w = chip_width(surface)
		extra_gap = chip_gap if rows[-1] else 0
		if rows[-1] and current_width + extra_gap + w > max_row_width:
			rows.append([surface])
			current_width = w
		else:
			rows[-1].append(surface)
			current_width += extra_gap + w

	y_cursor = top_margin
	for row in rows:
		x_cursor = left_margin
		row_height = 0
		for surface in row:
			chip_rect = pygame.Rect(x_cursor, y_cursor, chip_width(surface), surface.get_height() + chip_pad_y * 2)
			pygame.draw.rect(screen_surface, (8, 16, 36, 120), chip_rect, border_radius=8)
			pygame.draw.rect(screen_surface, (110, 155, 230, 165), chip_rect, width=1, border_radius=8)
			screen_surface.blit(surface, (chip_rect.x + chip_pad_x, chip_rect.y + chip_pad_y))
			x_cursor += chip_rect.width + chip_gap
			row_height = max(row_height, chip_rect.height)
		y_cursor += row_height + row_gap


def pause_ui_layout(screen_surface):
	width, height = screen_surface.get_size()
	panel_width = min(620, max(460, int(width * 0.52)))
	panel_height = min(500, max(400, int(height * 0.56)))
	panel_rect = pygame.Rect(width // 2 - panel_width // 2, height // 2 - panel_height // 2, panel_width, panel_height)

	button_width = panel_width - 120
	button_height = 72
	button_x = panel_rect.left + (panel_width - button_width) // 2
	resume_rect = pygame.Rect(button_x, panel_rect.top + 128, button_width, button_height)
	settings_rect = pygame.Rect(button_x, resume_rect.bottom + 20, button_width, button_height)
	menu_rect = pygame.Rect(button_x, settings_rect.bottom + 20, button_width, button_height)

	return {
		"panel": panel_rect,
		"resume": resume_rect,
		"settings": settings_rect,
		"menu": menu_rect,
	}


def draw_pause_overlay(screen_surface, mouse_pos):
	overlay = pygame.Surface(screen_surface.get_size(), pygame.SRCALPHA)
	overlay.fill((4, 10, 24, 165))
	screen_surface.blit(overlay, (0, 0))

	layout = pause_ui_layout(screen_surface)
	panel_rect = layout["panel"]
	resume_rect = layout["resume"]
	settings_rect = layout["settings"]
	menu_rect = layout["menu"]

	title_font = get_font(56 if screen_surface.get_width() >= 1100 else 48, bold=True)
	body_font = get_font(36 if screen_surface.get_width() >= 1100 else 30, bold=True)

	draw_panel(screen_surface, panel_rect, border_color=(255, 109, 109), fill_color=(10, 24, 58), shadow_offset=(8, 9))

	title = title_font.render("Tạm Dừng", True, (255, 140, 140))
	screen_surface.blit(title, title.get_rect(center=(panel_rect.centerx, panel_rect.top + 56)))

	draw_button(screen_surface, resume_rect, "Tiếp Tục", (30, 155, 186), body_font, hover=resume_rect.collidepoint(mouse_pos))
	draw_button(screen_surface, settings_rect, "Cài Đặt", (228, 131, 10), body_font, hover=settings_rect.collidepoint(mouse_pos))
	draw_button(screen_surface, menu_rect, "Về Menu", (88, 101, 122), body_font, hover=menu_rect.collidepoint(mouse_pos))
