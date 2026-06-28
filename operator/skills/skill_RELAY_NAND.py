# AUTO-GENERATED at runtime by operator/synth.py from a referee-verified trajectory.
# task: RELAY_NAND  |  source_trajectory: trajectories/RELAY_NAND.json
# This file did not exist before the verified solve — it IS the synthesized skill. Do not hand-edit.
DESCRIPTOR = {
    "name": "RELAY_NAND",
    "params": [
        "Input_a",
        "Input_b",
        "Input_V",
        "Output"
    ],
    "description": "NAND gate built from relays: outputs NOT(a AND b). Built by placing 2 component(s) and making 5 named connection(s).",
    "signature": "skill_RELAY_NAND(env, Input_a, Input_b, Input_V, Output)"
}


def skill_RELAY_NAND(env, Input_a, Input_b, Input_V, Output):
    n0 = env.place_component("RELAY-OFF")
    n1 = env.place_component("RELAY-ON")
    env.connect_pins(Input_a, f"{n0}.in")
    env.connect_pins(Input_b, f"{n0}.c")
    env.connect_pins(Input_V, f"{n1}.in")
    env.connect_pins(f"{n0}.out", f"{n1}.c")
    env.connect_pins(f"{n1}.out", Output)
    return env.referee_check()
