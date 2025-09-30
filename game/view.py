"""Rendering helpers for SlingDuel game scenes."""
from __future__ import annotations

import pygame

from constants import COLOR_BG, MAX_HEALTH, SCREEN_WIDTH
from sprites.hero import Hero

from .resources import GameResources
from .world import GameWorld


class GameSceneRenderer:
    """Responsible for all drawing in the active and idle states."""

    def __init__(self, screen: pygame.Surface, resources: GameResources) -> None:
        self.screen = screen
        self.resources = resources

        self._title_color = (111, 196, 169)
        self._title_surf = resources.game_font.render("Slingduel", False, self._title_color)
        self._title_rect = self._title_surf.get_rect(center=(SCREEN_WIDTH // 2, 130))
        self._prompt_center = (SCREEN_WIDTH // 2, 320)
        self._result_center = (SCREEN_WIDTH // 2, 260)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def draw_start_screen(self, winner: Hero | None = None, draw: bool = False) -> None:
        self.screen.fill(COLOR_BG)
        self.screen.blit(self._title_surf, self._title_rect)

        prompt_text = "Press SPACE to START"
        if winner is not None or draw:
            prompt_text = "Press SPACE to PLAY AGAIN"
        prompt_surf = self.resources.game_font.render(prompt_text, False, self._title_color)
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
            pygame.draw.line(self.screen, (255, 255, 255), player.rect.center, aim_pos, 3)
            target_rect = self.resources.target.get_rect(center=aim_pos)
            self.screen.blit(self.resources.target, target_rect)


__all__ = ["GameSceneRenderer"]
