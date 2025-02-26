import pygame
import math
from settings import *

TILE_SIZE = 100
const = 0.0001  # to avoid division by zero


class RayCast:
    def __init__(self, game):
        self.game = game
        self.ray_cast_result = []
        self.rendering_objects = []
        self.textures = self.game.render.wall_textures

    def get_rendering_objects(self):
        self.rendering_objects = []
        for ray, values in enumerate(self.ray_cast_result):
            depth, projection_height, texture, offset = values
            if projection_height < HEIGHT:
                wall_column = self.textures[texture].subsurface(offset * (TEXTURE_SIZE - SCALE), 0, SCALE, TEXTURE_SIZE)
                wall_column = pygame.transform.scale(wall_column, (SCALE, projection_height))
                wall_column_position = (ray * SCALE, HALF_HEIGHT - projection_height // 2)
            else:
                texture_height = TEXTURE_SIZE * HEIGHT / projection_height
                wall_column = self.textures[texture].subsurface(offset * (TEXTURE_SIZE - SCALE),
                                                                HALF_TEXTURE_SIZE - texture_height // 2, SCALE,
                                                                texture_height)
                wall_column = pygame.transform.scale(wall_column, (SCALE, HEIGHT))
                wall_column_position = (ray * SCALE, 0)

            self.rendering_objects.append((depth, wall_column, wall_column_position))

    def ray_cast(self):
        self.ray_cast_result = []
        ox, oy = self.game.player.position
        x_map, y_map = self.game.player.map_position

        texture_vertical, texture_horizontal = True, True

        ray_angle = self.game.player.angle - HALF_FOV + const

        for ray in range(NUMBER_RAYS):
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            # Find the vertical intersection
            x_vertical, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)

            depth_vertical = (x_vertical - ox) / cos_a
            y_vertical = oy + depth_vertical * sin_a

            delta_depth = dx / cos_a
            dy = delta_depth * sin_a

            for _ in range(MAX_DEPTH):
                tile_vertical = int(x_vertical), int(y_vertical)
                if tile_vertical in self.game.map.world_map:
                    texture_vertical = self.game.map.world_map[tile_vertical]
                    break
                x_vertical += dx
                y_vertical += dy
                depth_vertical += delta_depth
            # Find the horizontal intersection
            y_horizontal, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)

            depth_horizontal = (y_horizontal - oy) / sin_a
            x_horizontal = ox + depth_horizontal * cos_a

            delta_depth = dy / sin_a
            dx = delta_depth * cos_a

            for _ in range(MAX_DEPTH):
                tile_horizontal = int(x_horizontal), int(y_horizontal)
                if tile_horizontal in self.game.map.world_map:
                    texture_horizontal = self.game.map.world_map[tile_horizontal]
                    break
                x_horizontal += dx
                y_horizontal += dy
                depth_horizontal += delta_depth

            # Depth and Texture
            if depth_horizontal < depth_vertical:
                depth, texture = depth_horizontal, texture_horizontal
                x_horizontal %= 1
                offset = (1 - x_horizontal) if sin_a > 0 else x_horizontal

            else:
                depth, texture = depth_vertical, texture_vertical
                y_vertical %= 1
                offset = y_vertical if cos_a > 0 else (1 - y_vertical)

            # Draw 3D projection
            projection_height = SCREEN_DISTANCE / (depth + const)

            depth *= math.cos(self.game.player.angle - ray_angle)

            # Ray casting result
            self.ray_cast_result.append((depth, projection_height, texture, offset))

            ray_angle += DELTA_ANGLE

    def update(self):
        self.ray_cast()
        self.get_rendering_objects()
