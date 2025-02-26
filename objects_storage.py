from npc import *
from random import choices, randrange


class ObjectStorage:
    def __init__(self, game):
        self.game = game
        self.object_list = []
        self.npc_list = []
        self.npc_objects_path = 'Graphics/resources/nps/'
        self.static_objects_path = 'Graphics/resources/static_objects/'
        self.animated_objects_path = 'Graphics/resources/animated_objects/'
        add_object = self.add_object
        add_npc = self.add_npc
        self.npc_positions = {}

        # spawn npc
        self.enemies = 1  # npc count
        self.npc_types = [LostSoulNPC, MarineNPC, CyberDemonNPC]
        self.weights = [0, 0, 20]
        self.restricted_area = {(i, j) for i in range(10) for j in range(10)}
        self.spawn_npc()

        # Objects map
        add_object(StaticObject(game))
        add_object(AnimatedObject(game))
        add_object(AnimatedObject(game, path='Graphics/resources/animated_objects/deadbody/deadbody1.png', pos=(8, 8),
                                  scale=0.6, shift=0.5))

    def check_win(self):
        if not len(self.npc_positions):
            self.game.render.win()
            pygame.display.flip()
            pygame.time.delay(1500)
            self.game.new_game()

    def update(self):
        self.npc_positions = {npc.map_position for npc in self.npc_list if npc.alive}
        [objects.update() for objects in self.object_list]
        [npc.update() for npc in self.npc_list]
        self.check_win()

    def spawn_npc(self):
        # Spawn NPCs at random positions
        for i in range(self.enemies):
            npc = choices(self.npc_types, self.weights)[0]
            pos = x, y = randrange(self.game.map.cols), randrange(self.game.map.rows)
            while (pos in self.game.map.world_map) or (pos in self.restricted_area):
                pos = x, y = randrange(self.game.map.cols), randrange(self.game.map.rows)
            self.add_npc(npc(self.game, pos=(x + 0.5, y + 0.5)))

    def add_npc(self, npc):
        # Add an NPC to the list
        self.npc_list.append(npc)

    def add_object(self, object):
        # Add an object to the list
        self.object_list.append(object)
