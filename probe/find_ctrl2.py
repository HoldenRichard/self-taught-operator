# FIND CTRL 2 — search the relay's LEFT/coil side and other regions for the control
# connector (connectorId 2). pin-first wire to 'a'; read target id; hunt for "2".
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
    if el: el.click(); pg.wait_for_timeout(420)
def drag(pg,x1,y1,x2,y2,s=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=s);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)
def cancel(pg):
    pg.keyboard.press("Escape"); pg.wait_for_timeout(70); pg.mouse.click(1250,260); pg.wait_for_timeout(110); pg.keyboard.press("Escape"); pg.wait_for_timeout(70)
def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        clear(pg); drag(pg,375,215,700,400); cancel(pg)
        a=pg.evaluate("()=>{const e=document.querySelector('.input-node .output-connector.a circle.connector-circle').getBoundingClientRect();return[Math.round(e.x+e.width/2),Math.round(e.y+e.height/2)]}")
        # relay box at (661,362,80,90). Search left/coil edge, middle, and a wide net.
        cands=[(669,407),(665,400),(672,420),(661,407),(675,407),(680,407),  # left/coil
               (700,440),(706,440),(718,440),                                  # right of in
               (688,430),(700,430),                                            # upper bottom row
               (670,440),(665,447)]                                            # far-left bottom
        for (px,py) in cands:
            clear(pg); drag(pg,375,215,700,400); cancel(pg)
            before={json.dumps(c) for c in conns(pg)}
            pg.keyboard.press("Escape"); pg.wait_for_timeout(40)
            pg.mouse.click(px,py); pg.wait_for_timeout(140); pg.mouse.click(a[0],a[1]); pg.wait_for_timeout(160)
            new=[c for c in conns(pg) if json.dumps(c) not in before]
            tid=new[0]["target"]["connectorId"] if (new and new[0]["target"]["nodeId"]=="0") else None
            print(f"click({px},{py}) -> id={tid}{' <<< CTRL 2' if tid=='2' else ''}  {json.dumps(new) if new else ''}")
        b.close()
if __name__=="__main__": main()
