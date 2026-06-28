# WIRE ISOLATE — pinpoint why connections to relay '.in' malform. Verify each click point
# resolves to the intended connector (elementFromPoint at rest), then test single wires in
# isolation and print the recorded connection.
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"

PINS = r"""
() => {
  const cp = (connEl) => { if(!connEl) return null;
    const el = connEl.querySelector('polygon.triangle') || connEl.querySelector('circle.connector-circle') || connEl.querySelector('polygon,circle') || connEl;
    const r = el.getBoundingClientRect(); return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)}; };
  const box = n => { const r=n.getBoundingClientRect(); return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)}; };
  const o={};
  o.a=cp(document.querySelector('.input-node .output-connector.a'));
  o.b=cp(document.querySelector('.input-node .output-connector.b'));
  o.V=cp(document.querySelector('.input-node .output-connector.V'));
  o.output=cp(document.querySelector('.output-node .input-connector'));
  const placed=Array.from(document.querySelectorAll('.diagram-node'))
    .filter(n=>n.querySelector('.input-connector.c')&&n.querySelector('.input-connector.in'))
    .filter(n=>{const r=n.getBoundingClientRect();return r.x>460&&r.width>0;});
  if(placed[0]){const n=placed[0];
    o.A_out=cp(n.querySelector('.output-connector')); o.A_c=cp(n.querySelector('.input-connector.c')); o.A_in=cp(n.querySelector('.input-connector.in'));
  }
  return o;
}
"""
def efp(pg,x,y): return pg.evaluate("(p)=>{const e=document.elementFromPoint(p[0],p[1]);return e?((e.getAttribute&&e.getAttribute('class'))||e.tagName):'null'}", [x,y])
def conns(pg): return pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return o.connections||[]}" % LS_KEY)
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d: d.accept()); el=pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)
def tap(pg,p,dy=0):
    pg.mouse.move(p["x"],p["y"]+dy); pg.wait_for_timeout(60); pg.mouse.click(p["x"],p["y"]+dy); pg.wait_for_timeout(180)
def drag(pg,x1,y1,x2,y2,steps=28):
    pg.mouse.move(x1,y1); pg.wait_for_timeout(60); pg.mouse.down(); pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4); pg.wait_for_timeout(30); pg.mouse.move(x2,y2,steps=steps); pg.wait_for_timeout(120); pg.mouse.up(); pg.wait_for_timeout(250)

def setup(pg):
    clear(pg); drag(pg,375,215,660,400); return pg.evaluate(PINS)

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        pins=setup(pg)
        print("PINS:", json.dumps(pins))
        print("\nelementFromPoint at rest:")
        for k in ["a","b","V","output","A_out","A_c","A_in"]:
            if pins.get(k): print(f"  {k} {pins[k]} -> {efp(pg, pins[k]['x'], pins[k]['y'])}")

        tests = [("a->A_in","a","A_in"),("V->A_in","V","A_in"),("a->A_c","a","A_c"),("A_out->output","A_out","output")]
        for name, sk, tk in tests:
            pins=setup(pg)  # fresh relay each time
            s,t = pins.get(sk), pins.get(tk)
            tap(pg, s); tap(pg, t)
            c = conns(pg)
            print(f"\n{name}: {len(c)} conn(s) -> {json.dumps(c)}")
        b.close()

if __name__=="__main__":
    main()
