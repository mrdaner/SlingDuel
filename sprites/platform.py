# sprites/platform.py
import pygame

class Platform(pygame.sprite.Sprite):
    """
    Static floating platform. The image is decorative; the *solid* part is the
    bottom half only. We expose `surface_top` which is the y-coordinate where
    players should stand.
    """
    def __init__(self, image: pygame.Surface, midtop: tuple[int, int]):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(midtop=midtop)

    @property
    def surface_top(self) -> int:
        # top of the solid region (bottom half)
        return self.rect.top + self.rect.height // 2
