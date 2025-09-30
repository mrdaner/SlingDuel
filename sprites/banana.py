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
    """A stationary banana that sits until a player picks it up."""
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
      - 'falling_after_hit'   : switched to splat image after hitting a player; falls to surface, 3s timer starts AFTER landing
      - 'splatted_persist'    : landed without hitting player; lies there until stepped on (or culled by limits)
      - 'splatted_temp'       : splatted (after hit or after stepped); disappears after 3s
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

        self._already_damaged_player = False
        self._stepped_once = False

        # NEW: landing metadata for culling / rules
        self.on_ground: bool | None = None       # True if landed on ground, False if on platform, None if not yet
        self.landed_at_ms: int | None = None     # when it became splatted_persist

    def can_hit(self, target) -> bool:
        # no damage more than once per throw
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
        """Snap to ground or platform if intersecting, return ('ground'|'platform'|None)."""
        # Ground check
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            return "ground"

        # Platform check
        if platforms:
            hit = pygame.sprite.spritecollideany(self, platforms)
            if hit:
                # place banana on top of platform
                self.rect.bottom = hit.rect.top
                return "platform"

        return None

    def _to_splat(self):
        center = self.rect.center
        self.image = self.splat_image
        self.rect = self.image.get_rect(center=center)
        self.velocity.update(0, 0)

    def on_hit(self, target):
        """Direct hit on a player: deal 1 dmg once, switch to splat image, fall to a surface, then disappear after 3s."""
        if self._already_damaged_player:
            return
        self._already_damaged_player = True
        # change to splat immediately
        self._to_splat()
        # start falling until surface; timer starts after landing
        self.state = "falling_after_hit"

        if hasattr(target, "take_damage"):
            target.take_damage(self.damage_direct)

    def update(self, platforms=None):
        if self.state == "flying":
            self._apply_gravity()
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
            self._animate_rotation()

            where = self._land_on_surface(platforms)
            if where is not None:
                # landed without hitting a player -> persistent splat
                self._to_splat()
                self.state = "splatted_persist"
                self.on_ground = (where == "ground")
                self.landed_at_ms = pygame.time.get_ticks()
                return

            # walls -> persist where it hits
            if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
                self._to_splat()
                self.state = "splatted_persist"
                # consider wall as not ground (won't count against ground cap)
                self.on_ground = False
                self.landed_at_ms = pygame.time.get_ticks()
                return

        elif self.state == "falling_after_hit":
            # already splat image; just fall to surface
            self._apply_gravity()
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
            where = self._land_on_surface(platforms)
            if where is not None:
                self.velocity.update(0, 0)
                self.state = "splatted_temp"
                self.on_ground = (where == "ground")
                self.landed_at_ms = pygame.time.get_ticks()
                self.despawn_at_ms = self.landed_at_ms + 3000  # 3s after landing

        elif self.state == "splatted_persist":
            # Wait until stepped or culled by main; no timer here
            pass

        elif self.state == "splatted_temp":
            now = pygame.time.get_ticks()
            if self.despawn_at_ms is not None and now >= self.despawn_at_ms:
                self.kill()

    # Helper to process "stepped on" from main loop (so we can pass players easily)
    def stepped_on_by(self, player):
        if self.state != "splatted_persist":
            return
        if self._stepped_once:
            return
        self._stepped_once = True
        if hasattr(player, "take_damage"):
            player.take_damage(self.damage_step)
        self.state = "splatted_temp"
        self.landed_at_ms = pygame.time.get_ticks()
        self.despawn_at_ms = self.landed_at_ms + 3000
