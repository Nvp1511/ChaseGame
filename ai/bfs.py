from collections import deque
from config.settings import ROWS, COLS
from map.map_data import map_data

def bfs(start, target):
    queue = deque()
    visited = set()

    queue.append((start, []))
    visited.add(tuple(start))

    dirs = [(1,0),(-1,0),(0,1),(0,-1)]

    while queue:
        (r,c), path = queue.popleft()

        if [r,c] == target:
            return path + [[r,c]]

        for dr,dc in dirs:
            nr, nc = r+dr, c+dc

            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if map_data[nr][nc] != 'X' and (nr,nc) not in visited:
                    visited.add((nr,nc))
                    queue.append(([nr,nc], path + [[r,c]]))
    return None