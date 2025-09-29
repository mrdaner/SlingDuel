# main.py
import pygame
from random import randint, choice, sample, random
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_BG, GROUND_Y
from assets import (
    get_background, get_font, get_target,
    get_heart, get_heart_half, get_banana_image, get_floor_images, get_hook_image
)
from sprites import Hero
from sprites.banana import BananaPickup, Banana
from sprites.platform import Platform
from sprites.health import HealthPickup   # <-- NEW

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("SlingDuel")
clock = pygame.time.Clock()

game_font = get_font(size=100)

# Backgrounds
sky_surf, ground_surf = get_background()

# UI assets
target_surf = get_target()
heart_surf = get_heart()
heart_half_surf = get_heart_half()
banana_icon = get_banana_image()
hook_icon = get_hook_image()

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
health_pickups = pygame.sprite.Group()    # <-- NEW
platforms = pygame.sprite.Group()

# Timers
SPAWN_EVENT = pygame.USEREVENT + 10          # bananas (every 5s)
HEALTH_EVENT = pygame.USEREVENT + 11         # hearts (every 60s)
pygame.time.set_timer(SPAWN_EVENT, 5000)
pygame.time.set_timer(HEALTH_EVENT, 60000)   # once per minute

last_winner_text = ""

def draw_hearts(player, left=True):
    full_hearts = int(player.health)
    has_half = (player.health - full_hearts) >= 0.5 - 1e-6

    if left:
        for i in range(full_hearts):
            screen.blit(heart_surf, (pad + i * (heart_w + gap), pad))
        if has_half:
            screen.blit(heart_half_surf, (pad + full_hearts * (heart_w + gap), pad))
    else:
        for i in range(full_hearts):
            x = SCREEN_WIDTH - pad - (i + 1) * (heart_w + gap) + gap
            screen.blit(heart_surf, (x, pad))
        if has_half:
            x = SCREEN_WIDTH - pad - (full_hearts + 1) * (heart_w + gap) + gap
            screen.blit(heart_half_surf, (x, pad))

def spawn_platforms():
    """Spawn 8 platforms using a 5x5 logical grid region to avoid stacking."""
    platforms.empty()
    floor_imgs = get_floor_images()

    margin_x = 120
    margin_top = 80
    margin_bottom = 140
    region_left = margin_x
    region_right = SCREEN_WIDTH - margin_x
    region_top = margin_top
    region_bottom = GROUND_Y - margin_bottom

    cols, rows = 5, 5
    cell_w = (region_right - region_left) / cols
    cell_h = (region_bottom - region_top) / rows

    all_cells = [(c, r) for c in range(cols) for r in range(rows)]
    chosen = sample(all_cells, 8)

    for (c, r) in chosen:
        img = floor_imgs[(c + r) % len(floor_imgs)]
        cx = int(region_left + c * cell_w + cell_w / 2)
        cy = int(region_top + r * cell_h + cell_h / 2)
        platforms.add(Platform(img, midtop=(cx, cy)))

def spawn_banana_if_needed():
    """
    Keep at most 4 bananas total.
    - Max 1 banana on base ground.
    - With weighting: if ground slot is free, 75% chance to spawn on ground (≈3× more likely).
    - Otherwise spawn on a random platform (fallback to ground if none).
    """
    if len(banana_pickups) >= 4:
        return

    ground_count = sum(1 for b in banana_pickups if b.rect.bottom == GROUND_Y)

    if ground_count < 1 and random() < 0.75:
        x = randint(60, SCREEN_WIDTH - 60)
        banana_pickups.add(BananaPickup(x, GROUND_Y))
        return

    if len(platforms) > 0:
        plat = list(platforms)[randint(0, len(platforms) - 1)]
        min_x = plat.rect.left + 10
        max_x = plat.rect.right - 10
        x = randint(min_x, max_x) if min_x <= max_x else plat.rect.centerx
        banana_pickups.add(BananaPickup(x, plat.rect.top))
    else:
        x = randint(60, SCREEN_WIDTH - 60)
        banana_pickups.add(BananaPickup(x, GROUND_Y))

