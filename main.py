import sys
import pygame
from map import *
from player import *
from raycast import *
from rendering import *
from weapon import *
from sound import *
from objects import *
from objects_storage import *
from settings import *
from pathfinding import *


class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pygame.USEREVENT + 0
        pygame.time.set_timer(self.global_event, 50)
        self.sound = Sound(self)
        self.map = Map(self)
        self.player = Player(self)
        self.render = ObjectRender(self)
        self.raycast = RayCast(self)
        self.objects_storage = ObjectStorage(self)
        self.weapon = Weapon(self)
        self.sound = Sound(self)
        self.pathfinding = PathFindingAlgorithm(self)
        self.new_game()


    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)
        self.render = ObjectRender(self)
        self.raycast = RayCast(self)
        self.objects_storage = ObjectStorage(self)
        self.weapon = Weapon(self)
        self.sound = Sound(self)
        self.pathfinding = PathFindingAlgorithm(self)
        pygame.mixer.music.play(-1)

    def update(self):
        self.player.update()
        self.raycast.update()
        self.objects_storage.update()
        self.weapon.update()
        pygame.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pygame.display.set_caption(f'{self.clock.get_fps() :.1f}')

    def draw(self):
        self.render.draw()
        self.weapon.draw()
         #self.map.draw()
         #self.player.draw()

    def check_events(self):
        self.global_trigger = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == self.global_event:
                self.global_trigger = True
            self.player.single_shoot(event)

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


if __name__ == '__main__':
    game = Game()
    game.run()
