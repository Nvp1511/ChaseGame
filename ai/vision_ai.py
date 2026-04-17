import random
from config.settings import ROWS, COLS
from map.map_data import map_data

def vision_move(enemy, player):
    er, ec = enemy
    pr, pc = player

    directions = []
    if pr > er:
        directions.append((1, 0))   # xuống
    elif pr < er:
        directions.append((-1, 0))  # lên
    if pc > ec:
        directions.append((0, 1))   # phải
    elif pc < ec:
        directions.append((0, -1))  # trái
    directions += [(1,0),(-1,0),(0,1),(0,-1)]
    random.shuffle(directions)

    for dr, dc in directions:
        nr, nc = er + dr, ec + dc

        if 0 <= nr < ROWS and 0 <= nc < COLS:
            if map_data[nr][nc] != 'X':
                return [nr, nc]

    return enemy 