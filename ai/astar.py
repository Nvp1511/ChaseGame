import heapq
from config.settings import ROWS, COLS
from map.map_data import map_data

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(start, target):
    pq = []
    heapq.heappush(pq, (0, start, [], 0))  # (f, node, path, g)

    visited = {}

    dirs = [(1,0),(-1,0),(0,1),(0,-1)]

    while pq:
        f, (r,c), path, g = heapq.heappop(pq)

        if [r,c] == target:
            return path + [[r,c]]

        if (r,c) in visited and visited[(r,c)] <= g:
            continue
        visited[(r,c)] = g

        for dr,dc in dirs:
            nr, nc = r+dr, c+dc

            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if map_data[nr][nc] != 'X':
                    new_g = g + 1
                    h = heuristic([nr,nc], target)
                    new_f = new_g + h

                    heapq.heappush(pq, (new_f, [nr,nc], path + [[r,c]], new_g))

    return None