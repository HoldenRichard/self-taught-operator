# Debug the OR solve: reach OR, place inv/inv/nand, log placements + pins + per-connect result + the
# actual connections + referee failing cases, to see why OR=nand(inv a, inv b) failed.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
import synth

SK = "/Users/holden/HackathonSF26/operator/skills"
lc = lambda bc: [c["name"] for c in bc.list_connectors()["connectors"]]
def pins(b, nm): return sorted(x for x in nm if x.startswith(b + ".") and not x.endswith(".out")), b + ".out"

with ZoomSnapComputer() as bc:
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
    for skill in ("skill_RELAY_NAND.py", "skill_INV.py"):
        clear_canvas(pg); assert synth.run_skill(f"{SK}/{skill}", bc).passed
        advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()
    # solve AND adaptively to reach OR (all at the proven zoom 1.4; gates now placed tight + on-canvas)
    clear_canvas(pg)
    n, iv = bc.place_component("nand"), bc.place_component("inv"); nm = lc(bc)
    ni, no = pins(n, nm); ii, io = pins(iv, nm)
    for s, t in [("Input_a", ni[0]), ("Input_b", ni[1]), (no, ii[0]), (io, "Output")]:
        bc.connect_pins(s, t)
    assert bc.referee_check().passed, "AND failed"
    advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()

    print("=== OR level ===", pg.evaluate("()=>localStorage.getItem('NandGame:Levels')"))
    clear_canvas(pg)
    ia, ib, g = bc.place_component("inv"), bc.place_component("inv"), bc.place_component("nand")
    print("placed:", ia, ib, g)
    nm = lc(bc); print("connectors:", nm)
    ia_i, ia_o = pins(ia, nm); ib_i, ib_o = pins(ib, nm); g_i, g_o = pins(g, nm)
    plan = [("Input_a", ia_i[0]), ("Input_b", ib_i[0]), (ia_o, g_i[0]), (ib_o, g_i[1]), (g_o, "Output")]
    for s, t in plan:
        r = bc.connect_pins(s, t); print(f"  {s:12s} -> {t:12s}: {r['success']}")
    conns = pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('NandGame:Levels:OR')||'{}')}catch(e){};return o.connections}")
    print("OR connections:", json.dumps(conns))
    v = bc.referee_check()
    print("OR referee:", v.status, "| failing:", v.failing_cases, "| raw:", repr(v.raw_dialog)[:120])
