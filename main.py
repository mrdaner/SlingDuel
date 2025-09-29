import pygame
from sys import exit
from constants import *
from random import randint


def obstacle_movement(obstacle_list):
    if obstacle_list:
        for obstacle_rect in obstacle_list:
            obstacle_rect.x -= 5

            if obstacle_rect.bottom == 665:
                screen.blit(banana_surf_current, obstacle_rect)
            else:
                screen.blit(boss_surf_current, obstacle_rect)
        obstacle_list = [obstacle for obstacle in obstacle_list if obstacle.x > -100]
        return obstacle_list
    else: return []


def display_score(game_font, screen, start_time):
    current_time = int(pygame.time.get_ticks() / 1000) - start_time
    score_surf = game_font.render(f'Score: {current_time}',False,(64,64,64))
    score_rect = score_surf.get_rect(center=(400, 50))
    screen.blit(score_surf, score_rect)
    return current_time

def collisions(hero, obstacles):
    if obstacles:
        for obstacle_rect in obstacles:
            if hero.colliderect(obstacle_rect):
                return False
    return True

def hero_animation():
    global hero_surf, hero_run_index, hero_jump_index

    if hero_rect.bottom < 680:  # jumping
        hero_jump_index = (hero_jump_index + 0.1) % len(hero_jump)
        hero_surf = hero_jump[int(hero_jump_index)]
    else:  # running
        hero_run_index = (hero_run_index + 0.4) % len(hero_run)
        hero_surf = hero_run[int(hero_run_index)]


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('SlingDuel')
clock = pygame.time.Clock()
game_font = pygame.font.Font('graphics/ByteBounce.ttf', 100)
game_active = False
start_time = 0
score = 0

# updatable = pygame.sprite.Group()
# drawable = pygame.sprite.Group()
# bananas = pygame.sprite.Group()

# Player.containers = (updatable, drawable)



sky_surf = pygame.image.load('graphics/Background/Sky.png').convert_alpha()
ground_surf = pygame.image.load('graphics/Background/Ground.png').convert_alpha()

#TEXT
# text_surf = font.render('Slingduel', False, 'Black')
# text_rect = text_surf.get_rect(center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 5))

# health_surf = font.render('Health', False, 'Black')
# health_rect = health_surf.get_rect(center = (SCREEN_WIDTH / 10, SCREEN_HEIGHT / 10))

#HERO
hero_stand = pygame.image.load('graphics/Hero/Hero_stand.png').convert_alpha()
hero_run_1 = pygame.image.load('graphics/Hero/Hero_run_1.png').convert_alpha()
hero_run_2 = pygame.image.load('graphics/Hero/Hero_run_2.png').convert_alpha()
hero_run_3 = pygame.image.load('graphics/Hero/Hero_run_3.png').convert_alpha()
hero_run_4 = pygame.image.load('graphics/Hero/Hero_run_4.png').convert_alpha()
hero_run = [hero_stand, hero_run_1, hero_run_2, hero_run_3, hero_run_4]
hero_run_index = 0

hero_jump_1 = pygame.image.load('graphics/Hero/Hero_jump_1.png').convert_alpha()
hero_jump_2 = pygame.image.load('graphics/Hero/Hero_jump_2.png').convert_alpha()
hero_jump_3 = pygame.image.load('graphics/Hero/Hero_jump_3.png').convert_alpha()
hero_jump = [hero_jump_1, hero_jump_2, hero_jump_3]
hero_jump_index = 0

hero_surf = hero_run[hero_run_index]
hero_rect = hero_surf.get_rect(midbottom = (200, 680))
hero_gravity = PLAYER_GRAVITY

#intro screen
hero_stand = pygame.image.load('graphics/Hero/Hero_stand.png').convert_alpha()     #intro screen
hero_stand = pygame.transform.rotozoom(hero_stand, 0, 2) #scaled hero_stand
hero_stand_rect = hero_stand.get_rect(center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))     #intro screen

game_name = game_font.render('Slingduel', False, (111,196,169))
game_name_rect = game_name.get_rect(center = (400, 130))

game_message = game_font.render('Press SPACE to START', False, (111,196,169))
game_message_rect = game_message.get_rect(center = (400,320))

#Obstacle BANANA
banana_surf = pygame.image.load('graphics/banana.png').convert_alpha()
banana_frames = [
    banana_surf,
    pygame.transform.rotate(banana_surf, 90),
    pygame.transform.rotate(banana_surf, 180),
    pygame.transform.rotate(banana_surf, 270)
]
banana_index = 0
banana_surf_current = banana_frames[banana_index]


