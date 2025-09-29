# main.py
import pygame
from random import randint, choice
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_BG, GROUND_Y
from assets import (
    get_background, get_font, get_target,
    get_heart, get_heart_half, get_banana_image, get_floor_images
)
from sprites import Hero
from sprites.banana import BananaPickup, Banana   # <-- Banana imported for step-on check
from sprites.platform import Platform

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("SlingDuel")
clock = pygame.time.Clock()

game_font = get_font(size=100)

# Backgrounds
sky_surf, ground_surf = get_background()

# Target + Heart
target_surf = get_target()
heart_surf = get_heart()
heart_half_surf = get_heart_half()
banana_icon = get_banana_image()
heart_w = heart_surf.get_width()
pad, gap = 20, 10

# UI texts
game_name = game_font.render("Slingduel", False, (111, 196, 169))
game_name_rect = game_name.get_rect(center=(SCREEN_WIDTH // 2, 130))
game_message = game_font.render("Press SPACE to START", False, (111, 196, 169))
game_message_rect = game_message.get_rect(center=(SCREEN_WIDTH // 2, 320))

# Players (P1: jump=C, sling=R; P2: jump=N, sling=U)
p1_controls = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
                   throw=pygame.K_f, sling=pygame.K_r, jump=pygame.K_c)
p2_controls = dict(left=pygame.K_j, right=pygame.K_l, up=pygame.K_i, down=pygame.K_k,
                   throw=pygame.K_h, sling=pygame.K_u, jump=pygame.K_n)

player1 = Hero(controls=p1_controls, start_x=200)
player2 = Hero(controls=p2_controls, start_x=SCREEN_WIDTH - 200)
players = pygame.sprite.Group(player1, player2)

# Groups
throwables = pygame.sprite.Group()
hooks = pygame.sprite.Group()
banana_pickups = pygame.sprite.Group()
platforms = pygame.sprite.Group()

# Banana spawn timer (every 5s)
SPAWN_EVENT = pygame.USEREVENT + 10
pygame.time.set_timer(SPAWN_EVENT, 5000)

def spawn_banana_if_needed():
    if len(banana_pickups) >= 4:
        return
    x = randint(60, SCREEN_WIDTH - 60)
    banana_pickups.add(BananaPickup(x))

def spawn_platforms():
    platforms.empty()
    floor_imgs = get_floor_images()
    # spawn 8 floating platforms
    for _ in range(8):
        img = choice(floor_imgs)
        x = randint(120, SCREEN_WIDTH - 120)
        y = randint(120, GROUND_Y - 120)
        platforms.add(Platform(img, midtop=(x, y)))

def draw_hearts(player, left=True):
    """Draw full and half hearts for the given player."""
    full_hearts = int(player.health)
    has_half = abs(player.health - full_hearts) >= 0.5

    if left:
        # full hearts left→right
        for i in range(full_hearts):
            screen.blit(heart_surf, (pad + i * (heart_w + gap), pad))
        if has_half:
            screen.blit(heart_half_surf, (pad + full_hearts * (heart_w + gap), pad))
    else:
        # full hearts right→left
        for i in range(full_hearts):
            x = SCREEN_WIDTH - pad - (i + 1) * (heart_w + gap) + gap
            screen.blit(heart_surf, (x, pad))
        if has_half:
            x = SCREEN_WIDTH - pad - (full_hearts + 1) * (heart_w + gap) + gap
            screen.blit(heart_half_surf, (x, pad))

def reset_round_state():
    """Reset players and world for a new round."""
    for p in players.sprites():
        p.reset()
    banana_pickups.empty()
    throwables.empty()
    hooks.empty()
    spawn_platforms()

game_active = False

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit

        if not game_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                reset_round_state()
        else:
            if event.type == SPAWN_EVENT:
                spawn_banana_if_needed()

    if game_active:
        # Update
        players.update(throwables, hooks)
        throwables.update(platforms)   # bananas get platforms for landing logic
        hooks.update(platforms)
        banana_pickups.update()

        # Players collect bananas (max 1 each)
        for p in (player1, player2):
            if not p.has_banana:
                hit = pygame.sprite.spritecollideany(p, banana_pickups)
                if hit:
                    p.has_banana = True
                    hit.kill()

        # Projectile → player hits (direct 1.0 damage)
        for proj in throwables.sprites():
            hit = pygame.sprite.spritecollideany(proj, players)
            if hit and getattr(proj, "can_hit", lambda *_: True)(hit):
                proj.on_hit(hit)
                if hasattr(proj, "damage"):
                    hit.take_damage(proj.damage)

        # --- NEW: step-on damage for persistent splats (0.5 dmg once) ---
        for b in [s for s in throwables.sprites() if isinstance(s, Banana) and s.state == "splatted_persist"]:
            for p in (player1, player2):
                if b.rect.colliderect(p.rect):
                    b.stepped_on_by(p)  # applies 0.5 dmg once and starts 3s despawn
        # -----------------------------------------------------------------

        # Game over check — bounce to start screen if anyone reaches 0
        if player1.is_dead or player2.is_dead:
            game_active = False

        # Draw
        screen.blit(sky_surf, (0, 0))
        screen.blit(ground_surf, (0, 0))

        platforms.draw(screen)
        banana_pickups.draw(screen)

        # Hearts + banana icons
        draw_hearts(player1, left=True)
        draw_hearts(player2, left=False)

        if player1.has_banana:
            screen.blit(banana_icon, (pad, pad + heart_surf.get_height() + 8))
        if player2.has_banana:
            x = SCREEN_WIDTH - pad - banana_icon.get_width()
            screen.blit(banana_icon, (x, pad + heart_surf.get_height() + 8))

        # Players & projectiles
        players.draw(screen)
        throwables.draw(screen)

        # Hooks: rope then hook sprite
        for h in hooks.sprites():
            if not isinstance(h.owner, Hero):
                continue
            start = h.owner.rect.center
            end = h.rope_world_anchor()
            pygame.draw.line(screen, (139, 69, 19), start, end, 3)
        hooks.draw(screen)

        # Aim targets (always visible)
        for p in (player1, player2):
            aim_pos = p.get_aim_pos()
            pygame.draw.line(screen, (255, 255, 255), p.rect.center, aim_pos, 3)
            screen.blit(target_surf, target_surf.get_rect(center=aim_pos))

    else:
        # Start screen
        screen.fill(COLOR_BG)
        screen.blit(game_name, game_name_rect)
        screen.blit(game_message, game_message_rect)

    pygame.display.update()
    clock.tick(FPS)
