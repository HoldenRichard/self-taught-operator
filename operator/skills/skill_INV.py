# AUTO-GENERATED at runtime by operator/synth.py from a referee-verified trajectory.
# task: INV  |  source_trajectory: trajectories/INV.json
# This file did not exist before the verified solve — it IS the synthesized skill. Do not hand-edit.
DESCRIPTOR = {
    "name": "INV",
    "params": [
        "Input",
        "Output"
    ],
    "description": "Inverter (NOT gate): outputs the logical NOT of its input (0->1, 1->0). Built by placing 1 component(s) and making 3 named connection(s).",
    "signature": "skill_INV(env, Input, Output)"
}


def skill_INV(env, Input, Output):
    n0 = env.place_component("nand")
    env.connect_pins(Input, f"{n0}.a")
    env.connect_pins(Input, f"{n0}.b")
    env.connect_pins(f"{n0}.out", Output)
    return env.referee_check()
