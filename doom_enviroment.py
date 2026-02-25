# doom_enviroment.py
import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces

from main import Game
from settings import NUMBER_RAYS


class DoomEnv(gym.Env):
    """
    Actions: 0 noop, 1 turn_left, 2 turn_right, 3 forward, 4 shoot,
             5 shoot+turn_left, 6 shoot+turn_right
    """
    metadata = {"render_modes": ["none"]}

    # Дефолтные коэффициенты наград — можно переопределить через phase_config["rewards"]
    DEFAULT_REWARDS = {
        "kill":           100.0,  # за каждое убийство
        "aim_max":          0.5,  # макс бонус за прицеливание (враг виден)
        "aim_angle":       30.0,  # угловой конус прицеливания, градусы
        "no_vis_penalty":  -0.05, # штраф за каждый шаг, пока враг не виден
        "approach":         0.3,  # коэф. сближения с врагом
        "aim_track":        0.1,  # коэф. трекинга наводки
        "damage":          -0.1,  # штраф за единицу полученного урона
    }

    def __init__(
        self,
        max_steps: int = 600,
        depth_clip: float = 20.0,
        phase_config: dict | None = None,
    ):
        super().__init__()
        self.max_steps = int(max_steps)
        self.depth_clip = float(depth_clip)

        # phase_config передаётся из ноутбука, применяется в reset()
        # Поддерживаемые ключи:
        #   "npc_types"  : list[type]  — классы NPC для спавна
        #   "weights"    : list[int]   — веса для random.choices
        #   "enemies"    : int         — кол-во NPC на карте
        #   "rewards"    : dict        — переопределение коэффициентов наград
        self.phase_config = phase_config or {}

        # Собираем итоговые коэффициенты наград (дефолт + переопределения)
        self.R = {**self.DEFAULT_REWARDS, **self.phase_config.get("rewards", {})}

        self.action_space = spaces.Discrete(11)

        obs_dim = NUMBER_RAYS + 10   # было +8; +2: npc_hp_norm, reloading
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )

        self.game = None
        self.step_count = 0
        self.prev_kills = 0
        self.prev_health = 0
        self.prev_npc_dist = 0.0
        self.prev_abs_err = 0.0

    # ---- phase config ----

    def _apply_phase_config(self):
        """Применяет phase_config к ObjectStorage после new_game()."""
        cfg = self.phase_config
        storage = self.game.objects_storage

        if "npc_types" in cfg:
            storage.npc_types = cfg["npc_types"]
        if "weights" in cfg:
            storage.weights = cfg["weights"]
        if "enemies" in cfg:
            storage.enemies = cfg["enemies"]

        if any(k in cfg for k in ("npc_types", "weights", "enemies")):
            # Пересоздаём NPC с новыми параметрами
            storage.npc_list.clear()
            storage.npc_positions.clear()
            storage.spawn_npc()

    # ---- helpers ----

    def _alive_count(self) -> int:
        return sum(1 for npc in self.game.objects_storage.npc_list
                   if getattr(npc, "alive", True))

    def _alive_npcs(self):
        return [n for n in self.game.objects_storage.npc_list
                if getattr(n, "alive", True)]

    @staticmethod
    def _wrap_pi(a: float) -> float:
        return (a + math.pi) % (2 * math.pi) - math.pi

    def _nearest_npc_features(self):
        alive = self._alive_npcs()
        if not alive:
            return 0.0, 0.0, 1.0, 0.0, 0.0

        px, py = float(self.game.player.x), float(self.game.player.y)
        best = min(alive, key=lambda n: math.hypot(float(n.x) - px, float(n.y) - py))

        nx, ny = float(best.x), float(best.y)
        dist = math.hypot(nx - px, ny - py)
        ang_to = math.atan2(ny - py, nx - px)
        err = self._wrap_pi(ang_to - float(self.game.player.angle))
        vis = 1.0 if getattr(best, "ray_casting_value", False) else 0.0
        npc_hp = float(getattr(best, "health", 100))
        npc_hp_norm = max(0.0, min(1.0, npc_hp / 100.0))

        return dist, math.sin(err), math.cos(err), vis, npc_hp_norm

    def _get_obs(self) -> np.ndarray:
        depths = np.array(
            [t[0] for t in self.game.raycast.ray_cast_result], dtype=np.float32
        )
        if depths.size < NUMBER_RAYS:
            depths = np.pad(depths, (0, NUMBER_RAYS - depths.size), mode="edge")
        else:
            depths = depths[:NUMBER_RAYS]
        depths = np.clip(depths, 0.0, self.depth_clip) / self.depth_clip

        ang = float(self.game.player.angle)
        health = float(self.game.player.health) / 100.0
        alive_scaled = min(float(self._alive_count()), 10.0) / 10.0

        dist, sin_err, cos_err, vis, npc_hp_norm = self._nearest_npc_features()
        dist_scaled = min(dist, 20.0) / 20.0
        reloading = 1.0 if self.game.weapon.reloading else 0.0

        tail = np.array([
            math.sin(ang), math.cos(ang), health, alive_scaled,
            dist_scaled, sin_err, cos_err, vis,
            npc_hp_norm, reloading,   # новые признаки
        ], dtype=np.float32)

        return np.concatenate([depths, tail]).astype(np.float32)

    # ---- Gymnasium API ----

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.step_count = 0

        if self.game is None:
            self.game = Game(headless=True, render=False)
        else:
            self.game.new_game()

        self._apply_phase_config()  # <-- применяем конфиг

        self.game.player.control_mode = "rl"
        self.game.tick()

        self.prev_kills = self.game.player.kills
        self.prev_health = self.game.player.health

        alive = self._alive_npcs()
        if alive:
            dist, _, cos_err, _, _ = self._nearest_npc_features()
            self.prev_npc_dist = dist
            self.prev_abs_err = abs(self._wrap_pi(
                math.atan2(
                    float(alive[0].y) - float(self.game.player.y),
                    float(alive[0].x) - float(self.game.player.x)
                ) - float(self.game.player.angle)
            ))
        else:
            self.prev_npc_dist = 0.0
            self.prev_abs_err = 0.0

        return self._get_obs(), {}

    def step(self, action):
        self.step_count += 1

        self.game.apply_action(int(action))
        self.game.tick()

        kills = self.game.player.kills
        health = self.game.player.health
        dk = kills - self.prev_kills
        dh = self.prev_health - health

        dist, sin_err, cos_err, vis, _ = self._nearest_npc_features()
        abs_err = math.acos(max(-1.0, min(1.0, cos_err)))

        # ---- reward ----
        R = self.R
        reward = 0.0
        reward += R["kill"] * dk                                       # убийство

        if vis > 0.5:
            # dense: постоянный бонус за прицеливание
            aim_cone = math.radians(R["aim_angle"])
            aim_bonus = R["aim_max"] * max(0.0, 1.0 - abs_err / aim_cone)
            reward += aim_bonus
        else:
            # штраф пока враг не виден — ищи его
            reward += R["no_vis_penalty"]

        reward += R["approach"] * (self.prev_npc_dist - dist)         # сближение
        reward += R["aim_track"] * (self.prev_abs_err - abs_err) * (1.0 if vis > 0.5 else 0.1)  # наводка
        if dh > 0:
            reward += R["damage"] * float(dh)                         # урон

        self.prev_kills = kills
        self.prev_health = health
        self.prev_npc_dist = dist
        self.prev_abs_err = abs_err

        terminated = bool(self.game.win or self.game.dead)
        truncated = bool(self.step_count >= self.max_steps)

        obs = self._get_obs()
        info = {"kills": kills, "alive": self._alive_count(), "health": health}
        return obs, float(reward), terminated, truncated, info

    def close(self):
        if self.game is not None:
            self.game.close()
            self.game = None