#Obstacle BOSS
boss_surf = pygame.image.load('graphics/boss.png').convert_alpha()
boss_frames = [
    boss_surf,
    pygame.transform.rotate(boss_surf, 90),
    pygame.transform.rotate(boss_surf, 180),
    pygame.transform.rotate(boss_surf, 270)
]
boss_index = 0
boss_surf_current = boss_frames[boss_index]
obstacle_rect_list = []


#Timer
obstacle_timer = pygame.USEREVENT + 1
pygame.time.set_timer(obstacle_timer, 1100)

banana_animation_timer = pygame.USEREVENT + 2
pygame.time.set_timer(banana_animation_timer, 200)

boss_animation_timer = pygame.USEREVENT + 3
pygame.time.set_timer(boss_animation_timer, 500)

#EVENT LOOP
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if game_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and hero_rect.bottom >= 680:
                    print("pressing space")
                    hero_gravity = -25

            if event.type == pygame.MOUSEBUTTONDOWN:
                if hero_rect.collidepoint(event.pos):
                    hero_gravity = -25
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                start_time = int(pygame.time.get_ticks() / 1000)
    
        if game_active:
            if event.type == obstacle_timer:
                if randint(0, 2):
                    obstacle_rect_list.append(banana_surf.get_rect(midbottom = (randint(800,1100), 665)))
                else:
                    obstacle_rect_list.append(boss_surf.get_rect(midbottom = (randint(800,1100), 365)))
            if event.type == banana_animation_timer and game_active:
                banana_index = (banana_index + 1) % len(banana_frames)
                banana_surf_current = banana_frames[banana_index]
            if event.type == boss_animation_timer and game_active:
                boss_index = (boss_index + 1) % len(boss_frames)
                boss_surf_current = boss_frames[boss_index]


    
    #GAME CODE
    if game_active:
        screen.blit(sky_surf, (0, 0))
        screen.blit(ground_surf, (0, 0))

        score = display_score(game_font, screen, start_time)
        # pygame.draw.rect(screen, 'White', text_rect, 6)
        # pygame.draw.rect(screen, 'White', text_rect)
        # screen.blit(text_surf, text_rect)
        # pygame.draw.rect(screen, 'White', health_rect)
        # screen.blit(health_surf, health_rect)
        display_score(game_font, screen, start_time)


        #TARGET VECTOR IDEA
        # pygame.draw.line(screen, 'White', hero_rect.center, pygame.mouse.get_pos(),5)

        # pygame.draw.ellipse(screen, 'Brown', pygame.Rect(50,200,100,130))

        #banana movement

        # banana_rect.x -= 12
        # if banana_rect.right <= 0: banana_rect.left = SCREEN_WIDTH
        # screen.blit(banana_surf, banana_rect)

        #HERO
        hero_gravity += 1
        hero_rect.bottom += hero_gravity
        if hero_rect.bottom >= 680: hero_rect.bottom = 680
        hero_animation()
        screen.blit(hero_surf, hero_rect)

        #Obstacle movenent

        obstacle_rect_list = obstacle_movement(obstacle_rect_list)

        #collision
        # if banana_rect.colliderect(hero_rect): print('COLLISION')
        # else: print('Normal')
        game_active = collisions(hero_rect, obstacle_rect_list)

        # mouse_pos = pygame.mouse.get_pos()

        # if hero_rect.collidepoint(mouse_pos):
        #     print('It is')
        # else:
        #     print('nope')

        #PLAYER INPUT

        # keys = pygame.key.get_pressed()
        # if keys[pygame.K_SPACE]:
        #     print('jump')


    #ENDSCREEN code
    else:
        screen.fill((94,129,162)) # these numbers are a tuple color
        screen.blit(hero_stand, hero_stand_rect)
        obstacle_rect_list.clear()
        hero_rect.midbottom = (200, 680)
        hero_gravity = 0

        score_message = game_font.render(f'Your score: {score}', False, (111,196,169))
        score_message_rect = score_message.get_rect(center = (400,330))
        screen.blit(game_name, game_name_rect)
        if score == 0:
            screen.blit(game_message, game_message_rect)
        else:
            screen.blit(score_message, score_message_rect)
        if event.type == pygame.KEYDOWN:
            game_active = True

    pygame.display.update()
    clock.tick(60)