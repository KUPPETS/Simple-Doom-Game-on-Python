# doom_env.py
import numpy as np
import gymnasium as gym
from gymnasium import spaces

from main import Game


class DoomEnv(gym.Env):
    """
    RL environment wrapper for Simple Doom (pygame).
    Observation: raycast depths + sin/cos(angle) + health + alive_npcs
    Actions: 0 noop, 1 turn_left, 2 turn_right, 3 move_forward, 4 shoot
    """
    metadata = {"render_modes": ["none"]}

    def __init__(self, max_steps: int = 1500, depth_clip: float = 20.0):
        super().__init__()
        self.max_steps = int(max_steps)
        self.depth_clip = float(depth_clip)

        self.action_space = spaces.Discrete(5)

        # observation_space зададим после первого reset() когда узнаем размер
        self.observation_space = None

        self.game = None
        self.step_count = 0
        self.prev_kills = 0
        self.prev_health = 0

    def _alive_count(self) -> int:
        return sum(1 for npc in self.game.objects_storage.npc_list if getattr(npc, "alive", True))

    def _get_obs(self) -> np.ndarray:
        # ray_cast_result: list of tuples (depth, proj_height, texture, offset)
        depths = np.array([t[0] for t in self.game.raycast.ray_cast_result], dtype=np.float32)
        depths = np.clip(depths, 0.0, self.depth_clip) / self.depth_clip

        ang = float(self.game.player.angle)
        health = np.float32(self.game.player.health / 100.0)
        alive = np.float32(self._alive_count())

        obs = np.concatenate([
            depths,
            np.array([np.sin(ang), np.cos(ang), health, alive], dtype=np.float32)
        ]).astype(np.float32)

        return obs

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.step_count = 0

        # headless + no render for training
        self.game = Game(headless=True, render=False)
        self.game.player.control_mode = "rl"

        # прогреть 1 тик, чтобы raycast_result не был пустой
        self.game.tick()

        obs = self._get_obs()

        if self.observation_space is None:
            self.observation_space = spaces.Box(
                low=-np.inf, high=np.inf, shape=obs.shape, dtype=np.float32
            )

        self.prev_kills = self.game.player.kills
        self.prev_health = self.game.player.health

        info = {}
        return obs, info

    def step(self, action):
        self.step_count += 1

        self.game.apply_action(int(action))
        self.game.tick()

        # reward: +1 per kill, small time penalty, penalty for taking damage
        kills = self.game.player.kills
        health = self.game.player.health
        dk = kills - self.prev_kills
        dh = self.prev_health - health  # >0 means took damage

        reward = 1.0 * dk - 0.001
        if dh > 0:
            reward -= 0.05 * float(dh)

        self.prev_kills = kills
        self.prev_health = health

        terminated = bool(self.game.win or self.game.dead)
        truncated = bool(self.step_count >= self.max_steps)

        obs = self._get_obs()
        info = {"kills": kills, "alive": self._alive_count(), "health": health}

        return obs, float(reward), terminated, truncated, info

    def close(self):
        if self.game is not None:
            self.game.close()
            self.game = None
