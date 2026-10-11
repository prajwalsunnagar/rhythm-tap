
import pygame

LANES = 4
LANE_KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
LANE_LABELS = ["D", "F", "J", "K"]
LANE_COLORS = [
    (220, 80, 80),
    (80, 180, 220),
    (100, 220, 100),
    (220, 180, 60),
]


class Note:
    WIDTH = 70
    HEIGHT = 20
    HOLD_HEIGHT = 60
    HOLD_DURATION_FRAMES = 60  # 1 second at 60 FPS

    def __init__(self, lane, y=-30, speed=4, is_hold=False):
        self.lane = lane
        self.y = y
        self.speed = speed

        self.hit = False
        self.missed = False

        # Hold-note state
        self.is_hold = is_hold
        self.holding = False
        self.hold_frames = 0
        self.hold_start_distance = 0

    def update(self):
        # Freeze the note at the hit line while the player holds it.
        if not self.holding:
            self.y += self.speed

    def get_rect(self, lane_x):
        return pygame.Rect(
            lane_x - self.WIDTH // 2,
            int(self.y),
            self.WIDTH,
            self.HEIGHT,
        )
