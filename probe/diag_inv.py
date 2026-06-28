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
    clear_canvas(pg); v = synth.run_skill(f"{SK}/skill_RELAY_NAND.py", bc)
    print("RELAY_NAND:", v.status)
    advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()
    clear_canvas(pg); v = synth.run_skill(f"{SK}/skill_INV.py", bc)
    print("INV:", v.status, "| placed:", bc._placed_bases(), "| failing:", v.failing_cases)
    print("connectors:", [c["name"] for c in bc.list_connectors()["connectors"]])
    conns = pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('NandGame:Levels:INV')||'{}')}catch(e){};return o.connections}")
    print("INV connections:", json.dumps(conns))
    # component + terminal positions
    pos = pg.evaluate("""()=>{const r=e=>{const b=e.getBoundingClientRect();return [Math.round(b.x+b.width/2),Math.round(b.y+b.height/2)];};
      const out={terminals:{}, nand:null};
      const i=document.querySelector('.input-node .output-connector'); if(i)out.terminals.Input=r(i);
      const o=document.querySelector('.output-node .input-connector'); if(o)out.terminals.Output=r(o);
      const n=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>!x.closest('.toolbox')&&!x.classList.contains('input-node')&&!x.classList.contains('output-node')&&x.getBoundingClientRect().x>150)[0];
      if(n){const b=n.getBoundingClientRect();out.nand=[Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height)];}
      return out;}""")
    print("positions:", json.dumps(pos))
    pg.screenshot(path="/Users/holden/HackathonSF26/probe/diag_inv.png")
    print("screenshot -> probe/diag_inv.png")
