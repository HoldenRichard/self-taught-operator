# Reference-scaffold AND/OR/XOR: reach each level via banked skills, solve it adaptively (place gates by
# TYPE, discover pins, wire), record the trajectory, synthesize -> validate (cold-execute) -> bank.
# These are source:"reference" machinery-validation skills (the demo flips them to agent-sourced in pre-warm).
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
from referee import dismiss_verdict_popup
from trajectory import save_trajectory, load_trajectory
import synth

SK = "/Users/holden/HackathonSF26/operator/skills"

# Each gate: (component types to place left-to-right, wires, functional goal).
# A wire endpoint is ("T", terminal_name) | (comp_index, "out") | (comp_index, "in", pin_index).
GATES = {
    "AND": (["nand", "inv"],
            [(("T", "Input_a"), (0, "in", 0)), (("T", "Input_b"), (0, "in", 1)),
             ((0, "out"), (1, "in", 0)), ((1, "out"), ("T", "Output"))],
            "Logical AND of two inputs: outputs 1 only when both a and b are 1 (= NOT(NAND(a,b)))."),
    "OR":  (["inv", "inv", "nand"],
            [(("T", "Input_a"), (0, "in", 0)), (("T", "Input_b"), (1, "in", 0)),
             ((0, "out"), (2, "in", 0)), ((1, "out"), (2, "in", 1)), ((2, "out"), ("T", "Output"))],
            "Logical OR of two inputs: outputs 1 when a or b (or both) is 1 (= NAND(NOT a, NOT b))."),
    "XOR": (["or", "nand", "and"],
            [(("T", "Input_a"), (0, "in", 0)), (("T", "Input_b"), (0, "in", 1)),
             (("T", "Input_a"), (1, "in", 0)), (("T", "Input_b"), (1, "in", 1)),
             ((0, "out"), (2, "in", 0)), ((1, "out"), (2, "in", 1)), ((2, "out"), ("T", "Output"))],
            "Exclusive-OR (XOR) of two inputs: outputs 1 when exactly one of a, b is 1 (= AND(OR(a,b), NAND(a,b)))."),
}


def solve_gate(bc, comps, wires):
    bases = [bc.place_component(c) for c in comps]
    nm = [c["name"] for c in bc.list_connectors()["connectors"]]
    pins = [(sorted(x for x in nm if x.startswith(b + ".") and not x.endswith(".out")), b + ".out") for b in bases]
    def res(spec):
        if spec[0] == "T": return spec[1]
        return pins[spec[0]][1] if spec[1] == "out" else pins[spec[0]][0][spec[2]]
    ok = True
    for s, t in wires:
        ok = bc.connect_pins(res(s), res(t))["success"] and ok
    return bc.referee_check(), bases


def main():
    with ZoomSnapComputer() as bc:
        pg = bc._page; pg.on("dialog", lambda d: d.accept())
        pg.wait_for_timeout(1500); dismiss_popup(pg)
        pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
        for skill in ("skill_RELAY_NAND.py", "skill_INV.py"):
            clear_canvas(pg); assert synth.run_skill(f"{SK}/{skill}", bc).passed
            advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()

        for gate in ("AND", "OR", "XOR"):
            comps, wires, goal = GATES[gate]
            print(f"\n=== {gate}  (levels {pg.evaluate(chr(39)+'()=>localStorage.getItem(\"NandGame:Levels\")'+chr(39))}) ===")
            bc.start_recording(gate, gate, source="reference", goal=goal)
            clear_canvas(pg)
            v, bases = solve_gate(bc, comps, wires)
            print(f"  adaptive solve: {v.status}  (placed {bases})")
            assert v.passed, f"{gate} adaptive solve failed"
            tpath = save_trajectory(bc.trajectory(), v); bc.stop_recording()
            spath = synth.synthesize(load_trajectory(tpath))
            print(f"  synthesized {spath}")
            dismiss_verdict_popup(pg); dismiss_popup(pg); clear_canvas(pg); pg.wait_for_timeout(300)
            vv = synth.run_skill(spath, bc)
            print(f"  cold-exec validate: {vv.status}")
            assert vv.passed, f"{gate} generated skill failed validation"
            synth.bank(load_trajectory(tpath), spath)
            print(f"  BANKED skill_{gate}")
            advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()

        print("\nregistry:", json.dumps(json.load(open(f"{SK}/registry.json")), indent=0)[:400])
        print("ALL GATES BANKED ✓")


if __name__ == "__main__":
    main()
