import pygame
from circleshape import CircleShape
from constants import *

class Player(CircleShape):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load('graphics/player/hero_blue.png').convert_alpha
        self.rect = self.image.get_rect(midbottom = (200,300))
        self.gravity = 0

    def player_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.rect.bottom >=300:
            self.gravity = -20

    def apply_gravity(self):
        self.gravity += 1
        self.rect.y += self.gravity
        if self.rect.bottom >= 300:
            self.rect.bottom = 300

    def udpate(self):
        self.player_input()
        self.apply_gravity()
