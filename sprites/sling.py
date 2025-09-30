# sprites/sling.py
import pygame
from constants import (
    SCREEN_WIDTH,
    GROUND_Y,
    PROJECTILE_GRAVITY,
    MAX_PROJECTILE_FALL_SPEED,
)
from assets import get_hook_image


class Sling(pygame.sprite.Sprite):
    """
    Grapple hook projectile: sticks for a short time, can reel-in on jump, or act like a sling.
    - On attach: stays for STICK_MS by default (even if the key is released)
    - If the player HOLDS/PRESSES JUMP while attached -> strong reel-in toward anchor
      (on reaching anchor, launch slightly forward past the cling point)
    - If not jumping -> behave like a sling: keep rope length ~constant and allow swinging.
    """

    # How long it stays attached if the player doesn't reel in
    STICK_MS = 2000

    # Safety cap (if you really want to force-kill after some long time)
    DETACH_AFTER_MS = 6000

    # Reel-in (winch) tuning
    break_dist = 20            # distance we consider "arrived"
    MIN_PULL = 10              # minimum pull step (px/frame)
    PULL_GAIN = 0.12           # extra pull per pixel of distance
    MAX_PULL = 30              # max pull step (px/frame)
    OVERSHOOT_PX = 40          # how far past the anchor we launch on completion

    # Sling / swing tuning
    SWING_THRUST = 6           # tangential "push" (px/frame) to keep swinging
    ROPE_ENFORCE = 0.35        # how strongly we correct if rope is stretched

    def __init__(self, pos, velocity, owner=None):
        super().__init__()
        self.owner = owner
        self.image = get_hook_image()
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.Vector2(velocity)

        # Rope attaches at bottom-left of the hook image (relative to center)
        r = self.image.get_rect()
        self.rope_anchor_local = pygame.Vector2(r.left, r.bottom) - pygame.Vector2(r.center)

        # State
        self.state = "flying"            # "flying" -> "attached" -> "done"
        self.anchor = None               # world point where we latched
        self.attached_at_ms = None
        self.rope_len = None             # fixed length once attached

        # Remember owner's last velocity-ish (we synthesize from rect motion)
        self._last_owner_center = None

    # --- helpers ----------------------------------------------------------

    def rope_world_anchor(self) -> tuple[int, int]:
        """Where the rope should connect on the hook image (world coordinates)."""
        world_anchor = pygame.Vector2(self.rect.center) + self.rope_anchor_local
        return int(world_anchor.x), int(world_anchor.y)

    def _apply_gravity(self):
        # Small gravity so the hook arcs a bit before sticking
        self.velocity.y = min(self.velocity.y + PROJECTILE_GRAVITY * 0.5, MAX_PROJECTILE_FALL_SPEED)

    def _owner_velocity(self) -> pygame.Vector2:
        """Approximate owner's velocity from last frame (purely kinematic)."""
        if not self.owner:
            return pygame.Vector2()
        c = pygame.Vector2(self.owner.rect.center)
        if self._last_owner_center is None:
            self._last_owner_center = c
            return pygame.Vector2()
        v = c - self._last_owner_center
        self._last_owner_center = pygame.Vector2(self.owner.rect.center)
        return v

    def _give_tangential_kick(self):
        """On attach: give the owner an initial tangential impulse to help start a swing."""
        if not self.owner or not self.anchor:
            return
        owner_center = pygame.Vector2(self.owner.rect.center)
        r = owner_center - pygame.Vector2(self.anchor)
        if r.length_squared() == 0:
            return
        # tangent direction (perpendicular to rope)
        t = pygame.Vector2(-r.y, r.x)
        if t.length_squared() == 0:
            return
        t.scale_to_length(self.SWING_THRUST * 1.5)  # a bit stronger kick at the start
        self.owner.rect.centerx += int(t.x)
        self.owner.rect.centery += int(t.y)

    def attach(self):
        """Stick in place and stop moving; define rope length; slight up+forward assist."""
        self.state = "attached"
        self.anchor = self.rect.center
        self.velocity.update(0, 0)
        self.attached_at_ms = pygame.time.get_ticks()

        if self.owner:
            # Set the rope length to current distance
            owner_center = pygame.Vector2(self.owner.rect.center)
            self.rope_len = (owner_center - pygame.Vector2(self.anchor)).length()

            # Small upward nudge so player starts to rise a bit
            if getattr(self.owner, "gravity", 0) > -10:
                self.owner.gravity = -10

            # Tangential kick to encourage swinging motion
            self._give_tangential_kick()

    # --- update -----------------------------------------------------------

    def update(self, platforms=None):
        now = pygame.time.get_ticks()

        if self.state == "flying":
            self._apply_gravity()
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y

            # Attach to ground
            if self.rect.bottom >= GROUND_Y:
                self.rect.bottom = GROUND_Y
                self.attach()
                return

            # Attach to platforms
            if platforms:
                hit = pygame.sprite.spritecollideany(self, platforms)
                if hit:
                    self.rect.bottom = hit.rect.top
                    self.attach()
                    return

            # Off screen → done
            if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
                self.state = "done"
                self.kill()
                return

        elif self.state == "attached":
            # Auto-detach after stick window (unless already reeled and launched)
            if self.attached_at_ms and now - self.attached_at_ms >= self.STICK_MS:
                # still allow some extra safety cap
                if now - self.attached_at_ms >= self.DETACH_AFTER_MS:
                    self.state = "done"
                    self.kill()
                    return

            if self.owner and self.anchor and self.rope_len is not None:
                # Read jump press directly (reel-in trigger)
                keys = pygame.key.get_pressed()
                jump_key = self.owner.controls.get("jump")
                jump_pressed = bool(jump_key is not None and keys[jump_key])

                owner_center = pygame.Vector2(self.owner.rect.center)
                to_anchor = pygame.Vector2(self.anchor) - owner_center
                dist = to_anchor.length()

                if jump_pressed:
                    # --- REEL-IN MODE ---
                    if dist <= self.break_dist:
                        # Arrived: launch forward past the cling point
                        if dist != 0:
                            dir_to_anchor = to_anchor.normalize()
                            overshoot_point = pygame.Vector2(self.anchor) + dir_to_anchor * self.OVERSHOOT_PX
                            self.owner.rect.centerx = int(overshoot_point.x)
                            self.owner.rect.centery  = int(overshoot_point.y)
                        self.state = "done"
                        self.kill()
                        return

                    # Distance-scaled pull
                    step = min(self.MAX_PULL, max(self.MIN_PULL, dist * self.PULL_GAIN))
                    to_anchor.scale_to_length(step)

                    # Cancel gravity when moving upward so climb isn't damped
                    if to_anchor.y < 0 and getattr(self.owner, "gravity", 0) > 0:
                        self.owner.gravity = 0

                    self.owner.rect.centerx += int(to_anchor.x)
                    self.owner.rect.centery  += int(to_anchor.y)

                    # Update rope length while reeling, so we don't snap back
                    owner_center = pygame.Vector2(self.owner.rect.center)
                    self.rope_len = (owner_center - pygame.Vector2(self.anchor)).length()

                else:
                    # --- SLING / SWING MODE ---
                    # Let hero gravity do its thing (already applied in Hero.update),
                    # but enforce max rope length (pull back toward circle if stretched)
                    r = pygame.Vector2(self.owner.rect.center) - pygame.Vector2(self.anchor)
                    L = r.length()
                    if L > self.rope_len:  # stretched, pull radially back
                        if L != 0:
                            correction = (L - self.rope_len) * self.ROPE_ENFORCE
                            r_norm = r.normalize()
                            self.owner.rect.centerx -= int(r_norm.x * correction)
                            self.owner.rect.centery  -= int(r_norm.y * correction)

                    # Add a small tangential push to help maintain swinging
                    if r.length_squared() != 0:
                        tangent = pygame.Vector2(-r.y, r.x)
                        if tangent.length_squared() != 0:
                            tangent.scale_to_length(self.SWING_THRUST)
                            self.owner.rect.centerx += int(tangent.x)
                            self.owner.rect.centery  += int(tangent.y)

        elif self.state == "done":
            self.kill()
