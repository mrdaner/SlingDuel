import pygame

class Throwable(pygame.sprite.Sprite):
    def __init__(self, pos, velocity, image, owner=None):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.Vector2(velocity)
        self.owner = owner

    def update(self):
        # Default movement
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y
        # Optional: destroy if offscreen
        self.destroy_if_offscreen()

    def destroy_if_offscreen(self):
        screen_w, screen_h = pygame.display.get_surface().get_size()
        if (self.rect.right < 0 or self.rect.left > screen_w or
            self.rect.bottom < 0 or self.rect.top > screen_h):
            self.kill()

    def on_hit(self, target):
        """Override in subclasses to define what happens when it hits something."""
        pass
