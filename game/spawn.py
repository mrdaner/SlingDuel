"""Logic for creating platforms and pickups within the arena."""
from __future__ import annotations

from random import choice, randint
from typing import Iterable

import pygame

from constants import GROUND_Y, SCREEN_WIDTH
from sprites.banana import BananaPickup
from sprites.health import HealthPickup
from sprites.platform import Platform
from assets import get_floor_images


class PickupSpawner:
    """Responsible for placing platforms and pickups without overlap."""

    def __init__(self, *, platforms: pygame.sprite.Group, banana_pickups: pygame.sprite.Group,
                 health_pickups: pygame.sprite.Group) -> None:
        self._platforms = platforms
        self._banana_pickups = banana_pickups
        self._health_pickups = health_pickups

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def spawn_platforms(self) -> None:
        """Create a fresh set of floating platforms for a new round."""
        self._platforms.empty()
        floor_imgs = get_floor_images()
        if not floor_imgs:
            return

        cols, rows = 5, 5
        cell_w = SCREEN_WIDTH // (cols + 1)
        cell_h = (GROUND_Y - 120) // (rows + 1)
        candidates: list[tuple[int, int]] = []
        for r_idx in range(1, rows + 1):
            for c_idx in range(1, cols + 1):
                candidates.append((c_idx * cell_w, r_idx * cell_h))

        choices: list[tuple[int, int]] = []
        while candidates and len(choices) < 8:
            idx = randint(0, len(candidates) - 1)
            choices.append(candidates.pop(idx))

        for (c_x, c_y) in choices:
            img = choice(floor_imgs)
            platform = Platform(img, midtop=(c_x, c_y))
            self._platforms.add(platform)

    def spawn_banana_if_needed(self) -> None:
        if len(self._banana_pickups) >= 4:
            return

        self._spawn_banana_on_ground()
        while len(self._banana_pickups) < 4:
            if not self._spawn_banana_on_platform():
                break

    def spawn_heart_if_needed(self) -> None:
        if len(self._health_pickups) >= 1 or not self._platforms:
            return

        for _ in range(20):
            platform = choice(self._platforms.sprites())
            x_pos = self._random_x_on_platform(platform)
            candidate = HealthPickup(x_pos, y_bottom=platform.stand_rect.top)
            if self._non_overlapping(candidate.rect, (self._banana_pickups, self._health_pickups)):
                self._health_pickups.add(candidate)
                return

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _spawn_banana_on_ground(self) -> bool:
        ground_count = sum(1 for banana in self._banana_pickups if banana.rect.bottom == GROUND_Y)
        if ground_count >= 1:
            return False

        x_pos = randint(60, SCREEN_WIDTH - 60)
        candidate = BananaPickup(x_pos, y_bottom=GROUND_Y)
        if self._non_overlapping(candidate.rect, (self._banana_pickups, self._health_pickups)):
            self._banana_pickups.add(candidate)
            return True
        return False

    def _spawn_banana_on_platform(self) -> bool:
        platforms = self._platforms.sprites()
        if not platforms:
            return False

        for _ in range(12):
            platform = choice(platforms)
            x_pos = self._random_x_on_platform(platform)
            candidate = BananaPickup(x_pos, y_bottom=platform.stand_rect.top)
            if self._non_overlapping(candidate.rect, (self._banana_pickups, self._health_pickups)):
                self._banana_pickups.add(candidate)
                return True
        return False

    @staticmethod
    def _non_overlapping(rect: pygame.Rect, groups: Iterable[pygame.sprite.Group]) -> bool:
        for group in groups:
            for sprite in group.sprites():
                if rect.colliderect(sprite.rect):
                    return False
        return True

    @staticmethod
    def _random_x_on_platform(platform: Platform) -> int:
        left = platform.rect.left + 20
        right = platform.rect.right - 20
        return randint(left, right)


__all__ = ["PickupSpawner"]
