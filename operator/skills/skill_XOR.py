# AUTO-GENERATED at runtime by operator/synth.py from a referee-verified trajectory.
# task: XOR  |  source_trajectory: trajectories/XOR.json
# This file did not exist before the verified solve — it IS the synthesized skill. Do not hand-edit.
DESCRIPTOR = {
    "name": "XOR",
    "params": [
        "Input_a",
        "Input_b",
        "Output"
    ],
    "description": "Exclusive-OR (XOR) of two inputs: outputs 1 when exactly one of a, b is 1. Built by placing 3 component(s) and making 7 named connection(s).",
    "signature": "skill_XOR(env, Input_a, Input_b, Output)"
}


def skill_XOR(env, Input_a, Input_b, Output):
    n0 = env.place_component("or")
    n1 = env.place_component("nand")
    n2 = env.place_component("and")
    env.connect_pins(Input_a, f"{n0}.a")
    env.connect_pins(Input_b, f"{n0}.b")
    env.connect_pins(Input_a, f"{n1}.a")
    env.connect_pins(Input_b, f"{n1}.b")
    env.connect_pins(f"{n0}.out", f"{n2}.a")
    env.connect_pins(f"{n1}.out", f"{n2}.b")
    env.connect_pins(f"{n2}.out", Output)
    return env.referee_check()
