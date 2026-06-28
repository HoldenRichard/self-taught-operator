# VERIFY IDS — nail every connectorId via reliable tap-tap with delta-reading.
# tap V->output reveals V's id; tap V->relay.in reveals in's id (and if the click works).
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"

PINS = r"""
() => { const c=el=>{if(!el)return null;const r=el.getBoundingClientRect();return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};};
  const o={}; o.a=c(document.querySelector('.input-node .output-connector.a')); o.b=c(document.querySelector('.input-node .output-connector.b'));
  o.V=c(document.querySelector('.input-node .output-connector.V')); o.output=c(document.querySelector('.output-node .input-connector'));
  const relay=Array.from(document.querySelectorAll('.diagram-node')).filter(n=>n.querySelector('.input-connector.c')&&n.querySelector('.input-connector.in')).filter(n=>{const r=n.getBoundingClientRect();return r.x>460;})[0];
  if(relay){o.r_out=c(relay.querySelector('.output-connector')); o.r_c=c(relay.querySelector('.input-connector.c')); o.r_in=c(relay.querySelector('.input-connector.in'));}
  return o; }
"""
def conns(pg): return pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return o.connections||[]}" % LS_KEY)
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d:d.accept()); el=pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(400)
def drag(pg,x1,y1,x2,y2,steps=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=steps);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)

def tap_wire(pg, src, tgt):
    before = json.dumps(conns(pg))
    for sdy,tdy in [(0,0),(0,7),(0,10),(0,4),(0,-4),(-3,7),(3,10)]:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(50)
        pg.mouse.click(src["x"], src["y"]+sdy); pg.wait_for_timeout(140)
        pg.mouse.click(tgt["x"], tgt["y"]+tdy); pg.wait_for_timeout(160)
        now = conns(pg)
        if json.dumps(now) != before:
            # return the newly-added connection(s)
            bset = {json.dumps(c) for c in json.loads(before)}
            return [c for c in now if json.dumps(c) not in bset]
    return []

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
        pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)
        drag(pg,375,215,700,400)
        pins=pg.evaluate(PINS); print("PINS:", json.dumps(pins))
        for name, s, t in [("V->output", pins["V"], pins["output"]),
                           ("a->relay.c", pins["a"], pins["r_c"]),
                           ("relay.out->output", pins["r_out"], pins["output"]),
                           ("V->relay.in", pins["V"], pins["r_in"]),
                           ("b->relay.in(retry)", pins["b"], pins["r_in"])]:
            delta = tap_wire(pg, s, t)
            print(f"{name}: NEW={json.dumps(delta)}")
        print("\nALL CONNS:", json.dumps(conns(pg), indent=1))
        b.close()

if __name__=="__main__":
    main()
