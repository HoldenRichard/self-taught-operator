# Validate the role-aware snap by SIMULATING an imprecise agent: click ~40-70px off each pin,
# in the inverter wiring order, through the snapped click_at. Snap must land all 3 wires -> PASS.
# Key stress: both nand-input wires aim at the SAME spot; prefer-unwired must route them to a AND b.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import (ZoomSnapComputer, solve_relay_nand, advance_to_next_level, dismiss_popup,
                          clear_canvas, toolbox_item, _drag, _cancel_armed, output_pin, _center, conn_count)
from referee import referee_check

def nand_pins(pg):
    return pg.evaluate("""()=>{const ns=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>{const r=x.getBoundingClientRect(); return r.x>660 && r.width>0 && !x.closest('[class*=palette]') && !x.closest('.toolbox');});
      const n=ns[0]; if(!n)return null;
      const ins=Array.from(n.querySelectorAll('.input-connector')).map(c=>{const e=c.querySelector('polygon.triangle')||c; const r=e.getBoundingClientRect(); return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];});
      const oe=n.querySelector('.output-connector circle.connector-circle'); const r=oe.getBoundingClientRect();
      return {ins, out:[Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)]};}""")

def main():
    with ZoomSnapComputer() as bc:
        pg = bc._page; pg.on("dialog", lambda d: d.accept())
        pg.wait_for_timeout(1500); dismiss_popup(pg)
        pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
        solve_relay_nand(bc); v = referee_check(pg)
        if not v.passed: print("nand setup failed:", v.status); return
        advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()
        inp = _center(pg, '.input-node .output-connector', 'circle.connector-circle'); outp = output_pin(pg)
        clear_canvas(pg)
        nt = toolbox_item(pg, "nand"); _drag(pg, nt[0], nt[1], 700, 500); _cancel_armed(pg)
        n = nand_pins(pg)
        a, b, out = n['ins'][0], n['ins'][1], n['out']
        mid = [(a[0]+b[0])//2, (a[1]+b[1])//2]   # midpoint of a,b — ambiguous on purpose
        print("true pins -> Input:", inp, "a:", a, "b:", b, "out:", out, "Output:", outp)

        def sclick(p, ox, oy):  # imprecise click through the snap
            bc.click_at(p[0]+ox, p[1]+oy)

        bc._pending = None; bc._wired = set()
        # Wire 1: Input -> nand input (aim at the ambiguous midpoint, +offset)
        sclick(inp, 55, -45); sclick(mid, 35, 50)
        # Wire 2: Input -> nand input (aim at the SAME ambiguous midpoint again)
        sclick(inp, -40, -30); sclick(mid, -30, 45)
        # Wire 3: nand output -> Output terminal
        sclick(out, 40, -35); sclick(outp, -50, 40)

        print("conns:", conn_count(pg, "INV"), "| snap events:", len(bc._snap_log))
        print("snap log:", json.dumps(bc._snap_log))
        vi = referee_check(pg)
        print("\nSIM RESULT — INV referee:", vi.status, "| passed:", vi.passed)
        print("raw:", repr(vi.raw_dialog)[:140])
        pg.screenshot(path="/Users/holden/HackathonSF26/probe/snap_sim_result.png")

if __name__ == "__main__":
    main()
