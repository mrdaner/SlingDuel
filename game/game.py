"""High level orchestration of the SlingDuel gameplay loop."""
from __future__ import annotations

import pygame

from constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from sprites.hero import Hero
from keymap import save_controls, default_controls
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
        self.test_mode = False
        self.world = GameWorld(test_mode=self.test_mode)
        self.renderer = GameSceneRenderer(self.screen, self.resources)

        self.game_active = False
        self.paused = False
        self.last_winner: Hero | None = None
        self.last_round_draw = False
        self._restart_available_at = 0
        self.keymap_mode = False
        self._keymap_selection = 0
        self._keymap_waiting = False
        self._keymap_actions = ["left", "right", "up", "down", "jump", "sling", "throw"]
        self._keymap_labels = {
            "left": "Move Left",
            "right": "Move Right",
            "up": "Aim Up",
            "down": "Aim Down",
            "jump": "Jump",
            "sling": "Hook",
            "throw": "Throw Banana",
        }

        self._spawn_event = pygame.USEREVENT + 10
        self._regen_event = pygame.USEREVENT + 11
        self._heart_spawn_event = pygame.USEREVENT + 12

        pygame.time.set_timer(self._spawn_event, 10000)
        pygame.time.set_timer(self._regen_event, 30000)
        pygame.time.set_timer(self._heart_spawn_event, 60000)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        while True:
            self._handle_events()
            if self.game_active:
                if not self.paused:
                    self.world.update()
                    self.renderer.draw_gameplay(self.world)
                    if self.world.round_over:
                        self.last_winner = self.world.round_winner
                        self.last_round_draw = self.world.round_draw
                        self.game_active = False
                        self.paused = False
                        self._restart_available_at = pygame.time.get_ticks() + 3000
                else:
                    self.renderer.draw_gameplay(self.world)
                    self.renderer.draw_pause_overlay(test_mode=self.test_mode)
            else:
                if self.keymap_mode:
                    entries = self._keymap_entries()
                    self.renderer.draw_keymap_menu(
                        entries,
                        selected_index=self._keymap_selection,
                        awaiting=self._keymap_waiting,
                        test_mode=self.test_mode,
                    )
                else:
                    self.renderer.draw_start_screen(
                        winner=self.last_winner,
                        draw=self.last_round_draw,
                        test_mode=self.test_mode,
                    )

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
                if event.type == pygame.KEYDOWN:
                    if self.keymap_mode:
                        self._handle_keymap_event(event)
                    else:
                        if event.key == pygame.K_SPACE:
                            if pygame.time.get_ticks() >= self._restart_available_at:
                                self._start_round()
                        elif event.key == pygame.K_t:
                            self._toggle_test_mode()
                        elif event.key == pygame.K_k:
                            self._enter_keymap_mode()
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.paused:
                            self.paused = False
                        else:
                            self.paused = True
                    elif self.paused and event.key == pygame.K_m:
                        self.paused = False
                        self.game_active = False
                        self.keymap_mode = False
                        self._keymap_waiting = False
                        self._restart_available_at = pygame.time.get_ticks() + 300
                    elif self.paused and event.key == pygame.K_t:
                        self._toggle_test_mode()
                    elif self.paused and event.key == pygame.K_k and not self.keymap_mode:
                        self._enter_keymap_mode()
                        self.paused = False
                        self.game_active = False
                if not self.paused:
                    if event.type == self._spawn_event:
                        self.world.spawner.spawn_banana_if_needed()
                    elif event.type == self._heart_spawn_event:
                        self.world.spawner.spawn_heart_if_needed()
                    elif event.type == self._regen_event:
                        self.world.regenerate_players(0.5)

    def _start_round(self) -> None:
        self.game_active = True
        self.paused = False
        self.keymap_mode = False
        self._keymap_waiting = False
        self.last_winner = None
        self.last_round_draw = False
        self._restart_available_at = 0
        self.world.begin_round()

    def _toggle_test_mode(self) -> None:
        self.test_mode = not self.test_mode
        self.world.set_test_mode(self.test_mode)
        if self.keymap_mode:
            self._keymap_selection = 0
            self._keymap_waiting = False

    def _enter_keymap_mode(self) -> None:
        self.keymap_mode = True
        self._keymap_selection = 0
        self._keymap_waiting = False

    def _exit_keymap_mode(self) -> None:
        self.keymap_mode = False
        self._keymap_waiting = False

    def _handle_keymap_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        entries = self._keymap_entries()
        count = len(entries)
        if self._keymap_waiting:
            if event.key == pygame.K_ESCAPE:
                self._keymap_waiting = False
                return
            self._apply_keymap_change(self._keymap_selection, event.key)
            self._keymap_waiting = False
            return

        if event.key == pygame.K_ESCAPE:
            self._exit_keymap_mode()
        elif event.key == pygame.K_UP:
            if count:
                self._keymap_selection = (self._keymap_selection - 1) % count
        elif event.key == pygame.K_DOWN:
            if count:
                self._keymap_selection = (self._keymap_selection + 1) % count
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if count:
                self._keymap_waiting = True
        elif event.key == pygame.K_r:
            self._reset_keymap_defaults()
        elif event.key == pygame.K_t:
            self._toggle_test_mode()

    def _apply_keymap_change(self, index: int, new_key: int) -> None:
        entries = self._keymap_entries()
        if not entries:
            return
        index = max(0, min(index, len(entries) - 1))
        entry = entries[index]
        hero = entry["hero"]
        action = entry["action_key"]
        hero.controls[action] = new_key
        save_controls(self.world.players.first.controls, self.world.players.second.controls)

    def _reset_keymap_defaults(self) -> None:
        p1_defaults, p2_defaults = default_controls()
        self.world.players.first.controls = p1_defaults
        self.world.players.second.controls = p2_defaults
        save_controls(p1_defaults, p2_defaults)
        self._keymap_selection = 0
        self._keymap_waiting = False

    def _keymap_entries(self) -> list[dict]:
        entries: list[dict] = []
        players = [
            ("Player 1", self.world.players.first),
            ("Player 2", self.world.players.second),
        ]
        for label, hero in players:
            for action in self._keymap_actions:
                keycode = hero.controls.get(action)
                key_name = pygame.key.name(keycode) if keycode is not None else "—"
                entries.append({
                    "player": label,
                    "action_label": self._keymap_labels.get(action, action.title()),
                    "action_key": action,
                    "key_name": key_name,
                    "hero": hero,
                })
        return entries


__all__ = ["Game"]
