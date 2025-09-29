import pygame
from sys import exit
from constants import *
from random import randint, choice

class Hero(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        hero_stand = pygame.image.load('graphics/Hero/Hero_stand.png').convert_alpha()
        hero_run_1 = pygame.image.load('graphics/Hero/Hero_run_1.png').convert_alpha()
        hero_run_2 = pygame.image.load('graphics/Hero/Hero_run_2.png').convert_alpha()
        hero_run_3 = pygame.image.load('graphics/Hero/Hero_run_3.png').convert_alpha()
        hero_run_4 = pygame.image.load('graphics/Hero/Hero_run_4.png').convert_alpha()
        self.hero_run = [hero_stand, hero_run_1, hero_run_2, hero_run_3, hero_run_4]
        self.hero_run_index = 0.0

        hero_jump_1 = pygame.image.load('graphics/Hero/Hero_jump_1.png').convert_alpha()
        hero_jump_2 = pygame.image.load('graphics/Hero/Hero_jump_2.png').convert_alpha()
        hero_jump_3 = pygame.image.load('graphics/Hero/Hero_jump_3.png').convert_alpha()
        self.hero_jump = [hero_jump_1, hero_jump_2, hero_jump_3]
        self.hero_jump_index = 0.0

        self.image = self.hero_run[0]
        self.rect = self.image.get_rect(midbottom=(200, 680))
        self.gravity = 0

    def hero_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.rect.bottom >= 680:
            self.gravity = -25


    def apply_gravity(self):
        self.gravity += 1
        self.rect.y += self.gravity
        if self.rect.bottom >= 680:
            self.rect.bottom = 680


    def animate(self):
        if self.rect.bottom < 680:  # jumping
            self.hero_jump_index = (self.hero_jump_index + 0.1) % len(self.hero_jump)
            self.image = self.hero_jump[int(self.hero_jump_index)]
        else:  # running
            self.hero_run_index = (self.hero_run_index + 0.4) % len(self.hero_run)
            self.image = self.hero_run[int(self.hero_run_index)]

    def update(self):
        self.hero_input()
        self.apply_gravity()
        self.animate()


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, kind):
        super().__init__()

        if kind == 'banana':
            banana_surf = pygame.image.load('graphics/banana.png').convert_alpha()
            self.frames = [
                banana_surf,
                pygame.transform.rotate(banana_surf, 90),
                pygame.transform.rotate(banana_surf, 180),
                pygame.transform.rotate(banana_surf, 270)
            ]
            y_pos = 665
            self.speed = 10
        else:  # 'boss'
            boss_surf = pygame.image.load('graphics/boss.png').convert_alpha()
            self.frames = [
                boss_surf,
                pygame.transform.rotate(boss_surf, 90),
                pygame.transform.rotate(boss_surf, 180),
                pygame.transform.rotate(boss_surf, 270)
            ]
            y_pos = 365
            self.speed = 10

        self.animation_index = 0.0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=(randint(900, 1100), y_pos))

    
    def animate(self):
        self.animation_index = (self.animation_index + 0.2) % len(self.frames)
        self.image = self.frames[int(self.animation_index)]

    
    def update(self):
        self.rect.x -= self.speed
        self.animate()


    def destroy(self):
        if self.rect.right < -100:
            self.kill()



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



pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('SlingDuel')
clock = pygame.time.Clock()
game_font = pygame.font.Font('graphics/ByteBounce.ttf', 100)
game_active = False
start_time = 0
score = 0

#Groups
hero = pygame.sprite.GroupSingle()
hero.add(Hero())

obstacle_group = pygame.sprite.Group()

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
                if event.key == pygame.K_SPACE and hero.sprite.rect.bottom >= 680:
                    hero.sprite.gravity = -25

            if event.type == pygame.MOUSEBUTTONDOWN:
                if hero.sprite.rect.collidepoint(event.pos):
                    hero.sprite.gravity = -25
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                start_time = int(pygame.time.get_ticks() / 1000)
    
        if game_active:
            if event.type == obstacle_timer:
                obstacle_group.add(Obstacle(choice(['banana', 'banana', 'boss'])))


            if event.type == banana_animation_timer and game_active:
                banana_index = (banana_index + 1) % len(banana_frames)
                banana_surf_current = banana_frames[banana_index]
            if event.type == boss_animation_timer and game_active:
                boss_index = (boss_index + 1) % len(boss_frames)
                boss_surf_current = boss_frames[boss_index]


    
    #GAME CODE
    if game_active:
        # Update sprites
        hero.update()
        obstacle_group.update()

        #Destroy off-screen obstacles
        for obs in obstacle_group.sprites():
            obs.destroy()

        screen.blit(sky_surf, (0, 0))
        screen.blit(ground_surf, (0, 0))
        score = display_score(game_font, screen, start_time)
        hero.draw(screen)
        obstacle_group.draw(screen)

        if pygame.sprite.spritecollide(hero.sprite, obstacle_group, False):
            game_active = False

    #ENDSCREEN code
    else:
        screen.fill((94,129,162)) # these numbers are a tuple color
        screen.blit(hero_stand, hero_stand_rect)

        obstacle_group.empty()  
        
        hero.sprite.rect.midbottom = (200, 680)
        hero.sprite.gravity = 0


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