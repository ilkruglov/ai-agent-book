"""Execute the book's PPO example against a hand-computed two-rollout batch."""

import math
import re
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def mean(value: float | list[float]) -> float:
    return sum(value) / len(value) if isinstance(value, list) else value


def test_ppo_update_includes_both_trajectories() -> None:
    blocks = re.findall(
        r"```python\n(.*?)\n```", (ROOT / "book/chapter8.md").read_text(), re.S
    )
    code = next(block for block in blocks if "old_policy.log_prob" in block)
    updates: list[float] = []

    def update(policy: object, value_model: object, loss: float) -> None:
        updates.append(loss)

    policy = SimpleNamespace(log_prob=lambda actions: 0.0)
    namespace = {
        "rollouts": [
            SimpleNamespace(rewards=1.0, states=0.0, actions=0.0),
            SimpleNamespace(rewards=3.0, states=0.0, actions=0.0),
        ],
        "discounted_returns": lambda rewards: rewards,
        "value_model": lambda states: 0.0,
        "stop_gradient": lambda value: value,
        "policy": policy,
        "old_policy": policy,
        "exp": math.exp,
        "clip": lambda value, low, high: min(max(value, low), high),
        "mean": mean,
        "epsilon": 0.2,
        "value_coef": 0.5,
        "update": update,
    }
    exec(compile(code, "chapter8-ppo-example", "exec"), namespace)
    # Ratio=1, V=0: mean policy loss=-2; mean value loss=5; total=-2+0.5*5.
    assert updates == [0.5]
