# Advance AND -> OR -> XOR via banked skills + adaptive solves; solve AND=invert(nand) and
# OR=nand(inv a, inv b); dump each level's toolbox type-classes + I/O so solve_xor can be written.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
import synth

SK = "/Users/holden/HackathonSF26/operator/skills"

def lc(bc):
    return [c["name"] for c in bc.list_connectors()["connectors"]]

def pins(base, names):
    ins = sorted(x for x in names if x.startswith(base + ".") and not x.endswith(".out"))
    return ins, base + ".out"

def dump(pg, label):
    t = pg.evaluate("""()=>Array.from(document.querySelectorAll('.toolbox .diagram-node, [class*=palette] .diagram-node'))
        .map(n=>({cls:(n.getAttribute('class')||''), text:(n.textContent||'').trim().slice(0,14)}))""")
    io = pg.evaluate("""()=>({ins:Array.from(document.querySelectorAll('.input-node .output-connector')).map(c=>(c.textContent||'').trim()),
        outs:Array.from(document.querySelectorAll('.output-node .input-connector')).map(c=>(c.textContent||'').trim()),
        level:localStorage.getItem('NandGame:Levels')})""")
    print(f"  [{label}] io={json.dumps(io)}\n        toolbox={json.dumps(t)}")

with ZoomSnapComputer() as bc:
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
    for skill in ("skill_RELAY_NAND.py", "skill_INV.py"):
        clear_canvas(pg); assert synth.run_skill(f"{SK}/{skill}", bc).passed
        advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()

    dump(pg, "AND")
    clear_canvas(pg)
    n, iv = bc.place_component("nand"), bc.place_component("inv")
    nm = lc(bc); n_in, n_out = pins(n, nm); iv_in, iv_out = pins(iv, nm)
    for s, t in [("Input_a", n_in[0]), ("Input_b", n_in[1]), (n_out, iv_in[0]), (iv_out, "Output")]:
        bc.connect_pins(s, t)
    print("  AND ->", bc.referee_check().status)
    advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()

    dump(pg, "OR")
    clear_canvas(pg)
    ia, ib, g = bc.place_component("inv"), bc.place_component("inv"), bc.place_component("nand")
    nm = lc(bc); ia_in, ia_out = pins(ia, nm); ib_in, ib_out = pins(ib, nm); g_in, g_out = pins(g, nm)
    for s, t in [("Input_a", ia_in[0]), ("Input_b", ib_in[0]), (ia_out, g_in[0]), (ib_out, g_in[1]), (g_out, "Output")]:
        bc.connect_pins(s, t)
    print("  OR ->", bc.referee_check().status)
    advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()

    dump(pg, "XOR")
