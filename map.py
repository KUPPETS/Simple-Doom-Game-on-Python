import pygame

TILE_SIZE = 100
COLOR_WALL = 'darkgray'

# Define the mini-map
_ = False
mini_map = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, _, _, _, 3, 3, _, _, _, _, _, _, 5, _, _, _, _, _, _, 1],
    [1, _, _, 3, 3, 3, _, _, _, 4, 4, _, _, _, _, _, _, _, _, 1],
    [1, _, _, _, _, _, _, _, _, _, 4, 4, _, _, _, _, _, _, _, 1],
    [1, _, _, _, 5, 5, _, _, 4, 4, 4, _, _, _, _, 4, 4, _, _, 1],
    [1, _, _, 3, 3, 3, _, _, _, _, _, _, _, _, _, _, 4, 4, _, 1],
    [1, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
    [1, _, _, _, 5, 5, _, _, _, _, 5, 5, 5, 5, _, _, _, _, _, 1],
    [1, _, _, _, _, _, _, _, _, _, _, _, _, _, 5, _, _, _, _, 1],
    [1, _, _, 3, 3, 3, _, _, _, _, _,_ ,_, _, 5, 5, 5, 5, _, _, 1],
    [1, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
    [1, _, _, _, 5, 2, 2, 2, 2, 3, _, _, 3, 2, 2, 2, 2, _, _, 1],
    [1, _, _, 3, 3, 2, _, _, _, _, _, _, _, _, _, _, 2, _, _, 1],
    [1, _, _, _, _, 2, _, _, _, _, _, _, _, _, _, _, 2, _, _, 1],
    [1, _, _, _, 5, 2, _, _, _, _, _, _, _, _, _, _, 2, _, _, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]


class Map:
    def __init__(self, game):
        self.game = game
        self.mini_map = mini_map
        self.world_map = {}
        self.rows = len(self.mini_map)
        self.cols = len(self.mini_map[0])
        self.get_map()

    def get_map(self):
        for y, row in enumerate(self.mini_map):
            for x, value in enumerate(row):
                if value:
                    self.world_map[(x, y)] = value

    def draw(self):
        for position in self.world_map:
            pygame.draw.rect(
                self.game.screen,
                COLOR_WALL,
                (position[0] * TILE_SIZE, position[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                2
            )
