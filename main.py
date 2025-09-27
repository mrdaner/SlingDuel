import pygame
from sys import exit
from constants import *
from circleshape import CircleShape
from player import Player


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('SlingDuel')
    clock = pygame.time.Clock()

    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    shots = pygame.sprite.Group()

    Player.containers = (updatable, drawable)

    player_red = Player(SCREEN_WIDTH / 4, SCREEN_HEIGHT / 4)
    player_blue = Player(SCREEN_WIDTH / 8, SCREEN_HEIGHT / 4)

    test_font = pygame.font.Font('graphics/ByteBounce.ttf', 100)

    sky_surface = pygame.image.load('graphics/City.png').convert_alpha()
    ground_surface = pygame.image.load('graphics/Ground.png').convert_alpha()
    text_surface = test_font.render('Slingduel', False, 'Black')

    hero_red_x_pos = 950
    hero_red_y_pos = 600

    hero_blue_x_pos = 200
    hero_blue_y_pos = 600

    hero_red_surface = pygame.image.load('graphics/hero/hero_red_right.png').convert_alpha()
    hero_red_rectangle = hero_red_surface.get_rect(topleft = (hero_red_x_pos, hero_red_y_pos))

    hero_blue_surface = pygame.image.load('graphics/hero/hero_blue.png').convert_alpha()
    hero_blue_rectangle = hero_blue_surface.get_rect(topleft = (hero_blue_x_pos, hero_blue_y_pos))

    # banana_surface = pygame.image.load('graphics/banana.png').convert_alpha()


    dt = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        screen.blit(sky_surface,(-100, -150))
        screen.blit(ground_surface,(-50,250))
        screen.blit(text_surface, (400, 50))


        if hero_red_x_pos < -100: hero_red_x_pos = 1560
        if hero_red_x_pos > 1561: hero_red_x_pos = -99

        
        if hero_blue_x_pos < -100: hero_blue_x_pos = 1560
        if hero_blue_x_pos > 1561: hero_blue_x_pos = -99

        hero_red_rectangle.left -= 1
        hero_blue_rectangle.left += 1

        screen.blit(hero_red_surface, hero_red_rectangle)
        screen.blit(hero_blue_surface, hero_blue_rectangle)
        # screen.blit(banana_surface, (650, 750))

        pygame.display.update()
        dt = clock.tick(60) / 1000


if __name__ == "__main__":
    main()
