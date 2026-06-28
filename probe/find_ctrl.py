# FIND CTRL — locate the click point that reaches the relay's control connector (id 2).
# Grid points around the c pin; pin-first wire to terminal 'a'; read the target connectorId.
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
def info(pg):
    return pg.evaluate("""()=>{const n=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>x.querySelector('.input-connector.c')&&x.querySelector('.input-connector.in')).filter(x=>x.getBoundingClientRect().x>460)[0];
      const box=n.getBoundingClientRect(); const ctr=e=>{const r=e.getBoundingClientRect();return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];};
      const a=document.querySelector('.input-node .output-connector.a circle.connector-circle').getBoundingClientRect();
      return {box:[Math.round(box.x),Math.round(box.y),Math.round(box.width),Math.round(box.height)],
              c:ctr(n.querySelector('.input-connector.c circle.connector-circle')), in:ctr(n.querySelector('.input-connector.in circle.connector-circle')),
              a:[Math.round(a.x+a.width/2),Math.round(a.y+a.height/2)]};}""")
def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        clear(pg); drag(pg,375,215,700,400); cancel(pg)
        meta=info(pg); print("relay box/c/in/a:", json.dumps(meta))
        cx,cy = meta["c"]; a = meta["a"]
        # candidate points around c (circle ~cy, triangle ~cy+14), plus left of c
        cands=[]
        for dx in [-12,-6,0,6]:
            for dy in [0,8,14,20]:
                cands.append((cx+dx, cy+dy))
        for (px,py) in cands:
            clear(pg); drag(pg,375,215,700,400); cancel(pg)
            before={json.dumps(c) for c in conns(pg)}
            pg.keyboard.press("Escape"); pg.wait_for_timeout(40)
            pg.mouse.click(px,py); pg.wait_for_timeout(140); pg.mouse.click(a[0],a[1]); pg.wait_for_timeout(160)
            new=[c for c in conns(pg) if json.dumps(c) not in before]
            tid = new[0]["target"]["connectorId"] if (new and new[0]["target"]["nodeId"]=="0") else None
            mark = " <<< CTRL id 2" if tid=="2" else ""
            print(f"click({px},{py}) -> target_id={tid}{mark}  new={json.dumps(new)}")
        b.close()
if __name__=="__main__": main()
