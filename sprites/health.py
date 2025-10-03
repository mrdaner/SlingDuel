# sprites/health.py
import pygame
from assets import get_heart

class HealthPickup(pygame.sprite.Sprite):
    """Heart pickup (+1.0 HP). Placed midbottom=(x,y_bottom)."""
    def __init__(self, x: int, y_bottom: int):
        super().__init__()
        self.image = get_heart()
        self.rect = self.image.get_rect(midbottom=(x, y_bottom))

    def update(self):
        pass
