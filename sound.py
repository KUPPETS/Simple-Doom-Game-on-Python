import pygame


class Sound:
    def __init__(self, game):
        self.game = game
        pygame.mixer.init()
        self.path = 'Graphics/resources/sounds/'
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
