import pygame
from sys import exit
from constants import *


def display_score():
    current_time = pygame.time.get_ticks()
    score_surf = game_font.render(f'{current_time}',False,(64,64,64))
    score_rect = score_surf.get_rect(center = (400, 50))
    screen.blit(score_surf, score_rect)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('SlingDuel')
    clock = pygame.time.Clock()
    test_font = pygame.font.Font('graphics/ByteBounce.ttf', 100)
    game_active = True

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
    hero_surf = pygame.image.load('graphics/Hero/Hero_stand.png').convert_alpha()
    hero_rect = hero_surf.get_rect(midbottom = (200, 680))
    hero_gravity = PLAYER_GRAVITY


    #BANANA
    banana_surf = pygame.image.load('graphics/banana.png')
    banana_rect = banana_surf.get_rect(midbottom = (800, 665))




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
                    banana_rect.left = SCREEN_WIDTH


        #GAME CODE
        if game_active:
            screen.blit(sky_surf, (0, 0))
            screen.blit(ground_surf, (0, 0))

            # pygame.draw.rect(screen, 'White', text_rect, 6)
            # pygame.draw.rect(screen, 'White', text_rect)
            # screen.blit(text_surf, text_rect)
            # pygame.draw.rect(screen, 'White', health_rect)
            # screen.blit(health_surf, health_rect)
            display_score()


            #TARGET VECTOR IDEA
            # pygame.draw.line(screen, 'White', hero_rect.center, pygame.mouse.get_pos(),5)

            # pygame.draw.ellipse(screen, 'Brown', pygame.Rect(50,200,100,130))



            #banana

            banana_rect.x -= 12
            if banana_rect.right <= 0: banana_rect.left = SCREEN_WIDTH

            screen.blit(banana_surf, banana_rect)

            #HERO
            hero_gravity += 1
            hero_rect.bottom += hero_gravity
            if hero_rect.bottom >= 680: hero_rect.bottom = 680

            screen.blit(hero_surf, hero_rect)

            #collision
            # if banana_rect.colliderect(hero_rect): print('COLLISION')
            # else: print('Normal')
            mouse_pos = pygame.mouse.get_pos()
            # if hero_rect.collidepoint(mouse_pos):
            #     print('It is')
            # else:
            #     print('nope')


            #PLAYER INPUT

            # keys = pygame.key.get_pressed()
            # if keys[pygame.K_SPACE]:
            #     print('jump')


        #COLLISION which stops game
            if banana_rect.colliderect(hero_rect):
                game_active = False

        #ENDSCREEN code
        else:
            screen.fill('Yellow')
            if event.type == pygame.KEYDOWN:
                game_active = True


        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()
