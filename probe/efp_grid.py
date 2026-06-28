# EFP GRID — map exactly where the relay's bottom connectors (c, in) are hittable at rest,
# to find the precise click point for 'in' (and what occludes it when it snaps to output).
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
def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)
        drag(pg,375,215,700,400)
        # exact triangle + circle coords for c and in
        info=pg.evaluate("""()=>{const n=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>x.querySelector('.input-connector.c')&&x.querySelector('.input-connector.in')).filter(x=>x.getBoundingClientRect().x>460)[0];
          const ctr=e=>{const r=e.getBoundingClientRect();return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];};
          return {c_circ:ctr(n.querySelector('.input-connector.c circle.connector-circle')), c_tri:ctr(n.querySelector('.input-connector.c polygon.triangle')),
                  in_circ:ctr(n.querySelector('.input-connector.in circle.connector-circle')), in_tri:ctr(n.querySelector('.input-connector.in polygon.triangle')),
                  out_circ:ctr(n.querySelector('.output-connector circle.connector-circle'))};}""")
        print("coords:", json.dumps(info))
        # grid EFP over the bottom region
        grid=pg.evaluate("""()=>{const out=[]; for(let y=430;y<=466;y+=4){let row=[]; for(let x=672;x<=728;x+=4){const e=document.elementFromPoint(x,y); let c=e?((e.getAttribute&&e.getAttribute('class'))||e.tagName):'-'; c=String(c); let tag=/in\\b/.test(c)&&/connector/.test(c)?'IN':/\\bc\\b/.test(c)&&/connector/.test(c)?'C ':/output|droptarget/.test(c)?'O ':/event-overlay/.test(c)?'ev':/triangle/.test(c)?'tr':c.slice(0,2); row.push(tag);} out.push('y='+y+' '+row.join(' '));} return out;}""")
        print("\nEFP grid (x 672..728 step4):")
        for r in grid: print("  ", r)
        b.close()
if __name__=="__main__": main()
