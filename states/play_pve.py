import os
import time
import math
import random
from collections import deque

import pygame

from ai.astar import astar
from ai.bfs import bfs
from ai.vision_ai import vision_move
from config.settings import FPS, TILE, TIME_LIMIT
from core.audio_manager import play_sound
from entities.enemy import Enemy
from entities.player import Player
from map.game_map import draw_map as draw_game_map
from map.game_map import is_walkable
from map.map_data import map_data, set_map_for_difficulty


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLAYER_STEP_MS = 110
PLAYER_ANIM_MS = 90
ENEMY_STEP_MS = 110
ENEMY_ANIM_MS = 90

DIFFICULTY_CONFIG = {
	"easy": {
		"time_limit": 35,
		"enemy_step_ms": ENEMY_STEP_MS+35,
		"algorithms": ("vision", "vision", "vision"),
	},
	"medium": {
		"time_limit": TIME_LIMIT + 4,
		"enemy_step_ms": ENEMY_STEP_MS+5,
		"algorithms": ("vision", "vision", "bfs"),
	},
	"hard": {
		"time_limit": max(12, TIME_LIMIT - 4),
		"enemy_step_ms": ENEMY_STEP_MS - 5,
		"algorithms": ("vision", "bfs", "astar"),
	},
}

DIFFICULTY_LABELS = {
	"easy": "De",
	"medium": "Trung binh",
	"hard": "Kho",
}

OBJECTIVE_TARGETS = {
	"easy": 3,
	"medium": 3,
	"hard": 4,
}

POWERUP_DURATION_MS = 4200
POWERUP_RESPAWN_RANGE_MS = (2200, 5200)
POWERUP_ON_MAP_CAP = 2
OBJECTIVE_RELOCATE_MS = 7600
POWERUP_LIFETIME_MS = 6500
POWERUP_PLAYER_STEP_BONUS = 34
DANGER_DISTANCE_THRESHOLD = 8

KEY_TO_DIR = {
	pygame.K_w: (-1, 0),
	pygame.K_s: (1, 0),
	pygame.K_a: (0, -1),
	pygame.K_d: (0, 1),
}


def load_scaled_image(path, size):
	image = pygame.image.load(path)
	return pygame.transform.scale(image, size)


def reset_game_objects():
	player_img = load_scaled_image(os.path.join(BASE_DIR, "assets", "images", "blue.png"), (TILE, TILE))
	enemy_img = load_scaled_image(os.path.join(BASE_DIR, "assets", "images", "ghost_20.png"), (TILE, TILE))
	return Player(player_img), enemy_img


def _build_enemy_path(algo_name, enemy_pos, player_pos, previous_pos=None):
	if algo_name == "vision":
		next_pos = vision_move(enemy_pos, player_pos, previous_pos)
		return [list(enemy_pos), list(next_pos)]
	if algo_name == "astar":
		return astar(enemy_pos, player_pos)
	return bfs(enemy_pos, player_pos)


def _spawn_enemies(enemy_img, count, blocked_cells=None, player_anchor=None, min_player_distance=0):
	blocked_cells = blocked_cells or set()
	player_anchor = player_anchor or [1, 1]

	def manhattan(a, b):
		return abs(a[0] - b[0]) + abs(a[1] - b[1])

	def gather_cells(distance_threshold):
		cells = []
		for row_index in range(1, len(map_data) - 1):
			for col_index in range(1, len(map_data[0]) - 1):
				if (
					map_data[row_index][col_index] == " "
					and (row_index, col_index) not in blocked_cells
					and manhattan([row_index, col_index], player_anchor) >= distance_threshold
				):
					cells.append([row_index, col_index])
		return cells

	open_cells = gather_cells(min_player_distance)

	# Relax threshold gradually only when map cannot satisfy the minimum distance.
	if not open_cells and min_player_distance > 0:
		for threshold in range(min_player_distance - 1, -1, -1):
			open_cells = gather_cells(threshold)
			if open_cells:
				break

	if not open_cells:
		fallback = [len(map_data) - 2, len(map_data[0]) - 2]
		return [Enemy(enemy_img, fallback.copy()) for _ in range(count)]

	spawn_points = []
	available = list(open_cells)

	for _ in range(count):
		best_index = 0
		best_score = (-1, -1)
		for index, cell in enumerate(available):
			dist_from_player = manhattan(cell, player_anchor)
			dist_from_group = min((manhattan(cell, other) for other in spawn_points), default=999)
			score = (dist_from_player, dist_from_group)
			if score > best_score:
				best_score = score
				best_index = index

		spawn_points.append(available.pop(best_index))
		if not available:
			available = list(open_cells)

	return [Enemy(enemy_img, pos) for pos in spawn_points]


