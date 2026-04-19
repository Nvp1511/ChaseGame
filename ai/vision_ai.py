from config.settings import COLS, ROWS
from map.map_data import map_data


def _is_open(cell):
    row_index, col_index = cell
    return 0 <= row_index < ROWS and 0 <= col_index < COLS and map_data[row_index][col_index] != "X"


def _line_clear(enemy, player):
    er, ec = enemy
    pr, pc = player

    if er == pr:
        start = min(ec, pc) + 1
        end = max(ec, pc)
        return all(map_data[er][col] != "X" for col in range(start, end))

    if ec == pc:
        start = min(er, pr) + 1
        end = max(er, pr)
        return all(map_data[row][ec] != "X" for row in range(start, end))

    return False


def vision_move(enemy, player, previous=None):
    """Greedy chase with line-of-sight preference and anti-oscillation fallback."""
    er, ec = enemy
    pr, pc = player

    preferred_dirs = []

    # If enemy can see player on same row/column, move directly first.
    if _line_clear(enemy, player):
        if pr > er:
            preferred_dirs.append((1, 0))
        elif pr < er:
            preferred_dirs.append((-1, 0))
        if pc > ec:
            preferred_dirs.append((0, 1))
        elif pc < ec:
            preferred_dirs.append((0, -1))

    # Always keep greedy Manhattan options.
    if pr > er:
        preferred_dirs.append((1, 0))
    elif pr < er:
        preferred_dirs.append((-1, 0))
    if pc > ec:
        preferred_dirs.append((0, 1))
    elif pc < ec:
        preferred_dirs.append((0, -1))

    # Add all directions as fallback without duplicates, preserving order.
    for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if direction not in preferred_dirs:
            preferred_dirs.append(direction)

    best_cell = list(enemy)
    best_score = float("inf")
    fallback_cell = None

    for dr, dc in preferred_dirs:
        candidate = [er + dr, ec + dc]
        if not _is_open(candidate):
            continue

        # Prefer not to immediately walk back to previous cell.
        if previous is not None and candidate == list(previous):
            if fallback_cell is None:
                fallback_cell = candidate
            continue

        score = abs(candidate[0] - pr) + abs(candidate[1] - pc)
        if score < best_score:
            best_score = score
            best_cell = candidate

    if best_cell != list(enemy):
        return best_cell
    if fallback_cell is not None:
        return fallback_cell
    return list(enemy)