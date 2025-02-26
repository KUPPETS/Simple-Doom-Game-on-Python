import pygame
from settings import *
import os
from collections import deque
import math


class StaticObject:
    def __init__(self, game, path='Graphics/resources/static_objects/blood.png', pos=(10.5, 3.5), scale=0.5, shift=0.9):
        # Initialize the static object with game reference, image path, position, scale, and shift
        self.game = game
        self.player = game.player
        self.x, self.y = pos
        self.image = pygame.image.load(path).convert_alpha()
        self.IMAGE_WIDTH = self.image.get_width()
        self.IMAGE_HALF_WIDTH = self.IMAGE_WIDTH // 2
        self.IMAGE_RATIO = self.IMAGE_WIDTH / self.image.get_height()
        self.dx, self.dy, self.theta, self.screen_x, self.distance, self.normal_distance, self.object_half_width = 0, 0, 0, 0, 1, 1, 0
        self.OBJECT_SCALE = scale
        self.OBJECT_Y_SHIFT = shift

    def get_object_projection(self):
        # Calculate the projection of the object on the screen
        projection = SCREEN_DISTANCE / self.normal_distance * self.OBJECT_SCALE
        projection_width, projection_height = projection * self.IMAGE_RATIO, projection

        # Scale the image to the calculated projection size
        image = pygame.transform.scale(self.image, (projection_width, projection_height))

        # Calculate the position to blit the image on the screen
        self.object_half_width = projection_width // 2
        y_shift = self.OBJECT_Y_SHIFT * projection_height
        position = self.screen_x - self.object_half_width, HALF_HEIGHT - projection_height // 2 + y_shift

        # Append the object to the rendering list
        self.game.raycast.rendering_objects.append((self.normal_distance, image, position))

    def get_object(self):
        # Calculate the distance and angle of the object relative to the player
        dx, dy = self.x - self.player.x, self.y - self.player.y
        self.dx, self.dy = dx, dy
        self.theta = math.atan2(dy, dx)

        # Calculate the angle difference between the object and the player's view
        delta = self.theta - self.player.angle
        if (dx > 0 and self.player.angle > math.pi) or (dx < 0 and dy < 0):
            delta += math.pi * 2

        # Calculate the screen position of the object
        delta_rays = delta / DELTA_ANGLE
        self.screen_x = SCALE * (HALF_NUMBER_RAYS + delta_rays)
        self.distance = math.hypot(dx, dy)
        self.normal_distance = self.distance * math.cos(delta)

        # If the object is within the screen bounds and close enough, project it
        if -self.IMAGE_HALF_WIDTH < self.screen_x < (WIDTH + self.IMAGE_HALF_WIDTH) and self.normal_distance > 0.5:
            self.get_object_projection()

    def update(self):
        # Update the object's position and projection
        self.get_object()


class AnimatedObject(StaticObject):
    def __init__(self, game, path='Graphics/resources/animated_objects/keg/keg1.png', pos=(11.5, 3.5), scale=0.6,
                 shift=0.5, animation_time=120):
        # Initialize the animated object with additional animation parameters
        super().__init__(game, path, pos, scale, shift)
        self.animation_time = animation_time
        self.path = path.rsplit('/', 1)[0]
        self.images = self.get_images(self.path)
        self.animation_time_previous = pygame.time.get_ticks()
        self.animation_trigger = False

    def update(self):
        # Update the object's position, projection, and animation
        super().update()
        self.check_animation_time()
        self.animation(self.images)

    def animation(self, images):
        # Rotate the images to create an animation effect
        if self.animation_trigger:
            images.rotate(-1)
            self.image = images[0]

    def check_animation_time(self):
        # Check if it's time to update the animation frame
        self.animation_trigger = False
        current_time = pygame.time.get_ticks()
        if current_time - self.animation_time_previous > self.animation_time:
            self.animation_trigger = True
            self.animation_time_previous = current_time

    def get_images(self, path):
        # Load all images from the specified path for the animation
        images = deque()
        for file_name in os.listdir(path):
            if os.path.isfile(os.path.join(path, file_name)):
                image = pygame.image.load(path + '/' + file_name).convert_alpha()
                images.append(image)
        return images
