# main.py
import os
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
    def __init__(self, headless: bool = False, render: bool = True):
        """
        headless=True  -> без нормального окна (для обучения RL в ноутбуке)
        render=False   -> не делать draw/flip/caption (ускоряет обучение)
        """
        self.headless = headless
        self.render_enabled = render

        # флаги окончания эпизода (для RL)
        self.win = False
        self.dead = False

        # важно: env var должен быть выставлен ДО pygame.init() и set_mode()
        if self.headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        pygame.init()
        pygame.mouse.set_visible(False)

        # экран: нормальный для игры, 1x1 для headless
        if self.headless:
            pygame.display.set_mode((1, 1))
            self.screen = pygame.Surface((WIDTH, HEIGHT)).convert()
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        self.clock = pygame.time.Clock()
        self.delta_time = 1

        # если тебе нужен глобальный триггер/таймер для NPC — оставляем
        self.global_trigger = False
        self.global_event = pygame.USEREVENT + 0
        pygame.time.set_timer(self.global_event, 50)

        # создание объектов
        self.sound = Sound(self)
        self.map = Map(self)
        self.player = Player(self)
        self.render = ObjectRender(self)
        self.raycast = RayCast(self)
        self.objects_storage = ObjectStorage(self)
        self.weapon = Weapon(self)
        self.pathfinding = PathFindingAlgorithm(self)

        self.new_game()

    def new_game(self):
        # пересоздаём состояние мира
        self.win = False
        self.dead = False

        self.map = Map(self)
        self.player = Player(self)
        self.render = ObjectRender(self)
        self.raycast = RayCast(self)
        self.objects_storage = ObjectStorage(self)
        self.weapon = Weapon(self)
        self.sound = Sound(self)
        self.pathfinding = PathFindingAlgorithm(self)

        # музыку можно оставить только для human режима
        if not self.headless:
            pygame.mixer.music.play(-1)

    # --- RL: применить дискретное действие ---
    def apply_action(self, action: int):
        """
        Действия (пример):
        0 noop
        1 turn_left
        2 turn_right
        3 move_forward
        4 shoot
        """
        # Player должен быть пропатчен: control_mode + set_rl_action(...)
        self.player.control_mode = "rl"
        move = 1 if action == 3 else 0
        turn = -1 if action == 1 else (1 if action == 2 else 0)
        shoot = (action == 4)
        self.player.set_rl_action(move=move, strafe=0, turn=turn, shoot=shoot)

    # --- 1 тик симуляции (без вечного цикла) ---
    def tick(self):
        # обновляем логику
        self.player.update()
        self.raycast.update()
        self.objects_storage.update()
        self.weapon.update()

        # тайминг
        self.delta_time = self.clock.tick(FPS)

        # всё, что связано с окном — только если render_enabled
        if self.render_enabled and (not self.headless):
            pygame.display.set_caption(f"{self.clock.get_fps():.1f}")

    def draw(self):
        if not self.render_enabled:
            return
        self.render.draw()
        self.weapon.draw()

    def flip(self):
        if not self.render_enabled:
            return
        if not self.headless:
            pygame.display.flip()

    # --- события нужны только для human режима ---
    def check_events(self):
        self.global_trigger = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.close()
                sys.exit()

            elif event.type == self.global_event:
                self.global_trigger = True

            # стрельба мышью — только human
            self.player.single_shoot(event)

    def close(self):
        pygame.quit()

    # --- основной цикл (для игры человеком) ---
    def run(self):
        # для человека включаем human режим
        self.player.control_mode = "human"
        self.render_enabled = True

        while True:
            self.check_events()
            self.tick()
            self.draw()
            self.flip()


if __name__ == "__main__":
    game = Game(headless=False, render=True)
    game.run()
