"""Utility helpers for generating projectile trajectories for debug rendering."""
from __future__ import annotations

from typing import Iterable
import pygame

def simulate_trajectory(
    start: Iterable[float],
    velocity: pygame.Vector2,
    *,
    gravity: float,
    gravity_scale: float,
    max_fall: float | None,
    steps: int,
    ground_y: int,
    screen_width: int,
) -> list[tuple[int, int]]:
    """Return a list of integer coordinate points approximating a projectile arc."""
    pos = pygame.Vector2(start)
    vel = pygame.Vector2(velocity)
    points: list[tuple[int, int]] = []

    for _ in range(steps):
        pos += vel
        vel.y += gravity * gravity_scale
        if max_fall is not None and vel.y > max_fall:
            vel.y = max_fall
        points.append((int(pos.x), int(pos.y)))
        if pos.y >= ground_y or pos.x < 0 or pos.x > screen_width:
            break

    return points
