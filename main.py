import pygame
import sys
from collections import deque
import time

pygame.init()

TILE = 25
ROWS = 26
COLS = 33

WIDTH = COLS * TILE
HEIGHT = ROWS * TILE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BFS Chase Game")

clock = pygame.time.Clock()

# Load ảnh
player_img = pygame.image.load("assets/images/blue.png")
enemy_img = pygame.image.load("assets/images/ghost_20.png")

player_img = pygame.transform.scale(player_img, (TILE, TILE))
enemy_img = pygame.transform.scale(enemy_img, (TILE, TILE))

# Map
map_data = [
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
"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

player = [1, 1]
enemy = [18, 18]

start_time = time.time()
time_limit = 20

enemy_delay = 2
frame_count = 0

# BFS
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

# Game loop
while True:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Player đi 1 bước mỗi lần bấm
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_UP:
                if map_data[player[0]-1][player[1]] != 'X':
                    player[0] -= 1

            if event.key == pygame.K_DOWN:
                if map_data[player[0]+1][player[1]] != 'X':
                    player[0] += 1

            if event.key == pygame.K_LEFT:
                if map_data[player[0]][player[1]-1] != 'X':
                    player[1] -= 1

            if event.key == pygame.K_RIGHT:
                if map_data[player[0]][player[1]+1] != 'X':
                    player[1] += 1

    # Enemy tự động đuổi
    frame_count += 1
    if frame_count % enemy_delay == 0:
        path = bfs(enemy, player)
        if path and len(path) > 1:
            enemy = path[1]

    # Check lose
    if player == enemy:
        print("You lose!")
        pygame.quit()
        sys.exit()

    # Check win
    if time.time() - start_time >= time_limit:
        print("You win!")
        pygame.quit()
        sys.exit()

    # Draw
    screen.fill((0,0,0))

    for r in range(len(map_data)):
       for c in range(len(map_data[0])):

        tile = map_data[r][c]

        # Tường
        if tile == 'X':
            pygame.draw.rect(screen, (0,0,255), (c*TILE, r*TILE, TILE, TILE))

        # Chấm
        elif tile == '.':
            pygame.draw.circle(screen, (255,255,255),
                               (c*TILE + TILE//2, r*TILE + TILE//2), 3)

        # Điểm đặc biệt
        elif tile == 'O':
            pygame.draw.circle(screen, (255,255,0),
                               (c*TILE + TILE//2, r*TILE + TILE//2), 6)

    # Vẽ nhân vật bằng ảnh
    screen.blit(player_img, (player[1]*TILE, player[0]*TILE))
    screen.blit(enemy_img, (enemy[1]*TILE, enemy[0]*TILE))

    pygame.display.flip()
    clock.tick(10)