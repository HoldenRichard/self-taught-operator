# CLEAN IN TEST — definitively answer: can the relay 'in' pin be wired by clicking its
# triangle handle, in a carryover-free state? Cancel the post-placement armed wire, verify
# no stray connection, then click V -> in-triangle and read the recorded connectorId. 3x.
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
def drag(pg,x1,y1,x2,y2,s=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=s);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)
def cancel_armed(pg):
    # press Escape, click far empty canvas to drop any armed wire, Escape again
    pg.keyboard.press("Escape"); pg.wait_for_timeout(80)
    pg.mouse.click(1250,260); pg.wait_for_timeout(120)
    pg.keyboard.press("Escape"); pg.wait_for_timeout(80)
def coords(pg):
    return pg.evaluate("""()=>{const n=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>x.querySelector('.input-connector.c')&&x.querySelector('.input-connector.in')).filter(x=>x.getBoundingClientRect().x>460)[0];
      const ctr=e=>{const r=e.getBoundingClientRect();return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];};
      const V=document.querySelector('.input-node .output-connector.V circle.connector-circle');
      const vr=V.getBoundingClientRect();
      return {V:[Math.round(vr.x+vr.width/2),Math.round(vr.y+vr.height/2)],
              c_tri:ctr(n.querySelector('.input-connector.c polygon.triangle')),
              in_tri:ctr(n.querySelector('.input-connector.in polygon.triangle'))};}""")
def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        for trial in range(3):
            clear(pg); drag(pg,375,215,700,400)
            cancel_armed(pg)
            n_after_cancel = len(conns(pg))
            cc = coords(pg)
            V, intri = cc["V"], cc["in_tri"]
            before={json.dumps(c) for c in conns(pg)}
            # click V then in-triangle
            pg.mouse.click(V[0],V[1]); pg.wait_for_timeout(150)
            pg.mouse.click(intri[0],intri[1]); pg.wait_for_timeout(180)
            new=[c for c in conns(pg) if json.dumps(c) not in before]
            print(f"trial {trial+1}: armed_leftover={n_after_cancel} V={V} in_tri={intri} -> NEW={json.dumps(new)}")
        b.close()
if __name__=="__main__": main()
