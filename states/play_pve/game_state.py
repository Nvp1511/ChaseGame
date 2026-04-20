import math
import time

import pygame

from config.settings import FPS, TILE
from core.audio_manager import play_sound
from map.game_map import draw_map as draw_game_map
from map.map_data import map_data, set_map_for_difficulty
from states import settings_state

from .ai_logic import algorithm_priority, enemy_move_candidates, enemy_step_interval_ms
from .assets import reset_game_objects
from .constants import (
	DANGER_DISTANCE_THRESHOLD,
	DIFFICULTY_CONFIG,
	KEY_TO_DIR,
	OBJECTIVE_RELOCATE_MS,
	OBJECTIVE_TARGETS,
	PLAYER_ANIM_MS,
	PLAYER_STEP_MS,
	POWERUP_DURATION_MS,
	POWERUP_LIFETIME_MS,
	POWERUP_ON_MAP_CAP,
	POWERUP_PLAYER_STEP_BONUS,
	POWERUP_RESPAWN_RANGE_MS,
)
from .render import (
	draw_danger_feedback,
	draw_hud,
	draw_objectives,
	draw_pause_overlay,
	draw_powerups,
	pause_ui_layout,
)
from .spawn import (
	objective_min_spacing_by_difficulty,
	pick_collectible_cells,
	random_respawn_delay,
	spawn_enemies,
	spawn_min_distance_by_difficulty,
	spawn_powerup_cell,
)


