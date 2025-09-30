# main.py
import pygame
from random import randint, choice
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_BG, GROUND_Y, MAX_HEALTH
from assets import (
    get_background, get_font, get_target,
    get_heart, get_heart_half, get_banana_image, get_floor_images, get_hook_image
)
from sprites import Hero
from sprites.banana import BananaPickup, Banana
from sprites.platform import Platform
from sprites.health import HealthPickup
from keymap import load_controls  # existing

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("SlingDuel")
clock = pygame.time.Clock()

game_font = get_font(size=100)
name_font = get_font(size=36)

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

# Players (loaded from keys.json)
p1_controls, p2_controls = load_controls()
player1 = Hero(controls=p1_controls, start_x=200, name="Red", name_color=(220, 60, 60))
player2 = Hero(controls=p2_controls, start_x=SCREEN_WIDTH - 200, name="Blue", name_color=(80, 140, 255))
players = pygame.sprite.Group(player1, player2)

# Groups
throwables = pygame.sprite.Group()       # Banana projectiles (and splats)
hooks = pygame.sprite.Group()            # Active grapples
banana_pickups = pygame.sprite.Group()   # Ground/platform bananas to pick
health_pickups = pygame.sprite.Group()   # Hearts to pick
platforms = pygame.sprite.Group()

# Timers
SPAWN_EVENT       = pygame.USEREVENT + 10   # bananas every 5s
REGEN_EVENT       = pygame.USEREVENT + 11   # +0.5 HP every 30s
HEART_SPAWN_EVENT = pygame.USEREVENT + 12   # heart pickup every 60s

pygame.time.set_timer(SPAWN_EVENT, 5000)
pygame.time.set_timer(REGEN_EVENT, 30000)
pygame.time.set_timer(HEART_SPAWN_EVENT, 60000)

# ---------- spawning helpers ----------

def _non_overlapping_rect(pos_rect: pygame.Rect, groups: list[pygame.sprite.Group]) -> bool:
    """Return True if pos_rect doesn't overlap any sprite rect in given groups."""
    for g in groups:
        for s in g.sprites():
            if pos_rect.colliderect(s.rect):
                return False
    return True

def spawn_platforms():
    """Spawn ~8 platforms on an implicit 5x5 grid to avoid stacking/overlap."""
    platforms.empty()
    floor_imgs = get_floor_images()

    cols, rows = 5, 5
    cell_w = SCREEN_WIDTH // (cols + 1)
    cell_h = (GROUND_Y - 120) // (rows + 1)  # leave headroom and ground margin
    candidates = []
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            cx = c * cell_w
            cy = r * cell_h   # midtop y
            candidates.append((cx, cy))
    # pick 8 spaced cells
    choices = []
    while candidates and len(choices) < 8:
        idx = randint(0, len(candidates) - 1)
        choices.append(candidates.pop(idx))

    for (cx, cy) in choices:
        img = choice(floor_imgs)
        p = Platform(img, midtop=(cx, cy))
        platforms.add(p)

def _random_x_on_platform(plat: Platform) -> int:
    left = plat.rect.left + 20
    right = plat.rect.right - 20
    return randint(left, right)

def _spawn_banana_on_ground() -> bool:
    """Try spawn exactly 1 pickup on ground (if none present)."""
    if sum(1 for b in banana_pickups if b.rect.bottom == GROUND_Y) >= 1:
        return False
    x = randint(60, SCREEN_WIDTH - 60)
    temp = BananaPickup(x, y_bottom=GROUND_Y)
    if _non_overlapping_rect(temp.rect, [banana_pickups, health_pickups]):
        banana_pickups.add(temp)
        return True
    return False

def _spawn_banana_on_platform() -> bool:
    """Spawn a pickup banana on a random platform top, avoiding overlap."""
    plats = platforms.sprites()
    if not plats:
        return False
    for _ in range(12):  # a few tries
        plat = choice(plats)
        x = _random_x_on_platform(plat)
        temp = BananaPickup(x, y_bottom=plat.stand_rect.top)
        if _non_overlapping_rect(temp.rect, [banana_pickups, health_pickups]):
            banana_pickups.add(temp)
            return True
    return False

def spawn_banana_if_needed():
    """Maintain up to 4 pickup bananas; at most 1 on ground; others on platforms; no overlap."""
    if len(banana_pickups) >= 4:
        return
    # First ensure 1 ground banana if possible
    spawned = _spawn_banana_on_ground()
    # Then fill remaining slots with platform bananas
    while len(banana_pickups) < 4:
        if not _spawn_banana_on_platform():
            break

def spawn_heart_if_needed():
    """Spawn a single heart pickup on a random platform (max 1 on map)."""
    if len(health_pickups) >= 1:
        return
    if not platforms:
        return
    for _ in range(20):
        plat = choice(platforms.sprites())
        x = _random_x_on_platform(plat)
        temp = HealthPickup(x, y_bottom=plat.stand_rect.top)
        if _non_overlapping_rect(temp.rect, [banana_pickups, health_pickups]):
            health_pickups.add(temp)
            return

# --------- hearts drawing ---------

