import os
import time

import pygame

from config.settings import FPS, TILE
from core.audio_manager import play_background_music, play_sound, stop_background_music
from entities.player import Player
from map.game_map import draw_map as draw_game_map
from map.map_data import map_data, set_map_for_difficulty
from states.main_menu import draw_button, get_font
from utils.runtime_paths import resource_path


PVP_TIME_LIMIT_SEC = 60
PVP_STEP_MS = 110
PVP_ANIM_MS = 90
PVP_TAG_SWITCH_COOLDOWN_MS = 800
PVP_SWITCH_BANNER_MS = 1100

KEY_TO_DIR_P1 = {
	pygame.K_w: (-1, 0),
	pygame.K_s: (1, 0),
	pygame.K_a: (0, -1),
	pygame.K_d: (0, 1),
}

KEY_TO_DIR_P2 = {
	pygame.K_UP: (-1, 0),
	pygame.K_DOWN: (1, 0),
	pygame.K_LEFT: (0, -1),
	pygame.K_RIGHT: (0, 1),
}


def _load_scaled_image(path, size):
	image = pygame.image.load(path)
	return pygame.transform.scale(image, size)


def _build_player_images():
	player1_img = _load_scaled_image(resource_path("assets", "images", "blue.png"), (TILE, TILE)).convert_alpha()
	player2_img = player1_img.copy()
	# Tint second player so both are easy to distinguish.
	player2_img.fill((255, 170, 130, 255), special_flags=pygame.BLEND_RGBA_MULT)
	return player1_img, player2_img


def _find_spawn_cell(start_row, start_col, row_step, col_step):
	rows = range(start_row, len(map_data), row_step) if row_step > 0 else range(start_row, -1, row_step)
	cols = range(start_col, len(map_data[0]), col_step) if col_step > 0 else range(start_col, -1, col_step)
	for row_index in rows:
		for col_index in cols:
			if map_data[row_index][col_index] == " ":
				return [row_index, col_index]
	return [1, 1]


def _pick_direction(player, queued_turn, active_dirs):
	if queued_turn and player.can_move(queued_turn):
		return queued_turn
	for direction in reversed(active_dirs):
		if player.can_move(direction):
			return direction
	return None


def _cell_after_move(current_pos, direction):
	if direction is None:
		return tuple(current_pos)
	return current_pos[0] + direction[0], current_pos[1] + direction[1]


def _apply_cell_move(player, target_cell):
	if tuple(player.pos) == tuple(target_cell):
		return False
	player.prev_pos = player.pos.copy()
	player.pos = [target_cell[0], target_cell[1]]
	player.anim_progress = 0.0
	return True


