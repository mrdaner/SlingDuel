"""Hero sprite logic: player movement, combat, and grappling hook control."""
import math
import pygame
from constants import SCREEN_WIDTH, GROUND_Y, HERO_JUMP_FORCE, GRAVITY_PER_TICK, MAX_HEALTH
from assets import get_hero_frames, get_banana_image
from .banana import Banana
from .sling import Sling

class Hero(pygame.sprite.Sprite):
    def __init__(self, controls: dict | None = None, start_x: int = 200, name="Player", name_color=(255,255,255)):
        super().__init__()

        stand, self.hero_run, self.hero_jump, self.hero_throw = get_hero_frames()
        self.hero_stand = stand

        self.name = name
        self.name_color = name_color

        default_controls = {
            "left":  pygame.K_a,
            "right": pygame.K_d,
            "up":    pygame.K_w,
            "down":  pygame.K_s,
            "throw": pygame.K_f,
            "sling": pygame.K_LSHIFT,
            "jump":  pygame.K_SPACE
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

        self.max_health = MAX_HEALTH
        self.health = float(self.max_health)

        # Aim reticle rotates around the hero; shrink radius to keep targets readable.
        self.aim_radius = int(150 * 0.7)
        self.aim_angle = 0.0
        self.aim_step = 0.06
        self.aim_min = -1.25
        self.aim_max =  1.25

        # Player starts unarmed; this flag flips when touching a banana pickup.
        self.has_banana = False
        self.infinite_bananas = False

        # Throw state is buffered so the projectile spawns after the animation frame kicks off.
        self._pending_throw = False
        self._throw_velocity = pygame.Vector2()
        self._banana_refill_time = 0

        # Grapple timing; fast recovery keeps test mode iterations tight.
        self.hook_cooldown_ms = 500
        self.hook_ready_time = 0
        self.hook_active = False
        self.hook_sprite: Sling | None = None
        self._hook_prev = False  # previous-frame pressed state

        # Store horizontal impulse inflected by the hook so we can bleed it off each frame.
        self._hook_momentum_x = 0.0
        self._hook_momentum_remainder = 0.0

        # Shrink banana hit detection so glancing contacts do not register.
        self._banana_hitbox_shrink = pygame.Vector2(16, 12)

        # Track when platform friction should zero vertical speed.
        self.on_platform = False

    # ------------------- input / movement / animation -------------------
    def hero_input(self, hooks_group: pygame.sprite.Group | None):
        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()

        if self.infinite_bananas and not self.has_banana and now >= self._banana_refill_time:
            self.has_banana = True

        # Only allow the jump key to fire when feet are planted or on a platform.
        jump_key = self.controls.get("jump")
        if jump_key is not None and keys[jump_key] and (self.rect.bottom >= GROUND_Y or self.on_platform):
            self.gravity = HERO_JUMP_FORCE

        # Acceleration is constant; left/right key overrides residual hook momentum.
        if keys[self.controls["left"]]:
            self.speed = -6
            self.facing_right = False
        elif keys[self.controls["right"]]:
            self.speed = 6
            self.facing_right = True
        else:
            self.speed = 0

        if self.speed != 0:
            self._hook_momentum_x = 0.0
            self._hook_momentum_remainder = 0.0

        # Adjust aim reticle with the same keys used for the menus (W/S or custom bindings).
        if keys[self.controls["up"]]:
            self.aim_angle = min(self.aim_max, self.aim_angle + self.aim_step)
        elif keys[self.controls["down"]]:
            self.aim_angle = max(self.aim_min, self.aim_angle - self.aim_step)

        # Throw only if the hero is currently carrying a banana (or in infinite test mode).
        if keys[self.controls["throw"]] and self.has_banana and not self._pending_throw:
            dir_vec = self._aim_direction()
            self._start_throw_animation()
            self._throw_velocity = dir_vec * 12
            self._pending_throw = True
            self.has_banana = False  # consume now
            if self.infinite_bananas:
                self._banana_refill_time = now + 1000

        # Hook dispatch and rope control share logic between normal and test modes.
        if hooks_group is not None:
            hook_pressed = keys[self.controls["sling"]]
            jump_pressed = (jump_key is not None) and keys[jump_key]

            # Single-shot on the frame the key becomes active.
            if hook_pressed and not self._hook_prev:
                if (not self.hook_active) and (now >= self.hook_ready_time):
                    dir_vec = self._aim_direction()
                    velocity = dir_vec * (14 * 1.3)  # hook starts faster than bananas
                    self.hook_sprite = Sling(self.rect.center, velocity, owner=self)
                    hooks_group.add(self.hook_sprite)
                    self._start_throw_animation()
                    self.hook_active = True
                    self.hook_ready_time = now + self.hook_cooldown_ms

            # Hook releases are handled by the sling sprite after the cooldown window.
            if (not hook_pressed) and self._hook_prev:
                if self.hook_active and self.hook_sprite:
                    self.hook_sprite.request_release()  # tells hook key is up

            # Passing jump state lets the hook decide whether to reel or to swing freely.
            if self.hook_active and self.hook_sprite:
                self.hook_sprite.set_pull(jump_pressed)

            self._hook_prev = hook_pressed

    def apply_gravity(self, platforms=None):
        self.on_platform = False

        # basic gravity
        self.gravity += GRAVITY_PER_TICK
        prev_bottom = self.rect.bottom
        self.rect.y += self.gravity

        # Ground collision
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.gravity = 0
            self._hook_momentum_x *= 0.6
            self._hook_momentum_remainder *= 0.6

        # Platform collision (falling from above only; bottom half is standable)
        if platforms and self.gravity >= 0:
            hits = pygame.sprite.spritecollide(self, platforms, False)
            for plat in hits:
                top = plat.stand_rect.top
                # from above: previous bottom was above the top stand line
                if prev_bottom <= top and self.rect.bottom >= top:
                    self.rect.bottom = top
                    self.gravity = 0
                    self.on_platform = True
                    self._hook_momentum_x *= 0.6
                    self._hook_momentum_remainder *= 0.6

    def move_horizontal(self):
        total = self.speed + self._hook_momentum_x + self._hook_momentum_remainder
        dx = int(total)
        self._hook_momentum_remainder = total - dx
        self.rect.x += dx

        # apply damping so momentum dissipates over time
        self._hook_momentum_x *= 0.96
        if abs(self._hook_momentum_x) < 0.08:
            self._hook_momentum_x = 0.0
            self._hook_momentum_remainder = 0.0

        if self.rect.left < 0:
            self.rect.left = 0
            self._hook_momentum_x = 0.0
            self._hook_momentum_remainder = 0.0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self._hook_momentum_x = 0.0
            self._hook_momentum_remainder = 0.0

    def animate(self):
        frame = self.hero_stand

        if self.is_throwing:
            self.hero_throw_index += 0.2
            if self.hero_throw_index >= len(self.hero_throw):
                self.hero_throw_index = 0.0
                self.is_throwing = False
            else:
                frame = self.hero_throw[int(self.hero_throw_index)]

        if not self.is_throwing:
            if self.rect.bottom == GROUND_Y or self.on_platform:
                if self.speed != 0:
                    self.hero_run_index = (self.hero_run_index + 0.4) % len(self.hero_run)
                    frame = self.hero_run[int(self.hero_run_index)]
                else:
                    frame = self.hero_stand
            else:
                self.hero_jump_index = (self.hero_jump_index + 0.1) % len(self.hero_jump)
                frame = self.hero_jump[int(self.hero_jump_index)]

        self.image = frame if self.facing_right else pygame.transform.flip(frame, True, False)

    # ------------------- helpers -------------------
    def get_aim_pos(self) -> tuple[int, int]:
        cx, cy = self.rect.center
        cos_a = math.cos(self.aim_angle)
        sin_a = math.sin(self.aim_angle)
        dx = self.aim_radius * (cos_a if self.facing_right else -cos_a)
        dy = self.aim_radius * (-sin_a)
        return int(cx + dx), int(cy + dy)

    def _aim_direction(self) -> pygame.Vector2:
        tx, ty = self.get_aim_pos()
        vec = pygame.Vector2(tx - self.rect.centerx, ty - self.rect.centery)
        if vec.length_squared() == 0:
            vec = pygame.Vector2(1 if self.facing_right else -1, 0)
        else:
            vec = vec.normalize()
        return vec

    def _start_throw_animation(self):
        self.is_throwing = True
        self.hero_throw_index = 0.0

    def banana_hitbox(self) -> pygame.Rect:
        shrink_x = int(self._banana_hitbox_shrink.x)
        shrink_y = int(self._banana_hitbox_shrink.y)
        hitbox = self.rect.inflate(-shrink_x, -shrink_y)
        if hitbox.width <= 0 or hitbox.height <= 0:
            return self.rect.copy()
        return hitbox

    def _finish_hook(self):
        """Mark the hook as finished and clear state."""
        if self.hook_sprite is not None:
            self.hook_sprite = None
        if self.hook_active:
            self.hook_active = False

    def apply_hook_impulse(self, velocity: pygame.Vector2) -> None:
        """Receive velocity from a released hook swing."""
        max_speed = 30.0
        impulse = pygame.Vector2(velocity)
        if impulse.length() > max_speed:
            impulse.scale_to_length(max_speed)

        self._hook_momentum_x = impulse.x
        self._hook_momentum_remainder = 0.0
        self.gravity = impulse.y
        self.on_platform = False

    def reset(self):
        self.rect.bottom = GROUND_Y
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
        self.health = float(self.max_health)
        self.on_platform = False
        self.has_banana = self.infinite_bananas
        self._banana_refill_time = 0

        # hook state
        self.hook_ready_time = 0
        self.hook_active = False
        self.hook_sprite = None
        self._hook_prev = False
        self._hook_momentum_x = 0.0
        self._hook_momentum_remainder = 0.0

    def take_damage(self, amount: float = 1.0):
        self.health = max(0.0, self.health - amount)

    @property
    def is_dead(self) -> bool:
        return self.health <= 0.0

    def update(self,
               projectiles: pygame.sprite.Group | None = None,
               hooks_group: pygame.sprite.Group | None = None,
               platforms: pygame.sprite.Group | None = None):
        self.hero_input(hooks_group)
        self.apply_gravity(platforms)
        self.move_horizontal()
        self.animate()

        # spawn banana if requested
        if self._pending_throw and projectiles is not None:
            banana_img = get_banana_image()
            projectiles.add(Banana(self.rect.center, self._throw_velocity, banana_img, owner=self))
            self._pending_throw = False

        if self.hook_active:
            if self.hook_sprite is None or not self.hook_sprite.alive():
                self._finish_hook()
