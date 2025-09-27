import pygame
from sys import exit

pygame.init()
screen = pygame.display.set_mode((1460, 900))
pygame.display.set_caption('SlingDuel')
clock = pygame.time.Clock()
test_font = pygame.font.Font('graphics/ByteBounce.ttf', 100)

sky_surface = pygame.image.load('graphics/City.png')
ground_surface = pygame.image.load('graphics/Ground.png')
text_surface = test_font.render('Slingduel', False, 'Black')

hero_red_surface = pygame.image.load('graphics/hero/hero_red.png')
hero_blue_surface = pygame.image.load('graphics/hero/hero_blue.png') 
banana_surface = pygame.image.load('graphics/banana.png')

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    screen.blit(sky_surface,(-100, -150))
    screen.blit(ground_surface,(-50,250))
    screen.blit(text_surface, (400, 50))
    screen.blit(hero_red_surface, (650, 650))
    screen.blit(hero_blue_surface, (200, 650))
    screen.blit(banana_surface, (650, 750))

    pygame.display.update()
    clock.tick(60)


if __name__ == "__main__":
    main()
