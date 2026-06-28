# Reach the AND level via banked skills, then solve AND = invert(nand(a,b)) adaptively (discover the exact
# pin names from place_component + list_connectors), referee. If PASS, this is solve_and_reference.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
import synth

SK = "/Users/holden/HackathonSF26/operator/skills"

with ZoomSnapComputer() as bc:
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
    for skill in ("skill_RELAY_NAND.py", "skill_INV.py"):
        clear_canvas(pg); v = synth.run_skill(f"{SK}/{skill}", bc)
        assert v.passed, f"{skill} failed"
        advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()
    print("at level:", pg.evaluate("()=>localStorage.getItem('NandGame:Levels')"))

    clear_canvas(pg)
    n1 = bc.place_component("nand")     # nand(a,b)
    n2 = bc.place_component("inv")      # invert
    names = [c["name"] for c in bc.list_connectors()["connectors"]]
    print("placed:", n1, n2)
    print("connectors:", names)
    nand_ins = sorted(x for x in names if x.startswith(n1 + ".") and not x.endswith(".out"))
    inv_ins = [x for x in names if x.startswith(n2 + ".") and not x.endswith(".out")]
    print("nand_ins:", nand_ins, "| inv_in:", inv_ins, "| nand_out:", n1 + ".out", "| inv_out:", n2 + ".out")

    for s, t in [("Input_a", nand_ins[0]), ("Input_b", nand_ins[1]),
                 (n1 + ".out", inv_ins[0]), (n2 + ".out", "Output")]:
        r = bc.connect_pins(s, t); print(f"  connect {s} -> {t}: {r['success']}")

    v = bc.referee_check()
    print("\nAND referee:", v.status, "| passed:", v.passed)
