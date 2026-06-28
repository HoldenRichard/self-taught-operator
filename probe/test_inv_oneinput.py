# Does the inverter need BOTH nand inputs wired, or does ONE suffice (the other defaulting)?
# If one suffices, the a/b ambiguity vanishes and a large snap radius becomes safe.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import (ZoomSnapComputer, solve_relay_nand, advance_to_next_level, dismiss_popup,
                          clear_canvas, robust_wire, toolbox_item, _drag, _cancel_armed, output_pin, _center)
from referee import referee_check, dismiss_verdict_popup

def nand_pins(pg):
    return pg.evaluate("""()=>{const ns=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>{const r=x.getBoundingClientRect(); return r.x>660 && r.width>0 && !x.closest('[class*=palette]') && !x.closest('.toolbox');});
      const n=ns[0]; if(!n)return null;
      const ins=Array.from(n.querySelectorAll('.input-connector')).map(c=>{const e=c.querySelector('polygon.triangle')||c; const r=e.getBoundingClientRect(); return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];});
      const oe=n.querySelector('.output-connector circle.connector-circle'); const r=oe.getBoundingClientRect();
      return {ins, out:[Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)]};}""")

def place_nand(pg):
    clear_canvas(pg)
    nt = toolbox_item(pg, "nand")
    _drag(pg, nt[0], nt[1], 700, 500); _cancel_armed(pg)
    return nand_pins(pg)

def main():
    with ZoomSnapComputer() as bc:
        pg = bc._page; pg.on("dialog", lambda d: d.accept())
        pg.wait_for_timeout(1500); dismiss_popup(pg)
        pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
        solve_relay_nand(bc); v = referee_check(pg); print("NAND:", v.status)
        if not v.passed: print("nand setup failed"); return
        advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()
        inp = _center(pg, '.input-node .output-connector', 'circle.connector-circle'); outp = output_pin(pg)

        # TEST A — ONE input: Input -> nand.a, nand.out -> Output
        n = place_nand(pg)
        robust_wire(pg, inp, n['ins'][0], "INV")
        robust_wire(pg, n['out'], outp, "INV")
        vA = referee_check(pg)
        print("ONE-INPUT (Input->a, out->Output):", vA.status, "| passed:", vA.passed, "| raw:", repr(vA.raw_dialog)[:110])
        dismiss_verdict_popup(pg)

        # TEST B — BOTH inputs (control)
        n = place_nand(pg)
        robust_wire(pg, inp, n['ins'][0], "INV"); robust_wire(pg, inp, n['ins'][1], "INV")
        robust_wire(pg, n['out'], outp, "INV")
        vB = referee_check(pg)
        print("BOTH-INPUTS (Input->a, Input->b, out->Output):", vB.status, "| passed:", vB.passed)

if __name__ == "__main__":
    main()
