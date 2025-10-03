"""High level orchestration of the SlingDuel gameplay loop and UI states."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from sprites.hero import Hero
from keymap import save_controls, default_controls
from .resources import GameResources
from .view import GameSceneRenderer
from .world import GameWorld


screen_buffer = True


@dataclass(frozen=True)
class KeymapEntry:
    """Lightweight view-model describing a single action binding."""

    player_label: str
    action_label: str
    action_key: str
    hero: Hero

    @property
    def key_name(self) -> str:
        keycode = self.hero.controls.get(self.action_key)
        return pygame.key.name(keycode) if keycode is not None else "—"


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
        self.world.on_self_banana_hit = self._trigger_self_hit_modal

        self.game_active = False
        self.paused = False
        self.self_hit_modal_active = False
        self._self_hit_message = ""
        self._self_hit_unlock_at = 0
        self.last_winner: Hero | None = None
        self.last_round_draw = False
        self._restart_available_at = 0
        self._round_over_recorded = False
        self._round_over_time = 0
        self.keymap_mode = False
        self._keymap_selection = 0
        self._keymap_waiting = False
        self._resume_after_keymap = False
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

        self._self_hit_focus_hero: Hero | None = None

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        while True:
            self._handle_events()
            if self.self_hit_modal_active:
                if self.world.round_over:
                    self._record_round_end(defer_exit=True)
                self.renderer.draw_gameplay(self.world)
                prompt_visible = pygame.time.get_ticks() >= self._self_hit_unlock_at
                self.renderer.draw_self_hit_overlay(
                    self._self_hit_message,
                    prompt_visible=prompt_visible,
                    focus_hero=self._self_hit_focus_hero,
                )
            elif self.game_active:
                if not self.paused:
                    self.world.update()
                    self.renderer.draw_gameplay(self.world)
                    if self.world.round_over:
                        self._record_round_end(defer_exit=False)
                else:
                    self.renderer.draw_gameplay(self.world)
                    if self.keymap_mode:
                        entries = self._keymap_entries()
                        self.renderer.draw_keymap_menu(
                            entries,
                            selected_index=self._keymap_selection,
                            awaiting=self._keymap_waiting,
                            test_mode=self.test_mode,
                            overlay=True,
                        )
                    else:
                        self.renderer.draw_pause_overlay(test_mode=self.test_mode)
            else:
                if self.keymap_mode:
                    self.renderer.draw_start_backdrop()
                    entries = self._keymap_entries()
                    self.renderer.draw_keymap_menu(
                        entries,
                        selected_index=self._keymap_selection,
                        awaiting=self._keymap_waiting,
                        test_mode=self.test_mode,
                        overlay=False,
                    )
                else:
                    self.renderer.draw_start_screen(
                        winner=self.last_winner,
                        draw=self.last_round_draw,
                        test_mode=self.test_mode,
                        dim=False,
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

            if self.self_hit_modal_active:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    if pygame.time.get_ticks() >= self._self_hit_unlock_at:
                        self._dismiss_self_hit_modal()
                continue

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
                    if self.keymap_mode:
                        self._handle_keymap_event(event)
                        continue
                    if event.key == pygame.K_ESCAPE:
                        if self.paused:
                            self.paused = False
                        else:
                            self.paused = True
                    elif self.paused and event.key == pygame.K_m:
                        self._reset_self_hit_modal()
                        self.paused = False
                        self.game_active = False
                        self.keymap_mode = False
                        self._keymap_waiting = False
                        self._restart_available_at = pygame.time.get_ticks() + 300
                    elif self.paused and event.key == pygame.K_t:
                        self._toggle_test_mode()
                    elif self.paused and event.key == pygame.K_k and not self.keymap_mode:
                        self._resume_after_keymap = True
                        self._enter_keymap_mode()
                if not self.paused:
                    if event.type == self._spawn_event:
                        self.world.spawner.spawn_banana_if_needed()
                    elif event.type == self._heart_spawn_event:
                        self.world.spawner.spawn_heart_if_needed()
                    elif event.type == self._regen_event:
                        self.world.regenerate_players(0.5)

    def _start_round(self) -> None:
        self._dismiss_self_hit_modal()
        self._reset_self_hit_modal()
        self.game_active = True
        self.paused = False
        self.keymap_mode = False
        self._keymap_waiting = False
        self.last_winner = None
        self.last_round_draw = False
        self._restart_available_at = 0
        self._round_over_recorded = False
        self._round_over_time = 0
        self._resume_after_keymap = False
        self.world.begin_round()

    def _toggle_test_mode(self) -> None:
        self.test_mode = not self.test_mode
        self.world.set_test_mode(self.test_mode)
        self._reset_self_hit_modal()
        if self.keymap_mode:
            self._keymap_selection = 0
            self._keymap_waiting = False

    def _record_round_end(self, *, defer_exit: bool) -> None:
        if self._round_over_recorded:
            return
        self._round_over_recorded = True
        self._round_over_time = pygame.time.get_ticks()
        self.last_winner = self.world.round_winner
        self.last_round_draw = self.world.round_draw
        ready_at = self._round_over_time + 3000
        self._restart_available_at = max(self._restart_available_at, ready_at)
        self.renderer.set_restart_prompt_visible_at(ready_at)
        if not defer_exit:
            self.game_active = False
            self.paused = False

    def _trigger_self_hit_modal(self, hero: Hero) -> None:
        if self.test_mode or not screen_buffer:
            return
        if self.self_hit_modal_active:
            return
        self.self_hit_modal_active = True
        self._self_hit_message = self.resources.self_hit_message
        self._self_hit_unlock_at = pygame.time.get_ticks() + 10000
        self._self_hit_focus_hero = hero

    def _dismiss_self_hit_modal(self) -> None:
        if not self.self_hit_modal_active:
            return
        self._reset_self_hit_modal()
        if self._round_over_recorded and self.game_active and self.world.round_over:
            self.game_active = False
            self.paused = False

    def _reset_self_hit_modal(self) -> None:
        self.self_hit_modal_active = False
        self._self_hit_message = ""
        self._self_hit_unlock_at = 0
        self._self_hit_focus_hero = None

    def _enter_keymap_mode(self) -> None:
        self._reset_self_hit_modal()
        self.keymap_mode = True
        self._keymap_selection = 0
        self._keymap_waiting = False

    def _exit_keymap_mode(self) -> None:
        self.keymap_mode = False
        self._keymap_waiting = False
        if self._resume_after_keymap:
            self._resume_after_keymap = False
            self.paused = True
            self.game_active = True

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
        hero = entry.hero
        action = entry.action_key
        hero.controls[action] = new_key
        save_controls(self.world.players.first.controls, self.world.players.second.controls)

    def _reset_keymap_defaults(self) -> None:
        p1_defaults, p2_defaults = default_controls()
        self.world.players.first.controls = p1_defaults
        self.world.players.second.controls = p2_defaults
        save_controls(p1_defaults, p2_defaults)
        self._keymap_selection = 0
        self._keymap_waiting = False

    def _keymap_entries(self) -> list[KeymapEntry]:
        entries: list[KeymapEntry] = []
        players = [
            ("Player 1", self.world.players.first),
            ("Player 2", self.world.players.second),
        ]
        for label, hero in players:
            for action in self._keymap_actions:
                entries.append(
                    KeymapEntry(
                        player_label=label,
                        action_label=self._keymap_labels.get(action, action.title()),
                        action_key=action,
                        hero=hero,
                    )
                )
        return entries


__all__ = ["Game"]
