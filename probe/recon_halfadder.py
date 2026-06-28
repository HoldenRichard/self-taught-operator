# Reach the level after XOR by running ALL banked skills in sequence, then dump its I/O (the half-adder
# has TWO outputs: sum, carry) + toolbox, so the composer + multi-output naming can be built.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
import synth

SK = "/Users/holden/HackathonSF26/operator/skills"
CHAIN = ["skill_RELAY_NAND.py", "skill_INV.py", "skill_AND.py", "skill_OR.py", "skill_XOR.py"]

with ZoomSnapComputer() as bc:
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
    for skill in CHAIN:
        clear_canvas(pg); v = synth.run_skill(f"{SK}/{skill}", bc)
        print(f"{skill}: {v.status}")
        assert v.passed, f"{skill} failed reaching half-adder"
        advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()

    io = pg.evaluate("""()=>({
      levels: localStorage.getItem('NandGame:Levels'),
      ins: Array.from(document.querySelectorAll('.input-node .output-connector')).map(c=>(c.textContent||'').trim()),
      outs: Array.from(document.querySelectorAll('.output-node .input-connector')).map(c=>(c.textContent||'').trim()),
      n_output_nodes: document.querySelectorAll('.output-node').length,
      n_input_nodes: document.querySelectorAll('.input-node').length,
      toolbox: Array.from(new Set(Array.from(document.querySelectorAll('.toolbox .diagram-node, .diagram-node.free-node')).map(n=>(n.getAttribute('class')||'').split(' ').pop())))
    })""")
    print("\nLEVEL AFTER XOR:", json.dumps(io, indent=2))
    print("named connectors:", json.dumps([c["name"] for c in bc.list_connectors()["connectors"]]))
    pg.screenshot(path="/Users/holden/HackathonSF26/probe/halfadder_level.png")
