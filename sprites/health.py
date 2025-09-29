# sprites/health.py
import pygame
from assets import get_heart

class HealthPickup(pygame.sprite.Sprite):
    """A heart pickup that grants +1 HP (up to max) when a player touches it."""
    def __init__(self, x: int, y_bottom: int):
        super().__init__()
        self.image = get_heart()
        self.rect = self.image.get_rect(midbottom=(x, y_bottom))

    def update(self):
        pass
