"""Rendering helpers for SlingDuel game scenes (HUD, sprites, debug overlays)."""
from __future__ import annotations

import pygame

from constants import (
    COLOR_BG,
    MAX_HEALTH,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GROUND_Y,
    PROJECTILE_GRAVITY,
    MAX_PROJECTILE_FALL_SPEED,
)
from sprites.hero import Hero

from .resources import GameResources
from .world import GameWorld


class GameSceneRenderer:
    """Responsible for all drawing in the active and idle states."""

    def __init__(self, screen: pygame.Surface, resources: GameResources) -> None:
        self.screen = screen
        self.resources = resources

        self._title_color = (243, 212, 67)  # ripe banana
        self._accent_color = (123, 86, 25)  # banana stem brown
        self._muted_color = (244, 230, 170)
        self._title_surf = resources.game_font.render("Slingduel", False, self._title_color)
        self._title_rect = self._title_surf.get_rect(center=(SCREEN_WIDTH // 2, 130))
        self._prompt_center = (SCREEN_WIDTH // 2, 320)
        self._result_center = (SCREEN_WIDTH // 2, 260)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def draw_start_screen(self, winner: Hero | None = None, draw: bool = False, *, test_mode: bool = False) -> None:
        self.screen.fill(COLOR_BG)
        self.screen.blit(self._title_surf, self._title_rect)

        prompt_text = "Press SPACE to START"
        if winner is not None or draw:
            prompt_text = "Press SPACE to PLAY AGAIN"
        prompt_surf = self.resources.game_font.render(prompt_text, False, self._accent_color)
        prompt_rect = prompt_surf.get_rect(center=self._prompt_center)
        self.screen.blit(prompt_surf, prompt_rect)

        outcome_text: str | None = None
        outcome_color = self._title_color

        if draw:
            outcome_text = "Draw!"
            outcome_color = (240, 240, 240)
        elif winner is not None:
            outcome_text = f"{winner.name} Wins!"
            outcome_color = winner.name_color

        if outcome_text:
            outcome_surf = self.resources.game_font.render(outcome_text, False, outcome_color)
            outcome_rect = outcome_surf.get_rect(center=self._result_center)
            self.screen.blit(outcome_surf, outcome_rect)

        status_color = (198, 120, 30) if test_mode else self._accent_color
        status_text = f"Test Mode: {'ON' if test_mode else 'OFF'}"
        status_surf = self.resources.name_font.render(status_text, False, status_color)
        status_rect = status_surf.get_rect(center=(SCREEN_WIDTH // 2, self._prompt_center[1] + 90))
        self.screen.blit(status_surf, status_rect)

        toggle_hint = "Press T to toggle test mode"
        hint_surf = self.resources.name_font.render(toggle_hint, False, self._muted_color)
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, status_rect.bottom + 40))
        self.screen.blit(hint_surf, hint_rect)

        remap_hint = "Press K to remap controls"
        remap_surf = self.resources.name_font.render(remap_hint, False, self._muted_color)
        remap_rect = remap_surf.get_rect(center=(SCREEN_WIDTH // 2, hint_rect.bottom + 32))
        self.screen.blit(remap_surf, remap_rect)

    def draw_gameplay(self, world: GameWorld) -> None:
        res = self.resources
        self.screen.blit(res.sky, (0, 0))
        self.screen.blit(res.ground, (0, 0))

        world.platforms.draw(self.screen)
        world.banana_pickups.draw(self.screen)
        world.health_pickups.draw(self.screen)

        self._draw_hearts(world.players.first, left=True)
        self._draw_hearts(world.players.second, left=False)
        self._draw_inventory_icons(world)
        self._draw_hook_icons(world)

        world.player_group.draw(self.screen)
        world.throwables.draw(self.screen)
        self._draw_name_tags(world)
        self._draw_hooks(world)
        self._draw_aim_targets(world)
        self._draw_trajectories(world)
        self._draw_debug_boxes(world)

    def draw_pause_overlay(self, *, test_mode: bool) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.resources.game_font.render("Paused", False, self._title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(title, title_rect)

        lines = [
            "Press ESC to continue",
            "Press M to return to menu",
            "Press K to remap controls",
        ]
        if test_mode:
            lines.append("Press T to toggle test mode")

        for idx, text in enumerate(lines):
            surf = self.resources.name_font.render(text, False, self._muted_color)
            rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + idx * 40))
            self.screen.blit(surf, rect)

    def draw_keymap_menu(self, entries: list[dict], selected_index: int, awaiting: bool, *, test_mode: bool) -> None:
        self.screen.fill(COLOR_BG)

        title = self.resources.game_font.render("Remap Controls", False, self._title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)

        info_color = self._muted_color
        info_text = "Use Up/Down to select, Enter to rebind, R to reset, ESC to exit"
        info_surf = self.resources.name_font.render(info_text, False, info_color)
        info_rect = info_surf.get_rect(center=(SCREEN_WIDTH // 2, title_rect.bottom + 40))
        self.screen.blit(info_surf, info_rect)

        if awaiting and 0 <= selected_index < len(entries):
            entry = entries[selected_index]
            waiting_text = f"Press new key for {entry['player']} - {entry['action_label']}"
            waiting_surf = self.resources.name_font.render(waiting_text, False, (218, 150, 32))
            waiting_rect = waiting_surf.get_rect(center=(SCREEN_WIDTH // 2, info_rect.bottom + 40))
            self.screen.blit(waiting_surf, waiting_rect)
            list_start_y = waiting_rect.bottom + 30
        else:
            list_start_y = info_rect.bottom + 30

        row_height = 34
        box_margin_x = 140
        for idx, entry in enumerate(entries):
            row_y = list_start_y + idx * row_height
            row_rect = pygame.Rect(80, row_y - 18, SCREEN_WIDTH - 160, row_height)
            if idx == selected_index:
                color = (139, 102, 33) if not awaiting else (180, 120, 40)
                pygame.draw.rect(self.screen, color, row_rect, border_radius=6)
            label = f"{entry['player']} — {entry['action_label']}"
            key_label = entry['key_name'].upper()
            label_surf = self.resources.name_font.render(label, False, (252, 244, 205))
            key_surf = self.resources.name_font.render(key_label, False, (252, 244, 205))
            label_pos = label_surf.get_rect(midleft=(box_margin_x, row_y))
            key_pos = key_surf.get_rect(midright=(SCREEN_WIDTH - box_margin_x, row_y))
            self.screen.blit(label_surf, label_pos)
            self.screen.blit(key_surf, key_pos)

        status_color = (198, 120, 30) if test_mode else self._accent_color
        status_text = f"Test Mode: {'ON' if test_mode else 'OFF'}"
        status_surf = self.resources.name_font.render(status_text, False, status_color)
        status_rect = status_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        self.screen.blit(status_surf, status_rect)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _draw_hearts(self, player: Hero, *, left: bool) -> None:
        res = self.resources
        full_hearts = int(player.health)
        has_half = (player.health - full_hearts) >= 0.5 - 1e-9

        pad = res.heart_padding
        gap = res.heart_gap
        heart_w = res.heart_width

        if left:
            for idx in range(full_hearts):
                self.screen.blit(res.heart, (pad + idx * (heart_w + gap), pad))
            if has_half and player.health < MAX_HEALTH:
                self.screen.blit(res.heart_half, (pad + full_hearts * (heart_w + gap), pad))
        else:
            for idx in range(full_hearts):
                x_pos = SCREEN_WIDTH - pad - (idx + 1) * (heart_w + gap) + gap
                self.screen.blit(res.heart, (x_pos, pad))
            if has_half and player.health < MAX_HEALTH:
                x_pos = SCREEN_WIDTH - pad - (full_hearts + 1) * (heart_w + gap) + gap
                self.screen.blit(res.heart_half, (x_pos, pad))

    def _draw_inventory_icons(self, world: GameWorld) -> None:
        res = self.resources
        pad = res.heart_padding
        heart_height = res.heart.get_height()
        banana_y = pad + heart_height + 8

        if world.players.first.has_banana:
            self.screen.blit(res.banana_icon, (pad, banana_y))

        if world.players.second.has_banana:
            x_pos = SCREEN_WIDTH - pad - res.banana_icon.get_width()
            self.screen.blit(res.banana_icon, (x_pos, banana_y))

    def _draw_hook_icons(self, world: GameWorld) -> None:
        res = self.resources
        pad = res.heart_padding
        banana_w = res.banana_icon.get_width()
        heart_height = res.heart.get_height()
        y_pos = pad + heart_height + 8
        now = pygame.time.get_ticks()

        player1 = world.players.first
        if (not player1.hook_active) and (now >= player1.hook_ready_time):
            self.screen.blit(res.hook_icon, (pad + banana_w + 8, y_pos))

        player2 = world.players.second
        if (not player2.hook_active) and (now >= player2.hook_ready_time):
            x_pos = SCREEN_WIDTH - pad - banana_w - 8 - res.hook_icon.get_width()
            self.screen.blit(res.hook_icon, (x_pos, y_pos))

    def _draw_name_tags(self, world: GameWorld) -> None:
        for player in world.players:
            tag = self.resources.name_font.render(player.name, False, player.name_color)
            tag_rect = tag.get_rect(midbottom=(player.rect.centerx, player.rect.top - 6))
            self.screen.blit(tag, tag_rect)

    def _draw_hooks(self, world: GameWorld) -> None:
        for hook in world.hooks.sprites():
            start = hook.owner.rect.center if hook.owner else hook.rect.center
            end = hook.rope_world_anchor()
            pygame.draw.line(self.screen, (139, 69, 19), start, end, 3)
        world.hooks.draw(self.screen)

    def _draw_aim_targets(self, world: GameWorld) -> None:
        for player in world.players:
            aim_pos = player.get_aim_pos()
            target_rect = self.resources.target.get_rect(center=aim_pos)
            target_img = self.resources.target if player.facing_right else self.resources.target_left
            target_rect = target_img.get_rect(center=aim_pos)
            self.screen.blit(target_img, target_rect)

    def _draw_dotted_line(self, start: tuple[int, int], end: tuple[int, int], color: tuple[int, int, int], width: int, dash_len: int, gap_len: int) -> None:
        """Placeholder kept for future reactivation of dotted drawing."""
        pygame.draw.line(self.screen, color, start, end, width)

    def _draw_debug_boxes(self, world: GameWorld) -> None:
        test_mode = any(getattr(player, "infinite_bananas", False) for player in world.players)
        if not test_mode:
            return

        red = (220, 40, 40)
        for player in world.players:
            pygame.draw.rect(self.screen, red, player.rect, 2)
        for banana in world.banana_pickups.sprites():
            pygame.draw.rect(self.screen, red, banana.rect, 2)
        for banana in world.throwables.sprites():
            pygame.draw.rect(self.screen, red, banana.rect, 2)
        for heart in world.health_pickups.sprites():
            pygame.draw.rect(self.screen, red, heart.rect, 2)
        for platform in world.platforms.sprites():
            pygame.draw.rect(self.screen, red, platform.rect, 2)
        for hook in world.hooks.sprites():
            pygame.draw.rect(self.screen, red, hook.rect, 2)

    def _draw_trajectories(self, world: GameWorld) -> None:
        if not any(getattr(player, "infinite_bananas", False) for player in world.players):
            return

        for player in world.players:
            start = pygame.Vector2(player.rect.center)
            aim_dir = player._aim_direction()

            banana_velocity = aim_dir * 12
            banana_path = self._simulate_trajectory(
                start,
                banana_velocity,
                gravity=PROJECTILE_GRAVITY,
                max_fall=MAX_PROJECTILE_FALL_SPEED,
                gravity_scale=1.0,
            )
            self._plot_path(banana_path, color=(250, 220, 90))

            hook_velocity = aim_dir * (14 * 1.3 * 1.5)
            hook_path = self._simulate_trajectory(
                start,
                hook_velocity,
                gravity=PROJECTILE_GRAVITY,
                max_fall=MAX_PROJECTILE_FALL_SPEED,
                gravity_scale=0.5,
            )
            self._plot_path(hook_path, color=(180, 230, 255))

    def _simulate_trajectory(
        self,
        start: pygame.Vector2,
        velocity: pygame.Vector2,
        *,
        gravity: float,
        gravity_scale: float,
        max_fall: float | None,
        steps: int = 90,
    ) -> list[tuple[int, int]]:
        pos = pygame.Vector2(start)
        vel = pygame.Vector2(velocity)
        points: list[tuple[int, int]] = []

        for _ in range(steps):
            pos += vel
            vel.y += gravity * gravity_scale
            if max_fall is not None and vel.y > max_fall:
                vel.y = max_fall
            points.append((int(pos.x), int(pos.y)))
            if pos.y >= GROUND_Y or pos.x < 0 or pos.x > SCREEN_WIDTH:
                break

        return points

    def _plot_path(self, points: list[tuple[int, int]], color: tuple[int, int, int]) -> None:
        if len(points) < 2:
            return
        for pt in points:
            pygame.draw.circle(self.screen, color, pt, 2)


__all__ = ["GameSceneRenderer"]