def run(screen_surface, game_clock, _payload=None):
	payload = _payload or {}
	selected_difficulty = payload.get("difficulty", "medium")
	config = DIFFICULTY_CONFIG.get(selected_difficulty, DIFFICULTY_CONFIG["medium"])
	set_map_for_difficulty(selected_difficulty)

	player, enemy_img = reset_game_objects()
	blocked = {tuple(player.pos)}
	for dr in (-1, 0, 1):
		for dc in (-1, 0, 1):
			blocked.add((player.pos[0] + dr, player.pos[1] + dc))
	spawn_min_distance = spawn_min_distance_by_difficulty(selected_difficulty)
	enemies = spawn_enemies(
		enemy_img,
		len(config["algorithms"]),
		blocked,
		player_anchor=player.pos,
		min_player_distance=spawn_min_distance,
	)
	current_time_limit = config["time_limit"]
	current_enemy_step_ms = config["enemy_step_ms"]
	from states.main_menu import get_font

	hud_font = get_font(16, bold=True)
	warning_font = get_font(28, bold=True)

	start_time = time.time()
	last_player_step_ms = pygame.time.get_ticks()
	base_enemy_tick_ms = pygame.time.get_ticks()
	enemy_next_step_ms = [base_enemy_tick_ms + index * 60 for index in range(len(enemies))]
	enemy_anim_duration_ms = [max(80, int(current_enemy_step_ms * 0.85)) for _ in enemies]

	objective_total = OBJECTIVE_TARGETS.get(selected_difficulty, 3)
	objective_cells = pick_collectible_cells(
		objective_total,
		player.pos,
		[enemy.pos for enemy in enemies],
		minimum_distance=8,
		min_spacing=objective_min_spacing_by_difficulty(selected_difficulty),
	)
	objective_total = len(objective_cells)
	objective_cell_set = {tuple(cell) for cell in objective_cells}
	objective_spawn_ms = {tuple(cell): base_enemy_tick_ms for cell in objective_cells}
	collected_objectives = 0

	powerup_cells = []
	powerup_cell_set = set()
	powerup_spawn_ms = {}
	first_powerup = spawn_powerup_cell(player.pos, [enemy.pos for enemy in enemies], objective_cells, minimum_distance=7)
	if first_powerup is not None:
		powerup_cells.append(first_powerup)
		powerup_cell_set.add(tuple(first_powerup))
		powerup_spawn_ms[tuple(first_powerup)] = base_enemy_tick_ms
	powerup_active_until_ms = 0
	next_powerup_spawn_ms = base_enemy_tick_ms + random_respawn_delay(POWERUP_RESPAWN_RANGE_MS)
	player_last_move_dir = (0, 0)
	danger_level = 0.0
	danger_alert = False
	play_sound("start_up")
	is_paused = False
	pause_started_sec = None
	paused_total_sec = 0.0

	active_dirs = []
	queued_turn = None

	while True:
		delta_ms = game_clock.tick(FPS)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return "quit", None

			if is_paused:
				layout = pause_ui_layout(screen_surface)
				resume_rect = layout["resume"]
				settings_rect = layout["settings"]
				menu_rect = layout["menu"]

				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if resume_rect.collidepoint(event.pos):
						is_paused = False
						if pause_started_sec is not None:
							paused_total_sec += time.time() - pause_started_sec
							pause_started_sec = None
						continue
					if settings_rect.collidepoint(event.pos):
						next_state, _payload = settings_state.run(
							screen_surface,
							game_clock,
							{"return_state": "pause"},
						)
						if next_state == "quit":
							return "quit", None
						continue
					if menu_rect.collidepoint(event.pos):
						return "menu", None

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					if is_paused:
						is_paused = False
						if pause_started_sec is not None:
							paused_total_sec += time.time() - pause_started_sec
							pause_started_sec = None
					else:
						is_paused = True
						pause_started_sec = time.time()
						active_dirs.clear()
						queued_turn = None
					continue
				if is_paused:
					if event.key == pygame.K_m:
						return "menu", None
					if event.key == pygame.K_s:
						next_state, _payload = settings_state.run(
							screen_surface,
							game_clock,
							{"return_state": "pause"},
						)
						if next_state == "quit":
							return "quit", None
						continue
					if event.key in (pygame.K_RETURN, pygame.K_SPACE):
						is_paused = False
						if pause_started_sec is not None:
							paused_total_sec += time.time() - pause_started_sec
							pause_started_sec = None
						continue
					continue
				if event.key in KEY_TO_DIR:
					direction = KEY_TO_DIR[event.key]
					queued_turn = direction
					if direction in active_dirs:
						active_dirs.remove(direction)
					active_dirs.append(direction)

			if (not is_paused) and event.type == pygame.KEYUP and event.key in KEY_TO_DIR:
				direction = KEY_TO_DIR[event.key]
				if direction in active_dirs:
					active_dirs.remove(direction)

		now_ms = pygame.time.get_ticks()

		if is_paused:
			elapsed_sec = 0.0
			if pause_started_sec is not None:
				elapsed_sec = max(0.0, pause_started_sec - start_time - paused_total_sec)
			mouse_pos = pygame.mouse.get_pos()

			screen_surface.fill((0, 0, 0))
			draw_game_map(screen_surface, map_data, TILE, selected_difficulty)
			draw_objectives(screen_surface, objective_cells)
			draw_powerups(screen_surface, powerup_cells)
			player.draw(screen_surface, TILE)
			for enemy in enemies:
				enemy.draw(screen_surface, TILE)

			min_enemy_distance = min(
				abs(enemy.pos[0] - player.pos[0]) + abs(enemy.pos[1] - player.pos[1]) for enemy in enemies
			)
			target_danger_level = max(
				0.0,
				(DANGER_DISTANCE_THRESHOLD - min_enemy_distance + 1) / (DANGER_DISTANCE_THRESHOLD + 1),
			)
			smoothing = min(1.0, delta_ms / 180.0)
			danger_level += (target_danger_level - danger_level) * smoothing
			if (not danger_alert) and min_enemy_distance <= 3:
				danger_alert = True
			elif danger_alert and danger_level < 0.36:
				danger_alert = False
			draw_danger_feedback(screen_surface, danger_level, warning_font, min_enemy_distance <= 3)
			boost_remaining_sec = max(0.0, (powerup_active_until_ms - now_ms) / 1000.0)
			draw_pause_overlay(screen_surface, mouse_pos)
			pygame.display.flip()
			continue

		player_step_ms = PLAYER_STEP_MS
		if now_ms < powerup_active_until_ms:
			player_step_ms = max(60, PLAYER_STEP_MS - POWERUP_PLAYER_STEP_BONUS)

		if now_ms - last_player_step_ms >= player_step_ms:
			moved = False
			used_dir = None

			if queued_turn and player.can_move(queued_turn):
				moved = player.move(queued_turn)
				used_dir = queued_turn
			else:
				for direction in reversed(active_dirs):
					if player.can_move(direction):
						moved = player.move(direction)
						used_dir = direction
						break

			if moved and queued_turn == used_dir:
				queued_turn = None
			if moved and used_dir is not None:
				player_last_move_dir = used_dir

			last_player_step_ms = now_ms

		player_cell = tuple(player.pos)
		if player_cell in objective_cell_set:
			objective_cells = [cell for cell in objective_cells if tuple(cell) != player_cell]
			objective_cell_set.discard(player_cell)
			objective_spawn_ms.pop(player_cell, None)
			collected_objectives += 1
			play_sound("eat")

		# Relocate objectives that stay too long without being collected.
		for objective_cell in list(objective_cells):
			cell_key = tuple(objective_cell)
			if now_ms - objective_spawn_ms.get(cell_key, now_ms) < OBJECTIVE_RELOCATE_MS:
				continue

			objective_cells.remove(objective_cell)
			objective_cell_set.discard(cell_key)
			objective_spawn_ms.pop(cell_key, None)
			replacement = spawn_powerup_cell(
				player.pos,
				[enemy.pos for enemy in enemies],
				objective_cells + powerup_cells + [objective_cell],
				minimum_distance=6,
			)
			if replacement is not None and tuple(replacement) not in objective_cell_set:
				objective_cells.append(replacement)
				objective_cell_set.add(tuple(replacement))
				objective_spawn_ms[tuple(replacement)] = now_ms

		for powerup_cell in list(powerup_cells):
			if tuple(powerup_cell) == player_cell:
				powerup_active_until_ms = max(powerup_active_until_ms, now_ms) + POWERUP_DURATION_MS
				powerup_cells.remove(powerup_cell)
				powerup_cell_set.discard(tuple(powerup_cell))
				powerup_spawn_ms.pop(tuple(powerup_cell), None)
				play_sound("eat")

		# Relocate stale powerups that stayed too long without being collected.
		for powerup_cell in list(powerup_cells):
			cell_key = tuple(powerup_cell)
			if now_ms - powerup_spawn_ms.get(cell_key, now_ms) < POWERUP_LIFETIME_MS:
				continue

			powerup_cells.remove(powerup_cell)
			powerup_cell_set.discard(cell_key)
			powerup_spawn_ms.pop(cell_key, None)
			replacement = spawn_powerup_cell(
				player.pos,
				[enemy.pos for enemy in enemies],
				objective_cells + powerup_cells + [powerup_cell],
				minimum_distance=5,
			)
			if replacement is not None and tuple(replacement) not in powerup_cell_set:
				powerup_cells.append(replacement)
				powerup_cell_set.add(tuple(replacement))
				powerup_spawn_ms[tuple(replacement)] = now_ms

		if len(powerup_cells) < POWERUP_ON_MAP_CAP and now_ms >= next_powerup_spawn_ms:
			new_powerup = spawn_powerup_cell(
				player.pos,
				[enemy.pos for enemy in enemies],
				objective_cells + powerup_cells,
				minimum_distance=5,
			)
			if new_powerup is not None and tuple(new_powerup) not in powerup_cell_set:
				powerup_cells.append(new_powerup)
				powerup_cell_set.add(tuple(new_powerup))
				powerup_spawn_ms[tuple(new_powerup)] = now_ms
			next_powerup_spawn_ms = now_ms + random_respawn_delay(POWERUP_RESPAWN_RANGE_MS)

		ready_indices = [index for index in range(len(enemies)) if now_ms >= enemy_next_step_ms[index]]
		if ready_indices:
			elapsed_ratio = min(1.0, (time.time() - start_time - paused_total_sec) / max(1.0, current_time_limit))
			start_cells = {index: tuple(enemies[index].pos) for index in ready_indices}
			all_occupied = {tuple(enemy.pos) for enemy in enemies}
			interval_by_index = {
				index: max(
					50,
					int(
						enemy_step_interval_ms(
							current_enemy_step_ms,
							config["algorithms"][index],
							index,
							selected_difficulty,
						)
						* (1.0 - 0.14 * elapsed_ratio)
					),
				)
				for index in ready_indices
			}
			candidate_by_index = {
				index: enemy_move_candidates(
					enemies[index],
					config["algorithms"][index],
					player.pos,
					index,
					selected_difficulty,
					player_last_move_dir,
					elapsed_ratio,
				)
				for index in ready_indices
			}

			primary_target = {
				index: candidate_by_index[index][0] if candidate_by_index[index] else start_cells[index]
				for index in ready_indices
			}
			index_by_start_cell = {cell: index for index, cell in start_cells.items()}

			moved_indices = set()
			claimed_targets = set()

			# Resolve direct swaps first so enemies do not freeze head-to-head.
			for index in ready_indices:
				if index in moved_indices:
					continue
				my_start = start_cells[index]
				my_primary = primary_target[index]
				other_index = index_by_start_cell.get(my_primary)
				if other_index is None or other_index == index or other_index in moved_indices:
					continue
				if primary_target.get(other_index) != my_start:
					continue

				enemies[index].update([list(my_start), list(my_primary)])
				enemies[other_index].update([list(start_cells[other_index]), list(my_start)])
				enemy_anim_duration_ms[index] = max(80, int(interval_by_index[index] * 0.9))
				enemy_anim_duration_ms[other_index] = max(80, int(interval_by_index[other_index] * 0.9))
				claimed_targets.add(my_primary)
				claimed_targets.add(my_start)
				moved_indices.add(index)
				moved_indices.add(other_index)
				enemy_next_step_ms[index] = now_ms + interval_by_index[index]
				enemy_next_step_ms[other_index] = now_ms + interval_by_index[other_index]

			# Resolve remaining enemies by priority with fallback candidates.
			remaining = [index for index in ready_indices if index not in moved_indices]
			remaining.sort(
				key=lambda index: (
					algorithm_priority(config["algorithms"][index]),
					abs(enemies[index].pos[0] - player.pos[0]) + abs(enemies[index].pos[1] - player.pos[1]),
					index,
				)
			)

			for index in remaining:
				enemy = enemies[index]
				start_cell = tuple(enemy.pos)
				chosen_cell = None

				for candidate in candidate_by_index[index]:
					if candidate == tuple(player.pos):
						chosen_cell = candidate
						break
					if candidate in claimed_targets:
						continue
					if candidate in all_occupied:
						continue
					chosen_cell = candidate
					break

				if chosen_cell is not None and chosen_cell != start_cell:
					all_occupied.discard(start_cell)
					enemy.update([list(start_cell), list(chosen_cell)])
					enemy_anim_duration_ms[index] = max(80, int(interval_by_index[index] * 0.9))
					all_occupied.add(tuple(enemy.pos))
					claimed_targets.add(chosen_cell)
					enemy_next_step_ms[index] = now_ms + interval_by_index[index]
				else:
					enemy_next_step_ms[index] = now_ms + max(42, interval_by_index[index] // 2)

		player.update_animation(delta_ms, PLAYER_ANIM_MS)
		for enemy_index, enemy in enumerate(enemies):
			enemy.update_animation(delta_ms, enemy_anim_duration_ms[enemy_index])

		if collected_objectives >= objective_total:
			play_sound("round_end")
			return "result", {"result": "win", "difficulty": selected_difficulty}

		if any(player.pos == enemy.pos for enemy in enemies):
			play_sound("death")
			return "result", {"result": "lose", "difficulty": selected_difficulty}

		elapsed_sec = time.time() - start_time - paused_total_sec
		if elapsed_sec >= current_time_limit:
			play_sound("round_end")
			return "result", {"result": "win", "difficulty": selected_difficulty}

		screen_surface.fill((0, 0, 0))
		draw_game_map(screen_surface, map_data, TILE, selected_difficulty)
		draw_objectives(screen_surface, objective_cells)
		draw_powerups(screen_surface, powerup_cells)
		player.draw(screen_surface, TILE)
		for enemy in enemies:
			enemy.draw(screen_surface, TILE)

		min_enemy_distance = min(
			abs(enemy.pos[0] - player.pos[0]) + abs(enemy.pos[1] - player.pos[1]) for enemy in enemies
		)
		target_danger_level = max(
			0.0,
			(DANGER_DISTANCE_THRESHOLD - min_enemy_distance + 1) / (DANGER_DISTANCE_THRESHOLD + 1),
		)
		smoothing = min(1.0, delta_ms / 180.0)
		danger_level += (target_danger_level - danger_level) * smoothing
		if (not danger_alert) and min_enemy_distance <= 3:
			danger_alert = True
		elif danger_alert and danger_level < 0.36:
			danger_alert = False
		draw_danger_feedback(screen_surface, danger_level, warning_font, min_enemy_distance <= 3)

		boost_remaining_sec = max(0.0, (powerup_active_until_ms - now_ms) / 1000.0)

		draw_hud(
			screen_surface,
			elapsed_sec,
			current_time_limit,
			hud_font,
			collected_objectives,
			objective_total,
			boost_remaining_sec,
			danger_alert,
		)

		pygame.display.flip()
