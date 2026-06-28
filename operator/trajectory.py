"""Trajectory persistence for the self-taught operator.

A trajectory is the recorded sequence of SEMANTIC actions (place_component / connect_pins-by-NAME) that
a solve executed, plus the referee verdict. It is recorded LIVE by the env (env.start_recording /
env.trajectory) as the agent — or a reference scaffold — operates the game; this module only saves and
loads that record. It contains NO circuit solution and no synthesis logic.

A trajectory is saved only on a referee-verified PASS — that is the moment the operator has earned
something worth turning into a skill.
"""
import os
import json

TRAJ_DIR = os.path.join(os.path.dirname(__file__), "trajectories")


def save_trajectory(traj, verdict):
    """Persist a recorded trajectory + its verdict. Saves ONLY on a real PASS (returns None otherwise)."""
    if not getattr(verdict, "passed", False):
        return None
    os.makedirs(TRAJ_DIR, exist_ok=True)
    record = dict(traj)
    record["verdict"] = verdict.status
    record["passed"] = True
    path = os.path.join(TRAJ_DIR, f"{traj['task']}.json")
    with open(path, "w") as f:
        json.dump(record, f, indent=2)
    return path


def load_trajectory(path):
    with open(path) as f:
        return json.load(f)
