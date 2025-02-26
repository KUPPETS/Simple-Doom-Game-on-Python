import pygame
import math
from settings import *


class Player:
    def __init__(self, game):
        self.game = game
        self.x, self.y = PLAYER_POSITION
        self.angle = PLAYER_ANGLE
        self.shot = False
        self.health = PLAYER_HEALTH
        self.rel = 0
        self.kills = 0
        self.health_regen_delay = 1000
        self.time_previous = pygame.time.get_ticks()

    def regen_health(self):
        if self.check_health_regen() and self.health < PLAYER_HEALTH:
            self.health += 1

    def check_health_regen(self):
        time_now = pygame.time.get_ticks()
        if time_now - self.time_previous > self.health_regen_delay:
            self.time_previous = time_now
            return True

    def game_over(self):
        if self.health < 1:
            self.game.render.game_over_screen()
            pygame.display.flip()
            pygame.time.delay(3000)
            self.game.new_game()

    def getting_damage(self, damage):
        self.health -= damage
        self.game.render.draw_damage_screen()
        self.game.sound.player_damaged.play()
        self.game_over()

    def single_shoot(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and not self.shot and not self.game.weapon.reloading:
                self.game.sound.shoot.play()
                self.shot = True
                self.game.weapon.reloading = True

    def movement(self):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        dx, dy = 0, 0
        speed = PLAYER_SPEED * self.game.delta_time
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            dx += speed_cos
            dy += speed_sin
        if keys[pygame.K_s]:
            dx += -speed_cos
            dy += -speed_sin
        if keys[pygame.K_a]:
            dx += speed_sin
            dy += -speed_cos
        if keys[pygame.K_d]:
            dx += -speed_sin
            dy += speed_cos

        self.check_collision(dx, dy)
        self.angle %= math.pi * 2

    def check_walls(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_collision(self, dx, dy):
        scale = PLAYER_SIZE / self.game.delta_time
        if self.check_walls(int(self.x + dx * scale), int(self.y)):
            self.x += dx
        if self.check_walls(int(self.x), int(self.y + dy * scale)):
            self.y += dy

    def draw(self):
        pygame.draw.circle(self.game.screen, 'green', (self.x * 100, self.y * 100), 15)
        pygame.draw.line(self.game.screen, 'red', (self.x * 100, self.y * 100),
                         (self.x * 100 + WIDTH * math.cos(self.angle), self.y * 100 + WIDTH * math.sin(self.angle)), 2)

    def mouse_motion(self):
        mx, my = pygame.mouse.get_pos()
        if mx < MOUSE_BORDER_LEFT or mx > MOUSE_BORDER_RIGHT:
            pygame.mouse.set_pos((HALF_WIDTH, HALF_HEIGHT))

        self.rel = pygame.mouse.get_rel()[0]
        self.rel = max(-MOUSE_MAX_RELATIVE, min(MOUSE_MAX_RELATIVE, self.rel))
        self.angle += self.rel * MOUSE_SENSITIVITY * self.game.delta_time

    def update(self):
        self.movement()
        self.mouse_motion()
        self.regen_health()

    @property
    def position(self):
        return self.x, self.y

    @property
    def map_position(self):
        return int(self.x), int(self.y)

    def add_kill(self):
        self.kills += 1
