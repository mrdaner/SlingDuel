# sprites/sling.py
import pygame
from constants import SCREEN_WIDTH, GROUND_Y, PROJECTILE_GRAVITY, MAX_PROJECTILE_FALL_SPEED
from assets import get_hook_image

class Sling(pygame.sprite.Sprite):
    """Grapple hook projectile. No damage, no splats.
       Flies forward, sticks to ground/platforms, pulls its owner toward the anchor.
       Auto-detaches after DETACH_AFTER_MS, or earlier if the owner releases (but
       the owner must hold for at least MIN_HOLD_MS).
    """
    DETACH_AFTER_MS = 5000   # hard safety auto-detach (ms)
    pull_speed = 8           # how fast hero is pulled each frame
    break_dist = 20          # consider arrived when closer than this

    def __init__(self, pos, velocity, owner=None):
        super().__init__()
        self.owner = owner
        self.image = get_hook_image()
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.Vector2(velocity)

        # Rope anchor: bottom-left corner of the hook image (attach rope here)
        r = self.image.get_rect()
        self.rope_anchor_local = pygame.Vector2(r.left, r.bottom) - pygame.Vector2(r.center)

        # state
        self.state = "flying"    # flying → attached → done
        self.anchor = None       # world point where we latched
        self.attached_at_ms = None
        self.spawned_at_ms = pygame.time.get_ticks()  # for min-hold logic (checked in Hero)

    def rope_world_anchor(self) -> tuple[int, int]:
        """Where the rope attaches on the hook image (world coordinates)."""
        world_anchor = pygame.Vector2(self.rect.center) + self.rope_anchor_local
        return int(world_anchor.x), int(world_anchor.y)

    def _apply_gravity(self):
        # small gravity so it arcs a bit
        self.velocity.y = min(self.velocity.y + PROJECTILE_GRAVITY * 0.5, MAX_PROJECTILE_FALL_SPEED)

    def attach(self):
        """Stick in place and stop moving."""
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

            # off screen → cancel
            if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
                self.state = "done"
                self.kill()

        elif self.state == "attached":
            # auto-detach after timeout
            if self.attached_at_ms and now - self.attached_at_ms >= self.DETACH_AFTER_MS:
                self.state = "done"
                self.kill()
                return

            # pull owner toward anchor (works horizontally AND vertically)
            if self.owner and self.anchor:
                owner_center = pygame.Vector2(self.owner.rect.center)
                to_anchor = pygame.Vector2(self.anchor) - owner_center
                dist = to_anchor.length()

                if dist <= self.break_dist:
                    self.state = "done"
                    self.kill()
                else:
                    to_anchor.scale_to_length(min(self.pull_speed, dist))
                    # Move hero in both axes
                    self.owner.rect.centerx += int(to_anchor.x)
                    self.owner.rect.centery += int(to_anchor.y)

        elif self.state == "done":
            self.kill()