def _draw_hud(screen_surface, remaining_sec, current_tagger, cooldown_left_ms, hud_font):
	runner = 1 if current_tagger == 2 else 2
	tagger_text = f"[D] Người đuổi: P{current_tagger}"
	runner_text = f"[C] Người chạy: P{runner}"

	items = [
		tagger_text,
		runner_text,
		f"Thời gian: {remaining_sec}s",
	]
	if cooldown_left_ms > 0:
		items.append(f"Đổi vai sau: {cooldown_left_ms / 1000:.1f}s")

	text_surfaces = [hud_font.render(item, True, (242, 246, 255)) for item in items]
	pad_x = 8
	pad_y = 4
	gap = 8

	chip_sizes = [(surface.get_width() + pad_x * 2, surface.get_height() + pad_y * 2) for surface in text_surfaces]
	bar_width = sum(width for width, _height in chip_sizes) + gap * (len(chip_sizes) - 1)
	bar_height = max(height for _width, height in chip_sizes)

	x = max(8, (screen_surface.get_width() - bar_width) // 2)
	y = screen_surface.get_height() - bar_height - 8

	for (surface, (chip_width, chip_height)) in zip(text_surfaces, chip_sizes):
		rect = pygame.Rect(x, y, chip_width, chip_height)
		pygame.draw.rect(screen_surface, (8, 16, 36, 108), rect, border_radius=8)
		pygame.draw.rect(screen_surface, (110, 155, 230, 150), rect, width=1, border_radius=8)
		screen_surface.blit(surface, (rect.x + pad_x, rect.y + pad_y))
		x += chip_width + gap


def _draw_switch_banner(screen_surface, message, banner_font):
	text_surface = banner_font.render(message, True, (255, 247, 230))
	rect = pygame.Rect(
		screen_surface.get_width() // 2 - text_surface.get_width() // 2 - 14,
		18,
		text_surface.get_width() + 28,
		text_surface.get_height() + 12,
	)
	pygame.draw.rect(screen_surface, (20, 36, 72, 170), rect, border_radius=10)
	pygame.draw.rect(screen_surface, (140, 184, 255, 190), rect, width=1, border_radius=10)
	screen_surface.blit(text_surface, (rect.x + 14, rect.y + 6))


def _draw_end_overlay(screen_surface, title_text, subtitle_text, mouse_pos, title_font, body_font):
	width, height = screen_surface.get_size()
	overlay = pygame.Surface((width, height), pygame.SRCALPHA)
	overlay.fill((6, 12, 28, 165))
	screen_surface.blit(overlay, (0, 0))

	panel_rect = pygame.Rect(width // 2 - 270, height // 2 - 160, 540, 320)
	pygame.draw.rect(screen_surface, (10, 24, 58), panel_rect, border_radius=16)
	pygame.draw.rect(screen_surface, (138, 177, 245), panel_rect, width=2, border_radius=16)

	title_surface = title_font.render(title_text, True, (255, 244, 224))
	screen_surface.blit(title_surface, title_surface.get_rect(center=(panel_rect.centerx, panel_rect.top + 72)))

	sub_surface = body_font.render(subtitle_text, True, (230, 236, 248))
	screen_surface.blit(sub_surface, sub_surface.get_rect(center=(panel_rect.centerx, panel_rect.top + 122)))

	restart_rect = pygame.Rect(panel_rect.centerx - 170, panel_rect.top + 176, 340, 56)
	menu_rect = pygame.Rect(panel_rect.centerx - 170, panel_rect.top + 244, 340, 48)

	draw_button(
		screen_surface,
		restart_rect,
		"Chơi Lại PvP",
		(36, 160, 130),
		body_font,
		hover=restart_rect.collidepoint(mouse_pos),
	)
	draw_button(
		screen_surface,
		menu_rect,
		"Về Menu",
		(92, 104, 126),
		body_font,
		hover=menu_rect.collidepoint(mouse_pos),
	)

	return restart_rect, menu_rect


def run(screen_surface, game_clock, _payload=None):
	play_background_music(loop=True, volume_scale=0.34)

	set_map_for_difficulty("medium")
	player1_img, player2_img = _build_player_images()
	player1 = Player(player1_img)
	player2 = Player(player2_img)

	player1.pos = _find_spawn_cell(1, 1, 1, 1)
	player2.pos = _find_spawn_cell(len(map_data) - 2, len(map_data[0]) - 2, -1, -1)
	if player1.pos == player2.pos:
		player2.pos = _find_spawn_cell(1, len(map_data[0]) - 2, 1, -1)
	player1.prev_pos = player1.pos.copy()
	player2.prev_pos = player2.pos.copy()

	hud_font = get_font(16, bold=True)
	title_font = get_font(52, bold=True)
	body_font = get_font(28, bold=True)
	banner_font = get_font(22, bold=True)

	last_step_p1_ms = pygame.time.get_ticks()
	last_step_p2_ms = pygame.time.get_ticks()
	start_time = time.time()

	active_dirs_p1 = []
	active_dirs_p2 = []
	queued_turn_p1 = None
	queued_turn_p2 = None

	current_tagger = 2
	last_switch_ms = pygame.time.get_ticks() - PVP_TAG_SWITCH_COOLDOWN_MS
	switch_banner_text = "Bắt đầu: [D] P2 đuổi | [C] P1 chạy"
	switch_banner_until_ms = pygame.time.get_ticks() + PVP_SWITCH_BANNER_MS
	was_touching_last_tick = False

	is_finished = False
	finish_title = ""
	finish_subtitle = ""
	frozen_remaining_sec = None

	while True:
		delta_ms = game_clock.tick(FPS)
		now_ms = pygame.time.get_ticks()
		mouse_pos = pygame.mouse.get_pos()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				stop_background_music(fade_ms=220)
				return "quit", None

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					stop_background_music(fade_ms=220)
					return "menu", None
				if not is_finished and event.key in KEY_TO_DIR_P1:
					direction = KEY_TO_DIR_P1[event.key]
					queued_turn_p1 = direction
					if direction in active_dirs_p1:
						active_dirs_p1.remove(direction)
					active_dirs_p1.append(direction)
				if not is_finished and event.key in KEY_TO_DIR_P2:
					direction = KEY_TO_DIR_P2[event.key]
					queued_turn_p2 = direction
					if direction in active_dirs_p2:
						active_dirs_p2.remove(direction)
					active_dirs_p2.append(direction)

			if event.type == pygame.KEYUP:
				if event.key in KEY_TO_DIR_P1:
					direction = KEY_TO_DIR_P1[event.key]
					if direction in active_dirs_p1:
						active_dirs_p1.remove(direction)
				if event.key in KEY_TO_DIR_P2:
					direction = KEY_TO_DIR_P2[event.key]
					if direction in active_dirs_p2:
						active_dirs_p2.remove(direction)

			if is_finished and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				restart_rect, menu_rect = _draw_end_overlay(
					screen_surface,
					finish_title,
					finish_subtitle,
					mouse_pos,
					title_font,
					body_font,
				)
				if restart_rect.collidepoint(event.pos):
					stop_background_music(fade_ms=220)
					return "pvp_placeholder", None
				if menu_rect.collidepoint(event.pos):
					stop_background_music(fade_ms=220)
					return "menu", None

		if not is_finished:
			due_p1 = now_ms - last_step_p1_ms >= PVP_STEP_MS
			due_p2 = now_ms - last_step_p2_ms >= PVP_STEP_MS

			old_p1 = tuple(player1.pos)
			old_p2 = tuple(player2.pos)

			dir_p1 = _pick_direction(player1, queued_turn_p1, active_dirs_p1) if due_p1 else None
			dir_p2 = _pick_direction(player2, queued_turn_p2, active_dirs_p2) if due_p2 else None

			target_p1 = _cell_after_move(player1.pos, dir_p1) if due_p1 else old_p1
			target_p2 = _cell_after_move(player2.pos, dir_p2) if due_p2 else old_p2

			if due_p1:
				_apply_cell_move(player1, target_p1)
				last_step_p1_ms = now_ms
				if dir_p1 is not None and queued_turn_p1 == dir_p1:
					queued_turn_p1 = None
			if due_p2:
				_apply_cell_move(player2, target_p2)
				last_step_p2_ms = now_ms
				if dir_p2 is not None and queued_turn_p2 == dir_p2:
					queued_turn_p2 = None

			p1_cell = tuple(player1.pos)
			p2_cell = tuple(player2.pos)

			touch_happened = p1_cell == p2_cell or (p1_cell == old_p2 and p2_cell == old_p1)
			new_touch_event = touch_happened and (not was_touching_last_tick)
			cooldown_ready = now_ms - last_switch_ms >= PVP_TAG_SWITCH_COOLDOWN_MS
			if new_touch_event and cooldown_ready:
				current_tagger = 1 if current_tagger == 2 else 2
				runner = 1 if current_tagger == 2 else 2
				last_switch_ms = now_ms
				switch_banner_text = f"Đổi vai: [D] P{current_tagger} đuổi | [C] P{runner} chạy"
				switch_banner_until_ms = now_ms + PVP_SWITCH_BANNER_MS
				play_sound("start_up", volume_scale=0.8, vary=True)

			was_touching_last_tick = touch_happened

			elapsed_sec = time.time() - start_time
			if (not is_finished) and elapsed_sec >= PVP_TIME_LIMIT_SEC:
				is_finished = True
				winner = 1 if current_tagger == 2 else 2
				finish_title = f"Player {winner} Thắng"
				finish_subtitle = f"Hết giờ: Player {current_tagger} còn là người đuổi"
				frozen_remaining_sec = 0
				play_sound("round_end")

		player1.update_animation(delta_ms, PVP_ANIM_MS)
		player2.update_animation(delta_ms, PVP_ANIM_MS)

		screen_surface.fill((0, 0, 0))
		draw_game_map(screen_surface, map_data, TILE, "pvp")
		player1.draw(screen_surface, TILE)
		player2.draw(screen_surface, TILE)

		if is_finished and frozen_remaining_sec is not None:
			remaining_sec = frozen_remaining_sec
		else:
			remaining_sec = max(0, int(PVP_TIME_LIMIT_SEC - (time.time() - start_time)))
		cooldown_left_ms = max(0, PVP_TAG_SWITCH_COOLDOWN_MS - (now_ms - last_switch_ms))
		_draw_hud(screen_surface, remaining_sec, current_tagger, cooldown_left_ms, hud_font)

		if (not is_finished) and now_ms < switch_banner_until_ms:
			_draw_switch_banner(screen_surface, switch_banner_text, banner_font)

		if is_finished:
			_draw_end_overlay(screen_surface, finish_title, finish_subtitle, mouse_pos, title_font, body_font)

		pygame.display.flip()
