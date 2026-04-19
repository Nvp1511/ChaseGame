from config.settings import COLS, ROWS


MAP_MEDIUM = [
	"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
	"X                               X",
	"X XXX XXX XXXXXX XXXXXX XXX XXX X",
	"X X X X X X    X X    X X X X X X",
	"X XXX X X XXXXXX XXXXXX X X XXX X",
	"X     XXX X    X X    X XXX     X",
	"XXXXX       XX X X XX       XXXXX",
	"X     XXXXX           XXXXX     X",
	"X XXX       XXXXXXXXX       XXX X",
	"X     XXXXX           XXXXX     X",
	"X XXX       XXXX XXXX       XXX X",
	"X X X XXXXX X  X X  X XXXXX X X X",
	"X X X X   X X  X X  X X   X X X X",
	"X X X X   X X  X X  X X   X X X X",
	"X X X XXXXX X  X X  X XXXXX X X X",
	"X XXX       XXXX XXXX       XXX X",
	"X     XXXXX           XXXXX     X",
	"X XXX       XXXXXXXXX       XXX X",
	"X     XXXXX           XXXXX     X",
	"XXXXX       XX X X XX       XXXXX",
	"X     XXX X    X X    X XXX     X",
	"X XXX X X XXXXXX XXXXXX X X XXX X",
	"X X X X X X    X X    X X X X X X",
	"X XXX XXX XXXXXX XXXXXX XXX XXX X",
	"X                               X",
	"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]

MAP_EASY = [
	"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
	"X                               X",
	"X XXXXX XX XX   XXXXX XXXXXXXX  X",
	"X X   X X   X   X   X X      X  X",
	"X X X X X X X   X X X X XXXX X  X",
	"X   X             X          X  X",
	"X XXXXXXXX  XXXXXXXX XXXXXXXXX  X",
	"X                               X",
	"X XXXXX  XXXXXXXXXXXX XXXXXXXX  X",
	"X                               X",
	"X XXXXX  XXXXXXXX  XXXXXXX  XXXXX",
	"X     X      X                  X",
	"X            X        X         X",
	"X        X            X         X",
	"X XXXXX  XXXXXXXX  XXXXXXX  XXXXX",
	"X                               X",
	"X XXXXX  XXXXXXXXXXXX  XXXXXXX  X",
	"X                               X",
	"X XXXXXXXX  XXXXXXXX  XXXXXXXX  X",
	"X       X         X             X",
	"X XXX X X XXX XXX X XXX XXX    XX",
	"X X   X X   X   X X   X   X   X X",
	"X XXXXX XXXXX XXX XXXXX XXX     X",
	"X       X     X   X          XX X",
	"X    X                X         X",
	"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]

MAP_HARD = [
"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
"X                               X",
"X XXX XXX XXXXXX XXXXXX XXX XXX X",
"X X X X X X    X X    X X X X X X",
"X XXX X X XXXXXX XXXXXX X X XXX X",
"X     XXX X    X X    X XXX     X",
"XXXXX       XX X X XX       XXXXX",
"X     XXXXX           XXXXX     X",
"X XXX       XXXXXXXXX       XXX X",
"X     XXXXX           XXXXX     X",
"X XXX       XXXX XXXX       XXX X",
"X X X XXXXX X  X X  X XXXXX X X X",
"X X X X   X X  X X  X X   X X X X",
"X X X X   X X  X X  X X   X X X X",
"X X X XXXXX X  X X  X XXXXX X X X",
"X XXX       XXXX XXXX       XXX X",
"X     XXXXX           XXXXX     X",
"X XXX       XXXXXXXXX       XXX X",
"X     XXXXX           XXXXX     X",
"XXXXX       XX X X XX       XXXXX",
"X     XXX X    X X    X XXX     X",
"X XXX X X XXXXXX XXXXXX X X XXX X",
"X X X X X X    X X    X X X X X X",
"X XXX XXX XXXXXX XXXXXX XXX XXX X",
"X                               X",
"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]



def _normalize_map(raw_map):
	"""Normalize maps so every difficulty always matches ROWS x COLS."""
	rows = list(raw_map[:ROWS])
	if len(rows) < ROWS:
		rows.extend(["X" + (" " * (COLS - 2)) + "X" for _ in range(ROWS - len(rows))])

	normalized = []
	for row_index, row in enumerate(rows):
		row = row[:COLS].ljust(COLS)
		if row_index == 0 or row_index == ROWS - 1:
			normalized.append("X" * COLS)
		else:
			normalized.append("X" + row[1:COLS - 1] + "X")

	return normalized


MAPS_BY_DIFFICULTY = {
	"easy": _normalize_map(MAP_EASY),
	"medium": _normalize_map(MAP_MEDIUM),
	"hard": _normalize_map(MAP_HARD),
}

# Mutable map object used by AI/entities modules.
map_data = list(MAPS_BY_DIFFICULTY["medium"])


def set_map_for_difficulty(difficulty):
	selected_map = MAPS_BY_DIFFICULTY.get(difficulty, MAPS_BY_DIFFICULTY["medium"])
	map_data[:] = selected_map