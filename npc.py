# npc.py
from objects import *
from random import randint, choice, random
import math

CONST = 1e-6  # защита от деления на ноль везде в файле


class NPC(AnimatedObject):
    def __init__(self, game, path, pos, scale, shift, animation_time):
        super().__init__(game, path, pos, scale, shift, animation_time)
        self.attack_images = self.get_images(self.path + '/attack')
        self.death_images = self.get_images(self.path + '/death')
        self.rotation_images = self.get_images(self.path + '/rotation')
        self.movement_images = self.get_images(self.path + '/movement')
        self.damage_images = self.get_images(self.path + '/damage')

        self.attack_distance = randint(3, 6)
        self.size = 10
        self.health = 100
        self.speed = 0.03
        self.damage = 10
        self.accuracy = 0.2
        self.alive = True
        self.pain = False
        self.ray_casting_value = False
        self.frame_counter = 0
        self.player_search_trigger = False

        self.attack_sound = None
        self.damaged_sound = None
        self.death_sound = None

    def update(self):
        self.check_animation_time()
        self.get_object()
        self.logic()

    def check_walls(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_collision(self, dx, dy):
        if self.check_walls(int(self.x + dx * self.size), int(self.y)):
            self.x += dx
        if self.check_walls(int(self.x), int(self.y + dy * self.size)):
            self.y += dy

    def movement(self):
        path = self.game.pathfinding.get_path(self.map_position, self.game.player.map_position)
        if len(path) > 1:
            next_position = path[1]
            next_x_position, next_y_position = next_position
            if next_position not in self.game.objects_storage.npc_positions:
                angle = math.atan2(next_y_position + 0.5 - self.y, next_x_position + 0.5 - self.x)
                dx = math.cos(angle) * self.speed
                dy = math.sin(angle) * self.speed
                self.check_collision(dx, dy)

    def attack(self):
        if self.animation_trigger:
            if self.attack_sound and not self.game.headless:
                self.attack_sound.play()
            if random() < self.accuracy:
                self.game.player.getting_damage(self.damage)

    def animation_of_death(self):
        if not self.alive:
            if self.game.global_trigger and self.frame_counter < len(self.death_images) - 1:
                self.death_images.rotate(-1)
                self.image = self.death_images[0]
                self.frame_counter += 1

    def damage_animation(self):
        self.animation(self.damage_images)
        if self.animation_trigger:
            self.pain = False

    def check_damage_to_npc(self):
        if self.ray_casting_value and self.game.player.shot:
            if HALF_WIDTH - self.object_half_width < self.screen_x < HALF_WIDTH + self.object_half_width:
                if self.damaged_sound and not self.game.headless:
                    self.damaged_sound.play()
                self.game.player.shot = False
                self.pain = True
                self.health -= self.game.weapon.damage
                self.check_health()

    def check_health(self):
        if self.health < 1:
            self.alive = False
            if self.death_sound and not self.game.headless:
                self.death_sound.play()
            self.game.player.add_kill()

    def logic(self):
        if self.alive:
            self.ray_casting_value = self.ray_casting_player_to_npc()
            self.check_damage_to_npc()

            if self.pain:
                self.damage_animation()
            elif self.ray_casting_value:
                self.player_search_trigger = True
                if self.distance < self.attack_distance:
                    self.animation(self.attack_images)
                    self.attack()
                else:
                    self.animation(self.movement_images)
                    self.movement()
            elif self.player_search_trigger:
                self.animation(self.movement_images)
                self.movement()
            else:
                self.animation(self.rotation_images)
        else:
            self.animation_of_death()

    @property
    def map_position(self):
        return int(self.x), int(self.y)

    def ray_casting_player_to_npc(self):
        if self.game.player.map_position == self.map_position:
            return True

        wall_distance_vertical, wall_distance_horizontal = 0, 0
        player_distance_vertical, player_distance_horizontal = 0, 0

        ox, oy = self.game.player.position
        x_map, y_map = self.game.player.map_position

        ray_angle = self.theta

        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        # ── вертикальные пересечения ──────────────────────────────────────
        x_vertical, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)
        depth_vertical = (x_vertical - ox) / (cos_a if abs(cos_a) > CONST else CONST)
        y_vertical = oy + depth_vertical * sin_a
        delta_depth = dx / (cos_a if abs(cos_a) > CONST else CONST)
        dy = delta_depth * sin_a

        for _ in range(MAX_DEPTH):
            tile_vertical = int(x_vertical), int(y_vertical)
            if tile_vertical == self.map_position:
                player_distance_vertical = depth_vertical
                break
            if tile_vertical in self.game.map.world_map:
                wall_distance_vertical = depth_vertical
                break
            x_vertical += dx
            y_vertical += dy
            depth_vertical += delta_depth

        # ── горизонтальные пересечения ────────────────────────────────────
        y_horizontal, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)
        depth_horizontal = (y_horizontal - oy) / (sin_a if abs(sin_a) > CONST else CONST)
        x_horizontal = ox + depth_horizontal * cos_a
        delta_depth = dy / (sin_a if abs(sin_a) > CONST else CONST)
        dx = delta_depth * cos_a

        for _ in range(MAX_DEPTH):
            tile_horizontal = int(x_horizontal), int(y_horizontal)
            if tile_horizontal == self.map_position:
                player_distance_horizontal = depth_horizontal
                break
            if tile_horizontal in self.game.map.world_map:
                wall_distance_horizontal = depth_horizontal
                break
            x_horizontal += dx
            y_horizontal += dy
            depth_horizontal += delta_depth

        player_distance = max(player_distance_horizontal, player_distance_vertical)
        wall_distance = max(wall_distance_horizontal, wall_distance_vertical)

        if 0 < player_distance < wall_distance or not wall_distance:
            return True
        return False


