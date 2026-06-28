# Test minimal topologies that AVOID the hard-to-click 'in' connector: relay control + output
# only (parallel). If one passes, the relay-NAND is fully click-buildable on reliable connectors.
import json
from playwright.sync_api import sync_playwright
LS_KEY="NandGame:Levels:RELAY_NAND"; PROBE_DIR="/Users/holden/HackathonSF26/probe"
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(350)
    except Exception: pass
def close_popup(pg):
    el=pg.query_selector('.popup-close, button:has-text("Close")')
    if el:
        try: el.click(); pg.wait_for_timeout(200)
        except: pass
def variants():
    out=[]
    for t in ["RELAY-ON","RELAY-OFF"]:
        # control-only parallel (no in/V)
        out.append((f"{t} control-only parallel", t, [
          {"source":{"nodeId":"input","connectorId":"0"},"target":{"nodeId":"0","connectorId":"1"}},
          {"source":{"nodeId":"input","connectorId":"1"},"target":{"nodeId":"1","connectorId":"1"}},
          {"source":{"nodeId":"0","connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}},
          {"source":{"nodeId":"1","connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}}]))
        # control + V on output's other path? try V->relay.in via connectorId 2 AND control
        out.append((f"{t} ctrl+V-on-2 parallel", t, [
          {"source":{"nodeId":"input","connectorId":"0"},"target":{"nodeId":"0","connectorId":"1"}},
          {"source":{"nodeId":"input","connectorId":"1"},"target":{"nodeId":"1","connectorId":"1"}},
          {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":"0","connectorId":"2"}},
          {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":"1","connectorId":"2"}},
          {"source":{"nodeId":"0","connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}},
          {"source":{"nodeId":"1","connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}}]))
    return out
def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        found=None
        for label,t,conns in variants():
            circ={"nodes":[{"type":t,"x":190.49,"y":253,"id":"0"},{"type":t,"x":470.49,"y":253,"id":"1"}],"connections":conns}
            pg.evaluate("(v)=>localStorage.setItem('%s',v)" % LS_KEY, json.dumps(circ))
            pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2100); dismiss(pg)
            el=pg.query_selector('button:has-text("Check solution")')
            if el: el.click(); pg.wait_for_timeout(800)
            v=pg.evaluate("()=>({eb:!!document.querySelector('.error-banner'),tbl:(document.querySelector('.test-results')||{}).textContent||null,levels:localStorage.getItem('NandGame:Levels')})")
            print(f"[{label}] PASS={not v['eb']} levels={v['levels']} tbl={v['tbl']!r}")
            if not v["eb"]:
                found=(label,t,conns); pg.screenshot(path=PROBE_DIR+"/PASS_verdict.png"); break
            close_popup(pg)
        if found:
            print("\n##### PASS #####", found[0])
            with open(PROBE_DIR+"/winning.json","w") as f: json.dump({"label":found[0],"type":found[1],"connections":found[2]}, f, indent=1)
        else: print("\nno pass in no-in variants")
        pg.wait_for_timeout(400); b.close()
if __name__=="__main__": main()
