# FINAL SOLVE — discover the control connector's REAL id via a precise click-wire (exact
# connector-circle center, not div bbox), then inject the correct relay-NAND and find the PASS.
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"
PROBE_DIR = "/Users/holden/HackathonSF26/probe"

# precise circle-center of a connector's visible pin
CIRC = r"""
(sel) => { const el=document.querySelector(sel); if(!el) return null;
  const c=el.querySelector('circle.connector-circle')||el; const r=c.getBoundingClientRect();
  return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)}; }
"""
def circ(pg, sel): return pg.evaluate(CIRC, sel)
def relay_sel(which): # which: 'out','c','in' for the placed relay (x>460)
    base = "Array.from(document.querySelectorAll('.diagram-node')).filter(n=>n.querySelector('.input-connector.c')&&n.querySelector('.input-connector.in')).filter(n=>n.getBoundingClientRect().x>460)[0]"
    m = {"out":".output-connector","c":".input-connector.c","in":".input-connector.in"}[which]
    return base, m
def relay_circ(pg, which):
    base,m = relay_sel(which)
    return pg.evaluate("(m)=>{const n=%s; if(!n)return null; const el=n.querySelector(m); const c=el.querySelector('circle.connector-circle')||el; const r=c.getBoundingClientRect(); return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};}" % base, m)

def conns(pg): return pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return o.connections||[]}" % LS_KEY)
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(350)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d:d.accept()); el=pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(400)
def drag(pg,x1,y1,x2,y2,steps=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=steps);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)

def click_wire(pg, src, tgt):
    before={json.dumps(c) for c in conns(pg)}
    for sdy,tdy in [(0,0),(0,2),(0,-2),(0,4)]:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(40)
        pg.mouse.click(src["x"],src["y"]+sdy); pg.wait_for_timeout(130)
        pg.mouse.click(tgt["x"],tgt["y"]+tdy); pg.wait_for_timeout(150)
        now=conns(pg)
        new=[c for c in now if json.dumps(c) not in before]
        if new: return new
    return []

def inject_check(pg, t, in_id, c_id):
    A,B="0","1"
    nodes=[{"type":t,"x":190.49,"y":253,"id":A},{"type":t,"x":470.49,"y":253,"id":B}]
    c=[{"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":A,"connectorId":in_id}},
       {"source":{"nodeId":"input","connectorId":"0"},"target":{"nodeId":A,"connectorId":c_id}},
       {"source":{"nodeId":A,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}},
       {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":B,"connectorId":in_id}},
       {"source":{"nodeId":"input","connectorId":"1"},"target":{"nodeId":B,"connectorId":c_id}},
       {"source":{"nodeId":B,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}}]
    pg.evaluate("(v)=>localStorage.setItem('%s', v)" % LS_KEY, json.dumps({"nodes":nodes,"connections":c}))
    pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2100); dismiss(pg)
    el=pg.query_selector('button:has-text("Check solution")')
    if el: el.click(); pg.wait_for_timeout(800)
    return pg.evaluate("()=>({eb:!!document.querySelector('.error-banner'), tbl:(document.querySelector('.test-results')||{}).textContent||null, dlg:(document.querySelector('[class*=popup-dialog]')||{}).className||null})")

def close_popup(pg):
    el=pg.query_selector('.popup-close, button:has-text("Close")')
    if el:
        try: el.click(); pg.wait_for_timeout(250)
        except Exception: pass

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
        pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)
        drag(pg,375,215,700,400)
        a=circ(pg,'.input-node .output-connector.a'); V=circ(pg,'.input-node .output-connector.V')
        out=circ(pg,'.output-node .input-connector')
        r_c=relay_circ(pg,"c"); r_in=relay_circ(pg,"in"); r_out=relay_circ(pg,"out")
        print("precise circles: a",a,"V",V,"out",out,"| r_c",r_c,"r_in",r_in,"r_out",r_out)
        # discover control id: precise click a -> relay c-circle
        new = click_wire(pg, a, r_c)
        print("a->relay.c(precise):", json.dumps(new))
        ctrl_id = new[0]["target"]["connectorId"] if new and new[0]["target"]["nodeId"]=="0" else None
        # discover in id: precise click V -> relay in-circle
        new2 = click_wire(pg, V, r_in)
        print("V->relay.in(precise):", json.dumps(new2))
        in_id = new2[0]["target"]["connectorId"] if new2 and new2[0]["target"]["nodeId"]=="0" else None
        print(f"\nDISCOVERED: control_id={ctrl_id}  in_id={in_id}")
        if ctrl_id is None or in_id is None:
            print("discovery failed; precise clicks still missing"); b.close(); return
        clear(pg)
        # now inject correct NAND for both types
        found=None
        for t in ["RELAY-ON","RELAY-OFF"]:
            v=inject_check(pg, t, in_id, ctrl_id)
            print(f"[{t} in={in_id} c={ctrl_id}] error_banner={v['eb']} dlg={v['dlg']} tbl={v['tbl']!r}")
            if not v["eb"]:
                found=(t,v); pg.screenshot(path=PROBE_DIR+"/PASS_verdict.png"); break
            close_popup(pg)
        if found:
            print("\n##### PASS captured with", found[0], "#####"); print(json.dumps(found[1], indent=2))
        else:
            print("\nstill no pass — control gating still not working")
        pg.wait_for_timeout(500); b.close()

if __name__=="__main__":
    main()
