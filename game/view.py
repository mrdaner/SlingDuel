"""Rendering helpers for SlingDuel game scenes (HUD, sprites, debug overlays)."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from constants import (
    COLOR_BG,
    COLOR_TITLE,
    COLOR_ACCENT,
    COLOR_MUTED,
    COLOR_CALLOUT,
    COLOR_WARNING,
    OVERLAY_RGBA,
    MAX_HEALTH,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GROUND_Y,
    PROJECTILE_GRAVITY,
    MAX_PROJECTILE_FALL_SPEED,
    BANANA_THROW_SPEED,
    HOOK_THROW_BASE_SPEED,
    HOOK_THROW_SPEED_MULTIPLIER,
)
from sprites.hero import Hero
from sprites.banana import Banana

from .resources import GameResources
from .trajectory import simulate_trajectory
from .world import GameWorld

if TYPE_CHECKING:
    from .game import KeymapEntry


class GameSceneRenderer:
    """Responsible for all drawing in the active and idle states."""

    def __init__(self, screen: pygame.Surface, resources: GameResources) -> None:
        self.screen = screen
        self.resources = resources

        self._title_color = COLOR_TITLE
        self._accent_color = COLOR_ACCENT
        self._muted_color = COLOR_MUTED
        self._callout_color = COLOR_CALLOUT
        self._warning_color = COLOR_WARNING
        self._overlay_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self._overlay_surface.fill(OVERLAY_RGBA)
        self._title_text = "SlingDuel"
        title_measure = resources.game_font.render(self._title_text, False, self._title_color)
        self._title_rect = title_measure.get_rect(center=(SCREEN_WIDTH // 2, 130))
        self._prompt_center = (SCREEN_WIDTH // 2, 320)
        self._result_center = (SCREEN_WIDTH // 2, 260)
        self._restart_prompt_visible_at = 0
        self._start_bg_color = (32, 120, 70)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def draw_start_backdrop(self) -> None:
        self.screen.fill(self._start_bg_color)

    def draw_start_screen(
        self,
        winner: Hero | None = None,
        draw: bool = False,
        *,
        test_mode: bool = False,
        dim: bool = False,
    ) -> None:
        self.draw_start_backdrop()
        if dim:
            self.screen.blit(self._overlay_surface, (0, 0))
        self._draw_shadowed_text(
            self._title_text,
            font=self.resources.game_font,
            color=self._title_color,
            center=self._title_rect.center,
            max_width=SCREEN_WIDTH - 80,
        )

        prompt_text = "Press SPACE to START"
        show_prompt = True
        if winner is not None or draw:
            show_prompt = pygame.time.get_ticks() >= self._restart_prompt_visible_at
            prompt_text = "Press SPACE to PLAY AGAIN"
        if show_prompt:
            self._draw_shadowed_text(
                prompt_text,
                font=self.resources.game_font,
                color=self._accent_color,
                center=self._prompt_center,
                max_width=SCREEN_WIDTH - 80,
            )

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

        status_color = self._warning_color if test_mode else self._accent_color
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

    def set_restart_prompt_visible_at(self, timestamp_ms: int) -> None:
        self._restart_prompt_visible_at = timestamp_ms

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
        self._draw_hit_stars(world)
        world.throwables.draw(self.screen)
        self._draw_name_tags(world)
        self._draw_hooks(world)
        self._draw_aim_targets(world)
        self._draw_trajectories(world)
        self._draw_debug_boxes(world)

    def draw_pause_overlay(self, *, test_mode: bool) -> None:
        self.screen.blit(self._overlay_surface, (0, 0))

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

    def draw_self_hit_overlay(
        self,
        message: str,
        *,
        prompt_visible: bool = True,
        focus_hero: Hero | None = None,
    ) -> None:
        self.screen.blit(self._overlay_surface, (0, 0))

        title_text = self.resources.self_hit_banner
        title = self.resources.game_font.render(title_text, False, self._title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 140))
        self.screen.blit(title, title_rect)

        text_bottom = self._draw_shadowed_text(
            message,
            font=self.resources.game_font,
            color=self._callout_color,
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10),
            max_width=SCREEN_WIDTH - 160,
        )

        if prompt_visible:
            prompt = "Press any key to continue"
            prompt_surf = self.resources.name_font.render(prompt, False, self._muted_color)
            prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, text_bottom + 50))
            self.screen.blit(prompt_surf, prompt_rect)

    def _draw_shadowed_text(
        self,
        text: str,
        *,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        center: tuple[int, int],
        max_width: int,
        shadow_offset: tuple[int, int] = (4, 4),
    ) -> int:
        """Render multiline text with a drop shadow, returning the final bottom y."""
        words = text.split()
        if not words:
            return center[1]

        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}" if current else word
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        line_height = font.get_linesize()
        total_height = line_height * len(lines)
        start_y = center[1] - total_height // 2 + line_height // 2
        shadow_dx, shadow_dy = shadow_offset

        for idx, line in enumerate(lines):
            line_center_y = start_y + idx * line_height
            shadow = font.render(line, False, (20, 20, 20))
            main = font.render(line, False, color)
            shadow_rect = shadow.get_rect(center=(center[0] + shadow_dx, line_center_y + shadow_dy))
            main_rect = main.get_rect(center=(center[0], line_center_y))
            self.screen.blit(shadow, shadow_rect)
            self.screen.blit(main, main_rect)

        return start_y + (len(lines) - 1) * line_height + line_height // 2

    def draw_keymap_menu(
        self,
        entries: list[KeymapEntry],
        selected_index: int,
        awaiting: bool,
        *,
        test_mode: bool,
        overlay: bool,
    ) -> None:
        if overlay:
            self.screen.blit(self._overlay_surface, (0, 0))

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
            waiting_text = f"Press new key for {entry.player_label} - {entry.action_label}"
            waiting_surf = self.resources.name_font.render(waiting_text, False, self._callout_color)
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
                color = self._accent_color if not awaiting else self._callout_color
                pygame.draw.rect(self.screen, color, row_rect, border_radius=6)
            label = f"{entry.player_label} — {entry.action_label}"
            key_label = entry.key_name.upper()
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
        if not world.is_test_mode:
            return

        red = (220, 40, 40)
        yellow = (240, 200, 30)
        standable_color = (120, 200, 120)
        for player in world.players:
            pygame.draw.rect(self.screen, red, player.rect, 2)
            pygame.draw.rect(self.screen, yellow, player.banana_hitbox(), 2)
        for banana in world.banana_pickups.sprites():
            pygame.draw.rect(self.screen, red, banana.rect, 2)
        for banana in world.throwables.sprites():
            pygame.draw.rect(self.screen, red, banana.rect, 2)
            if isinstance(banana, Banana) and banana.state == "splatted_persist":
                pygame.draw.rect(self.screen, yellow, banana.rect.inflate(10, 6), 2)
            elif isinstance(banana, Banana):
                pygame.draw.rect(self.screen, yellow, banana.rect, 2)
        for heart in world.health_pickups.sprites():
            pygame.draw.rect(self.screen, red, heart.rect, 2)
        for platform in world.platforms.sprites():
            pygame.draw.rect(self.screen, red, platform.rect, 2)
            pygame.draw.rect(self.screen, standable_color, platform.stand_rect, 2)
        ground_rect = pygame.Rect(0, GROUND_Y - 4, SCREEN_WIDTH, 8)
        pygame.draw.rect(self.screen, standable_color, ground_rect, 2)
        for hook in world.hooks.sprites():
            pygame.draw.rect(self.screen, red, hook.rect, 2)
        pickup_color = (255, 180, 100)
        for hero in world.players:
            pygame.draw.rect(self.screen, pickup_color, hero.pickup_hitbox(), 2)

    def _draw_hit_stars(self, world: GameWorld) -> None:
        frames = getattr(self.resources, "hit_stars_frames", ())
        if not frames:
            return
        now = pygame.time.get_ticks()
        for hero in world.players:
            start = getattr(hero, "hit_stars_start", 0)
            end = getattr(hero, "hit_stars_until", 0)
            if end <= now:
                continue
            duration = max(1, end - start)
            elapsed = max(0, now - start)
            slice_length = duration / len(frames)
            index = min(len(frames) - 1, int(elapsed / slice_length))
            sprite = frames[index]
            rect = sprite.get_rect(midtop=(hero.rect.centerx + 6, hero.rect.top + 3))
            self.screen.blit(sprite, rect)

    def _draw_trajectories(self, world: GameWorld) -> None:
        if not world.is_test_mode:
            return

        for player in world.players:
            start = pygame.Vector2(player.rect.center)
            aim_dir = player._aim_direction()

            launch_vec = pygame.Vector2(aim_dir.x, aim_dir.y - 0.35)
            if launch_vec.length_squared() == 0:
                launch_vec = aim_dir
            else:
                launch_vec = launch_vec.normalize()

            banana_velocity = launch_vec * BANANA_THROW_SPEED
            banana_velocity.y += PROJECTILE_GRAVITY
            banana_path = simulate_trajectory(
                start,
                banana_velocity,
                gravity=PROJECTILE_GRAVITY,
                gravity_scale=1.0,
                max_fall=MAX_PROJECTILE_FALL_SPEED,
                steps=90,
                ground_y=GROUND_Y,
                screen_width=SCREEN_WIDTH,
            )
            self._plot_path(banana_path, color=(250, 220, 90))

            hook_velocity = aim_dir * (HOOK_THROW_BASE_SPEED * HOOK_THROW_SPEED_MULTIPLIER)
            hook_path = simulate_trajectory(
                start,
                hook_velocity,
                gravity=PROJECTILE_GRAVITY,
                gravity_scale=0.5,
                max_fall=MAX_PROJECTILE_FALL_SPEED,
                steps=90,
                ground_y=GROUND_Y,
                screen_width=SCREEN_WIDTH,
            )
            self._plot_path(hook_path, color=(180, 230, 255))

    def _plot_path(self, points: list[tuple[int, int]], color: tuple[int, int, int]) -> None:
        if len(points) < 2:
            return
        for pt in points:
            pygame.draw.circle(self.screen, color, pt, 2)


__all__ = ["GameSceneRenderer"]
