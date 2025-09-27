import pygame
from sys import exit

pygame.init()
screen = pygame.display.set_mode((1536, 1024))
pygame.display.set_caption('SlingDuel')
clock = pygame.time.Clock()

test_surface = pygame.image.load('graphics/full_background.png')

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    screen.blit(test_surface,(0,0))


    pygame.display.update()
    clock.tick(60)


if __name__ == "__main__":
    main()
