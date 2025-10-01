"""GameWorld aggregates mutable runtime state and mediates cross-system interactions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Tuple

import pygame

from constants import MAX_HEALTH, SCREEN_WIDTH, GROUND_Y
from keymap import load_controls
from sprites import Hero
from sprites.banana import Banana
from .spawn import PickupSpawner


@dataclass(slots=True)
class Players:
    first: Hero
    second: Hero

    def as_tuple(self) -> Tuple[Hero, Hero]:
        return self.first, self.second

    def __iter__(self) -> Iterator[Hero]:
        yield self.first
        yield self.second


class GameWorld:
    """Owns sprite groups, player references, and round lifecycle helpers."""

    def __init__(self, *, test_mode: bool = False) -> None:
        self.players = Players(*self._create_players())
        self.player_group = pygame.sprite.Group(*self.players.as_tuple())
        self.throwables = pygame.sprite.Group()
        self.hooks = pygame.sprite.Group()
        self.banana_pickups = pygame.sprite.Group()
        self.health_pickups = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()

        self.test_mode = bool(test_mode)

        self.spawner = PickupSpawner(
            platforms=self.platforms,
            banana_pickups=self.banana_pickups,
            health_pickups=self.health_pickups,
            players=self.players,
        )

        self._apply_test_mode_to_players()

    @property
    def player1(self) -> Hero:
        return self.players.first

    @property
    def player2(self) -> Hero:
        return self.players.second

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def begin_round(self) -> None:
        self._apply_test_mode_to_players()
        for player in self.players:
            player.reset()
        self.banana_pickups.empty()
        self.health_pickups.empty()
        self.throwables.empty()
        self.hooks.empty()
        self.spawner.spawn_platforms()
        self.spawner.spawn_banana_if_needed()

    def update(self) -> None:
        self.player_group.update(self.throwables, self.hooks, self.platforms)
        self.throwables.update(self.platforms)
        self.hooks.update(self.platforms)
        self.banana_pickups.update()
        self.health_pickups.update()

        self._collect_pickups()
        self._handle_projectile_hits()
        self._handle_splats()

    def regenerate_players(self, amount: float) -> None:
        for player in self.players:
            player.health = min(MAX_HEALTH, player.health + amount)

    def reload_controls(self) -> None:
        p1_controls, p2_controls = load_controls()
        self.players.first.controls = p1_controls
        self.players.second.controls = p2_controls

    @property
    def is_test_mode(self) -> bool:
        """Expose whether test-mode visuals should be enabled."""
        return self.test_mode

    def set_test_mode(self, enabled: bool) -> None:
        if self.test_mode == bool(enabled):
            return
        self.test_mode = bool(enabled)
        self._apply_test_mode_to_players()

    @property
    def round_over(self) -> bool:
        return any(player.is_dead for player in self.players)

    @property
    def round_winner(self) -> Hero | None:
        """Return the surviving hero when a round ends, otherwise None."""
        alive = [player for player in self.players if not player.is_dead]
        if len(alive) == 1:
            return alive[0]
        return None

    @property
    def round_draw(self) -> bool:
        """True when all players are eliminated at the end of a round."""
        return all(player.is_dead for player in self.players)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _collect_pickups(self) -> None:
        for player in self.players:
            if not player.has_banana:
                hit = pygame.sprite.spritecollideany(player, self.banana_pickups)
                if hit:
                    player.has_banana = True
                    hit.kill()

        for player in self.players:
            hit = pygame.sprite.spritecollideany(player, self.health_pickups)
            if hit:
                player.health = min(MAX_HEALTH, player.health + 0.5)
                hit.kill()

    def _handle_projectile_hits(self) -> None:
        for projectile in self.throwables.sprites():
            for player in self.players:
                if not getattr(projectile, "can_hit", lambda *_: True)(player):
                    continue
                if projectile.rect.colliderect(player.banana_hitbox()):
                    projectile.on_hit(player)
                    break

    def _handle_splats(self) -> None:
        splats = [
            sprite
            for sprite in self.throwables.sprites()
            if isinstance(sprite, Banana) and sprite.state == "splatted_persist"
        ]

        for splat in splats:
            hitbox = splat.rect.inflate(10, 6)
            for player in self.players:
                if hitbox.colliderect(player.banana_hitbox()):
                    splat.stepped_on_by(player)

        ground_splats = [s for s in splats if s.rect.bottom == GROUND_Y]
        if len(ground_splats) > 2:
            ground_splats.sort(key=lambda spr: spr.splat_time or 0)
            for old in ground_splats[:-2]:
                old.kill()

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def _create_players(self) -> Tuple[Hero, Hero]:
        p1_controls, p2_controls = load_controls()
        player1 = Hero(controls=p1_controls, start_x=200, name="Red", name_color=(220, 60, 60), facing_right=True)
        player2 = Hero(
            controls=p2_controls,
            start_x=SCREEN_WIDTH - 200,
            name="Blue",
            name_color=(80, 140, 255),
            facing_right=False,
        )
        return player1, player2

    def _apply_test_mode_to_players(self) -> None:
        for hero in (self.players.first, self.players.second):
            hero.infinite_bananas = self.test_mode
            hero._banana_refill_time = 0
            if self.test_mode and not hero.has_banana:
                hero.has_banana = True



__all__ = ["GameWorld"]
