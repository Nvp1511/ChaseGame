from ai.astar import astar
from ai.bfs import bfs
from ai.vision_ai import vision_move
from map.game_map import is_walkable
from map.map_data import map_data


def build_enemy_path(algo_name, enemy_pos, player_pos, previous_pos=None):
	if algo_name == "vision":
		next_pos = vision_move(enemy_pos, player_pos, previous_pos)
		return [list(enemy_pos), list(next_pos)]
	if algo_name == "astar":
		return astar(enemy_pos, player_pos)
	return bfs(enemy_pos, player_pos)


def chase_target_for_enemy(player_pos, enemy_index, difficulty, algorithm, player_move_dir=(0, 0), elapsed_ratio=0.0):
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


def enemy_step_interval_ms(base_step_ms, algorithm, enemy_index, difficulty):
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


def algorithm_priority(algorithm):
	if algorithm == "astar":
		return 0
	if algorithm == "bfs":
		return 1
	return 2


def enemy_move_candidates(enemy, algorithm, player_pos, enemy_index, difficulty, player_move_dir, elapsed_ratio):
	target = chase_target_for_enemy(player_pos, enemy_index, difficulty, algorithm, player_move_dir, elapsed_ratio)
	path = build_enemy_path(algorithm, enemy.pos, target, enemy.prev_pos)

	if (not path or len(path) <= 1) and target != player_pos:
		path = build_enemy_path(algorithm, enemy.pos, player_pos, enemy.prev_pos)

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


def format_ai_team(algorithms):
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
