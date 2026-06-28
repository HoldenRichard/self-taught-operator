# COMPOSITION GATE: build a half-adder by RETRIEVING skill_XOR + skill_AND from Atlas by similarity and
# INVOKING them on the HALFADD level's connectors. The half-adder was never banked; it is composed from two
# independently-banked skills -> proves the library is GENERATIVE, not a lookup table.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
import synth, library, compose

SK = "/Users/holden/HackathonSF26/operator/skills"
CHAIN = ["skill_RELAY_NAND.py", "skill_INV.py", "skill_AND.py", "skill_OR.py", "skill_XOR.py"]
# The half-adder's logical DEFINITION (the goal): sum = XOR(a,b) -> low bit l; carry = AND(a,b) -> high bit h.
SPEC = {"inputs": ["Input_a", "Input_b"],
        "outputs": {"Output_l": "exclusive-or (XOR) of the two inputs",
                    "Output_h": "logical AND of the two inputs"}}

print("=== sync library -> Atlas (all banked skills) ===")
print(" ", library.sync_registry())

with ZoomSnapComputer(viewport=(2600, 1400)) as bc:   # wider canvas so the half-adder's 5 gates fit one row
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
    print("=== reach HALFADD via banked skills ===")
    for skill in CHAIN:
        clear_canvas(pg); assert synth.run_skill(f"{SK}/{skill}", bc).passed, f"{skill} failed"
        advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()
    print("  at:", pg.evaluate("()=>localStorage.getItem('NandGame:Levels')"))
    print("  connectors:", json.dumps([c["name"] for c in bc.list_connectors()["connectors"]]))

    print("=== COMPOSE half-adder (retrieve skills by similarity, invoke on connectors) ===")
    clear_canvas(pg)
    verdict, plan = compose.compose(SPEC, bc)
    for p in plan:
        print(f"  {p['output']} <- retrieved skill_{p['skill']} (score {p.get('score')}, {p.get('via')}) "
              f"for sub-goal {p['subgoal']!r}")
    print("\nHALF-ADDER referee:", verdict.status, "| passed:", verdict.passed)
    print("raw:", repr(verdict.raw_dialog)[:180])
    pg.screenshot(path="/Users/holden/HackathonSF26/probe/halfadder_composed.png")
