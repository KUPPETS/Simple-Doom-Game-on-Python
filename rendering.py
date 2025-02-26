import pygame
from settings import *


class ObjectRender:
    def __init__(self, game):
        # Initialize the render object with game and screen references
        self.game = game
        self.screen = game.screen
        self.wall_textures = self.load_wall_textures()
        self.sky_image = self.get_texture('Graphics/textures/sky.png', (WIDTH, HALF_HEIGHT))
        self.sky_offset = 0
        self.damage_screen = self.get_texture('Graphics/textures/screens/damage_screen.png', (WIDTH, HEIGHT))
        self.digit_size = 50
        self.digit_images = [self.get_texture(f'Graphics/textures/digits/{i}.png', [self.digit_size] * 2) for i in
                             range(11)]
        self.digits_dictionary = dict(zip(map(str, range(11)), self.digit_images))
        self.game_over = self.get_texture('Graphics/textures/screens/game_over.png', (WIDTH, HEIGHT))
        self.win_image = self.get_texture('Graphics/textures/screens/win.png', (WIDTH, HEIGHT))
        self.letter_size = 50
        self.letter_images = {
            'k': self.get_texture('Graphics/textures/letters/k.png', [self.letter_size] * 2),
            'i': self.get_texture('Graphics/textures/letters/i.png', [self.letter_size] * 2),
            'l': self.get_texture('Graphics/textures/letters/l.png', [self.letter_size] * 2),
            's': self.get_texture('Graphics/textures/letters/s.png', [self.letter_size] * 2),
            'h': self.get_texture('Graphics/textures/letters/h.png', [self.letter_size] * 2),
            'e': self.get_texture('Graphics/textures/letters/e.png', [self.letter_size] * 2),
            'a': self.get_texture('Graphics/textures/letters/a.png', [self.letter_size] * 2),
            't': self.get_texture('Graphics/textures/letters/t.png', [self.letter_size] * 2),
        }
        self.colon_image = self.get_texture('Graphics/textures/letters/colon.png', [self.letter_size] * 2)
        self.percent_image = self.get_texture('Graphics/textures/digits/10.png', [self.letter_size] * 2)

    def draw(self):
        # Draw sky, objects, health, and kills on the screen
        self.draw_sky()
        self.render_objects()
        self.draw_health()
        self.draw_kills()

    def win(self):
        # Display win screen
        self.screen.blit(self.win_image, (0, 0))

    def game_over_screen(self):
        # Display game over screen
        self.screen.blit(self.game_over, (0, 0))

    def draw_health(self):
        # Draw the player's health on the screen
        word = 'health'
        word_width = len(word) * self.letter_size

        start_x = 10
        start_y = HEIGHT - self.letter_size - 10

        for i, char in enumerate(word):
            if char in self.letter_images:
                self.screen.blit(self.letter_images[char], (start_x + i * self.letter_size, start_y))

        colon_x = start_x + word_width
        self.screen.blit(self.colon_image, (colon_x, start_y))

        health = str(self.game.player.health)
        for i, char in enumerate(health):
            self.screen.blit(self.digits_dictionary[char], (colon_x + self.letter_size + i * self.digit_size, start_y))

        percent_x = colon_x + self.letter_size + len(health) * self.digit_size
        self.screen.blit(self.percent_image, (percent_x, start_y))

    def draw_kills(self):
        # Draw the number of kills on the screen
        word = 'kills'
        word_width = len(word) * self.letter_size

        start_x = WIDTH - (word_width + len(str(self.game.player.kills)) * self.digit_size + 2 * self.letter_size)
        start_y = HEIGHT - self.letter_size - 10

        for i, char in enumerate(word):
            if char in self.letter_images:
                self.screen.blit(self.letter_images[char], (start_x + i * self.letter_size, start_y))

        colon_x = start_x + word_width
        self.screen.blit(self.colon_image, (colon_x, start_y))

        kills = str(self.game.player.kills)
        for i, char in enumerate(kills):
            self.screen.blit(self.digits_dictionary[char], (colon_x + self.letter_size + i * self.digit_size, start_y))

    def draw_damage_screen(self):
        # Display damage screen when the player gets hurt
        self.screen.blit(self.damage_screen, (0, 0))

    def draw_sky(self):
        # Render the sky with an offset based on player movement
        self.sky_offset = (self.sky_offset + 4.5 * self.game.player.rel) % WIDTH
        self.screen.blit(self.sky_image, (-self.sky_offset, 0))
        self.screen.blit(self.sky_image, (WIDTH - self.sky_offset, 0))
        pygame.draw.rect(self.screen, FLOOR_COLOR, (0, HALF_HEIGHT, WIDTH, HEIGHT))

    def render_objects(self):
        # Render game objects sorted by depth
        objects_list = sorted(self.game.raycast.rendering_objects, key=lambda x: x[0], reverse=True)
        for depth, image, position in objects_list:
            self.screen.blit(image, position)

    @staticmethod
    def get_texture(path, resolution=(TEXTURE_SIZE, TEXTURE_SIZE)):
        # Load and scale texture from path
        texture = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(texture, resolution)

    def load_wall_textures(self):
        # Load wall textures into a dictionary
        return {
            1: self.get_texture('Graphics/textures/walls/pic1.png'),
            2: self.get_texture('Graphics/textures/walls/pic2.png'),
            3: self.get_texture('Graphics/textures/walls/pic3.png'),
            4: self.get_texture('Graphics/textures/walls/pic4.png'),
            5: self.get_texture('Graphics/textures/walls/pic5.png'),
        }
