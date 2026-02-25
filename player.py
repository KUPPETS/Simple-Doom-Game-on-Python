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

        # --- RL control fields ---
        self.control_mode = "human"  # "human" or "rl"
        self.rl_move = 0             # -1 back, 0 none, +1 forward
        self.rl_strafe = 0           # -1 left, 0 none, +1 right
        self.rl_turn = 0             # -1 left, 0 none, +1 right

        # RL стрельба как "клик"
        self.rl_shoot_request = False

    # ---------- RL API ----------
    def set_rl_action(self, move=0, strafe=0, turn=0, shoot=False):
        self.rl_move = int(move)
        self.rl_strafe = int(strafe)
        self.rl_turn = int(turn)
        if shoot:
            self.rl_shoot_request = True

    def rl_shoot_step(self):
        if self.rl_shoot_request and (not self.game.weapon.reloading) and (not self.shot):
            try:
                self.game.sound.shoot.play()
            except Exception:
                pass
            self.shot = True
            self.game.weapon.reloading = True
        self.rl_shoot_request = False

    # ---------- Health ----------
    def regen_health(self):
        if self.check_health_regen() and self.health < PLAYER_HEALTH:
            self.health += 1

    def check_health_regen(self):
        time_now = pygame.time.get_ticks()
        if time_now - self.time_previous > self.health_regen_delay:
            self.time_previous = time_now
            return True
        return False

    def game_over(self):
        if self.health < 1:
            if getattr(self, "control_mode", "human") == "rl":
                self.game.dead = True
            else:
                self.game.render.game_over_screen()
                pygame.display.flip()
                pygame.time.delay(3000)
                self.game.new_game()

    def getting_damage(self, damage):
        self.health -= damage
        if getattr(self, "control_mode", "human") != "rl":
            self.game.render.draw_damage_screen()
        try:
            self.game.sound.player_damaged.play()
        except Exception:
            pass
        self.game_over()

    # ---------- Human input ----------
    def single_shoot(self, event):
        if self.control_mode != "human":
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and (not self.shot) and (not self.game.weapon.reloading):
                self.game.sound.shoot.play()
                self.shot = True
                self.game.weapon.reloading = True

    # ---------- Movement / rotation ----------
    def movement(self):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)

        dx, dy = 0.0, 0.0
        speed = PLAYER_SPEED * self.game.delta_time
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a

        if self.control_mode == "human":
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
        else:
            if self.rl_move == 1:
                dx += speed_cos
                dy += speed_sin
            elif self.rl_move == -1:
                dx += -speed_cos
                dy += -speed_sin

            if self.rl_strafe == -1:
                dx += speed_sin
                dy += -speed_cos
            elif self.rl_strafe == 1:
                dx += -speed_sin
                dy += speed_cos

        self.check_collision(dx, dy)
        self.angle %= (math.pi * 2)

    def mouse_motion(self):
        if self.control_mode == "human":
            mx, my = pygame.mouse.get_pos()
            if mx < MOUSE_BORDER_LEFT or mx > MOUSE_BORDER_RIGHT:
                pygame.mouse.set_pos((HALF_WIDTH, HALF_HEIGHT))

            self.rel = pygame.mouse.get_rel()[0]
            self.rel = max(-MOUSE_MAX_RELATIVE, min(MOUSE_MAX_RELATIVE, self.rel))
            self.angle += self.rel * MOUSE_SENSITIVITY * self.game.delta_time
        else:
            turn_speed = 0.02
            self.rel = self.rl_turn
            self.angle += self.rl_turn * turn_speed

    # ---------- Collision ----------
    def check_walls(self, x, y):
        # x,y в тайлах; вне карты считаем стеной
        if x < 0 or y < 0 or x >= self.game.map.cols or y >= self.game.map.rows:
            return False
        return (int(x), int(y)) not in self.game.map.world_map

    def check_collision(self, dx, dy):
        # радиус игрока в тайлах (подстрой 0.15..0.30 если нужно)
        r = 0.20

        # X
        nx = self.x + dx
        if (self.check_walls(nx - r, self.y - r) and
            self.check_walls(nx - r, self.y + r) and
            self.check_walls(nx + r, self.y - r) and
            self.check_walls(nx + r, self.y + r)):
            self.x = nx

        # Y
        ny = self.y + dy
        if (self.check_walls(self.x - r, ny - r) and
            self.check_walls(self.x - r, ny + r) and
            self.check_walls(self.x + r, ny - r) and
            self.check_walls(self.x + r, ny + r)):
            self.y = ny

        # страховка от выхода за карту
        self.x = max(0.5, min(self.x, self.game.map.cols - 0.5))
        self.y = max(0.5, min(self.y, self.game.map.rows - 0.5))

    # ---------- Update ----------
    def update(self):
        self.movement()
        self.mouse_motion()

        if self.control_mode == "rl":
            self.rl_shoot_step()

        self.regen_health()

    # ---------- Utils ----------
    def draw(self):
        pygame.draw.circle(self.game.screen, 'green', (self.x * 100, self.y * 100), 15)
        pygame.draw.line(
            self.game.screen, 'red', (self.x * 100, self.y * 100),
            (self.x * 100 + WIDTH * math.cos(self.angle), self.y * 100 + WIDTH * math.sin(self.angle)), 2
        )

    @property
    def position(self):
        return self.x, self.y

    @property
    def map_position(self):
        return int(self.x), int(self.y)

    def add_kill(self):
        self.kills += 1
