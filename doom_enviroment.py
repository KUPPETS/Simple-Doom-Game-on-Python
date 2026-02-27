import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces

from main import Game
from settings import NUMBER_RAYS


class DoomEnv(gym.Env):
    metadata = {"render_modes": ["none", "human"]}

    DEFAULT_REWARDS = {
        "kill": 100.0,
        "step_penalty": -0.1,
        "no_vis_penalty": -0.1,

        # tile overstay
        "tile_stay_limit": 99999,
        "tile_stay_penalty": 0.0,

        # terminal rewards
        "win_bonus": 0.0,
        "death_penalty": 0.0,

        # выключено по дефолту
        "aim_max": 0.0,
        "aim_angle": 35.0,
        "aim_track": 0.0,
        "approach": 0.0,
        "explore_bonus": 0.0,
        "see_bonus": 0.0,
        "idle_penalty": 0.0,
        "aim_decay_horizon": 60,
        "aim_no_shoot_penalty": 0.0,
        "shoot_aimed_bonus": 0.0,
        "damage": 0.0,
        "approach_invis_scale": 0.0,
    }

    def __init__(
        self,
        max_steps: int = 400,
        depth_clip: float = 20.0,
        phase_config: dict | None = None,
        render_game: bool = False,
        ray_count_override: int | None = None,
    ):
        super().__init__()
        self.max_steps = int(max_steps)
        self.depth_clip = float(depth_clip)
        self.phase_config = phase_config or {}
        self.render_game = bool(render_game)

        self.ray_count = int(ray_count_override) if ray_count_override is not None else NUMBER_RAYS
        self.R = {**self.DEFAULT_REWARDS, **self.phase_config.get("rewards", {})}

        self.action_space = spaces.Discrete(11)
        obs_dim = self.ray_count + 10
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )

        self.game = None
        self.step_count = 0

        self.prev_kills = 0
        self.prev_health = 0
        self.prev_npc_dist = 0.0
        self.prev_abs_err = 0.0
        self.prev_vis = 0.0

        self.visited = set()
        self.tile_visit_counts = {}

        # last-seen memory
        self.last_seen_dist = 20.0
        self.last_seen_sin_err = 0.0
        self.last_seen_cos_err = 1.0
        self.last_seen_hp_norm = 1.0
        self.steps_since_seen = 9999

        # cached npc features (set in step/reset, read in _get_obs)
        self._cached_npc_features = (20.0, 0.0, 1.0, 0.0, 1.0)

        # anti-stuck
        self.stuck_steps = 0
        self.stuck_eps = 0.002
        self.stuck_patience = 100
        self.stuck_penalty = -1.0
        self._prev_pos = None

        # actions
        self.MOVE_ACTIONS = {3, 7, 8, 9, 10}
        self.SHOOT_ACTIONS = {4, 5, 6, 9, 10}

        self.collision_eps = 0.005
        self.collision_penalty = -0.1
        self.collision_escalate = -0.01
        self.collision_streak = 0

        self.continuous_aim_steps = 0

        # tile overstay
        self.current_tile = None
        self.tile_stay_steps = 0

    def _apply_phase_config(self):
        cfg = self.phase_config
        storage = self.game.objects_storage
        changed_spawn = False

        if "npc_types" in cfg:
            storage.npc_types = cfg["npc_types"]
            changed_spawn = True
        if "weights" in cfg:
            storage.weights = cfg["weights"]
            changed_spawn = True
        if "enemies" in cfg:
            storage.enemies = cfg["enemies"]
            changed_spawn = True
        if "dummy_spawn" in cfg:
            storage.dummy_spawn = cfg["dummy_spawn"]
            changed_spawn = True
        if "dummy_random_area" in cfg:
            storage.dummy_random_area = cfg["dummy_random_area"]
            changed_spawn = True

        if changed_spawn:
            storage.npc_list.clear()
            storage.npc_positions.clear()
            storage.spawn_npc()

        self.R = {**self.DEFAULT_REWARDS, **self.phase_config.get("rewards", {})}

    def _alive_count(self) -> int:
        return sum(
            1 for npc in self.game.objects_storage.npc_list
            if getattr(npc, "alive", True)
        )

    def _alive_npcs(self):
        return [
            n for n in self.game.objects_storage.npc_list
            if getattr(n, "alive", True)
        ]

    @staticmethod
    def _wrap_pi(a: float) -> float:
        return (a + math.pi) % (2 * math.pi) - math.pi

    def _nearest_npc_features(self):
        alive = self._alive_npcs()
        if not alive:
            self.steps_since_seen = min(self.steps_since_seen + 1, 9999)
            return (
                float(self.last_seen_dist),
                float(self.last_seen_sin_err),
                float(self.last_seen_cos_err),
                0.0,
                float(self.last_seen_hp_norm),
            )

        px, py = float(self.game.player.x), float(self.game.player.y)
        best = min(alive, key=lambda n: math.hypot(float(n.x) - px, float(n.y) - py))

        vis = 1.0 if getattr(best, "ray_casting_value", False) else 0.0
        npc_hp = float(getattr(best, "health", 100.0))
        npc_hp_norm = max(0.0, min(1.0, npc_hp / 100.0))

        if vis > 0.5:
            nx, ny = float(best.x), float(best.y)
            dist = math.hypot(nx - px, ny - py)
            ang_to = math.atan2(ny - py, nx - px)
            err = self._wrap_pi(ang_to - float(self.game.player.angle))

            self.last_seen_dist = float(dist)
            self.last_seen_sin_err = float(math.sin(err))
            self.last_seen_cos_err = float(math.cos(err))
            self.last_seen_hp_norm = float(npc_hp_norm)
            self.steps_since_seen = 0

            return dist, math.sin(err), math.cos(err), 1.0, npc_hp_norm

        self.steps_since_seen = min(self.steps_since_seen + 1, 9999)
        return (
            float(self.last_seen_dist),
            float(self.last_seen_sin_err),
            float(self.last_seen_cos_err),
            0.0,
            float(self.last_seen_hp_norm),
        )

    def _get_obs(self) -> np.ndarray:
        raw = np.array([t[0] for t in self.game.raycast.ray_cast_result], dtype=np.float32)
        n_raw = raw.size
        rc = self.ray_count

        if n_raw == 0:
            depths = np.zeros(rc, dtype=np.float32)
        elif n_raw <= rc:
            depths = np.pad(raw, (0, rc - n_raw), mode="edge")[:rc]
        else:
            idx = np.linspace(0, n_raw - 1, rc, dtype=int)
            depths = raw[idx]

        depths = np.clip(depths, 0.0, self.depth_clip) / self.depth_clip

        ang = float(self.game.player.angle)
        health = float(self.game.player.health) / 100.0
        since_seen_scaled = min(float(self.steps_since_seen), 200.0) / 200.0

        # use cached features instead of calling _nearest_npc_features again
        dist, sin_err, cos_err, vis, npc_hp_norm = self._cached_npc_features
        dist_scaled = min(float(dist), 20.0) / 20.0
        reloading = 1.0 if self.game.weapon.reloading else 0.0

        tail = np.array(
            [
                math.sin(ang), math.cos(ang),
                health, since_seen_scaled,
                dist_scaled, sin_err, cos_err, vis,
                npc_hp_norm, reloading,
            ],
            dtype=np.float32,
        )
        return np.concatenate([depths, tail]).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.step_count = 0

        desired_headless = not self.render_game
        desired_render = self.render_game

        if self.game is None:
            self.game = Game(headless=desired_headless, render=desired_render, phase_config=self.phase_config)
        else:
            if (self.game.headless != desired_headless) or (self.game.render_enabled != desired_render):
                self.game.close()
                self.game = Game(headless=desired_headless, render=desired_render, phase_config=self.phase_config)
            else:
                self.game.phase_config = self.phase_config
                self.game.new_game()

        self._apply_phase_config()
        self.game.player.control_mode = "rl"
        self.game.tick()

        if self.render_game:
            self.game.check_events()
            self.game.draw()
            self.game.flip()

        self.prev_kills = self.game.player.kills
        self.prev_health = self.game.player.health

        self.last_seen_dist = 20.0
        self.last_seen_sin_err = 0.0
        self.last_seen_cos_err = 1.0
        self.last_seen_hp_norm = 1.0
        self.steps_since_seen = 9999

        self._cached_npc_features = self._nearest_npc_features()
        dist, _, cos_err, vis, _ = self._cached_npc_features
        self.prev_npc_dist = float(dist)
        self.prev_abs_err = math.acos(max(-1.0, min(1.0, float(cos_err))))
        self.prev_vis = 0.0

        self.visited = set()
        self.visited.add(self.game.player.map_position)

        self.tile_visit_counts = {}

        self.stuck_steps = 0
        self.collision_streak = 0
        self.continuous_aim_steps = 0
        self._prev_pos = (float(self.game.player.x), float(self.game.player.y))

        # tile overstay
        self.current_tile = self.game.player.map_position
        self.tile_stay_steps = 0

        return self._get_obs(), {}

    def step(self, action):
        self.step_count += 1
        act = int(action)

        if not (self.game.win or self.game.dead):
            self.game.apply_action(act)
        self.game.tick()

        if self.render_game:
            self.game.check_events()
            self.game.draw()
            self.game.flip()

        px, py = float(self.game.player.x), float(self.game.player.y)
        if self._prev_pos is None:
            self._prev_pos = (px, py)
        dx = px - self._prev_pos[0]
        dy = py - self._prev_pos[1]
        moved = (dx * dx + dy * dy) ** 0.5

        # anti-stuck: only count move actions as potential stuck
        if act in self.MOVE_ACTIONS:
            if moved < self.stuck_eps:
                self.stuck_steps += 1
            else:
                self.stuck_steps = 0
        # non-move actions (shoot, turn) do not increment stuck counter
        self._prev_pos = (px, py)

        kills = self.game.player.kills
        health = self.game.player.health
        dk = kills - self.prev_kills
        dh = self.prev_health - health

        if dk > 0:
            self.last_seen_dist = 20.0
            self.last_seen_sin_err = 0.0
            self.last_seen_cos_err = 1.0
            self.last_seen_hp_norm = 1.0
            self.steps_since_seen = 9999
            self.continuous_aim_steps = 0

        # compute npc features once and cache for _get_obs
        self._cached_npc_features = self._nearest_npc_features()
        dist, sin_err, cos_err, vis, _ = self._cached_npc_features
        abs_err = math.acos(max(-1.0, min(1.0, float(cos_err))))

        R = self.R
        reward = 0.0
        is_shoot = act in self.SHOOT_ACTIONS

        # --- time penalty ---
        reward += float(R.get("step_penalty", 0.0))

        # --- no_vis_penalty ---
        if float(vis) <= 0.5:
            reward += float(R.get("no_vis_penalty", 0.0))

        # --- tile overstay ---
        mp = self.game.player.map_position
        tile_limit = int(R.get("tile_stay_limit", 300))
        tile_penalty = float(R.get("tile_stay_penalty", 0.0))

        self.tile_visit_counts[mp] = self.tile_visit_counts.get(mp, 0) + 1
        self.tile_stay_steps = self.tile_visit_counts[mp]

        if tile_penalty < 0.0 and self.tile_visit_counts[mp] > tile_limit:
            reward += tile_penalty

        # --- kill reward ---
        reward += float(R["kill"]) * float(dk)
        if dk > 0:
            self.continuous_aim_steps = 0

        # --- aim cone helpers ---
        aim_cone = math.radians(float(R.get("aim_angle", 35.0)))
        in_aim_cone = (float(vis) > 0.5) and (aim_cone > 1e-6) and (float(abs_err) < aim_cone)

        # --- aim_max with decay ---
        aim_max = float(R.get("aim_max", 0.0))
        if aim_max > 0.0:
            if in_aim_cone:
                self.continuous_aim_steps += 1
                horizon = max(1, int(R.get("aim_decay_horizon", 60)))
                decay = max(0.05, 1.0 - self.continuous_aim_steps / horizon)
                reward += aim_max * max(0.0, 1.0 - float(abs_err) / aim_cone) * decay
            elif float(vis) > 0.5:
                self.continuous_aim_steps = 0
                reward += aim_max * max(0.0, 1.0 - float(abs_err) / aim_cone)
            else:
                self.continuous_aim_steps = 0
        else:
            if not in_aim_cone:
                self.continuous_aim_steps = 0
            else:
                self.continuous_aim_steps += 1

        # --- shoot_aimed_bonus ---
        shoot_bonus = float(R.get("shoot_aimed_bonus", 0.0))
        if shoot_bonus > 0.0 and is_shoot and in_aim_cone:
            quality = max(0.0, 1.0 - float(abs_err) / aim_cone)
            reward += shoot_bonus * quality

        # --- aim_no_shoot_penalty ---
        aim_ns_pen = float(R.get("aim_no_shoot_penalty", 0.0))
        if aim_ns_pen < 0.0:
            tight_aim = (aim_cone > 1e-6) and (float(abs_err) < aim_cone * 0.4)
            weapon_ready = not self.game.weapon.reloading
            if (float(vis) > 0.5) and tight_aim and weapon_ready and (not is_shoot):
                reward += aim_ns_pen

        # --- see_bonus ---
        see_bonus = float(R.get("see_bonus", 0.0))
        if see_bonus > 0.0 and float(vis) > 0.5 and self.prev_vis <= 0.5:
            reward += see_bonus
        self.prev_vis = float(vis)

        # --- approach / aim_track ---
        vis_scale = 1.0 if float(vis) > 0.5 else float(R.get("approach_invis_scale", 0.0))
        approach = float(R.get("approach", 0.0))
        aim_track = float(R.get("aim_track", 0.0))
        if approach != 0.0:
            reward += approach * float(self.prev_npc_dist - float(dist)) * vis_scale
        if aim_track != 0.0:
            reward += aim_track * float(self.prev_abs_err - float(abs_err)) * vis_scale

        # --- explore_bonus ---
        explore_bonus = float(R.get("explore_bonus", 0.0))
        if explore_bonus > 0.0:
            if mp not in self.visited:
                self.visited.add(mp)
                reward += explore_bonus

        # --- idle_penalty ---
        idle_penalty = float(R.get("idle_penalty", 0.0))
        if idle_penalty < 0.0 and self._alive_count() > 0 and float(vis) <= 0.5:
            reward += idle_penalty

        # --- damage penalty ---
        if dh > 0:
            reward += float(R.get("damage", 0.0)) * float(dh)

        # --- collision penalty ---
        if act in self.MOVE_ACTIONS and moved < self.collision_eps:
            self.collision_streak += 1
            reward += float(self.collision_penalty)
            reward += float(self.collision_escalate) * float(min(self.collision_streak, 50))
        else:
            self.collision_streak = 0

        self.prev_kills = kills
        self.prev_health = health
        self.prev_npc_dist = float(dist)
        self.prev_abs_err = float(abs_err)

        terminated = bool(self.game.win or self.game.dead)
        truncated = bool(self.step_count >= self.max_steps)

        # --- terminal rewards ---
        if terminated:
            if self.game.win:
                reward += float(R.get("win_bonus", 0.0))
            if self.game.dead:
                reward += float(R.get("death_penalty", 0.0))

        stuck_truncate = (self.stuck_steps >= self.stuck_patience)
        if (not terminated) and (not truncated) and stuck_truncate:
            truncated = True
            reward += float(self.stuck_penalty)

        obs = self._get_obs()
        info = {
            "kills": kills,
            "alive": self._alive_count(),
            "health": health,
            "vis": float(vis),
            "moved": float(moved),
            "stuck_steps": int(self.stuck_steps),
            "collision_streak": int(self.collision_streak),
            "continuous_aim": int(self.continuous_aim_steps),
            "tile_stay_steps": int(self.tile_stay_steps),
        }
        if stuck_truncate:
            info["early_truncate"] = "stuck"

        return obs, float(reward), terminated, truncated, info

    def close(self):
        if self.game is not None:
            self.game.close()
            self.game = Non
