# sprites/banana.py
import pygame
from .throwable import Throwable
from constants import (
    SCREEN_WIDTH,
    GROUND_Y,
    PROJECTILE_GRAVITY,
    MAX_PROJECTILE_FALL_SPEED,
)
from assets import get_banana_image, get_banana_splashed

class BananaPickup(pygame.sprite.Sprite):
    """A stationary banana that sits until picked up."""
    def __init__(self, x: int, y_bottom: int):
        super().__init__()
        img = get_banana_image()
        self.image = img
        self.rect = self.image.get_rect(midbottom=(x, y_bottom))

    def update(self):
        pass


class Banana(Throwable):
    """
    States:
      - 'flying'              : moving with gravity, rotating
      - 'falling_after_hit'   : splat image falling to surface after direct hit
      - 'splatted_persist'    : landed without direct hit; stays until stepped on
      - 'splatted_temp'       : splatted (after hit or stepped); disappears after N ms
    """

    OWNER_IMMUNITY_MS = 150  # ignore collisions with owner for first 150ms

    def __init__(self, pos, velocity, image=None, owner=None, damage=1.0):
        base = image if image is not None else get_banana_image()
        super().__init__(pos, velocity, base, owner)

        self.frames = [
            base,
            pygame.transform.rotate(base, 90),
            pygame.transform.rotate(base, 180),
            pygame.transform.rotate(base, 270),
        ]
        self.frame_index = 0.0
        self.frame_speed = 0.3

        self.splat_image = get_banana_splashed()

        self.damage_direct = float(damage)   # 1.0 on direct hit
        self.damage_step = 0.5               # 0.5 when stepped on splat
        self.state = "flying"
        self.despawn_at_ms: int | None = None
        self.spawned_at_ms = pygame.time.get_ticks()
        self.splat_time: int | None = None

        self._already_damaged_player = False
        self._stepped_once = False

        self._prev_bottom = self.rect.bottom

    def can_hit(self, target) -> bool:
        # Only while flying; never after splatted
        if self.state != "flying":
            return False
        if self._already_damaged_player:
            return False
        if target is self.owner:
            if pygame.time.get_ticks() - self.spawned_at_ms < self.OWNER_IMMUNITY_MS:
                return False
        return True

    def _animate_rotation(self):
        self.frame_index = (self.frame_index + self.frame_speed) % len(self.frames)
        center = self.rect.center
        self.image = self.frames[int(self.frame_index)]
        self.rect = self.image.get_rect(center=center)

    def _apply_gravity(self):
        self.velocity.y = min(self.velocity.y + PROJECTILE_GRAVITY, MAX_PROJECTILE_FALL_SPEED)

    def _land_on_surface(self, platforms):
        """Snap to ground or platform if intersecting from above; return True if landed."""
        # ground check
        if self._prev_bottom <= GROUND_Y and self.rect.bottom >= GROUND_Y and self.velocity.y >= 0:
            self.rect.bottom = GROUND_Y
            return True

        # platforms: only from above onto stand_rect
        if platforms:
            for plat in platforms:
                top = plat.stand_rect.top
                if self._prev_bottom <= top and self.rect.bottom >= top and self.velocity.y >= 0:
                    # x overlap too
                    if self.rect.right >= plat.stand_rect.left and self.rect.left <= plat.stand_rect.right:
                        self.rect.bottom = top
                        return True
        return False

    def _to_splat(self):
        center = self.rect.center
        self.image = self.splat_image
        self.rect = self.image.get_rect(center=center)
        self.velocity.update(0, 0)
        self.splat_time = pygame.time.get_ticks()

    def on_hit(self, target):
        """Direct hit on a player: 1.0 dmg once, switch to splat image, fall to surface, then disappear after 0.5s."""
        if self._already_damaged_player or self.state != "flying":
            return
        self._already_damaged_player = True
        if hasattr(target, "take_damage"):
            target.take_damage(self.damage_direct)
        self._to_splat()
        self.state = "falling_after_hit"

    def update(self, platforms=None):
        self._prev_bottom = self.rect.bottom

        if self.state == "flying":
            self._apply_gravity()
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
            self._animate_rotation()

            if self._land_on_surface(platforms):
                self._to_splat()
                self.state = "splatted_persist"
                return

            if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
                self._to_splat()
                self.state = "splatted_persist"
                return

        elif self.state == "falling_after_hit":
            self._apply_gravity()
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
            if self._land_on_surface(platforms):
                self.velocity.update(0, 0)
                self.state = "splatted_temp"
                self.despawn_at_ms = pygame.time.get_ticks() + 500  # 0.5s after landing

        elif self.state == "splatted_persist":
            # waits until stepped_on_by; nothing here
            pass

        elif self.state == "splatted_temp":
            now = pygame.time.get_ticks()
            if self.despawn_at_ms is not None and now >= self.despawn_at_ms:
                self.kill()

    # API from main loop
    def stepped_on_by(self, player):
        if self.state != "splatted_persist":
            return
        if self._stepped_once:
            return
        self._stepped_once = True
        if hasattr(player, "take_damage"):
            player.take_damage(self.damage_step)
        self.state = "splatted_temp"
        self._rotate_splat_image(90)
        self.despawn_at_ms = pygame.time.get_ticks() + 750  # 0.75s

    def _rotate_splat_image(self, degrees: float) -> None:
        center = self.rect.center
        rotated = pygame.transform.rotate(self.image, degrees)
        self.image = rotated
        self.rect = self.image.get_rect(center=center)
