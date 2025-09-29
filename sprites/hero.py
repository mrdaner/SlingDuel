import pygame
import math
from constants import SCREEN_WIDTH, GROUND_Y, HERO_JUMP_FORCE, GRAVITY_PER_TICK
from assets import get_hero_frames

class Hero(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # get 4 sets of frames now: stand, run, jump, throw
        stand, self.hero_run, self.hero_jump, self.hero_throw = get_hero_frames()
        self.hero_stand = stand

        self.hero_run_index = 0.0
        self.hero_jump_index = 0.0
        self.hero_throw_index = 0.0
        self.is_throwing = False

        self.image = self.hero_stand
        self.rect = self.image.get_rect(midbottom=(200, GROUND_Y))
        self.gravity = 0
        self.speed = 0
        self.facing_right = True

        # --- aiming state: fixed radius, controlled by angle with W/S ---
        self.aim_radius = 150          # constant distance from hero
        self.aim_angle = 0.0           # 0 = straight ahead
        self.aim_step = 0.06           # radians per frame when holding W/S
        self.aim_min = -1.25           # about -72 degrees
        self.aim_max =  1.25           # about +72 degrees
        # -----------------------------------------------------------------

    def hero_input(self):
        keys = pygame.key.get_pressed()

        # Jump
        if keys[pygame.K_SPACE] and self.rect.bottom >= GROUND_Y:
            self.gravity = HERO_JUMP_FORCE

        # Horizontal movement + facing
        if keys[pygame.K_a]:
            self.speed = -6
            self.facing_right = False
        elif keys[pygame.K_d]:
            self.speed = 6
            self.facing_right = True
        else:
            self.speed = 0

        # Aim with W/S (around a circle)
        if keys[pygame.K_w]:
            self.aim_angle = min(self.aim_max, self.aim_angle + self.aim_step)
        elif keys[pygame.K_s]:
            self.aim_angle = max(self.aim_min, self.aim_angle - self.aim_step)

        # Throw
        if keys[pygame.K_f] and not self.is_throwing:
            self.is_throwing = True
            self.hero_throw_index = 0.0

    def apply_gravity(self):
        self.gravity += GRAVITY_PER_TICK
        self.rect.y += self.gravity
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y

    def move_horizontal(self):
        self.rect.x += self.speed
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def animate(self):
        # Throw takes priority while playing
        if self.is_throwing:
            self.hero_throw_index += 0.2
            if self.hero_throw_index >= len(self.hero_throw):
                self.hero_throw_index = 0.0
                self.is_throwing = False
                frame = self.hero_stand
            else:
                frame = self.hero_throw[int(self.hero_throw_index)]
        elif self.rect.bottom < GROUND_Y:  # jumping
            self.hero_jump_index = (self.hero_jump_index + 0.1) % len(self.hero_jump)
            frame = self.hero_jump[int(self.hero_jump_index)]
        elif self.speed != 0:              # running
            self.hero_run_index = (self.hero_run_index + 0.4) % len(self.hero_run)
            frame = self.hero_run[int(self.hero_run_index)]
        else:                              # idle
            frame = self.hero_stand

        # Face last direction
        self.image = frame if self.facing_right else pygame.transform.flip(frame, True, False)

    def get_aim_pos(self) -> tuple[int, int]:
        """Aim point at fixed radius around hero, rotated by aim_angle, mirrored by facing."""
        cx, cy = self.rect.center
        cos_a = math.cos(self.aim_angle)
        sin_a = math.sin(self.aim_angle)
        dx = self.aim_radius * ( cos_a if self.facing_right else -cos_a )
        dy = self.aim_radius * (-sin_a)   # Pygame Y+ is down
        return (int(cx + dx), int(cy + dy))

    def reset(self):
        self.rect.midbottom = (200, GROUND_Y)
        self.gravity = 0
        self.speed = 0
        self.hero_run_index = 0.0
        self.hero_jump_index = 0.0
        self.hero_throw_index = 0.0
        self.is_throwing = False
        self.image = self.hero_stand
        self.facing_right = True
        self.aim_angle = 0.0

    def update(self):
        self.hero_input()
        self.apply_gravity()
        self.move_horizontal()
        self.animate()