class MarineNPC(NPC):
    def __init__(self, game, path='Graphics/resources/nps/marine/starting.png',
                 pos=(10.5, 5.5), scale=0.8, shift=0.3, animation_time=180):
        super().__init__(game, path, pos, scale, shift, animation_time)
        self.attack_sound = game.sound.marine_attack
        self.damaged_sound = game.sound.marine_damaged
        self.death_sound = game.sound.marine_death



class LostSoulNPC(NPC):
    def __init__(self, game, path='Graphics/resources/nps/lost_soul/starting.png',
                 pos=(10.5, 6.5), scale=1, shift=0.1, animation_time=250):
        super().__init__(game, path, pos, scale, shift, animation_time)
        self.attack_distance = 1.0
        self.health = 100    # снижено с 150 — 2 попадания вместо 3, легче учить
        self.damage = 5     # было 0 — теперь кусает, есть сигнал уворачиваться
        self.speed = 0.05
        self.accuracy = 0.35
        self.attack_sound = game.sound.lost_soul_attack
        self.damaged_sound = game.sound.lost_soul_damaged
        self.death_sound = game.sound.lost_soul_death


class CyberDemonNPC(NPC):
    def __init__(self, game, path='Graphics/resources/nps/cyber_demon/starting.png',
                 pos=(10.6, 6.5), scale=1.6, shift=-0.1, animation_time=200):
        super().__init__(game, path, pos, scale, shift, animation_time)
        self.attack_distance = randint(4, 8)
        self.health = 300
        self.damage = 35
        self.speed = 0.04
        self.accuracy = 0.4
        self.attack_sound = game.sound.cyber_demon_attack
        self.damaged_sound = game.sound.cyber_demon_damaged
        self.death_sound = game.sound.cyber_demon_death
class DummyNPC(NPC):
    """Неподвижная мишень для первичного обучения — 1 хит, не атакует"""
    def __init__(self, game, path='Graphics/resources/nps/marine/starting.png',
                 pos=(10.5, 5.5), scale=0.8, shift=0.3, animation_time=180):
        super().__init__(game, path, pos, scale, shift, animation_time)
        self.health = 1        # 1 хит — убивается с первого выстрела
        self.speed = 0.0       # стоит на месте
        self.damage = 0        # не атакует
        self.accuracy = 0.0
        self.attack_distance = 0