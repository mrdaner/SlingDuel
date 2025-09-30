# sprites/platform.py
import pygame

class Platform(pygame.sprite.Sprite):
    """Static floating platform. Only the *bottom half* is standable."""
    def __init__(self, image: pygame.Surface, midtop: tuple[int, int]):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(midtop=midtop)
        # standable area = bottom half
        half_h = self.rect.height // 2
        self.stand_rect = pygame.Rect(self.rect.left, self.rect.top + half_h,
                                      self.rect.width, self.rect.height - half_h)
