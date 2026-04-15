from map.map_data import map_data


class Player:
    def __init__(self, image):
        self.pos = [1, 1]
        self.prev_pos = self.pos.copy()
        self.anim_progress = 1.0
        self.image = image

    def can_move(self, direction):
        dr, dc = direction
        nr = self.pos[0] + dr
        nc = self.pos[1] + dc

        if nr < 0 or nc < 0:
            return False
        if nr >= len(map_data) or nc >= len(map_data[0]):
            return False
        return map_data[nr][nc] != 'X'

    def move(self, direction):
        if not self.can_move(direction):
            return False

        dr, dc = direction
        self.prev_pos = self.pos.copy()
        self.pos = [self.pos[0] + dr, self.pos[1] + dc]
        self.anim_progress = 0.0
        return True

    def update_animation(self, delta_ms, duration_ms):
        if self.anim_progress >= 1.0:
            return
        self.anim_progress = min(1.0, self.anim_progress + (delta_ms / max(1, duration_ms)))

    def draw(self, screen, tile):
        t = self.anim_progress
        draw_r = self.prev_pos[0] + (self.pos[0] - self.prev_pos[0]) * t
        draw_c = self.prev_pos[1] + (self.pos[1] - self.prev_pos[1]) * t
        screen.blit(self.image, (draw_c * tile, draw_r * tile))