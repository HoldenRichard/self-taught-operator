# AUTO-GENERATED at runtime by operator/synth.py from a referee-verified trajectory.
# task: OR  |  source_trajectory: trajectories/OR.json
# This file did not exist before the verified solve — it IS the synthesized skill. Do not hand-edit.
DESCRIPTOR = {
    "name": "OR",
    "params": [
        "Input_a",
        "Input_b",
        "Output"
    ],
    "description": "Logical OR of two inputs: outputs 1 when a or b (or both) is 1 (= NAND(NOT a, NOT b)). Built by placing 3 component(s) and making 5 named connection(s).",
    "signature": "skill_OR(env, Input_a, Input_b, Output)"
}


def skill_OR(env, Input_a, Input_b, Output):
    n0 = env.place_component("inv")
    n1 = env.place_component("inv")
    n2 = env.place_component("nand")
    env.connect_pins(Input_a, f"{n0}.in0")
    env.connect_pins(Input_b, f"{n1}.in0")
    env.connect_pins(f"{n0}.out", f"{n2}.a")
    env.connect_pins(f"{n1}.out", f"{n2}.b")
    env.connect_pins(f"{n2}.out", Output)
    return env.referee_check()
