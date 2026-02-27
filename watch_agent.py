import glob
import os
import re
import time

import numpy as np
from sb3_contrib import RecurrentPPO
from doom_enviroment import DoomEnv
from settings import NUMBER_RAYS
import npc as _npc


PHASE_CFG = {
    "npc_types": [_npc.DummyNPC],
    "weights": [1],
    "enemies": 1,
    "dummy_spawn": "random",
    "rewards": {
        "kill": 80.0,
        "aim_max": 0.25,
        "aim_angle": 35.0,
        "aim_track": 0.03,
        "no_vis_penalty": -0.02,
        "step_penalty": -0.004,
        "explore_bonus": 0.003,
        "see_bonus": 2.0,
        "approach": 0.15,
        "approach_invis_scale": 0.0,
        "damage": 0.0,
    }
}

CKPT_DIR = "checkpoints"
PREFIX = "ppo_doom_search"

# fallback, если в имени чекпойнта нет _rNN_
DEFAULT_RAY_COUNT_OVERRIDE = NUMBER_RAYS // 2

_rx_steps = re.compile(r"_(\d+)_steps\.zip$")
_rx_rays  = re.compile(r"_r(\d+)(?:_|\.|$)")  # ищет _r64_ или _r64.zip


def _step_num(path: str) -> int:
    m = _rx_steps.search(os.path.basename(path))
    return int(m.group(1)) if m else -1


def _ray_num_from_name(path: str) -> int | None:
    m = _rx_rays.search(os.path.basename(path))
    return int(m.group(1)) if m else None


def list_checkpoints():
    pattern = os.path.join(CKPT_DIR, f"{PREFIX}_*_steps.zip")
    files = glob.glob(pattern)
    files = sorted(files, key=_step_num)
    return files


def choose_checkpoint(files):
    print("\nAvailable checkpoints:")
    for i, fp in enumerate(files, start=1):
        r = _ray_num_from_name(fp)
        r_s = f"r={r}" if r is not None else f"r=default({DEFAULT_RAY_COUNT_OVERRIDE})"
        print(f"{i:2d}) steps={_step_num(fp):>7d}   {r_s:>14s}   {fp}")

    while True:
        s = input("\nSelect number (Enter = latest, q = quit): ").strip().lower()
        if s == "":
            return files[-1]
        if s in ("q", "quit", "exit"):
            return None
        if s.isdigit():
            idx = int(s)
            if 1 <= idx <= len(files):
                return files[idx - 1]
        print("Invalid choice, try again.")


def play(model, env, fps_cap=60):
    obs, _ = env.reset()
    terminated = truncated = False

    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)

    dt = 1.0 / float(fps_cap) if fps_cap else 0.0

    while not (terminated or truncated):
        action, lstm_states = model.predict(
            obs,
            state=lstm_states,
            episode_start=episode_starts,
            deterministic=True,
        )
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        episode_starts = np.array([done], dtype=bool)
        if dt > 0:
            time.sleep(dt)


def make_env(ray_count: int):
    return DoomEnv(
        max_steps=900,
        phase_config=PHASE_CFG,
        render_game=True,
        ray_count_override=ray_count,
    )


def main():
    print("CWD =", os.getcwd())

    env = None
    current_rays = None

    while True:
        files = list_checkpoints()
        if not files:
            print(f"No checkpoints found in '{CKPT_DIR}'. Waiting...")
            time.sleep(2)
            continue

        ckpt = choose_checkpoint(files)
        if ckpt is None:
            break

        rays = _ray_num_from_name(ckpt)
        if rays is None:
            rays = DEFAULT_RAY_COUNT_OVERRIDE

        # пересоздаём env, если rays изменились
        if env is None or current_rays != rays:
            if env is not None:
                try:
                    env.close()
                except Exception:
                    pass
            env = make_env(ray_count=rays)
            current_rays = rays
            print(f"\nEnv rebuilt with ray_count_override={current_rays} (obs={env.observation_space})")

        print("\nLoading:", ckpt)
        model = RecurrentPPO.load(ckpt, env=env, device="cpu")
        play(model, env, fps_cap=60)


if __name__ == "__main__":
    main()
