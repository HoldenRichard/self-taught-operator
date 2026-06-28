# Recon the levels above INV (And/Or/Xor/Half-adder) so the reference solves + composition can be written
# correctly. Reaches each level by running the operator's OWN banked skills, then dumps toolbox + I/O.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
import synth

SK = "/Users/holden/HackathonSF26/operator/skills"
INSPECT = """()=>{
  const levels = localStorage.getItem('NandGame:Levels');
  const cur = (Array.from(document.querySelectorAll('h1,h2,.level-header,.current-level,[class*=title]'))
                 .map(e=>(e.textContent||'').trim()).filter(Boolean))[0] || null;
  const ins = Array.from(document.querySelectorAll('.input-node .output-connector')).map(c=>(c.textContent||'').trim());
  const outs = Array.from(document.querySelectorAll('.output-node .input-connector')).map(c=>(c.textContent||'').trim());
  const tools = Array.from(document.querySelectorAll('.toolbox .diagram-node, [class*=palette] .diagram-node, .palette-nodetype'))
     .map(n=>{const c=(n.getAttribute('class')||''); const t=(n.textContent||'').trim().slice(0,20); return (t||c.split(' ').pop())}).filter((v,i,a)=>a.indexOf(v)===i);
  return {levels, cur, ins, outs, tools};
}"""

with ZoomSnapComputer() as bc:
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()

    for skill in ("skill_RELAY_NAND.py", "skill_INV.py"):
        clear_canvas(pg)
        v = synth.run_skill(f"{SK}/{skill}", bc)
        print(f"solve {skill}: {v.status}")
        if not v.passed:
            print("  !! could not advance; stopping recon"); break
        advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()
        info = pg.evaluate(INSPECT)
        print(f"  -> now at: {json.dumps(info)}")
    # We are now on the level AFTER INV (expected: And). Dump it + named connectors.
    print("\nLEVEL AFTER INV:")
    print(json.dumps(pg.evaluate(INSPECT), indent=2))
    print("named connectors here:", json.dumps([c['name'] for c in bc.list_connectors()['connectors']]))
    pg.screenshot(path="/Users/holden/HackathonSF26/probe/level_after_inv.png")
