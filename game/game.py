"""High level orchestration of the SlingDuel gameplay loop."""
from __future__ import annotations

import pygame

from constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from sprites.hero import Hero
from .resources import GameResources
from .view import GameSceneRenderer
from .world import GameWorld


class Game:
    """Glue object coordinating input, world updates, and rendering."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("SlingDuel")
        self.clock = pygame.time.Clock()

        self.resources = GameResources.load()
        self.world = GameWorld()
        self.renderer = GameSceneRenderer(self.screen, self.resources)

        self.game_active = False
        self.last_winner: Hero | None = None
        self.last_round_draw = False

        self._spawn_event = pygame.USEREVENT + 10
        self._regen_event = pygame.USEREVENT + 11
        self._heart_spawn_event = pygame.USEREVENT + 12

        pygame.time.set_timer(self._spawn_event, 5000)
        pygame.time.set_timer(self._regen_event, 30000)
        pygame.time.set_timer(self._heart_spawn_event, 60000)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        while True:
            self._handle_events()
            if self.game_active:
                self.world.update()
                self.renderer.draw_gameplay(self.world)
                if self.world.round_over:
                    self.last_winner = self.world.round_winner
                    self.last_round_draw = self.world.round_draw
                    self.game_active = False
            else:
                self.renderer.draw_start_screen(winner=self.last_winner, draw=self.last_round_draw)

            pygame.display.update()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F9:
                self.world.reload_controls()

            if not self.game_active:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self._start_round()
            else:
                if event.type == self._spawn_event:
                    self.world.spawner.spawn_banana_if_needed()
                elif event.type == self._heart_spawn_event:
                    self.world.spawner.spawn_heart_if_needed()
                elif event.type == self._regen_event:
                    self.world.regenerate_players(0.5)

    def _start_round(self) -> None:
        self.game_active = True
        self.last_winner = None
        self.last_round_draw = False
        self.world.begin_round()


__all__ = ["Game"]
