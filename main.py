import pygame
from random import choice
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_BG, OBSTACLE_TIMER_MS, OBSTACLE_EVENT
from assets import get_background, get_font, get_target, get_heart
from sprites import Hero, Obstacle

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("SlingDuel")
clock = pygame.time.Clock()

game_font = get_font(size=100)

# Backgrounds
sky_surf, ground_surf = get_background()

# Target
target_surf = get_target()
target_rect = target_surf.get_rect()

#Health
heart_surf = get_heart()


# UI
game_name = game_font.render("Slingduel", False, (111, 196, 169))
game_name_rect = game_name.get_rect(center=(SCREEN_WIDTH // 2, 130))

game_message = game_font.render("Press SPACE to START", False, (111, 196, 169))
game_message_rect = game_message.get_rect(center=(SCREEN_WIDTH // 2, 320))

# Groups
hero = pygame.sprite.GroupSingle(Hero())
obstacles = pygame.sprite.Group()

# Timers
OBSTACLE_EVENT_ID = pygame.USEREVENT + OBSTACLE_EVENT
pygame.time.set_timer(OBSTACLE_EVENT_ID, OBSTACLE_TIMER_MS)

game_active = False
start_time = 0
score = 0

def display_score():
    curr = int(pygame.time.get_ticks() / 1000) - start_time
    text = game_font.render(f"Score: {curr}", False, (64, 64, 64))
    rect = text.get_rect(center=(SCREEN_WIDTH // 2, 50))
    screen.blit(text, rect)
    return curr

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit

        if not game_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                obstacles.empty()
                hero.sprite.reset()
                start_time = int(pygame.time.get_ticks() / 1000)

        else:
            if event.type == OBSTACLE_EVENT_ID:
                kind = choice(["banana", "banana", "boss"])
                obstacles.add(Obstacle(kind))

    if game_active:
        # Update
        hero.update()
        obstacles.update()
        for o in obstacles.sprites():
            o.destroy()

        # Draw
        screen.blit(sky_surf, (0, 0))
        screen.blit(ground_surf, (0, 0))
        score = display_score()

        for i in range(5):  # 5 hearts
            x = 20 + i * (heart_surf.get_width() + 10)   # spacing of 10px
            y = 20
            screen.blit(heart_surf, (x, y))


        hero.draw(screen)

        mouse_or_aim = hero.sprite.get_aim_pos()
        pygame.draw.line(screen, (255,255,255), hero.sprite.rect.center, mouse_or_aim, 3)
        tr = target_surf.get_rect(center=mouse_or_aim)
        screen.blit(target_surf, tr)

        obstacles.draw(screen)

        # Collisions (temporarily disabled by your choice)
        if pygame.sprite.spritecollide(hero.sprite, obstacles, False):
            pass  # game_active = False

    else:
        screen.fill(COLOR_BG)
        screen.blit(game_name, game_name_rect)
        if score == 0:
            screen.blit(game_message, game_message_rect)
        else:
            score_text = game_font.render(f"Your score: {score}", False, (111, 196, 169))
            screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, 330)))

    pygame.display.update()
    clock.tick(FPS)
