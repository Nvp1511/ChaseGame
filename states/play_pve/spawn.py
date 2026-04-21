import random
from collections import deque

from entities.enemy import Enemy
from map.game_map import is_walkable
from map.map_data import map_data


def spawn_enemies(enemy_images, count, blocked_cells=None, player_anchor=None, min_player_distance=0):
	blocked_cells = blocked_cells or set()
	player_anchor = player_anchor or [1, 1]
	if not enemy_images:
		raise ValueError("enemy_images must contain at least one image")

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
		return [Enemy(enemy_images[index % len(enemy_images)], fallback.copy()) for index in range(count)]

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

	return [Enemy(enemy_images[index % len(enemy_images)], pos) for index, pos in enumerate(spawn_points)]


def spawn_min_distance_by_difficulty(difficulty):
	if difficulty == "easy":
		return 16
	if difficulty == "medium":
		return 13
	return 10


def reachable_open_cells(start_pos):
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


def pick_collectible_cells(count, player_pos, enemy_positions, minimum_distance=7, min_spacing=6):
	excluded = {tuple(player_pos), *{tuple(pos) for pos in enemy_positions}}
	candidate_cells = []
	for cell in reachable_open_cells(player_pos):
		cell_key = tuple(cell)
		if cell_key in excluded:
			continue
		distance = abs(cell[0] - player_pos[0]) + abs(cell[1] - player_pos[1])
		if distance >= minimum_distance:
			candidate_cells.append(cell)

	if len(candidate_cells) < count:
		candidate_cells = [cell for cell in reachable_open_cells(player_pos) if tuple(cell) not in excluded]

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


def objective_min_spacing_by_difficulty(difficulty):
	if difficulty == "easy":
		return 7
	if difficulty == "medium":
		return 6
	return 5


def spawn_powerup_cell(player_pos, enemy_positions, objective_cells, minimum_distance=6):
	blocked = {tuple(player_pos), *{tuple(pos) for pos in enemy_positions}, *{tuple(cell) for cell in objective_cells}}
	candidates = []
	for cell in reachable_open_cells(player_pos):
		cell_key = tuple(cell)
		if cell_key in blocked:
			continue
		distance = abs(cell[0] - player_pos[0]) + abs(cell[1] - player_pos[1])
		if distance >= minimum_distance:
			candidates.append(cell)

	if not candidates:
		candidates = [cell for cell in reachable_open_cells(player_pos) if tuple(cell) not in blocked]
	if not candidates:
		return None

	return random.choice(candidates)


def random_respawn_delay(respawn_range):
	min_ms, max_ms = respawn_range
	return random.randint(min_ms, max_ms)
