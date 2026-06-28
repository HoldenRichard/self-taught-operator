# CAPTURE FULL — inject RELAY-ON parallel (confirmed ids: a->c=1, V->in=2, out=0->output=0),
# read back which connections/nodes survived, Check, and dump the FULL truth table + the exact
# PASS/FAIL DOM. Reveals whether the in=2 connections take effect.
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"
PROBE_DIR = "/Users/holden/HackathonSF26/probe"

def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass

def circuit(t):
    A,B="0","1"
    nodes=[{"type":t,"x":190.49,"y":253,"id":A},{"type":t,"x":470.49,"y":253,"id":B}]
    conns=[
      {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":A,"connectorId":"2"}},
      {"source":{"nodeId":"input","connectorId":"0"},"target":{"nodeId":A,"connectorId":"1"}},
      {"source":{"nodeId":A,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}},
      {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":B,"connectorId":"2"}},
      {"source":{"nodeId":"input","connectorId":"1"},"target":{"nodeId":B,"connectorId":"1"}},
      {"source":{"nodeId":B,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}},
    ]
    return json.dumps({"nodes":nodes,"connections":conns})

TABLE = r"""
() => {
  const tr = document.querySelector('.test-results');
  return { html: tr ? tr.outerHTML.slice(0,1500) : null,
           text: tr ? (tr.textContent||'').trim().replace(/\s+/g,' ') : null,
           error_banner: !!document.querySelector('.error-banner'),
           dialog_cls: (document.querySelector('[class*=popup-dialog]')||{}).className||null };
}
"""

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
        pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        for t in ["RELAY-ON"]:
            pg.evaluate("(v)=>localStorage.setItem('%s', v)" % LS_KEY, circuit(t))
            pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2300); dismiss(pg)
            after = json.loads(pg.evaluate("()=>localStorage.getItem('%s')" % LS_KEY))
            print(f"=== type={t} ===")
            print("nodes after reload:", [{ 'id':n['id'],'type':n['type']} for n in after.get('nodes',[])])
            print("conns after reload:", len(after.get('connections',[])), "/6")
            for c in after.get("connections",[]):
                print("   ", json.dumps(c))
            el=pg.query_selector('button:has-text("Check solution")')
            if el: el.click(); pg.wait_for_timeout(900)
            tbl=pg.evaluate(TABLE)
            print("\nFULL TABLE TEXT:", tbl["text"])
            print("\nTABLE HTML:\n", tbl["html"])
            pg.screenshot(path=PROBE_DIR+f"/full_{t}.png")
        b.close()

if __name__=="__main__":
    main()