def _spawn_min_distance_by_difficulty(difficulty):
	if difficulty == "easy":
		return 16
	if difficulty == "medium":
		return 13
	return 10


def _all_open_cells():
	open_cells = []
	for row_index in range(1, len(map_data) - 1):
		for col_index in range(1, len(map_data[0]) - 1):
			if map_data[row_index][col_index] == " ":
				open_cells.append([row_index, col_index])
	return open_cells


def _reachable_open_cells(start_pos):
	if not is_walkable(map_data, start_pos):
		return []

	queue = deque([tuple(start_pos)])
	visited = {tuple(start_pos)}
	reachable = []

	while queue:
		row_index, col_index = queue.popleft()
		reachable.append([row_index, col_index])

		for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
			nr = row_index + dr
			nc = col_index + dc
			next_cell = (nr, nc)
			if next_cell in visited:
				continue
			if not is_walkable(map_data, [nr, nc]):
				continue
			visited.add(next_cell)
			queue.append(next_cell)

	return reachable


def _pick_collectible_cells(count, player_pos, enemy_positions, minimum_distance=7, min_spacing=6):
	excluded = {tuple(player_pos), *{tuple(pos) for pos in enemy_positions}}
	candidate_cells = []
	for cell in _reachable_open_cells(player_pos):
		cell_key = tuple(cell)
		if cell_key in excluded:
			continue
		distance = abs(cell[0] - player_pos[0]) + abs(cell[1] - player_pos[1])
		if distance >= minimum_distance:
			candidate_cells.append(cell)

	if len(candidate_cells) < count:
		candidate_cells = [cell for cell in _reachable_open_cells(player_pos) if tuple(cell) not in excluded]

	def manhattan(a, b):
		return abs(a[0] - b[0]) + abs(a[1] - b[1])

	random.shuffle(candidate_cells)
	selected = []
	for cell in candidate_cells:
		if all(manhattan(cell, other) >= min_spacing for other in selected):
			selected.append(cell)
			if len(selected) >= count:
				return selected

	# If map is too constrained, gradually relax spacing.
	for spacing in range(min_spacing - 1, -1, -1):
		random.shuffle(candidate_cells)
		selected = []
		for cell in candidate_cells:
			if all(manhattan(cell, other) >= spacing for other in selected):
				selected.append(cell)
				if len(selected) >= count:
					return selected

	return selected


def _objective_min_spacing_by_difficulty(difficulty):
	if difficulty == "easy":
		return 7
	if difficulty == "medium":
		return 6
	return 5


def _spawn_powerup_cell(player_pos, enemy_positions, objective_cells, minimum_distance=6):
	blocked = {tuple(player_pos), *{tuple(pos) for pos in enemy_positions}, *{tuple(cell) for cell in objective_cells}}
	candidates = []
	for cell in _reachable_open_cells(player_pos):
		cell_key = tuple(cell)
		if cell_key in blocked:
			continue
		distance = abs(cell[0] - player_pos[0]) + abs(cell[1] - player_pos[1])
		if distance >= minimum_distance:
			candidates.append(cell)

	if not candidates:
		candidates = [cell for cell in _reachable_open_cells(player_pos) if tuple(cell) not in blocked]
	if not candidates:
		return None

	return random.choice(candidates)


def _random_respawn_delay(respawn_range):
	min_ms, max_ms = respawn_range
	return random.randint(min_ms, max_ms)


