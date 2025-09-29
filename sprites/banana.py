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
    """A banana you can collect. Position via (x, y_bottom)."""
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
      - 'falling_after_hit'   : switched to splat after hitting a player; falls to surface; 0.5s timer after landing
      - 'splatted_persist'    : landed without hitting player; lies there until stepped on
      - 'splatted_temp'       : splatted (after hit or after stepped); disappears after 3s (or 0.5s after direct hit landing)
    """

    OWNER_IMMUNITY_MS = 150   # ignore collisions with owner for first 150ms
    STEP_DESPAWN_MS = 3000    # after step-on
    DIRECT_HIT_DESPAWN_MS = 500  # 0.5s after it lands post-hit (twice as fast as 1s)

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

        self._already_damaged_player = False
        self._stepped_once = False

    def can_hit(self, target) -> bool:
        """Only allow direct-hit damage while the banana is FLYING."""
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

    def _land_on_surface(self, platforms, prev_bottom: int) -> bool:
        """Snap to ground or a platform if intersecting from above; return True if landed."""
        # Ground
        if self.rect.bottom >= GROUND_Y and self.velocity.y >= 0 and prev_bottom <= GROUND_Y:
            self.rect.bottom = GROUND_Y
            return True

        # Platforms: only land when coming from above (no splat if passing upward through)
        if platforms:
            hit = pygame.sprite.spritecollideany(self, platforms)
            if hit:
                if self.velocity.y >= 0 and prev_bottom <= hit.rect.top:
                    self.rect.bottom = hit.rect.top
                    return True
        return False

    def _to_splat(self):
        center = self.rect.center
        self.image = self.splat_image
        self.rect = self.image.get_rect(center=center)
        self.velocity.update(0, 0)

    def on_hit(self, target):
        """Direct hit on a player: 1 dmg once, switch to splat, then 0.5s after landing."""
        if self._already_damaged_player or self.state != "flying":
            return
        self._already_damaged_player = True

        if hasattr(target, "take_damage"):
            target.take_damage(self.damage_direct)

        # show splat while it falls to the nearest surface; timer starts after landing
        self._to_splat()
        self.state = "falling_after_hit"

    def update(self, platforms=None):
        if self.state == "flying":
            prev_bottom = self.rect.bottom

            self._apply_gravity()
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
            self._animate_rotation()

            if self._land_on_surface(platforms, prev_bottom):
                # landed without hitting a player -> persistent splat
                self._to_splat()
                self.state = "splatted_persist"
                return

            # walls -> persist where it hits
            if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
                self._to_splat()
                self.state = "splatted_persist"
                return

        elif self.state == "falling_after_hit":
            prev_bottom = self.rect.bottom
            self._apply_gravity()
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
            if self._land_on_surface(platforms, prev_bottom):
                self.velocity.update(0, 0)
                self.state = "splatted_temp"
                self.despawn_at_ms = pygame.time.get_ticks() + self.DIRECT_HIT_DESPAWN_MS

        elif self.state == "splatted_persist":
            # Wait to be stepped on
            pass

        elif self.state == "splatted_temp":
            now = pygame.time.get_ticks()
            if self.despawn_at_ms is not None and now >= self.despawn_at_ms:
                self.kill()

    # Called by main loop when a player steps on a persistent splat
    def stepped_on_by(self, player):
        if self.state != "splatted_persist" or self._stepped_once:
            return
        self._stepped_once = True
        if hasattr(player, "take_damage"):
            player.take_damage(self.damage_step)
        self.state = "splatted_temp"
        self.despawn_at_ms = pygame.time.get_ticks() + self.STEP_DESPAWN_MS
