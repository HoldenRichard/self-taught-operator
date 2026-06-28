# INSPECT relay DOM — ground-truth the connector id mapping. Dump the placed relay node's
# structure: each connector's classes + any data-* attributes + parent group, and the raw
# outerHTML so we can see how NandGame encodes connectorId for the 'in' connector.
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"

DUMP = r"""
() => {
  const relay = Array.from(document.querySelectorAll('.diagram-node'))
    .filter(n=>n.querySelector('.input-connector.c')&&n.querySelector('.input-connector.in'))
    .filter(n=>{const r=n.getBoundingClientRect();return r.x>460&&r.width>0;})[0];
  if(!relay) return {err:'no relay'};
  const desc = el => ({
    tag: el.tagName,
    cls: (el.getAttribute('class')||''),
    data: Object.assign({}, el.dataset),
    attrs: Array.from(el.attributes).map(a=>a.name+'='+a.value).filter(a=>!a.startsWith('class')).slice(0,8),
  });
  const conns = Array.from(relay.querySelectorAll('.input-connector, .output-connector')).map(c=>{
    const grp = c.closest('.connector-group'); const row = c.closest('.connector-row');
    return { self: desc(c), group: grp?desc(grp):null, row: row?desc(row):null,
             label: (c.textContent||'').trim().slice(0,8) };
  });
  return { node: desc(relay), connectors: conns, outerHTML: relay.outerHTML.slice(0, 2600) };
}
"""
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

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
        pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)
        drag(pg,375,215,700,400)
        d = pg.evaluate(DUMP)
        print("NODE:", json.dumps(d.get("node"), indent=1))
        print("\nCONNECTORS:")
        for c in d.get("connectors", []):
            print(json.dumps(c, indent=1))
        print("\nOUTERHTML (truncated):\n", d.get("outerHTML"))
        b.close()

if __name__=="__main__":
    main()
