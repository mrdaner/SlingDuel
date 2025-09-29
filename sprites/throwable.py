# throwable.py
import pygame

class Throwable(pygame.sprite.Sprite):
    def __init__(self, pos, velocity, image, owner=None):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=pos)

        # velocity is expected as a pygame.Vector2
        self.velocity = pygame.Vector2(velocity)
        self.owner = owner  # reference to Hero (or whoever threw it)

    def update(self):
        """Default movement logic"""
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

    def on_hit(self, target):
        """Called when hitting something. By default just despawns."""
        self.kill()
