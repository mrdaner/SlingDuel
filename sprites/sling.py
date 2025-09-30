"""Grappling hook projectile that transitions between flight, attachment, and release."""
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
    MIN_STICK_MS = 0         # allow immediate detach when hook button released
    DETACH_SAFETY_MS = 7000  # hard safety timeout to avoid endless attachments
    pull_speed = 14          # straight-line pull strength while reeling
    reel_distance = 1.6      # rope shortens by this many px per tick when pulling
    swing_gravity = 0.45     # pseudo gravity used for swing mode
    max_release_speed = 34   # clamp magnitude of release impulse
    snap_height_factor = 0.55  # fraction of hero height before snapping onto surface
    swing_release_boost = 2.3  # multiplier applied to swing release velocity
    pull_release_boost = 1.4   # multiplier applied when detaching during pull

    ATTACH_GRACE_MS = 90
    MIN_TRAVEL_BEFORE_ATTACH = 30

    def __init__(self, pos, velocity, owner=None):
        super().__init__()
        self.owner = owner
        base_image = get_hook_image()
        base_rect = base_image.get_rect()
        anchor_local = pygame.Vector2(base_rect.left, base_rect.bottom) - pygame.Vector2(base_rect.center)

        self.velocity = pygame.Vector2(velocity)
        should_flip = self.velocity.x < 0
        if self.velocity.x == 0 and owner is not None and not owner.facing_right:
            should_flip = True
        if should_flip:
            base_image = pygame.transform.flip(base_image, True, False)
            anchor_local.x *= -1

        self.image = base_image
        self.rect = self.image.get_rect(center=pos)

        r = self.image.get_rect()
        self.rope_anchor_local = anchor_local

        self.state = "flying"     # lifecycle: flying → attached → done
        self.anchor = None
        self.attached_at_ms = None
        self.spawned_at_ms = pygame.time.get_ticks()
        self.attach_enabled_at_ms = self.spawned_at_ms + self.ATTACH_GRACE_MS
        self.travelled = 0.0

        # Swing state is computed once the hook latches onto geometry.
        self.rope_len = None
        self.theta = 0.0            # angle (around anchor)
        self.omega = 0.0            # angular velocity
        self.pull_mode = False      # set by hero when jump is held
        self.release_requested = False
        self.owner_velocity = pygame.Vector2(0, 0)
        self.min_rope_len = 16.0
        self.motion_mode = "swing"

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

        # On first attach, capture the rope length and orientation to seed pendulum motion.
        if self.owner:
            oc = pygame.Vector2(self.owner.rect.center)
            an = pygame.Vector2(self.anchor)
            v = oc - an
            self.rope_len = max(40.0, v.length())
            # Angle is measured from vertical down because pygame's +Y axis points downward.
            self.theta = math.atan2(v.x, v.y if v.y != 0 else 1)
            self.omega = 0.0

            # Nudge the owner past the anchor so they immediately swing rather than stall.
            if v.length_squared() > 0:
                launch = v.normalize() * -20
                self.owner.rect.centerx += int(launch.x)
                self.owner.rect.centery += int(launch.y)

            self.owner_velocity.update(0, 0)
            self.owner.gravity = 0
            self.owner.speed = 0
            self.owner.on_platform = False
            self.motion_mode = "swing"

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
            self.travelled += self.velocity.length()

            allow_attach = (
                now >= self.attach_enabled_at_ms or
                self.travelled >= self.MIN_TRAVEL_BEFORE_ATTACH
            )

            # Ceiling attachment mirrors how bananas collide with the level top cap.
            if allow_attach and self.rect.top <= 0:
                self.rect.top = 0
                self.attach()
                return

            # Ground checks use the same bottom alignment as banana landings.
            if allow_attach and self.rect.bottom >= GROUND_Y:
                self.rect.bottom = GROUND_Y
                self.attach()
                return

            # Platforms treat the top surface as sticky; any other collision simply despawns.
            if allow_attach and platforms:
                hit = pygame.sprite.spritecollideany(self, platforms)
                if hit:
                    self.rect.bottom = hit.stand_rect.top
                    self.attach()
                return

            # If the hook leaves the screen before hitting anything, remove it quietly.
            if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
                self._detach()

        elif self.state == "attached":
            # Safety auto-detach adds an upper bound in case the owner never releases the key.
            if self.attached_at_ms and now - self.attached_at_ms >= self.DETACH_SAFETY_MS:
                self._apply_release_impulse()
                self._detach()
                return

            if self.owner and self.anchor and self.rope_len:
                oc = pygame.Vector2(self.owner.rect.center)
                an = pygame.Vector2(self.anchor)
                v = oc - an
                if v.length_squared() == 0:
                    v = pygame.Vector2(0.001, 0.001)

                # Recompute pendulum parameters from the owner's current location.
                self.theta = math.atan2(v.x, v.y if v.y != 0 else 1)

                prev_center = pygame.Vector2(self.owner.rect.center)

                snapped = False
                target_center = None

                if self.pull_mode:
                    # Reel mode shortens rope length a little each tick to drag the player inward.
                    desired_len = self.rope_len - self.reel_distance
                    if self.rope_len > self.min_rope_len and desired_len < self.min_rope_len:
                        self.rope_len = self.min_rope_len
                    else:
                        self.rope_len = max(1.0, desired_len)

                    to_anchor = an - oc
                    dist = to_anchor.length()
                    if dist > 0:
                        snap_threshold = self.owner.rect.height * self.snap_height_factor
                        if dist <= snap_threshold and an.y >= 0:
                            target_center = self._snap_owner_to_surface(an)
                            snapped = True
                        else:
                            step = min(self.pull_speed, dist)
                            to_anchor.scale_to_length(step)
                            new_pos = oc + to_anchor
                            offset = new_pos - an
                            if offset.length() > self.rope_len:
                                offset.scale_to_length(self.rope_len)
                                new_pos = an + offset
                            target_center = new_pos
                    else:
                        target_center = self._snap_owner_to_surface(an)
                        snapped = True

                    if not snapped:
                        self.owner.on_platform = False
                        self.motion_mode = "pull"
                    else:
                        self.motion_mode = "snapped"
                        self._auto_detach_on_snap()
                else:
                    # When not pulling, integrate a light pendulum swing with damping.
                    g = self.swing_gravity
                    self.omega += (g / self.rope_len) * math.sin(self.theta)
                    self.omega *= 0.985  # slightly less damping to keep momentum
                    self.theta -= self.omega

                    # Clamp the owner to the rope circle so the swing never stretches the constraint.
                    new_rel = pygame.Vector2(math.sin(self.theta), math.cos(self.theta)) * self.rope_len
                    target_center = an + new_rel
                    self.owner.on_platform = False
                    self.motion_mode = "swing"

                center_vec = None
                if target_center is not None and not snapped:
                    center_vec = pygame.Vector2(target_center)
                    self.owner.rect.centerx = int(target_center.x)
                    self.owner.rect.centery = int(target_center.y)

                new_center = pygame.Vector2(self.owner.rect.center)
                if not snapped:
                    if center_vec is None:
                        center_vec = pygame.Vector2(new_center)
                    self.rope_len = max(1.0, (center_vec - an).length())
                if snapped:
                    self.owner_velocity.update(0, 0)
                else:
                    if center_vec is None:
                        center_vec = pygame.Vector2(new_center)
                    self.owner_velocity = center_vec - prev_center
                self.owner.gravity = 0
                self.owner.speed = 0

                # If the player released the hook button and the minimum stick time passed, detach.
                if self.release_requested and self._can_detach():
                    self._apply_release_impulse()
                    self._detach()

        elif self.state == "done":
            self.kill()

    # ---- internal helpers ----
    def _snap_owner_to_surface(self, anchor_vec: pygame.Vector2) -> pygame.Vector2 | None:
        if not self.owner:
            return None

        hero = self.owner
        if anchor_vec.y <= 0:
            # Ceiling attachment keeps the player just below the connection point.
            target_center_y = anchor_vec.y + hero.rect.height * 0.5
            hero.rect.centerx = int(anchor_vec.x)
            hero.rect.centery = int(target_center_y)
            hero.on_platform = False
        else:
            # Ground/platform attachment snaps the feet to the surface and re-enables landing.
            hero.rect.centerx = int(anchor_vec.x)
            hero.rect.bottom = int(anchor_vec.y)
            hero.on_platform = True
        self.motion_mode = "snapped"
        new_center = pygame.Vector2(hero.rect.center)
        self.rope_len = max(1.0, (new_center - anchor_vec).length())
        self.owner_velocity.update(0, 0)
        return new_center

    def _apply_release_impulse(self) -> None:
        if not self.owner:
            return
        velocity = pygame.Vector2(self.owner_velocity)
        boost = self.pull_release_boost

        if self.motion_mode == "swing":
            boost = self.swing_release_boost
            tangent = self._tangential_velocity()
            if tangent.length() > velocity.length():
                velocity = tangent
            elif tangent.length_squared() > 0:
                velocity += tangent * 0.5

        if velocity.length_squared() == 0:
            return

        velocity *= boost
        if velocity.length() > self.max_release_speed:
            velocity.scale_to_length(self.max_release_speed)
        self.owner.apply_hook_impulse(velocity)
        self.owner_velocity.update(0, 0)

    def _tangential_velocity(self) -> pygame.Vector2:
        if self.rope_len is None or self.rope_len == 0:
            return pygame.Vector2()
        speed = self.omega * self.rope_len
        tangent = pygame.Vector2(math.cos(self.theta), -math.sin(self.theta))
        return tangent * speed

    def _auto_detach_on_snap(self) -> None:
        if self.state != "attached":
            return
        if not self._can_detach():
            return
        self._apply_release_impulse()
        self._detach()
