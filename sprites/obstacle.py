import pygame
from random import randint
from assets import get_obstacle_base
from constants import GROUND_Y

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, kind: str):
        super().__init__()
        base = get_obstacle_base(kind)
        self.frames = [
            base,
            pygame.transform.rotate(base, 90),
            pygame.transform.rotate(base, 180),
            pygame.transform.rotate(base, 270),
        ]
        self.animation_index = 0.0
        self.image = self.frames[0]

        if kind == "banana":
            y = GROUND_Y
            self.speed = 10
        else:  # boss
            y = GROUND_Y - 315  # matches your earlier 365 midbottom
            self.speed = 10

        self.rect = self.image.get_rect(midbottom=(randint(900, 1100), y))

    def animate(self):
        self.animation_index = (self.animation_index + 0.2) % len(self.frames)
        self.image = self.frames[int(self.animation_index)]

    def update(self):
        self.rect.x -= self.speed
        self.animate()

    def destroy(self):
        if self.rect.right < -100:
            self.kill()
