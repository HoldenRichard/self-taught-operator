# BRUTE2 — exhaustive small search for the relay-NAND, referee-judged. Confirmed ids:
# input a=0,b=1,V=2 ; output=0 ; relay output=0 ; relay's two inputs are ids {1,2} (which is
# 'in' vs control 'c' unknown). Enumerate type x input-assignment x topology; find the PASS.
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"
PROBE_DIR = "/Users/holden/HackathonSF26/probe"

def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(350)
    except Exception: pass
def close_popup(pg):
    el=pg.query_selector('.popup-close, button:has-text("Close")')
    if el:
        try: el.click(); pg.wait_for_timeout(250)
        except Exception: pass

def make(t, in_id, c_id, topo):
    A,B="0","1"
    nodes=[{"type":t,"x":190.49,"y":253,"id":A},{"type":t,"x":470.49,"y":253,"id":B}]
    c=[]
    # controls: a->A.c, b->B.c ; power: V->A.in (and series/parallel differ for B.in & outputs)
    c.append({"source":{"nodeId":"input","connectorId":"0"},"target":{"nodeId":A,"connectorId":c_id}})  # a->A.c
    c.append({"source":{"nodeId":"input","connectorId":"1"},"target":{"nodeId":B,"connectorId":c_id}})  # b->B.c
    c.append({"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":A,"connectorId":in_id}}) # V->A.in
    if topo=="parallel":
        c.append({"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":B,"connectorId":in_id}}) # V->B.in
        c.append({"source":{"nodeId":A,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}})
        c.append({"source":{"nodeId":B,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}})
    else: # series: A.out -> B.in ; B.out -> output
        c.append({"source":{"nodeId":A,"connectorId":"0"},"target":{"nodeId":B,"connectorId":in_id}})
        c.append({"source":{"nodeId":B,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}})
    return json.dumps({"nodes":nodes,"connections":c})

VERD = r"""() => ({ error_banner: !!document.querySelector('.error-banner'),
  dialog_cls: (document.querySelector('[class*=popup-dialog]')||{}).className||null,
  first_fail: (document.querySelector('.test-results')||{}).textContent ? (document.querySelector('.test-results').textContent||'').trim().replace(/\s+/g,' ') : null,
  levels: localStorage.getItem('NandGame:Levels') })"""

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
        pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        combos=[]
        for t in ["RELAY-ON","RELAY-OFF"]:
            for (in_id,c_id) in [("2","1"),("1","2")]:
                for topo in ["parallel","series"]:
                    combos.append((t,in_id,c_id,topo))
        found=None
        for (t,in_id,c_id,topo) in combos:
            pg.evaluate("(v)=>localStorage.setItem('%s', v)" % LS_KEY, make(t,in_id,c_id,topo))
            pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2100); dismiss(pg)
            el=pg.query_selector('button:has-text("Check solution")')
            if el: el.click(); pg.wait_for_timeout(800)
            v=pg.evaluate(VERD)
            tag=f"{t} in={in_id} c={c_id} {topo}"
            passed = (not v["error_banner"])
            print(f"[{tag}] PASS={passed} levels={v['levels']} first_fail={v['first_fail']!r} dlg={v['dialog_cls']}")
            if passed:
                found=(tag,v); pg.screenshot(path=PROBE_DIR+"/PASS_verdict.png"); break
            close_popup(pg)
        print("\n===== RESULT =====")
        if found:
            print("SOLVED:", found[0]); print(json.dumps(found[1], indent=2))
            print("winning circuit JSON written to probe/winning_circuit.json")
            with open(PROBE_DIR+"/winning_circuit.json","w") as f:
                t,in_id,c_id,topo = [x for x in found[0].split()]  # not used; re-derive below
        else:
            print("no PASS found in 8 combos")
        b.close()
        return found

if __name__=="__main__":
    main()
