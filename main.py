import pygame
import sys
import time
import os

from config.settings import TILE, WIDTH, HEIGHT, FPS, TIME_LIMIT
from map.map_data import map_data
from entities.player import Player
from entities.enemy import Enemy
from ai.bfs import bfs

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BFS Chase Game")
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PLAYER_STEP_MS = 110
PLAYER_ANIM_MS = 90
ENEMY_STEP_MS = 110
ENEMY_ANIM_MS = 90
KEY_TO_DIR = {
    pygame.K_w: (-1, 0),
    pygame.K_s: (1, 0),
    pygame.K_a: (0, -1),
    pygame.K_d: (0, 1),
}

player_img = pygame.image.load(os.path.join(BASE_DIR,"assets","images","blue.png"))
enemy_img = pygame.image.load(os.path.join(BASE_DIR,"assets","images","ghost_20.png"))

player_img = pygame.transform.scale(player_img, (TILE, TILE))
enemy_img = pygame.transform.scale(enemy_img, (TILE, TILE))

player = Player(player_img)
enemy = Enemy(enemy_img)

start_time = time.time()
last_player_step_ms = pygame.time.get_ticks()
last_enemy_step_ms = pygame.time.get_ticks()

active_dirs = []
queued_turn = None

while True:
    delta_ms = clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN and event.key in KEY_TO_DIR:
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

    if now_ms - last_player_step_ms >= PLAYER_STEP_MS:
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

        last_player_step_ms = now_ms

    if now_ms - last_enemy_step_ms >= ENEMY_STEP_MS:
        path = bfs(enemy.pos, player.pos)
        enemy.update(path)
        last_enemy_step_ms = now_ms

    player.update_animation(delta_ms, PLAYER_ANIM_MS)
    enemy.update_animation(delta_ms, ENEMY_ANIM_MS)

    if player.pos == enemy.pos:
        print("You Lose!")
        pygame.quit()
        sys.exit()

    if time.time() - start_time >= TIME_LIMIT:
        print("You Win!")
        pygame.quit()
        sys.exit()

    screen.fill((0,0,0))

    for r in range(len(map_data)):
        for c in range(len(map_data[0])):
            if map_data[r][c] == 'X':
                pygame.draw.rect(screen, (0,0,255),
                                 (c*TILE, r*TILE, TILE, TILE))

    player.draw(screen, TILE)
    enemy.draw(screen, TILE)

    pygame.display.flip()