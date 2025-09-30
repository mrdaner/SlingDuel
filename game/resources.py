"""Utilities for loading and grouping UI/game assets."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from assets import (
    get_background,
    get_banana_image,
    get_font,
    get_heart,
    get_heart_half,
    get_hook_image,
    get_target,
)


@dataclass(slots=True)
class GameResources:
    """Container that owns all static surfaces/fonts used by the game loop."""

    game_font: pygame.font.Font
    name_font: pygame.font.Font
    sky: pygame.Surface
    ground: pygame.Surface
    target: pygame.Surface
    target_left: pygame.Surface
    heart: pygame.Surface
    heart_half: pygame.Surface
    banana_icon: pygame.Surface
    hook_icon: pygame.Surface
    heart_padding: int = 20
    heart_gap: int = 10

    @classmethod
    def load(cls) -> "GameResources":
        sky, ground = get_background()
        target = get_target()
        return cls(
            game_font=get_font(size=100),
            name_font=get_font(size=36),
            sky=sky,
            ground=ground,
            target=target,
            target_left=pygame.transform.flip(target, True, False),
            heart=get_heart(),
            heart_half=get_heart_half(),
            banana_icon=get_banana_image(),
            hook_icon=get_hook_image(),
        )

    @property
    def heart_width(self) -> int:
        return self.heart.get_width()


__all__ = ["GameResources"]
