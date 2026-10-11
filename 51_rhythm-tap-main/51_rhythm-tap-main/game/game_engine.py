
import math
import random
from array import array

import pygame

from game.beat import (
    Note,
    LANES,
    LANE_KEYS,
    LANE_LABELS,
    LANE_COLORS,
)

WIDTH, HEIGHT = 480, 640
FPS = 60
BPM = 120

HIT_Y = HEIGHT - 80
HIT_WINDOW = 30

BG = (15, 10, 25)
LANE_W = WIDTH // LANES

GRADE_POINTS = {
    "PERFECT": 300,
    "GREAT": 200,
    "OK": 100,
}

GRADE_COLORS = {
    "PERFECT": (255, 220, 0),
    "GREAT": (100, 220, 100),
    "OK": (180, 180, 255),
    "MISS": (220, 60, 60),
}


def make_tone(frequency, duration=0.10, volume=0.25):
    """Generate a short stereo sound effect without external audio files."""
    sample_rate = 44100
    total_samples = int(sample_rate * duration)
    samples = array("h")

    for i in range(total_samples):
        fade_in = min(1.0, i / 200)
        fade_out = min(1.0, (total_samples - i) / 500)
        fade = max(0.0, min(fade_in, fade_out))

        value = int(
            32767
            * volume
            * fade
            * math.sin(2 * math.pi * frequency * i / sample_rate)
        )

        # Two samples per frame: left and right audio channels.
        samples.extend((value, value))

    return pygame.mixer.Sound(buffer=samples.tobytes())


