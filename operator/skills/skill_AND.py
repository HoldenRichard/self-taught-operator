# AUTO-GENERATED at runtime by operator/synth.py from a referee-verified trajectory.
# task: AND  |  source_trajectory: trajectories/AND.json
# This file did not exist before the verified solve — it IS the synthesized skill. Do not hand-edit.
DESCRIPTOR = {
    "name": "AND",
    "params": [
        "Input_a",
        "Input_b",
        "Output"
    ],
    "description": "Logical AND of two inputs: outputs 1 only when both a and b are 1. Built by placing 2 component(s) and making 4 named connection(s).",
    "signature": "skill_AND(env, Input_a, Input_b, Output)"
}


def skill_AND(env, Input_a, Input_b, Output):
    n0 = env.place_component("nand")
    n1 = env.place_component("inv")
    env.connect_pins(Input_a, f"{n0}.a")
    env.connect_pins(Input_b, f"{n0}.b")
    env.connect_pins(f"{n0}.out", f"{n1}.in0")
    env.connect_pins(f"{n1}.out", Output)
    return env.referee_check()
