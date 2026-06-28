"""COMPOSITION — build a NEW circuit by RETRIEVING banked skills by similarity and INVOKING them on the
target's connectors. This is what makes the library GENERATIVE rather than a lookup table.

Given a task spec {inputs, outputs: {connector: sub-goal text}} — the logical DEFINITION of the task, e.g. a
half-adder's "sum = XOR(a,b)", "carry = AND(a,b)" — the composer, for each output, retrieves the best banked
skill by vector similarity to that sub-goal (it DISCOVERS which skill, it is not told) and invokes it on the
task's inputs + that output. There is NO hardcoded circuit for any specific task here: the entire construction
comes from the retrieved skills. (grep-clean of place_component/connect_pins — those live only in the skills.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import library
import synth

SKILLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")


def compose(task_spec, env, retrieve=None):
    """Build `task_spec` by retrieving + composing banked skills. Returns (referee Verdict, plan)."""
    retrieve = retrieve or library.retrieve
    plan = []
    orig_referee = env.referee_check
    env.referee_check = lambda: None          # suppress each skill's intermediate self-check during the build
    try:
        for out_conn, subgoal in task_spec["outputs"].items():
            hits = retrieve(subgoal, k=1)                       # DISCOVER the skill by similarity
            name = hits[0]["name"] if hits else None
            if not name:
                plan.append({"output": out_conn, "subgoal": subgoal, "skill": None})
                continue
            path = os.path.join(SKILLS, f"skill_{name}.py")
            params = synth.load_skill(path).DESCRIPTOR["params"]      # [input..., output]
            pv = {p: task_spec["inputs"][i] for i, p in enumerate(params[:-1])}
            pv[params[-1]] = out_conn
            synth.run_skill(path, env, pv)                            # INVOKE it on the target's connectors
            plan.append({"output": out_conn, "subgoal": subgoal, "skill": name,
                         "score": round(hits[0].get("score", 0.0), 3), "via": hits[0].get("via"), "bind": pv})
    finally:
        env.referee_check = orig_referee
    return env.referee_check(), plan