class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.hit_sounds = {
            "PERFECT": make_tone(1000),
            "GREAT": make_tone(750),
            "OK": make_tone(500),
        }

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rhythm Tap")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 26, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 44, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 18, bold=True)

        self.reset()

    def reset(self):
        self.notes = []

        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.misses = 0

        # BPM-based spawning: at 120 BPM, spawn once every 30 frames.
        self.bpm = BPM
        self.beat_phase = 0.0

        self.speed = 5
        self.frame = 0

        self.feedback = []
        self.game_over = False

        # Count every recorded grade for the summary screen.
        self.grade_counts = {
            "PERFECT": 0,
            "GREAT": 0,
            "OK": 0,
            "MISS": 0,
        }

    def spawn_note(self):
        lane = random.randint(0, LANES - 1)

        # Some notes require a one-second hold.
        is_hold = random.random() < 0.20

        self.notes.append(
            Note(
                lane,
                y=-30,
                speed=self.speed,
                is_hold=is_hold,
            )
        )

    def record_grade(self, grade, lane):
        """Record a grade and display its feedback."""
        self.grade_counts[grade] += 1

        lane_x = lane * LANE_W + LANE_W // 2

        self.feedback.append(
            [
                grade,
                GRADE_COLORS[grade],
                40,
                lane_x,
                HIT_Y - 30,
            ]
        )

        # MISS has no sound. Successful grades have different pitches.
        if grade in self.hit_sounds:
            self.hit_sounds[grade].play()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()

                elif not self.game_over:
                    for lane, key in enumerate(LANE_KEYS):
                        if event.key == key:
                            self.process_tap(lane)
                            break

        return True

    def process_tap(self, lane):
        """Judge the closest eligible note in the pressed lane."""
        best = None
        best_dist = float("inf")

        for note in self.notes:
            if (
                note.lane == lane
                and not note.hit
                and not note.missed
                and not note.holding
            ):
                dist = abs(
                    note.y + Note.HEIGHT // 2 - HIT_Y
                )

                if dist < best_dist:
                    best_dist = dist
                    best = note

        if best is None or best_dist > HIT_WINDOW:
            self.combo = 0
            self.record_grade("MISS", lane)
            return

        # Hold notes start when their lane key is pressed.
        if best.is_hold:
            best.holding = True
            best.hold_frames = 0
            best.hold_start_distance = best_dist
            return

        # Ordinary notes are judged immediately.
        grade = self.get_grade(best_dist)

        best.hit = True
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)

        self.score += (
            GRADE_POINTS[grade] * max(1, self.combo // 5)
        )

        self.record_grade(grade, lane)

    @staticmethod
    def get_grade(distance):
        if distance < 8:
            return "PERFECT"
        elif distance < 18:
            return "GREAT"
        return "OK"

    def finish_hold(self, note):
        """Award a grade after the key has been held long enough."""
        grade = self.get_grade(note.hold_start_distance)

        note.holding = False
        note.hit = True

        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)

        self.score += (
            GRADE_POINTS[grade] * max(1, self.combo // 5)
        )

        self.record_grade(grade, note.lane)

    def fail_hold(self, note):
        """Fail a hold note if the player releases too early."""
        note.holding = False
        note.missed = True

        self.misses += 1
        self.combo = 0

        self.record_grade("MISS", note.lane)

    def update(self):
        if self.game_over:
            return

        self.frame += 1

        # Accumulate beats rather than using the old 45-frame timer.
        self.beat_phase += self.bpm / (60 * FPS)

        if self.beat_phase >= 1.0:
            self.beat_phase -= 1.0
            self.spawn_note()

        # Preserve the existing gradual increase in note speed.
        if self.frame % 600 == 0:
            self.speed = min(10, self.speed + 0.5)

        keys_pressed = pygame.key.get_pressed()

        for note in self.notes:
            if note.hit or note.missed:
                if not note.holding:
                    note.update()
                continue

            if note.holding:
                # The key must remain down for the full hold.
                if keys_pressed[LANE_KEYS[note.lane]]:
                    note.hold_frames += 1

                    if note.hold_frames >= Note.HOLD_DURATION_FRAMES:
                        self.finish_hold(note)
                else:
                    self.fail_hold(note)

                continue

            note.update()

            # An ordinary or unstarted hold note that passes the
            # hit zone without being hit counts as a missed note.
            if (
                not note.hit
                and not note.missed
                and note.y > HIT_Y + HIT_WINDOW + Note.HEIGHT
            ):
                note.missed = True
                self.misses += 1
                self.combo = 0
                self.record_grade("MISS", note.lane)

        # Remove completed notes and notes that have fallen offscreen.
        self.notes = [
            note
            for note in self.notes
            if not (
                note.hit
                or (
                    note.missed
                    and note.y > HEIGHT + 10
                )
            )
        ]

        self.feedback = [
            [text, color, ttl - 1, x, y]
            for text, color, ttl, x, y in self.feedback
            if ttl > 1
        ]

        # Preserve the original 15-miss game-over threshold.
        if self.misses >= 15:
            self.game_over = True

    def get_accuracy(self):
        """Calculate the percentage of recorded grades that are hits."""
        total = sum(self.grade_counts.values())

        if total == 0:
            return 0.0

        successful_hits = (
            self.grade_counts["PERFECT"]
            + self.grade_counts["GREAT"]
            + self.grade_counts["OK"]
        )

        return successful_hits / total * 100

    def draw(self):
        self.screen.fill(BG)

        # Lane dividers.
        for i in range(LANES + 1):
            pygame.draw.line(
                self.screen,
                (40, 40, 60),
                (i * LANE_W, 0),
                (i * LANE_W, HEIGHT),
                1,
            )

        # Hit line and lane labels.
        pygame.draw.line(
            self.screen,
            (80, 80, 100),
            (0, HIT_Y),
            (WIDTH, HIT_Y),
            2,
        )

        for i in range(LANES):
            lane_x = i * LANE_W + LANE_W // 2

            pygame.draw.rect(
                self.screen,
                LANE_COLORS[i],
                pygame.Rect(
                    lane_x - Note.WIDTH // 2,
                    HIT_Y - 12,
                    Note.WIDTH,
                    24,
                ),
                border_radius=6,
            )

            label = self.font.render(
                LANE_LABELS[i], True, (20, 20, 20)
            )

            self.screen.blit(
                label,
                (
                    lane_x - label.get_width() // 2,
                    HIT_Y - 10,
                ),
            )

        # Draw notes.
        for note in self.notes:
            if note.hit:
                continue

            lane_x = note.lane * LANE_W + LANE_W // 2

            # A tall stem distinguishes a hold note from a normal note.
            if note.is_hold:
                stem_height = Note.HOLD_HEIGHT

                pygame.draw.rect(
                    self.screen,
                    LANE_COLORS[note.lane],
                    pygame.Rect(
                        lane_x - Note.WIDTH // 4,
                        int(note.y) - stem_height + Note.HEIGHT,
                        Note.WIDTH // 2,
                        stem_height,
                    ),
                    border_radius=4,
                )

            pygame.draw.rect(
                self.screen,
                LANE_COLORS[note.lane],
                note.get_rect(lane_x),
                border_radius=5,
            )

            # Show hold progress while the key is held.
            if note.holding:
                progress = min(
                    1.0,
                    note.hold_frames / Note.HOLD_DURATION_FRAMES,
                )

                bar_width = int(Note.WIDTH * progress)

                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),
                    pygame.Rect(
                        lane_x - Note.WIDTH // 2,
                        int(note.y) - 8,
                        bar_width,
                        4,
                    ),
                )

        # Grade feedback.
        for text, color, ttl, x, y in self.feedback:
            surface = self.font.render(text, True, color)
            surface.set_alpha(min(255, ttl * 7))

            self.screen.blit(
                surface,
                (x - surface.get_width() // 2, y),
            )

        # HUD.
        score_surface = self.font.render(
            f"Score: {self.score}", True, (220, 220, 220)
        )
        combo_surface = self.font.render(
            f"Combo: {self.combo}x", True, (255, 220, 80)
        )
        misses_surface = self.font.render(
            f"Misses: {self.misses}/15",
            True,
            (220, 100, 100),
        )
        bpm_surface = self.small_font.render(
            f"BPM: {self.bpm}", True, (180, 180, 200)
        )

        self.screen.blit(score_surface, (10, 10))
        self.screen.blit(combo_surface, (10, 40))
        self.screen.blit(
            misses_surface, (WIDTH - 170, 10)
        )
        self.screen.blit(bpm_surface, (10, 72))

        if self.game_over:
            overlay = pygame.Surface(
                (WIDTH, HEIGHT), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 220))
            self.screen.blit(overlay, (0, 0))

            title = self.big_font.render(
                "GAME OVER", True, (220, 60, 60)
            )

            self.screen.blit(
                title,
                (
                    WIDTH // 2 - title.get_width() // 2,
                    120,
                ),
            )

            summary = [
                ("PERFECT", (255, 220, 0)),
                ("GREAT", (100, 220, 100)),
                ("OK", (180, 180, 255)),
                ("MISS", (220, 60, 60)),
            ]

            y = 200

            for grade, color in summary:
                text = self.font.render(
                    f"{grade}: {self.grade_counts[grade]}",
                    True,
                    color,
                )

                self.screen.blit(
                    text,
                    (
                        WIDTH // 2 - text.get_width() // 2,
                        y,
                    ),
                )

                y += 42

            accuracy = self.get_accuracy()

            accuracy_surface = self.font.render(
                f"Accuracy: {accuracy:.2f}%",
                True,
                (255, 255, 255),
            )

            self.screen.blit(
                accuracy_surface,
                (
                    WIDTH // 2 - accuracy_surface.get_width() // 2,
                    390,
                ),
            )

            final_score = self.small_font.render(
                f"Final Score: {self.score}  Max Combo: {self.max_combo}x",
                True,
                (200, 200, 200),
            )

            self.screen.blit(
                final_score,
                (
                    WIDTH // 2 - final_score.get_width() // 2,
                    440,
                ),
            )

            restart = self.small_font.render(
                "Press R to Restart",
                True,
                (180, 180, 180),
            )

            self.screen.blit(
                restart,
                (
                    WIDTH // 2 - restart.get_width() // 2,
                    500,
                ),
            )

        pygame.display.flip()

    def run(self):
        running = True

        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
