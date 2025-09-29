import pygame
from constants import GROUND_Y, HERO_JUMP_FORCE, GRAVITY_PER_TICK
from assets import get_hero_frames

class Hero(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        stand, self.hero_run, self.hero_jump = get_hero_frames()
        self.hero_run_index = 0.0
        self.hero_jump_index = 0.0

        self.image = self.hero_run[0]
        self.rect = self.image.get_rect(midbottom=(200, GROUND_Y))
        self.gravity = 0
        self.speed = 0   # horizontal speed (velocity in x)

    def hero_input(self):
        keys = pygame.key.get_pressed()

        # Jump
        if keys[pygame.K_SPACE] and self.rect.bottom >= GROUND_Y:
            self.gravity = HERO_JUMP_FORCE

        # Horizontal movement
        if keys[pygame.K_a]:
            self.speed = -6  # move left
        elif keys[pygame.K_d]:
            self.speed = 6   # move right
        else:
            self.speed = 0   # stop when no key pressed

    def apply_gravity(self):
        self.gravity += GRAVITY_PER_TICK
        self.rect.y += self.gravity
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y

    def move_horizontal(self):
        self.rect.x += self.speed
        # keep hero inside screen (example: 0 to 1280 width)
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > 1280:
            self.rect.right = 1280

    def animate(self):
        if self.rect.bottom < GROUND_Y:  # jumping
            self.hero_jump_index = (self.hero_jump_index + 0.1) % len(self.hero_jump)
            self.image = self.hero_jump[int(self.hero_jump_index)]
        else:  # running
            self.hero_run_index = (self.hero_run_index + 0.4) % len(self.hero_run)
            self.image = self.hero_run[int(self.hero_run_index)]

    def reset(self):
        self.rect.midbottom = (200, GROUND_Y)
        self.gravity = 0
        self.speed = 0
        self.hero_run_index = 0.0
        self.hero_jump_index = 0.0
        self.image = self.hero_run[0]

    def update(self):
        self.hero_input()
        self.apply_gravity()
        self.move_horizontal()   # <-- apply horizontal velocity
        self.animate()
