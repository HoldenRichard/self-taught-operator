# Does NandGame zoom? If the canvas zooms, relay connectors spread apart and the 'in' pin
# stops overlapping the output droptarget -> reliable clicks. Try wheel + ctrl+wheel + buttons.
import json
from playwright.sync_api import sync_playwright
LS_KEY="NandGame:Levels:RELAY_NAND"
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(350)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d:d.accept()); el=pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(400)
def drag(pg,x1,y1,x2,y2,s=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=s);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)
def spacing(pg):
    return pg.evaluate("""()=>{const n=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>x.querySelector('.input-connector.c')&&x.querySelector('.input-connector.in')).filter(x=>x.getBoundingClientRect().x>460)[0]; if(!n)return null;
      const c=n.querySelector('.input-connector.c').getBoundingClientRect(), i=n.querySelector('.input-connector.in').getBoundingClientRect(), o=n.querySelector('.output-connector').getBoundingClientRect(), box=n.getBoundingClientRect();
      return {node_w:Math.round(box.width), node_h:Math.round(box.height), c_x:Math.round(c.x+c.width/2), in_x:Math.round(i.x+i.width/2), c_in_gap:Math.round((i.x+i.width/2)-(c.x+c.width/2)), out_y:Math.round(o.y+o.height/2), in_y:Math.round(i.y+i.height/2)};}""")
def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)
        drag(pg,375,215,700,400)
        print("before zoom:", json.dumps(spacing(pg)))
        # method 1: wheel over canvas
        pg.mouse.move(700,400)
        for _ in range(3): pg.mouse.wheel(0,-150); pg.wait_for_timeout(200)
        print("after wheel up x3:", json.dumps(spacing(pg)))
        # method 2: ctrl+wheel
        pg.keyboard.down("Control")
        for _ in range(3): pg.mouse.wheel(0,-150); pg.wait_for_timeout(200)
        pg.keyboard.up("Control")
        print("after ctrl+wheel up x3:", json.dumps(spacing(pg)))
        # method 3: '+' key
        pg.keyboard.press("+"); pg.wait_for_timeout(300); pg.keyboard.press("=")
        pg.wait_for_timeout(300)
        print("after +/= keys:", json.dumps(spacing(pg)))
        # look for zoom controls in DOM
        ctrls = pg.evaluate("""()=>Array.from(document.querySelectorAll('button,[class*=zoom],[class*=scale]')).map(e=>(e.getAttribute('class')||'')+' | '+(e.textContent||'').trim().slice(0,12)).filter(s=>/zoom|scale|\\+|\\-/i.test(s)).slice(0,10)""")
        print("zoom-ish controls:", json.dumps(ctrls))
        b.close()
if __name__=="__main__": main()
