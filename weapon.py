import pygame.transform
from collections import deque
from settings import *
from objects import AnimatedObject


class Weapon(AnimatedObject):
    def __init__(self, game, path='Graphics/resources/weapon/gun1.png', scale=0.4, animation_time=90):
        super().__init__(game=game, path=path, scale=scale, animation_time=animation_time)
        self.images = deque(
            [pygame.transform.smoothscale(img, (self.image.get_width() * scale, self.image.get_height() * scale)) for
             img in self.images])
        self.weapon_position = (HALF_WIDTH - self.images[0].get_width() // 2, HEIGHT - self.images[0].get_height())
        self.reloading = False
        self.number_images = len(self.images)
        self.frame_counter = 0
        self.damage = 50

    def animation_shoot(self):
        if self.reloading:
            self.game.player.shot = False
            if self.animation_trigger:
                self.images.rotate(-1)
                self.image = self.images[0]
                self.frame_counter += 1
                if self.frame_counter == self.number_images:
                    self.reloading = False
                    self.frame_counter = 0

    def draw(self):
        self.game.screen.blit(self.images[0], self.weapon_position)

    def update(self):
        self.check_animation_time()
        self.animation_shoot()