def _draw_objectives(screen_surface, objective_cells):
	for row_index, col_index in objective_cells:
		center = (col_index * TILE + TILE // 2, row_index * TILE + TILE // 2)
		pygame.draw.circle(screen_surface, (255, 208, 76), center, max(4, TILE // 4))
		pygame.draw.circle(screen_surface, (255, 245, 210), center, max(2, TILE // 8))


def _draw_powerups(screen_surface, powerup_cells):
	for row_index, col_index in powerup_cells:
		rect = pygame.Rect(col_index * TILE + 5, row_index * TILE + 5, TILE - 10, TILE - 10)
		pygame.draw.rect(screen_surface, (89, 232, 159), rect, border_radius=6)
		pygame.draw.rect(screen_surface, (212, 255, 232), rect, width=2, border_radius=6)


def _draw_danger_feedback(screen_surface, min_enemy_distance, warning_font):
	if min_enemy_distance > DANGER_DISTANCE_THRESHOLD:
		return

	factor = (DANGER_DISTANCE_THRESHOLD - min_enemy_distance + 1) / (DANGER_DISTANCE_THRESHOLD + 1)
	alpha = min(62, max(10, int(70 * factor)))
	overlay = pygame.Surface(screen_surface.get_size(), pygame.SRCALPHA)
	overlay.fill((170, 22, 22, alpha))
	screen_surface.blit(overlay, (0, 0))

	# Strong warning through animated border instead of darkening the whole map.
	pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.012)
	border_alpha = min(220, max(85, int(95 + 120 * factor * pulse)))
	border_width = max(3, int(2 + 8 * factor))

	border_layer = pygame.Surface(screen_surface.get_size(), pygame.SRCALPHA)
	pygame.draw.rect(
		border_layer,
		(255, 82, 82, border_alpha),
		border_layer.get_rect().inflate(-4, -4),
		width=border_width,
		border_radius=12,
	)
	screen_surface.blit(border_layer, (0, 0))

	if min_enemy_distance <= 3:
		warning = warning_font.render("DANGER", True, (255, 244, 244))
		screen_surface.blit(warning, warning.get_rect(center=(screen_surface.get_width() // 2, 26)))


def _chase_target_for_enemy(player_pos, enemy_index, difficulty, algorithm, player_move_dir=(0, 0), elapsed_ratio=0.0):
	if difficulty == "easy":
		offsets = [(0, 0), (-1, 0), (0, -1), (1, 0), (0, 1)]
	elif difficulty == "hard":
		offsets = [(0, 0), (0, 1), (1, 0), (-1, 0), (0, -1)]
	else:
		offsets = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]

	# Give each AI family a distinct pursuit style.
	if algorithm == "vision":
		offsets = [
			(0, 1),
			(1, 0),
			(-1, 0),
			(0, -1),
			(0, 0),
		]
	elif algorithm == "bfs":
		predict_steps = 1 if difficulty != "hard" else 2
		target = [player_pos[0] + player_move_dir[0] * predict_steps, player_pos[1] + player_move_dir[1] * predict_steps]
		if is_walkable(map_data, target):
			return target

	# Keep A* focused while other AIs can flank to reduce identical movement.
	if algorithm == "astar":
		offsets = [(0, 0), (player_move_dir[0], player_move_dir[1]), (1, 0), (0, 1), (-1, 0), (0, -1)]

	# Late-game pressure: bias enemies to direct chase more aggressively.
	if elapsed_ratio >= 0.7 and (0, 0) in offsets:
		offsets = [(0, 0)] + [item for item in offsets if item != (0, 0)]

	chosen_offset = offsets[enemy_index % len(offsets)]
	target = [player_pos[0] + chosen_offset[0], player_pos[1] + chosen_offset[1]]
	if is_walkable(map_data, target):
		return target
	return list(player_pos)


def _enemy_step_interval_ms(base_step_ms, algorithm, enemy_index, difficulty):
	if algorithm == "vision":
		base = base_step_ms + 10
	elif algorithm == "bfs":
		base = base_step_ms
	else:
		base = max(55, base_step_ms - 12)

	if difficulty == "easy":
		base += 8
	elif difficulty == "hard":
		base = max(50, base - 8)

	return max(50, base + enemy_index * 12)


def _algorithm_priority(algorithm):
	if algorithm == "astar":
		return 0
	if algorithm == "bfs":
		return 1
	return 2


def _enemy_move_candidates(enemy, algorithm, player_pos, enemy_index, difficulty, player_move_dir, elapsed_ratio):
	target = _chase_target_for_enemy(player_pos, enemy_index, difficulty, algorithm, player_move_dir, elapsed_ratio)
	path = _build_enemy_path(algorithm, enemy.pos, target, enemy.prev_pos)

	if (not path or len(path) <= 1) and target != player_pos:
		path = _build_enemy_path(algorithm, enemy.pos, player_pos, enemy.prev_pos)

	candidates = []
	if path and len(path) > 1:
		candidates.append(tuple(path[1]))

	# Add nearby fallback cells to avoid deadlock when enemies block each other.
	directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
	neighbor_cells = []
	for dr, dc in directions:
		candidate = [enemy.pos[0] + dr, enemy.pos[1] + dc]
		if is_walkable(map_data, candidate):
			neighbor_cells.append(candidate)

	neighbor_cells.sort(
		key=lambda cell: (
			1 if cell == enemy.prev_pos else 0,
			abs(cell[0] - target[0]) + abs(cell[1] - target[1]),
			abs(cell[0] - player_pos[0]) + abs(cell[1] - player_pos[1]),
		)
	)

	for cell in neighbor_cells:
		cell_tuple = tuple(cell)
		if cell_tuple not in candidates:
			candidates.append(cell_tuple)

	return candidates


def _format_ai_team(algorithms):
	counts = {}
	for algorithm in algorithms:
		counts[algorithm] = counts.get(algorithm, 0) + 1

	labels = {
		"vision": "Vision",
		"bfs": "BFS",
		"astar": "A*",
	}
	parts = []
	for key in ("vision", "bfs", "astar"):
		if key in counts:
			parts.append(f"{labels[key]} x{counts[key]}")

	return " | ".join(parts)


def _draw_hud(
	screen_surface,
	elapsed_sec,
	time_limit,
	difficulty,
	algorithms,
	hud_font,
	objective_collected,
	objective_total,
	boost_remaining_sec,
):
	remaining = max(0, math.ceil(time_limit - elapsed_sec))
	difficulty_text = DIFFICULTY_LABELS.get(difficulty, difficulty.title())
	ai_text = _format_ai_team(algorithms)
	boost_text = f"Boost: {boost_remaining_sec:.1f}s" if boost_remaining_sec > 0 else "Boost: ready"

	hud_lines = [
		f"Time: {remaining}s",
		f"Do kho: {difficulty_text}",
		f"Muc tieu: {objective_collected}/{objective_total}",
		boost_text,
		f"AI Team: {ai_text}",
	]

	max_text_width = 0
	line_surfaces = []
	for line in hud_lines:
		surface = hud_font.render(line, True, (242, 246, 255))
		line_surfaces.append(surface)
		max_text_width = max(max_text_width, surface.get_width())

	padding_x = 10
	padding_y = 8
	line_gap = 5
	box_width = max_text_width + padding_x * 2
	box_height = sum(surface.get_height() for surface in line_surfaces) + line_gap * (len(line_surfaces) - 1) + padding_y * 2

	panel = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
	panel.fill((8, 16, 36, 170))
	pygame.draw.rect(panel, (110, 155, 230, 210), panel.get_rect(), width=2, border_radius=8)
	panel_x = screen_surface.get_width() - box_width - 10
	panel_y = 10
	screen_surface.blit(panel, (panel_x, panel_y))

	y_offset = panel_y + padding_y
	for surface in line_surfaces:
		screen_surface.blit(surface, (panel_x + padding_x, y_offset))
		y_offset += surface.get_height() + line_gap


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
	spawn_min_distance = _spawn_min_distance_by_difficulty(selected_difficulty)
	enemies = _spawn_enemies(
		enemy_img,
		len(config["algorithms"]),
		blocked,
		player_anchor=player.pos,
		min_player_distance=spawn_min_distance,
	)
	current_time_limit = config["time_limit"]
	current_enemy_step_ms = config["enemy_step_ms"]
	hud_font = pygame.font.SysFont("consolas", 20, bold=True)
	warning_font = pygame.font.SysFont("consolas", 28, bold=True)

	start_time = time.time()
	last_player_step_ms = pygame.time.get_ticks()
	base_enemy_tick_ms = pygame.time.get_ticks()
	enemy_next_step_ms = [base_enemy_tick_ms + index * 60 for index in range(len(enemies))]
	enemy_anim_duration_ms = [max(80, int(current_enemy_step_ms * 0.85)) for _ in enemies]

	objective_total = OBJECTIVE_TARGETS.get(selected_difficulty, 3)
	objective_cells = _pick_collectible_cells(
		objective_total,
		player.pos,
		[enemy.pos for enemy in enemies],
		minimum_distance=8,
		min_spacing=_objective_min_spacing_by_difficulty(selected_difficulty),
	)
	objective_total = len(objective_cells)
	objective_cell_set = {tuple(cell) for cell in objective_cells}
	objective_spawn_ms = {tuple(cell): base_enemy_tick_ms for cell in objective_cells}
	collected_objectives = 0

	powerup_cells = []
	powerup_cell_set = set()
	powerup_spawn_ms = {}
	first_powerup = _spawn_powerup_cell(player.pos, [enemy.pos for enemy in enemies], objective_cells, minimum_distance=7)
	if first_powerup is not None:
		powerup_cells.append(first_powerup)
		powerup_cell_set.add(tuple(first_powerup))
		powerup_spawn_ms[tuple(first_powerup)] = base_enemy_tick_ms
	powerup_active_until_ms = 0
	next_powerup_spawn_ms = base_enemy_tick_ms + _random_respawn_delay(POWERUP_RESPAWN_RANGE_MS)
	player_last_move_dir = (0, 0)
	play_sound("start_up")

	active_dirs = []
	queued_turn = None

	while True:
		delta_ms = game_clock.tick(FPS)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return "quit", None

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					return "menu", None
				if event.key in KEY_TO_DIR:
					direction = KEY_TO_DIR[event.key]
					queued_turn = direction
					if direction in active_dirs:
						active_dirs.remove(direction)
					active_dirs.append(direction)

			if event.type == pygame.KEYUP and event.key in KEY_TO_DIR:
				direction = KEY_TO_DIR[event.key]
				if direction in active_dirs:
					active_dirs.remove(direction)

		now_ms = pygame.time.get_ticks()

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
			replacement = _spawn_powerup_cell(
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
			replacement = _spawn_powerup_cell(
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
			new_powerup = _spawn_powerup_cell(
				player.pos,
				[enemy.pos for enemy in enemies],
				objective_cells + powerup_cells,
				minimum_distance=5,
			)
			if new_powerup is not None and tuple(new_powerup) not in powerup_cell_set:
				powerup_cells.append(new_powerup)
				powerup_cell_set.add(tuple(new_powerup))
				powerup_spawn_ms[tuple(new_powerup)] = now_ms
			next_powerup_spawn_ms = now_ms + _random_respawn_delay(POWERUP_RESPAWN_RANGE_MS)

		ready_indices = [index for index in range(len(enemies)) if now_ms >= enemy_next_step_ms[index]]
		if ready_indices:
			elapsed_ratio = min(1.0, (time.time() - start_time) / max(1.0, current_time_limit))
			start_cells = {index: tuple(enemies[index].pos) for index in ready_indices}
			all_occupied = {tuple(enemy.pos) for enemy in enemies}
			interval_by_index = {
				index: max(
					50,
					int(
						_enemy_step_interval_ms(
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
				index: _enemy_move_candidates(
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
					_algorithm_priority(config["algorithms"][index]),
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

		elapsed_sec = time.time() - start_time
		if elapsed_sec >= current_time_limit:
			play_sound("round_end")
			return "result", {"result": "win", "difficulty": selected_difficulty}

		screen_surface.fill((0, 0, 0))
		draw_game_map(screen_surface, map_data, TILE)
		_draw_objectives(screen_surface, objective_cells)
		_draw_powerups(screen_surface, powerup_cells)
		player.draw(screen_surface, TILE)
		for enemy in enemies:
			enemy.draw(screen_surface, TILE)

		min_enemy_distance = min(
			abs(enemy.pos[0] - player.pos[0]) + abs(enemy.pos[1] - player.pos[1]) for enemy in enemies
		)
		_draw_danger_feedback(screen_surface, min_enemy_distance, warning_font)

		boost_remaining_sec = max(0.0, (powerup_active_until_ms - now_ms) / 1000.0)
		_draw_hud(
			screen_surface,
			elapsed_sec,
			current_time_limit,
			selected_difficulty,
			config["algorithms"],
			hud_font,
			collected_objectives,
			objective_total,
			boost_remaining_sec,
		)

		pygame.display.flip()
