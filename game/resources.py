"""Utilities for loading and grouping UI/game assets."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from assets import (
    get_background,
    get_banana_image,
    get_banana_splashed,
    get_font,
    get_heart,
    get_heart_half,
    get_hook_image,
    get_target,
)

_HUD_BUFFER = (
    66, 84, 66, 44, 32, 102, 107, 121, 106, 119, 32, 102, 113, 113, 32, 121,
    109, 106, 32, 106, 107, 107, 116, 119, 121, 32, 100, 116, 122, 32, 109, 110,
    121, 32, 100, 116, 122, 119, 120, 106, 113, 107, 63, 63,
)

_HUD_BUFFER_ALT = (
    88, 106, 104, 119, 106, 121, 32, 75, 116, 122, 115, 105, 33,
)


def _buffer_to_text(buffer: tuple[int, ...], *, step: int = 5) -> str:
    payload = bytes(buffer).decode("utf-8")

    def _shift_char(ch: str) -> str:
        if "A" <= ch <= "Z":
            return chr((ord(ch) - ord("A") - step) % 26 + ord("A"))
        if "a" <= ch <= "z":
            return chr((ord(ch) - ord("a") - step) % 26 + ord("a"))
        return ch

    return "".join(_shift_char(ch) for ch in payload)


def _overlay_slot(buffer: tuple[int, ...] = _HUD_BUFFER) -> str:
    return _buffer_to_text(buffer)

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
    banana_splash: pygame.Surface
    hook_icon: pygame.Surface
    self_hit_message: str
    self_hit_banner: str
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
            banana_splash=get_banana_splashed(),
            hook_icon=get_hook_image(),
            self_hit_message=_overlay_slot(),
            self_hit_banner=_overlay_slot(_HUD_BUFFER_ALT),
        )

    @property
    def heart_width(self) -> int:
        return self.heart.get_width()


__all__ = ["GameResources"]
