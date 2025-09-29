import pygame
from throwable import Throwable

class BananaProjectile(Throwable):
    def __init__(self, pos, velocity, image, owner=None, damage=1):
        super().__init__(pos, velocity, image, owner)
        self.damage = damage

    def on_hit(self, target):
        # Example: apply damage, then vanish
        if hasattr(target, "take_damage"):
            target.take_damage(self.damage)
        self.kill()