class Enemy:
    def __init__(self, image, start_pos=None):
        self.pos = list(start_pos) if start_pos is not None else [18, 18]
        self.prev_pos = self.pos.copy()
        self.anim_progress = 1.0
        self.image = image

    def update(self, path):
        if path and len(path) > 1:
            self.prev_pos = self.pos.copy()
            self.pos = path[1]
            self.anim_progress = 0.0

    def update_animation(self, delta_ms, duration_ms):
        if self.anim_progress >= 1.0:
            return
        self.anim_progress = min(1.0, self.anim_progress + (delta_ms / max(1, duration_ms)))

    def draw(self, screen, tile):
        t = self.anim_progress
        draw_r = self.prev_pos[0] + (self.pos[0] - self.prev_pos[0]) * t
        draw_c = self.prev_pos[1] + (self.pos[1] - self.prev_pos[1]) * t
        screen.blit(self.image, (draw_c * tile, draw_r * tile))