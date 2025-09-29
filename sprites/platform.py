# sprites/platform.py
import pygame

class Platform(pygame.sprite.Sprite):
    """Static floating platform made from a provided image at a given midtop position."""
    def __init__(self, image: pygame.Surface, midtop: tuple[int, int]):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(midtop=midtop)
