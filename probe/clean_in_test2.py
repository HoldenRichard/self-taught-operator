# CLEAN IN TEST 2 — test ALL interaction modes on the relay 'in' pin in carryover-free state.
# Find ANY mode that wires V -> relay.in. Also test wiring to 'c' as a positive control.
import json
from playwright.sync_api import sync_playwright
LS_KEY="NandGame:Levels:RELAY_NAND"
def conns(pg): return pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return o.connections||[]}" % LS_KEY)
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(350)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d:d.accept()); el=pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)
def drag_place(pg,x1,y1,x2,y2,s=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=s);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)
def cancel_armed(pg):
    pg.keyboard.press("Escape"); pg.wait_for_timeout(80); pg.mouse.click(1250,260); pg.wait_for_timeout(120); pg.keyboard.press("Escape"); pg.wait_for_timeout(80)
def coords(pg):
    return pg.evaluate("""()=>{const n=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>x.querySelector('.input-connector.c')&&x.querySelector('.input-connector.in')).filter(x=>x.getBoundingClientRect().x>460)[0];
      const ctr=e=>{const r=e.getBoundingClientRect();return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];};
      const Vc=document.querySelector('.input-node .output-connector.V circle.connector-circle').getBoundingClientRect();
      const ac=document.querySelector('.input-node .output-connector.a circle.connector-circle').getBoundingClientRect();
      return {V:[Math.round(Vc.x+Vc.width/2),Math.round(Vc.y+Vc.height/2)], a:[Math.round(ac.x+ac.width/2),Math.round(ac.y+ac.height/2)],
              c_tri:ctr(n.querySelector('.input-connector.c polygon.triangle')), in_tri:ctr(n.querySelector('.input-connector.in polygon.triangle'))};}""")
def tclick(pg,pt): pg.mouse.click(pt[0],pt[1]); pg.wait_for_timeout(160)
def tdrag(pg,p,q,s=20):
    pg.mouse.move(p[0],p[1]);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(80)
    pg.mouse.move(p[0]+3,p[1]+3,steps=3);pg.mouse.move(q[0],q[1],steps=s);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(200)

def run(pg, fn):
    clear(pg); drag_place(pg,375,215,700,400); cancel_armed(pg)
    cc=coords(pg); before={json.dumps(c) for c in conns(pg)}
    fn(pg, cc)
    return [c for c in conns(pg) if json.dumps(c) not in before]

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        tests = {
          "POS a->c click": lambda pg,c:(tclick(pg,c["a"]),tclick(pg,c["c_tri"])),
          "in: V->in click":  lambda pg,c:(tclick(pg,c["V"]),tclick(pg,c["in_tri"])),
          "in: in->V click":  lambda pg,c:(tclick(pg,c["in_tri"]),tclick(pg,c["V"])),
          "in: drag V->in":   lambda pg,c:tdrag(pg,c["V"],c["in_tri"]),
          "in: drag in->V":   lambda pg,c:tdrag(pg,c["in_tri"],c["V"]),
          "in: dbl then V":   lambda pg,c:(pg.mouse.dblclick(c["in_tri"][0],c["in_tri"][1]),pg.wait_for_timeout(150),tclick(pg,c["V"])),
        }
        for name, fn in tests.items():
            new=run(pg, fn)
            print(f"{name}: NEW={json.dumps(new)}")
        b.close()
if __name__=="__main__": main()