def draw_hearts(player, left=True):
    """Draw full and half hearts for the given player (supports .5 steps)."""
    full_hearts = int(player.health)
    has_half = (player.health - full_hearts) >= 0.5 - 1e-9  # tolerate FP error

    if left:
        # full hearts left→right
        for i in range(full_hearts):
            screen.blit(heart_surf, (pad + i * (heart_w + gap), pad))
        if has_half and player.health < MAX_HEALTH:
            screen.blit(heart_half_surf, (pad + full_hearts * (heart_w + gap), pad))
    else:
        # full hearts right→left
        for i in range(full_hearts):
            x = SCREEN_WIDTH - pad - (i + 1) * (heart_w + gap) + gap
            screen.blit(heart_surf, (x, pad))
        if has_half and player.health < MAX_HEALTH:
            x = SCREEN_WIDTH - pad - (full_hearts + 1) * (heart_w + gap) + gap
            screen.blit(heart_half_surf, (x, pad))

def reset_round_state():
    """Reset players and world for a new round."""
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

        # Hot-reload controls with F9
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F9:
            p1_controls, p2_controls = load_controls()
            player1.controls = p1_controls
            player2.controls = p2_controls

        if not game_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                reset_round_state()
        else:
            if event.type == SPAWN_EVENT:
                spawn_banana_if_needed()
            if event.type == HEART_SPAWN_EVENT:
                spawn_heart_if_needed()
            if event.type == REGEN_EVENT:
                for p in (player1, player2):
                    p.health = min(MAX_HEALTH, p.health + 0.5)

    if game_active:
        # Update
        players.update(throwables, hooks, platforms)     # <- pass platforms
        throwables.update(platforms)                     # bananas get platforms
        hooks.update(platforms)                          # hook sees platforms
        banana_pickups.update()
        health_pickups.update()

        # Pickups: bananas
        for p in (player1, player2):
            if not p.has_banana:
                hit = pygame.sprite.spritecollideany(p, banana_pickups)
                if hit:
                    p.has_banana = True
                    hit.kill()

        # Pickups: health
        for p in (player1, player2):
            hit = pygame.sprite.spritecollideany(p, health_pickups)
            if hit:
                p.health = min(MAX_HEALTH, p.health + 0.5)
                hit.kill()

        # Projectile → player hits (direct damage handled inside Banana.on_hit)
        for proj in throwables.sprites():
            hit = pygame.sprite.spritecollideany(proj, players)
            if hit and getattr(proj, "can_hit", lambda *_: True)(hit):
                proj.on_hit(hit)

        # Step-on damage for persistent splats (0.5 dmg once)
        for b in [s for s in throwables.sprites()
                  if isinstance(s, Banana) and s.state == "splatted_persist"]:
            # generous hitbox
            b_hitbox = b.rect.inflate(10, 6)
            for p in (player1, player2):
                if b_hitbox.colliderect(p.rect):
                    b.stepped_on_by(p)

        # Limit ground splats to 2; remove oldest if exceeded
        ground_splats = [b for b in throwables.sprites()
                         if isinstance(b, Banana)
                         and b.state == "splatted_persist"
                         and b.rect.bottom == GROUND_Y]
        if len(ground_splats) > 2:
            ground_splats.sort(key=lambda spr: spr.splat_time or 0)
            for old in ground_splats[:-2]:
                old.kill()

        # Game over check
        if player1.is_dead or player2.is_dead:
            game_active = False

        # Draw
        screen.blit(sky_surf, (0, 0))
        screen.blit(ground_surf, (0, 0))

        platforms.draw(screen)
        banana_pickups.draw(screen)
        health_pickups.draw(screen)

        # Hearts + inventory icons
        draw_hearts(player1, left=True)
        draw_hearts(player2, left=False)

        if player1.has_banana:
            screen.blit(banana_icon, (pad, pad + heart_surf.get_height() + 8))
        if player2.has_banana:
            x = SCREEN_WIDTH - pad - banana_icon.get_width()
            screen.blit(banana_icon, (x, pad + heart_surf.get_height() + 8))

        # Hook icons (show when hook is READY)
        now = pygame.time.get_ticks()
        if (not player1.hook_active) and (now >= player1.hook_ready_time):
            screen.blit(hook_icon, (pad + banana_icon.get_width() + 8,
                                    pad + heart_surf.get_height() + 8))
        if (not player2.hook_active) and (now >= player2.hook_ready_time):
            x = SCREEN_WIDTH - pad - banana_icon.get_width() - 8 - hook_icon.get_width()
            y = pad + heart_surf.get_height() + 8
            screen.blit(hook_icon, (x, y))

        # Players & projectiles
        players.draw(screen)
        throwables.draw(screen)

        # Name tags
        for p in (player1, player2):
            tag = name_font.render(p.name, False, p.name_color)
            tr = tag.get_rect(midbottom=(p.rect.centerx, p.rect.top - 6))
            screen.blit(tag, tr)

        # Hooks: rope then hook sprite
        for h in hooks.sprites():
            start = h.owner.rect.center if h.owner else h.rect.center
            end = h.rope_world_anchor()
            pygame.draw.line(screen, (139, 69, 19), start, end, 3)
        hooks.draw(screen)

        # Aim targets
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
