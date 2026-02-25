import pygame


class Sound:
    def __init__(self, game):
        self.game = game
        pygame.mixer.init()
        self.path = 'Graphics/resources/sounds/'

        # В headless-режиме mixer выключен — все звуки None
        if game.headless:
            self.shoot = None
            self.player_damaged = None
            self.player_death = None
            self.music = None
            self.marine_death = None
            self.marine_damaged = None
            self.marine_attack = None
            self.lost_soul_death = None
            self.lost_soul_damaged = None
            self.lost_soul_attack = None
            self.cyber_demon_death = None
            self.cyber_demon_damaged = None
            self.cyber_demon_attack = None
            return

        pygame.mixer.init()
        self.shoot = pygame.mixer.Sound(self.path + 'pewgun.wav')
        self.player_damaged = pygame.mixer.Sound(self.path + 'player_damaged.wav')
        self.player_death = pygame.mixer.Sound(self.path + 'player_death.wav')
        self.music = pygame.mixer.music.load(self.path + 'background.mp3')

        # Marine sounds
        self.marine_death = pygame.mixer.Sound(self.path + 'marine_death.wav')
        self.marine_damaged = pygame.mixer.Sound(self.path + 'marine_damaged.wav')
        self.marine_attack = pygame.mixer.Sound(self.path + 'marine_attack.wav')

        # Lost Soul sounds
        self.lost_soul_death = pygame.mixer.Sound(self.path + 'lost_soul_death.wav')
        self.lost_soul_damaged = pygame.mixer.Sound(self.path + 'lost_soul_damaged.wav')
        self.lost_soul_attack = pygame.mixer.Sound(self.path + 'lost_soul_attack.wav')

        # Cyber Demon sounds
        self.cyber_demon_death = pygame.mixer.Sound(self.path + 'cyber_demon_death.wav')
        self.cyber_demon_damaged = pygame.mixer.Sound(self.path + 'cyber_demon_damaged.wav')
        self.cyber_demon_attack = pygame.mixer.Sound(self.path + 'cyber_demon_attack.wav')
