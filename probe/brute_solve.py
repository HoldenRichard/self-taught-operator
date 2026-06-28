# BRUTE SOLVE — find the correct relay-NAND by injecting circuits and letting the REFEREE
# judge. Reads the real default-off type string, then tries {2 relay types} x {2 in/c
# connectorId assignments} (out=0 confirmed). Captures the PASS verdict when found.
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"
PROBE_DIR = "/Users/holden/HackathonSF26/probe"

VERDICT = r"""
() => {
  const d = document.querySelector('[class*=popup-dialog]');
  const banner = document.querySelector('.error-banner');
  return {
    dialog_cls: d ? d.getAttribute('class') : null,
    dialog_txt: d ? (d.textContent||'').trim().replace(/\s+/g,' ').slice(0,240) : null,
    error_banner: !!banner,
    levels: localStorage.getItem('NandGame:Levels'),
    success_hits: Array.from(document.querySelectorAll('[class*=success],[class*=correct],[class*=solved],[class*=congrat],[class*=complete]')).map(e=>e.getAttribute('class')).slice(0,8),
  };
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
def close_popup(pg):
    el=pg.query_selector('.popup-close, button:has-text("Close")')
    if el:
        try: el.click(); pg.wait_for_timeout(300)
        except Exception: pass

def build(type_str, control_id, in_id):
    A,B="0","1"
    nodes=[{"type":type_str,"x":190.49,"y":253,"id":A},{"type":type_str,"x":470.49,"y":253,"id":B}]
    conns=[
      {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":A,"connectorId":in_id}},   # V->A.in
      {"source":{"nodeId":"input","connectorId":"0"},"target":{"nodeId":A,"connectorId":control_id}}, # a->A.control
      {"source":{"nodeId":A,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}},
      {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":B,"connectorId":in_id}},   # V->B.in
      {"source":{"nodeId":"input","connectorId":"1"},"target":{"nodeId":B,"connectorId":control_id}}, # b->B.control
      {"source":{"nodeId":B,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}},
    ]
    return json.dumps({"nodes":nodes,"connections":conns})

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
        pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)

        # learn default-off type string (toolbox default-off ~375,360)
        drag(pg,375,360,700,400)
        raw=json.loads(pg.evaluate("()=>localStorage.getItem('%s')" % LS_KEY))
        DOFF = raw["nodes"][0]["type"] if raw["nodes"] else "RELAY-OFF"
        print("default-OFF type string =", DOFF, "| default-ON = RELAY-ON")
        clear(pg)

        combos=[]
        for t in ["RELAY-ON", DOFF]:
            for control_id, in_id in [("1","2"),("2","1")]:
                combos.append((t,control_id,in_id))
        solved=None
        for (t,cid,iid) in combos:
            pg.evaluate("(v)=>localStorage.setItem('%s', v)" % LS_KEY, build(t,cid,iid))
            pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2200); dismiss(pg)
            el=pg.query_selector('button:has-text("Check solution")')
            if el: el.click(); pg.wait_for_timeout(900)
            v=pg.evaluate(VERDICT)
            tag=f"type={t} control_id={cid} in_id={iid}"
            print(f"\n[{tag}] error_banner={v['error_banner']} dialog_cls={v['dialog_cls']} levels={v['levels']}")
            print("   txt:", v["dialog_txt"])
            if not v["error_banner"]:
                solved=(tag, v); pg.screenshot(path=PROBE_DIR+"/PASS_verdict.png")
                print("   <<<<< PASS (no error banner) >>>>>")
                break
            close_popup(pg)
        if solved:
            print("\n##### SOLVED:", solved[0]); print(json.dumps(solved[1], indent=2))
        else:
            print("\nno PASS among combos — need to rethink topology")
        pg.wait_for_timeout(500); b.close()

if __name__=="__main__":
    main()
