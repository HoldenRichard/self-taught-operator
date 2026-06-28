# STRAT TEST — find ANY wiring strategy that records a DISTINCT relay-input connectorId
# (not 0). Tests reverse-order clicks and drags between a source and the relay's control.
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
    if el: el.click(); pg.wait_for_timeout(400)
def drag_place(pg,x1,y1,x2,y2,s=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=s);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)
def pts(pg):
    a=pg.evaluate("()=>{const e=document.querySelector('.input-node .output-connector.a').querySelector('circle.connector-circle');const r=e.getBoundingClientRect();return{x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)}}")
    def rtri(which):
        base="Array.from(document.querySelectorAll('.diagram-node')).filter(n=>n.querySelector('.input-connector.c')&&n.querySelector('.input-connector.in')).filter(n=>n.getBoundingClientRect().x>460)[0]"
        return pg.evaluate("()=>{const n=%s;const cc=n.querySelector('.input-connector.%s');const e=cc.querySelector('polygon.triangle');const r=e.getBoundingClientRect();return{x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)}}" % (base, which))
    return a, rtri("c"), rtri("in")
def setup(pg):
    clear(pg); drag_place(pg,375,215,700,400); return pts(pg)
def delta(pg, before): return [c for c in conns(pg) if json.dumps(c) not in before]
def click(pg,p,dy=0): pg.mouse.click(p["x"],p["y"]+dy); pg.wait_for_timeout(160)
def drag2(pg,p,q,s=22):
    pg.mouse.move(p["x"],p["y"]);pg.wait_for_timeout(50);pg.mouse.down();pg.wait_for_timeout(80)
    pg.mouse.move(p["x"]+3,p["y"]+3,steps=3);pg.mouse.move(q["x"],q["y"],steps=s);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(200)

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        strategies = [
            ("S1 click a then c", lambda a,c,i:(pg.keyboard.press("Escape"), click(pg,a), click(pg,c))),
            ("S2 click c then a (reverse)", lambda a,c,i:(pg.keyboard.press("Escape"), click(pg,c), click(pg,a))),
            ("S3 drag a->c", lambda a,c,i:(pg.keyboard.press("Escape"), drag2(pg,a,c))),
            ("S4 drag c->a", lambda a,c,i:(pg.keyboard.press("Escape"), drag2(pg,c,a))),
        ]
        for name, fn in strategies:
            a,c,i = setup(pg)
            before={json.dumps(x) for x in conns(pg)}
            fn(a,c,i); pg.wait_for_timeout(150)
            d = delta(pg, before)
            tgt = d[0]["target"] if d else None
            print(f"{name}: a={a} c_tri={c}  NEW={json.dumps(d)}")
        b.close()

if __name__=="__main__": main()
