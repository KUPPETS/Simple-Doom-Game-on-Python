import pygame
from npc import *
from random import choices, choice, randrange
from settings import PLAYER_POSITION


class ObjectStorage:
    DUMMY_SPAWN_POSITIONS = [
        (2.5, 6.0),
        (2.5, 5.0),
        (2.5, 4.0),
        (1.5, 6.0),
        (1.5, 4.0),
    ]

    def __init__(self, game):
        self.game = game
        self.object_list = []
        self.npc_list = []
        self.npc_positions = set()


        self.npc_objects_path = 'Graphics/resources/nps/'
        self.static_objects_path = 'Graphics/resources/static_objects/'
        self.animated_objects_path = 'Graphics/resources/animated_objects/'

        # читаем phase_config из game
        cfg = getattr(game, "phase_config", {}) or {}
        self.enemies = cfg.get("enemies", 1)
        self.npc_types = cfg.get("npc_types", [LostSoulNPC, MarineNPC, CyberDemonNPC, DummyNPC])
        self.weights = cfg.get("weights", [0, 1, 0, 0])

        # NEW: Dummy spawn режим
        # "fixed"  -> из DUMMY_SPAWN_POSITIONS
        # "random" -> рандом по карте (по свободным тайлам)
        self.dummy_spawn = cfg.get("dummy_spawn", "fixed")
        # NEW: ограничение области рандома (x0, y0, x1, y1) или None
        self.dummy_random_area = cfg.get("dummy_random_area", None)

        px, py = int(PLAYER_POSITION[0]), int(PLAYER_POSITION[1])
        self.restricted_area = {(px + i, py + j) for i in range(-2, 3) for j in range(-2, 3)}

        self.spawn_npc()

        self.add_object(StaticObject(game))
        self.add_object(AnimatedObject(game))
        self.add_object(AnimatedObject(
            game,
            path='Graphics/resources/animated_objects/deadbody/deadbody1.png',
            pos=(8, 8),
            scale=0.6,
            shift=0.5
        ))

    def alive_count(self):
        return sum(1 for npc in self.npc_list if getattr(npc, "alive", True))

    def check_win(self):
        if self.alive_count() == 0:
            if getattr(self.game.player, "control_mode", "human") == "rl":
                self.game.win = True
            else:
                self.game.render.win()
                pygame.display.flip()
                pygame.time.delay(1500)
                self.game.new_game()

    def update(self):
        self.npc_positions = {
            npc.map_position for npc in self.npc_list
            if getattr(npc, "alive", True)
        }
        for obj in self.object_list:
            obj.update()
        for npc in self.npc_list:
            npc.update()
        self.check_win()

    # -------- helpers --------
    def _random_free_tile(self, area=None, max_tries=500):
        """
        Возвращает (x, y) в тайлах (int), гарантированно не стена и не restricted_area.
        area: (x0, y0, x1, y1) где x in [x0, x1), y in [y0, y1) (семантика randrange). [web:282]
        """
        if area is None:
            x0, y0, x1, y1 = 0, 0, self.game.map.cols, self.game.map.rows
        else:
            x0, y0, x1, y1 = area

        for _ in range(max_tries):
            x = randrange(x0, x1)
            y = randrange(y0, y1)
            if (x, y) in self.game.map.world_map:
                continue
            if (x, y) in self.restricted_area:
                continue
            return x, y

        # fallback
        return 1, 1

    def spawn_npc(self):
        for _ in range(self.enemies):
            npc_cls = choices(self.npc_types, self.weights)[0]

            if npc_cls is DummyNPC:
                if self.dummy_spawn == "random":
                    x, y = self._random_free_tile(area=self.dummy_random_area)
                    pos_xy = (x + 0.5, y + 0.5)
                else:
                    pos_xy = choice(self.DUMMY_SPAWN_POSITIONS)  # random.choice выбирает элемент из списка [web:293]

                self.add_npc(npc_cls(self.game, pos=pos_xy))
                continue

            # остальные NPC — random free tile
            x, y = self._random_free_tile()
            self.add_npc(npc_cls(self.game, pos=(x + 0.5, y + 0.5)))

    def add_npc(self, npc):
        self.npc_list.append(npc)

    def add_object(self, obj):
        self.object_list.append(obj)
