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
    def __init__(self, headless: bool = False, render: bool = True, phase_config: dict = None):
        """
        headless=True     -> no window (for RL training)
        render=False      -> skip all rendering calls (faster tick)
        phase_config=dict -> NPC types/weights/enemies/rewards for RL phases
        """
        self.headless = headless
        self.render_enabled = render
        self.phase_config = phase_config or {}

        self.win = False
        self.dead = False

        # Headless driver handling
        if self.headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
        else:
            if os.environ.get("SDL_VIDEODRIVER") == "dummy":
                os.environ.pop("SDL_VIDEODRIVER", None)

        pygame.init()

        if not self.headless:
            pygame.mouse.set_visible(False)

        if self.headless:
            pygame.display.set_mode((1, 1))
            self.screen = pygame.Surface((WIDTH, HEIGHT)).convert()
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        self.clock = pygame.time.Clock()
        self.delta_time = 16

        self.global_trigger = False
        self.global_event = pygame.USEREVENT + 0
        pygame.time.set_timer(self.global_event, 50)

        self.new_game()

    def new_game(self):
        self.win = False
        self.dead = False

        self.map = Map(self)
        self.player = Player(self)
        self.render = ObjectRender(self)
        self.raycast = RayCast(self)
        self.sound = Sound(self)
        self.objects_storage = ObjectStorage(self)
        self.weapon = Weapon(self)
        self.pathfinding = PathFindingAlgorithm(self)

        if not self.headless:
            pygame.mixer.music.play(-1)

    def apply_action(self, action: int):
        """
         0  noop
         1  turn_left
         2  turn_right
         3  move_forward
         4  shoot
         5  shoot + turn_left
         6  shoot + turn_right
         7  strafe_left
         8  strafe_right
         9  shoot + strafe_left
         10 shoot + strafe_right
        """
        self.player.control_mode = "rl"

        move = 1 if action == 3 else 0
        turn = -1 if action in (1, 5) else (1 if action in (2, 6) else 0)
        strafe = -1 if action in (7, 9) else (1 if action in (8, 10) else 0)
        shoot = action in (4, 5, 6, 9, 10)

        self.player.set_rl_action(move=move, strafe=strafe, turn=turn, shoot=shoot)

    def tick(self):
        if self.headless or not self.render_enabled:
            self.delta_time = 16
        else:
            self.delta_time = max(1, self.clock.tick(FPS))

        self.player.update()
        self.raycast.update(render=not (self.headless or not self.render_enabled))
        self.objects_storage.update()
        self.weapon.update()

        if self.render_enabled and not self.headless:
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

    def check_events(self):
        self.global_trigger = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                self.close()
                sys.exit()
            elif event.type == self.global_event:
                self.global_trigger = True
            self.player.single_shoot(event)

    def close(self):
        pygame.quit()

    def run(self):
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
