# sprites/sling.py
import math
import pygame
from constants import SCREEN_WIDTH, GROUND_Y, PROJECTILE_GRAVITY, MAX_PROJECTILE_FALL_SPEED
from assets import get_hook_image

class Sling(pygame.sprite.Sprite):
    """Grapple (hook).
       - Flies outward with small gravity.
       - Attaches to ground, platforms (top half), or ceiling.
       - Stays a minimum of 2s even if key is released.
       - While attached:
           * If owner's jump is held -> pull hard towards anchor (launch past point)
           * Else -> swing (pendulum-like)
       - Releases on owner's jump key release (if min time passed) or auto when done.
    """
    MIN_STICK_MS = 2000      # minimum attach time even if key released
    DETACH_SAFETY_MS = 7000  # hard safety
    pull_speed = 12          # strong pull
    break_dist = 18          # “arrived” distance

    def __init__(self, pos, velocity, owner=None):
        super().__init__()
        self.owner = owner
        self.image = get_hook_image()
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.Vector2(velocity)

        r = self.image.get_rect()
        self.rope_anchor_local = pygame.Vector2(r.left, r.bottom) - pygame.Vector2(r.center)

        self.state = "flying"     # flying → attached → done
        self.anchor = None
        self.attached_at_ms = None
        self.spawned_at_ms = pygame.time.get_ticks()

        # swing state
        self.rope_len = None
        self.theta = 0.0            # angle (around anchor)
        self.omega = 0.0            # angular velocity
        self.pull_mode = False      # set by hero when jump is held
        self.release_requested = False

    # ---- external controls from Hero ----
    def set_pull(self, on: bool):
        self.pull_mode = bool(on)

    def request_release(self):
        self.release_requested = True

    # ---- helpers ----
    def rope_world_anchor(self) -> tuple[int, int]:
        world_anchor = pygame.Vector2(self.rect.center) + self.rope_anchor_local
        return int(world_anchor.x), int(world_anchor.y)

    def _apply_gravity(self):
        self.velocity.y = min(self.velocity.y + PROJECTILE_GRAVITY * 0.5, MAX_PROJECTILE_FALL_SPEED)

    def attach(self):
        self.state = "attached"
        self.anchor = self.rope_world_anchor()
        self.velocity.update(0, 0)
        self.attached_at_ms = pygame.time.get_ticks()

        # establish rope length and initial swing angle from anchor to owner
        if self.owner:
            oc = pygame.Vector2(self.owner.rect.center)
            an = pygame.Vector2(self.anchor)
            v = oc - an
            self.rope_len = max(40.0, v.length())
            # angle measured from vertical down; y+ is down in pygame
            # theta = atan2(horizontal, vertical down component)
            self.theta = math.atan2(v.x, v.y if v.y != 0 else 1)
            self.omega = 0.0

            # launch impulse (past clinging point)
            launch = v.normalize() * -20  # push toward/through anchor
            self.owner.rect.centerx += int(launch.x)
            self.owner.rect.centery += int(launch.y)

    def _can_detach(self) -> bool:
        if self.attached_at_ms is None:
            return False
        return (pygame.time.get_ticks() - self.attached_at_ms) >= self.MIN_STICK_MS

    def _detach(self):
        self.state = "done"
        self.kill()

    def update(self, platforms=None):
        now = pygame.time.get_ticks()

        if self.state == "flying":
            self._apply_gravity()
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y

            # Attach to ceiling
            if self.rect.top <= 0:
                self.rect.top = 0
                self.attach()
                return

            # Attach to ground
            if self.rect.bottom >= GROUND_Y:
                self.rect.bottom = GROUND_Y
                self.attach()
                return

            # Attach to platforms (top/stand area)
            if platforms:
                hit = pygame.sprite.spritecollideany(self, platforms)
                if hit:
                    self.rect.bottom = hit.stand_rect.top
                    self.attach()
                    return

            # off screen → cancel
            if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
                self._detach()

        elif self.state == "attached":
            # safety auto-detach
            if self.attached_at_ms and now - self.attached_at_ms >= self.DETACH_SAFETY_MS:
                self._detach()
                return

            if self.owner and self.anchor and self.rope_len:
                oc = pygame.Vector2(self.owner.rect.center)
                an = pygame.Vector2(self.anchor)
                v = oc - an
                if v.length() == 0:
                    v = pygame.Vector2(0.001, 0.001)

                # Convert to polar around anchor: theta, omega
                self.theta = math.atan2(v.x, v.y if v.y != 0 else 1)

                if self.pull_mode:
                    # Pull straight towards anchor
                    to_anchor = (an - oc)
                    dist = to_anchor.length()
                    if dist <= self.break_dist:
                        if self._can_detach() and self.release_requested:
                            self._detach()
                        return
                    # Move owner strongly towards anchor
                    to_anchor.scale_to_length(min(self.pull_speed, dist))
                    self.owner.rect.centerx += int(to_anchor.x)
                    self.owner.rect.centery += int(to_anchor.y)
                else:
                    # Pendulum swing: simple angular equation with pseudo-gravity
                    g = 0.35
                    self.omega += (g / self.rope_len) * math.sin(self.theta)
                    self.omega *= 0.99  # small damping
                    self.theta -= self.omega

                    # project back on circle
                    new_rel = pygame.Vector2(math.sin(self.theta), math.cos(self.theta)) * self.rope_len
                    new_pos = an + new_rel
                    self.owner.rect.centerx = int(new_pos.x)
                    self.owner.rect.centery = int(new_pos.y)

                # Detach when allowed and requested (jump released)
                if self.release_requested and self._can_detach():
                    self._detach()

        elif self.state == "done":
            self.kill()