def spawn_health_if_needed():
    """Spawn ONE heart on a random platform (max 1 on screen)."""
    if len(health_pickups) >= 1:
        return
    if len(platforms) == 0:
        return
    plat = list(platforms)[randint(0, len(platforms) - 1)]
    min_x = plat.rect.left + 10
    max_x = plat.rect.right - 10
    x = randint(min_x, max_x) if min_x <= max_x else plat.rect.centerx
    health_pickups.add(HealthPickup(x, plat.rect.top))

def reset_round_state():
    for p in players.sprites():
        p.reset()
    banana_pickups.empty()
    health_pickups.empty()
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
                last_winner_text = ""
                reset_round_state()
        else:
            if event.type == SPAWN_EVENT:
                spawn_banana_if_needed()
            if event.type == HEALTH_EVENT:
                spawn_health_if_needed()

    if game_active:
        # Update
        players.update(throwables, hooks)
        throwables.update(platforms)   # bananas see platforms for landing logic
        hooks.update(platforms)
        banana_pickups.update()
        health_pickups.update()

        # Banana pickups
        for p in (player1, player2):
            if not p.has_banana:
                hit = pygame.sprite.spritecollideany(p, banana_pickups)
                if hit:
                    p.has_banana = True
                    hit.kill()

        # Health pickup (+1, capped to max_health)
        for p in (player1, player2):
            hp = pygame.sprite.spritecollideany(p, health_pickups)
            if hp:
                p.health = min(p.max_health, p.health + 1.0)
                hp.kill()

        # Projectile → player direct hits
        for proj in throwables.sprites():
            hit = pygame.sprite.spritecollideany(proj, players)
            if hit and getattr(proj, "can_hit", lambda *_: True)(hit):
                proj.on_hit(hit)

        # Step-on damage for persistent splats (0.5 once)
        for b in [s for s in throwables.sprites()
                  if isinstance(s, Banana) and s.state == "splatted_persist"]:
            b_hitbox = b.rect.inflate(10, 6)
            for p in (player1, player2):
                if b_hitbox.colliderect(p.rect):
                    b.stepped_on_by(p)

        # Win check
        if player1.is_dead or player2.is_dead:
            game_active = False
            if player1.is_dead and player2.is_dead:
                last_winner_text = "Draw!"
            elif player2.is_dead:
                last_winner_text = "Player 1 Wins!"
            else:
                last_winner_text = "Player 2 Wins!"

        # Draw
        screen.blit(sky_surf, (0, 0))
        screen.blit(ground_surf, (0, 0))

        platforms.draw(screen)
        banana_pickups.draw(screen)
        health_pickups.draw(screen)   # <-- show hearts on platforms

        # Hearts + inventory icons
        draw_hearts(player1, left=True)
        draw_hearts(player2, left=False)

        if player1.has_banana:
            screen.blit(banana_icon, (pad, pad + heart_surf.get_height() + 8))
        if player2.has_banana:
            x = SCREEN_WIDTH - pad - banana_icon.get_width()
            screen.blit(banana_icon, (x, pad + heart_surf.get_height() + 8))

        now = pygame.time.get_ticks()
        if (not player1.hook_active) and (now >= player1.hook_ready_time):
            screen.blit(hook_icon, (pad + banana_icon.get_width() + 8,
                                    pad + heart_surf.get_height() + 8))
        if (not player2.hook_active) and (now >= player2.hook_ready_time):
            x = SCREEN_WIDTH - pad - banana_icon.get_width() - 8 - hook_icon.get_width()
            y = pad + heart_surf.get_height() + 8
            screen.blit(hook_icon, (x, y))

        players.draw(screen)
        throwables.draw(screen)

        for h in hooks.sprites():
            if isinstance(h.owner, Hero):
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
        screen.fill(COLOR_BG)
        screen.blit(game_name, game_name_rect)
        if last_winner_text:
            winner_text = game_font.render(last_winner_text, False, (255, 255, 255))
            screen.blit(winner_text, winner_text.get_rect(center=(SCREEN_WIDTH // 2, 240)))
        screen.blit(game_message, game_message_rect)

    pygame.display.update()
    clock.tick(FPS)
