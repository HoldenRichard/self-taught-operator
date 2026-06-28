# SOLVE relay-NAND by hand-script to CAPTURE THE PASS VERDICT (Gate 1 foundation).
# NAND = two 'default-on' (normally-closed) relays in parallel: each in<-V, control = a / b,
# both outputs -> output terminal. Build via place(drag) + wire(tap-tap at true hit-point),
# verify each wire against the localStorage oracle, then Check solution and capture verdict.
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"
PROBE_DIR = "/Users/holden/HackathonSF26/probe"

PINS = r"""
() => {
  const cp = (connEl) => {
    if(!connEl) return null;
    const el = connEl.querySelector('polygon.triangle') || connEl.querySelector('circle.connector-circle')
            || connEl.querySelector('polygon,circle') || connEl;
    const r = el.getBoundingClientRect();
    return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)};
  };
  const box = n => { const r=n.getBoundingClientRect(); return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)}; };
  const o = {};
  o.a = cp(document.querySelector('.input-node .output-connector.a'));
  o.b = cp(document.querySelector('.input-node .output-connector.b'));
  o.V = cp(document.querySelector('.input-node .output-connector.V'));
  o.output = cp(document.querySelector('.output-node .input-connector'));
  const placed = Array.from(document.querySelectorAll('.diagram-node'))
    .filter(n => n.querySelector('.input-connector.c') && n.querySelector('.input-connector.in'))
    .filter(n => !n.closest('[class*=palette]') && !n.closest('[class*=toolbox]'))
    .filter(n => { const r=n.getBoundingClientRect(); return r.x > 460 && r.width>0; });
  o.relays = placed.map(n => ({ box:box(n), cls:(n.getAttribute('class')||'').slice(0,40),
    out: cp(n.querySelector('.output-connector')),
    c:   cp(n.querySelector('.input-connector.c')),
    in_: cp(n.querySelector('.input-connector.in')) })).sort((p,q)=>p.box.x-q.box.x);
  return o;
}
"""
VERDICT = r"""
() => {
  const pick = sel => Array.from(document.querySelectorAll(sel)).map(e=>({cls:(e.getAttribute('class')||'').slice(0,70), txt:(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,160)}));
  return {
    dialogs: pick('[class*=popup-dialog]'),
    successish: pick('[class*=success],[class*=correct],[class*=solved],[class*=complete],[class*=congrat],[class*=passed]'),
    error_banner: !!document.querySelector('.error-banner'),
    errorish: pick('.error-banner,.error-dialog'),
    levels: localStorage.getItem('NandGame:Levels'),
  };
}
"""

def conn(pg): return pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return (o.connections||[]).length}" % LS_KEY)
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d: d.accept())
    el=pg.query_selector('button:has-text("Clear canvas")');
    if el: el.click(); pg.wait_for_timeout(450)
def tap(pg,p,dx=0,dy=0):
    pg.mouse.move(p["x"]+dx,p["y"]+dy); pg.wait_for_timeout(50); pg.mouse.click(p["x"]+dx,p["y"]+dy); pg.wait_for_timeout(150)
def drag(pg,x1,y1,x2,y2,steps=28):
    pg.mouse.move(x1,y1); pg.wait_for_timeout(60); pg.mouse.down(); pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4); pg.wait_for_timeout(30)
    pg.mouse.move(x2,y2,steps=steps); pg.wait_for_timeout(120); pg.mouse.up(); pg.wait_for_timeout(250)

def wire(pg, src, tgt):
    """tap source connector then target; verify oracle; one retry with small y nudges."""
    before = conn(pg)
    tap(pg, src); tap(pg, tgt)
    if conn(pg) > before: return True
    # retry: nudge target down a couple px (true hit-point is the triangle, slightly low)
    tap(pg, src); tap(pg, tgt, 0, 3)
    return conn(pg) > before

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)

        # place 2 'default-on' relays
        drag(pg,375,215,660,400); drag(pg,375,215,940,400)
        ndnodes = pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return (o.nodes||[]).length}" % LS_KEY)
        pins=pg.evaluate(PINS)
        print(f"localStorage nodes={ndnodes}  | DOM relays found={len(pins['relays'])}")
        if len(pins["relays"])<2:
            print("!! placement failed", json.dumps(pins)); b.close(); return
        A,B = pins["relays"][0], pins["relays"][1]
        print("A:",A); print("B:",B)
        print("terminals a/b/V/out:", pins["a"], pins["b"], pins["V"], pins["output"])

        plan = [
            ("V->A.in",  pins["V"], A["in_"]),
            ("a->A.c",   pins["a"], A["c"]),
            ("A.out->output", A["out"], pins["output"]),
            ("V->B.in",  pins["V"], B["in_"]),
            ("b->B.c",   pins["b"], B["c"]),
            ("B.out->output", B["out"], pins["output"]),
        ]
        for name, s, t in plan:
            ok = wire(pg, s, t)
            print(f"  wire {name}: {'OK' if ok else 'FAIL'}  (conn={conn(pg)})")

        st = pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return {nodes:(o.nodes||[]).length, conns:o.connections||[]}}" % LS_KEY)
        print("\nCIRCUIT:", json.dumps(st, indent=1))
        pg.screenshot(path=PROBE_DIR+"/solve_built.png")

        # CHECK SOLUTION -> capture verdict
        el=pg.query_selector('button:has-text("Check solution")');
        if el: el.click(); pg.wait_for_timeout(900)
        v = pg.evaluate(VERDICT)
        print("\n===== VERDICT after Check solution =====")
        print(json.dumps(v, indent=2))
        pg.screenshot(path=PROBE_DIR+"/solve_verdict.png")
        pg.wait_for_timeout(500); b.close()

if __name__=="__main__":
    main()
