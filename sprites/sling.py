# sprites/sling.py
import pygame
from constants import SCREEN_WIDTH, GROUND_Y, PROJECTILE_GRAVITY, MAX_PROJECTILE_FALL_SPEED
from assets import get_hook_image

class Sling(pygame.sprite.Sprite):
    """Grapple hook projectile. No damage, no splats.
       Flies, sticks to ground/platforms/top ceiling, then pulls owner toward anchor.
       Exists while held, but auto-detaches after a safety timeout.
    """
    DETACH_AFTER_MS = 5000      # safety timeout
    max_pull_speed   = 22       # absolute cap on pull per frame (pixels)
    pull_gain        = 0.35     # how strongly distance converts to speed
    anti_grav_boost  = 10       # upward boost applied to owner's gravity while attached
    break_dist       = 16       # consider arrived when within this distance

    def __init__(self, pos, velocity, owner=None):
        super().__init__()
        self.owner = owner
        self.image = get_hook_image()
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.Vector2(velocity)

        # Rope anchor: bottom-left corner of the hook image (relative to center)
        r = self.image.get_rect()
        self.rope_anchor_local = pygame.Vector2(r.left, r.bottom) - pygame.Vector2(r.center)

        # state
        self.state = "flying"    # flying → attached → done
        self.anchor = None       # world point where we latched
        self.attached_at_ms = None

    def rope_world_anchor(self) -> tuple[int, int]:
        world_anchor = pygame.Vector2(self.rect.center) + self.rope_anchor_local
        return int(world_anchor.x), int(world_anchor.y)

    def _apply_gravity(self):
        # small arc while flying
        self.velocity.y = min(self.velocity.y + PROJECTILE_GRAVITY * 0.5, MAX_PROJECTILE_FALL_SPEED)

    def attach(self):
        self.state = "attached"
        self.anchor = self.rect.center
        self.velocity.update(0, 0)
        self.attached_at_ms = pygame.time.get_ticks()

    def update(self, platforms=None):
        now = pygame.time.get_ticks()

        if self.state == "flying":
            self._apply_gravity()
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y

            # attach to ground
            if self.rect.bottom >= GROUND_Y:
                self.rect.bottom = GROUND_Y
                self.attach()
                return

            # attach to platforms
            if platforms:
                hit = pygame.sprite.spritecollideany(self, platforms)
                if hit:
                    self.rect.bottom = hit.rect.top
                    self.attach()
                    return

            # attach to top ceiling
            if self.rect.top <= 0:
                self.rect.top = 0
                self.attach()
                return

            # offscreen → done
            if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
                self.state = "done"
                self.kill()

        elif self.state == "attached":
            # safety timeout
            if self.attached_at_ms and now - self.attached_at_ms >= self.DETACH_AFTER_MS:
                self.state = "done"
                self.kill()
                return

            if self.owner and self.anchor:
                owner_center = pygame.Vector2(self.owner.rect.center)
                to_anchor = pygame.Vector2(self.anchor) - owner_center
                dist = to_anchor.length()

                if dist <= self.break_dist:
                    self.state = "done"
                    self.kill()
                    return

                # Distance-scaled pull with cap
                # (stronger when far, but never exceeding max_pull_speed)
                pull_mag = min(self.max_pull_speed, dist * self.pull_gain)
                if dist != 0:
                    to_anchor.scale_to_length(pull_mag)
                    # apply pull
                    self.owner.rect.centerx += int(to_anchor.x)
                    self.owner.rect.centery += int(to_anchor.y)

                # Counter gravity when anchor is above the player:
                # give a negative gravity (upward) bias so we climb.
                anchor_y = self.anchor[1]
                if self.owner.rect.centery > anchor_y:
                    # ensure upward motion can happen even if falling
                    self.owner.gravity = min(self.owner.gravity, -self.anti_grav_boost)

        elif self.state == "done":
            self.kill()
