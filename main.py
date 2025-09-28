import pygame
from sys import exit
from constants import *
# from player import Player


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('SlingDuel')
    clock = pygame.time.Clock()

    # updatable = pygame.sprite.Group()
    # drawable = pygame.sprite.Group()
    # bananas = pygame.sprite.Group()

    # Player.containers = (updatable, drawable)

    test_font = pygame.font.Font('graphics/ByteBounce.ttf', 100)

    sky_surface = pygame.image.load('graphics/Background/Sky.png').convert_alpha()
    ground_surface = pygame.image.load('graphics/Background/Ground.png').convert_alpha()
    text_surface = test_font.render('Slingduel', False, 'Black')
    hero_surface = pygame.image.load('graphics/Hero/Hero_stand.png').convert_alpha()


    dt = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        screen.blit(sky_surface,(0, 0))
        screen.blit(ground_surface,(0,0))
        screen.blit(text_surface, (480, 50))
        screen.blit(hero_surface, (300, 300))


        # screen.blit(hero_red_surface, hero_red_rectangle)
        # screen.blit(hero_blue_surface, hero_blue_rectangle)
        # screen.blit(banana_surface, (650, 750))

        pygame.display.update()
        dt = clock.tick(60) / 1000


if __name__ == "__main__":
    main()
