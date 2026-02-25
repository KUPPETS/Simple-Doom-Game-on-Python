import pygame
from settings import *
import os
from collections import deque
import math


class StaticObject:
    def __init__(self, game, path='Graphics/resources/static_objects/blood.png',
                 pos=(10.5, 3.5), scale=0.5, shift=0.9):
        self.game = game
        self.player = game.player
        self.x, self.y = pos
        self.OBJECT_SCALE = float(scale)
        self.OBJECT_Y_SHIFT = float(shift)

        # FIX: в headless не грузим текстуры — экономим RAM и время init
        if not game.headless:
            self.image = pygame.image.load(path).convert_alpha()
            self.IMAGE_WIDTH = self.image.get_width()
            self.IMAGE_HALF_WIDTH = self.IMAGE_WIDTH // 2
            self.IMAGE_RATIO = self.IMAGE_WIDTH / self.image.get_height()
        else:
            self.image = pygame.Surface((1, 1))
            self.IMAGE_WIDTH = 1
            self.IMAGE_HALF_WIDTH = 0
            self.IMAGE_RATIO = 1.0

        self.dx, self.dy, self.theta = 0.0, 0.0, 0.0
        self.screen_x = 0.0
        self.distance = 1.0
        self.normal_distance = 1.0
        self.object_half_width = 0

    def get_object_projection(self):
        # вызывается ТОЛЬКО в render-режиме
        projection = min(
            SCREEN_DISTANCE / max(self.normal_distance, 0.1) * self.OBJECT_SCALE,
            HEIGHT * 3
        )
        projection_width = max(1, int(projection * self.IMAGE_RATIO))
        projection_height = max(1, int(projection))

        image = pygame.transform.scale(self.image, (projection_width, projection_height))

        self.object_half_width = projection_width // 2
        y_shift = self.OBJECT_Y_SHIFT * projection_height
        position = (int(self.screen_x - self.object_half_width),
                    int(HALF_HEIGHT - projection_height // 2 + y_shift))

        self.game.raycast.rendering_objects.append((self.normal_distance, image, position))

    def _calc_object_half_width(self):
        """Вычисляет object_half_width без рендеринга — нужно для хитбокса в RL."""
        projection = min(
            SCREEN_DISTANCE / max(self.normal_distance, 0.1) * self.OBJECT_SCALE,
            HEIGHT * 3
        )
        projection_width = max(1, int(projection * self.IMAGE_RATIO))
        self.object_half_width = projection_width // 2

    def get_object(self):
        dx, dy = self.x - self.player.x, self.y - self.player.y
        self.dx, self.dy = dx, dy
        self.theta = math.atan2(dy, dx)

        delta = self.theta - self.player.angle
        if (dx > 0 and self.player.angle > math.pi) or (dx < 0 and dy < 0):
            delta += math.pi * 2

        delta_rays = delta / DELTA_ANGLE
        self.screen_x = SCALE * (HALF_NUMBER_RAYS + delta_rays)
        self.distance = math.hypot(dx, dy)
        self.normal_distance = self.distance * math.cos(delta)

        if (not self.game.headless) and self.game.render_enabled:
            if -self.IMAGE_HALF_WIDTH < self.screen_x < (WIDTH + self.IMAGE_HALF_WIDTH) \
                    and self.normal_distance > 0.5:
                self.get_object_projection()
        else:
            # В headless: считаем хитбокс без рендеринга (нужно для check_damage_to_npc)
            if self.normal_distance > 0.5:
                self._calc_object_half_width()

    def update(self):
        self.get_object()


class AnimatedObject(StaticObject):
    def __init__(self, game, path='Graphics/resources/animated_objects/keg/keg1.png',
                 pos=(11.5, 3.5), scale=0.6, shift=0.5, animation_time=120):
        super().__init__(game, path, pos, scale, shift)
        self.animation_time = int(animation_time)
        self.path = path.rsplit('/', 1)[0]
        self.animation_time_previous = pygame.time.get_ticks()
        self.animation_trigger = False

        # FIX: в headless не грузим кадры анимации — только заглушка
        if not game.headless:
            self.images = self.get_images(self.path)
        else:
            self.images = deque([pygame.Surface((1, 1))])

    def update(self):
        super().update()

        if self.game.headless or not self.game.render_enabled:
            return

        self.check_animation_time()
        self.animation(self.images)

    def animation(self, images):
        if self.animation_trigger:
            images.rotate(-1)
            self.image = images[0]

    def check_animation_time(self):
        self.animation_trigger = False
        current_time = pygame.time.get_ticks()
        if current_time - self.animation_time_previous > self.animation_time:
            self.animation_trigger = True
            self.animation_time_previous = current_time

    def get_images(self, path):
        images = deque()
        # FIX: sorted() гарантирует одинаковый порядок кадров на всех ОС
        for file_name in sorted(os.listdir(path)):
            if os.path.isfile(os.path.join(path, file_name)):
                image = pygame.image.load(
                    os.path.join(path, file_name)
                ).convert_alpha()
                images.append(image)
        return images
