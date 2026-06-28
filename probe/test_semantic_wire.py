# Validate the semantic wiring tools (list_connectors + connect_pins) by building the inverter
# through them directly (no Gemini). Then the referee must PASS.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
sys.path.insert(0, "/Users/holden/HackathonSF26/probe")
from nandgame_env import (ZoomSnapComputer, advance_to_next_level, dismiss_popup,
                          clear_canvas, toolbox_item, _drag, _cancel_armed)
from reference_solver import solve_relay_nand_reference as solve_relay_nand  # quarantined scaffolding
from referee import referee_check

def main():
    with ZoomSnapComputer() as bc:
        pg = bc._page; pg.on("dialog", lambda d: d.accept())
        pg.wait_for_timeout(1500); dismiss_popup(pg)
        pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
        v = referee_check(pg) if False else None
        n = solve_relay_nand(bc); v = referee_check(pg); print("NAND setup:", v.status)
        if not v.passed: print("setup failed"); return
        advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()
        clear_canvas(pg)
        nt = toolbox_item(pg, "nand"); _drag(pg, nt[0], nt[1], 900, 600); _cancel_armed(pg)

        print("\nlist_connectors() ->", json.dumps(bc.list_connectors(), indent=0))
        names = [c["name"] for c in bc.list_connectors()["connectors"]]
        nand_ins = sorted([x for x in names if x.startswith("nand") and not x.endswith(".out")])
        nand_out = next((x for x in names if x.startswith("nand") and x.endswith(".out")), None)
        print("nand inputs:", nand_ins, "| nand out:", nand_out)
        if len(nand_ins) < 2 or not nand_out:
            print("!! could not identify nand pins"); return

        print("\nconnect_pins results:")
        print(" ", bc.connect_pins("Input", nand_ins[0]))
        print(" ", bc.connect_pins("Input", nand_ins[1]))
        print(" ", bc.connect_pins(nand_out, "Output"))

        circ = pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('NandGame:Levels:INV')||'{}')}catch(e){};return o}")
        print("\nINV nodes:", json.dumps(circ.get("nodes")))
        print("INV connections:", json.dumps(circ.get("connections")))
        print("named pins:", json.dumps(bc._named_connectors()))
        vi = referee_check(pg)
        print("\nINV referee:", vi.status, "| passed:", vi.passed)
        print("raw:", repr(vi.raw_dialog)[:140])

if __name__ == "__main__":
    main()
