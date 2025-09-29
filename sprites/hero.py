# sprites/hero.py
import math
import pygame
from constants import SCREEN_WIDTH, GROUND_Y, HERO_JUMP_FORCE, GRAVITY_PER_TICK
from assets import get_hero_frames, get_banana_image
from .banana import Banana
from .sling import Sling

class Hero(pygame.sprite.Sprite):
    def __init__(self, controls: dict | None = None, start_x: int = 200):
        super().__init__()

        stand, self.hero_run, self.hero_jump, self.hero_throw = get_hero_frames()
        self.hero_stand = stand

        default_controls = {
            "left":  pygame.K_a,
            "right": pygame.K_d,
            "up":    pygame.K_w,
            "down":  pygame.K_s,
            "throw": pygame.K_f,
            "sling": pygame.K_r,     # default; p2 overrides to U in main
            "jump":  pygame.K_c      # default; p2 overrides to N in main
        }
        self.controls = (controls or default_controls)

        self.hero_run_index = 0.0
        self.hero_jump_index = 0.0
        self.hero_throw_index = 0.0
        self.is_throwing = False

        self.image = self.hero_stand
        self.rect = self.image.get_rect(midbottom=(start_x, GROUND_Y))
        self.gravity = 0
        self.speed = 0
        self.facing_right = True

        self.max_health = 5
        self.health = self.max_health

        # aim
        self.aim_radius = 150
        self.aim_angle = 0.0
        self.aim_step = 0.06
        self.aim_min = -1.25
        self.aim_max =  1.25

        # inventory
        self.has_banana = False

        # throws
        self._pending_throw = False
        self._throw_velocity = pygame.Vector2()

        # hook (sling) hold-to-keep
        self.hook_cooldown_ms = 1500
        self.hook_ready_time = 0
        self.hook_active = False
        self.hook_sprite: Sling | None = None
        self._hook_prev = False

        # grounded flag (true if on ground or on a platform)
        self.grounded = False

    # ------------------- input / movement / animation -------------------
    def hero_input(self, hooks_group: pygame.sprite.Group | None):
        keys = pygame.key.get_pressed()

        # Jump (optional key)
        jump_key = self.controls.get("jump")
        if jump_key is not None and keys[jump_key] and self.grounded:
            self.gravity = HERO_JUMP_FORCE
            self.grounded = False

        # Horizontal move + facing
        if keys[self.controls["left"]]:
            self.speed = -6
            self.facing_right = False
        elif keys[self.controls["right"]]:
            self.speed = 6
            self.facing_right = True
        else:
            self.speed = 0

        # Aim around circle
        if keys[self.controls["up"]]:
            self.aim_angle = min(self.aim_max, self.aim_angle + self.aim_step)
        elif keys[self.controls["down"]]:
            self.aim_angle = max(self.aim_min, self.aim_angle - self.aim_step)

        # Banana throw (only if carrying one)
        if keys[self.controls["throw"]] and not self.is_throwing and self.has_banana:
            self.is_throwing = True
            self.hero_throw_index = 0.0
            tx, ty = self.get_aim_pos()
            dir_vec = pygame.Vector2(tx - self.rect.centerx, ty - self.rect.centery).normalize()
            self._throw_velocity = dir_vec * 12
            self._pending_throw = True
            self.has_banana = False  # consume now

    # Hook logic: press to create, release to remove (cooldown starts on release)
        if hooks_group is not None:
            now = pygame.time.get_ticks()
            hook_pressed = keys[self.controls["sling"]]

            # Press edge: spawn if not active and off cooldown
            if hook_pressed and not self._hook_prev:
                if (not self.hook_active) and (now >= self.hook_ready_time):
                    tx, ty = self.get_aim_pos()
                    dir_vec = pygame.Vector2(tx - self.rect.centerx, ty - self.rect.centery).normalize()
                    velocity = dir_vec * (14 * 1.3)   # 30% longer throw than before
                    self.hook_sprite = Sling(self.rect.center, velocity, owner=self)
                    hooks_group.add(self.hook_sprite)
                    self.hook_active = True

            # Release edge: despawn and start cooldown
            if (not hook_pressed) and self._hook_prev:
                if self.hook_active and self.hook_sprite:
                    self.hook_sprite.kill()
                    self.hook_sprite = None
                self.hook_active = False
                self.hook_ready_time = now + self.hook_cooldown_ms

            self._hook_prev = hook_pressed

    def apply_gravity(self, platforms=None):
        self.gravity += GRAVITY_PER_TICK
        self.rect.y += self.gravity
        self.grounded = False  # will set True if we land somewhere

        # Ground collision
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.gravity = 0
            self.grounded = True

        # Platform collision (only if falling)
        if platforms and self.gravity >= 0:
            hits = pygame.sprite.spritecollide(self, platforms, False)
            for plat in hits:
                surface_top = getattr(plat, "surface_top", plat.rect.top)
                # ensure we're landing from above (tolerance)
                if self.rect.bottom <= surface_top + 20:
                    self.rect.bottom = surface_top
                    self.gravity = 0
                    self.grounded = True

    def move_horizontal(self):
        self.rect.x += self.speed
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def animate(self):
        if self.is_throwing:
            self.hero_throw_index += 0.2
            if self.hero_throw_index >= len(self.hero_throw):
                self.hero_throw_index = 0.0
                self.is_throwing = False
                frame = self.hero_stand
            else:
                frame = self.hero_throw[int(self.hero_throw_index)]
        elif not self.grounded:  # <- use grounded instead of comparing to GROUND_Y
            self.hero_jump_index = (self.hero_jump_index + 0.1) % len(self.hero_jump)
            frame = self.hero_jump[int(self.hero_jump_index)]
        elif self.speed != 0:
            self.hero_run_index = (self.hero_run_index + 0.4) % len(self.hero_run)
            frame = self.hero_run[int(self.hero_run_index)]
        else:
            frame = self.hero_stand

        self.image = frame if self.facing_right else pygame.transform.flip(frame, True, False)

    # ------------------- helpers -------------------
    def get_aim_pos(self) -> tuple[int, int]:
        cx, cy = self.rect.center
        cos_a = math.cos(self.aim_angle)
        sin_a = math.sin(self.aim_angle)
        dx = self.aim_radius * (cos_a if self.facing_right else -cos_a)
        dy = self.aim_radius * (-sin_a)
        return int(cx + dx), int(cy + dy)

    def reset(self):
        self.rect.midbottom = (self.rect.centerx, GROUND_Y)
        self.gravity = 0
        self.speed = 0
        self.hero_run_index = 0.0
        self.hero_jump_index = 0.0
        self.hero_throw_index = 0.0
        self.is_throwing = False
        self.image = self.hero_stand
        self.facing_right = True
        self.aim_angle = 0.0
        self._pending_throw = False
        self.health = self.max_health

        # hook state
        self.hook_ready_time = 0
        self.hook_active = False
        self.hook_sprite = None
        self._hook_prev = False

        # grounded
        self.grounded = True

    def take_damage(self, amount: float = 1):
        self.health = max(0.0, self.health - amount)

    @property
    def is_dead(self) -> bool:
        return self.health <= 0

    def update(self,
               projectiles: pygame.sprite.Group | None = None,
               hooks_group: pygame.sprite.Group | None = None,
               platforms: pygame.sprite.Group | None = None):
        self.hero_input(hooks_group)
        self.apply_gravity(platforms)
        self.move_horizontal()
        self.animate()

        # perform pending banana throw here
        if self._pending_throw and projectiles is not None:
            banana_img = get_banana_image()
            projectiles.add(Banana(self.rect.center, self._throw_velocity, banana_img, owner=self))
            self._pending_throw = False
