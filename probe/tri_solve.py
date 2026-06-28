# TRI SOLVE — click the polygon.triangle HANDLE of each relay input connector (the real wire
# handle), discover control/in ids, inject correct NAND, capture PASS.
import json
from playwright.sync_api import sync_playwright

LS_KEY="NandGame:Levels:RELAY_NAND"; PROBE_DIR="/Users/holden/HackathonSF26/probe"

def ctr(pg, sel, inner):
    return pg.evaluate("""(a)=>{const n=document.querySelector(a[0]); if(!n)return null; const e=n.querySelector(a[1])||n; const r=e.getBoundingClientRect(); return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};}""",[sel,inner])
def relay_tri(pg, which):
    base="Array.from(document.querySelectorAll('.diagram-node')).filter(n=>n.querySelector('.input-connector.c')&&n.querySelector('.input-connector.in')).filter(n=>n.getBoundingClientRect().x>460)[0]"
    m={"c":".input-connector.c","in":".input-connector.in","out":".output-connector"}[which]
    inner = "polygon.triangle" if which in ("c","in") else "circle.connector-circle"
    return pg.evaluate("(a)=>{const n=%s; if(!n)return null; const cc=n.querySelector(a[0]); const e=cc.querySelector(a[1])||cc; const r=e.getBoundingClientRect(); return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};}" % base,[m,inner])
def conns(pg): return pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return o.connections||[]}" % LS_KEY)
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
def click_wire(pg, src, tgt):
    before={json.dumps(c) for c in conns(pg)}
    for sdy,tdy in [(0,0),(0,3),(0,-3),(0,6),(0,-6)]:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(40)
        pg.mouse.click(src["x"],src["y"]+sdy); pg.wait_for_timeout(130)
        pg.mouse.click(tgt["x"],tgt["y"]+tdy); pg.wait_for_timeout(150)
        new=[c for c in conns(pg) if json.dumps(c) not in before]
        if new: return new
    return []
def inject_check(pg,t,in_id,c_id):
    A,B="0","1"; nodes=[{"type":t,"x":190.49,"y":253,"id":A},{"type":t,"x":470.49,"y":253,"id":B}]
    c=[{"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":A,"connectorId":in_id}},
       {"source":{"nodeId":"input","connectorId":"0"},"target":{"nodeId":A,"connectorId":c_id}},
       {"source":{"nodeId":A,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}},
       {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":B,"connectorId":in_id}},
       {"source":{"nodeId":"input","connectorId":"1"},"target":{"nodeId":B,"connectorId":c_id}},
       {"source":{"nodeId":B,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}}]
    pg.evaluate("(v)=>localStorage.setItem('%s',v)" % LS_KEY, json.dumps({"nodes":nodes,"connections":c}))
    pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2100); dismiss(pg)
    el=pg.query_selector('button:has-text("Check solution")')
    if el: el.click(); pg.wait_for_timeout(800)
    return pg.evaluate("()=>({eb:!!document.querySelector('.error-banner'),tbl:(document.querySelector('.test-results')||{}).textContent||null,dlg:(document.querySelector('[class*=popup-dialog]')||{}).className||null,levels:localStorage.getItem('NandGame:Levels')})")
def close_popup(pg):
    el=pg.query_selector('.popup-close, button:has-text("Close")')
    if el:
        try: el.click(); pg.wait_for_timeout(200)
        except: pass

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)
        drag(pg,375,215,700,400)
        a=ctr(pg,'.input-node .output-connector.a','circle.connector-circle'); V=ctr(pg,'.input-node .output-connector.V','circle.connector-circle')
        rc=relay_tri(pg,"c"); rin=relay_tri(pg,"in")
        print("a",a,"V",V,"relay c-triangle",rc,"in-triangle",rin)
        n1=click_wire(pg,a,rc); print("a->c_triangle:", json.dumps(n1))
        n2=click_wire(pg,V,rin); print("V->in_triangle:", json.dumps(n2))
        cid=n1[0]["target"]["connectorId"] if n1 and n1[0]["target"]["nodeId"]=="0" else None
        iid=n2[0]["target"]["connectorId"] if n2 and n2[0]["target"]["nodeId"]=="0" else None
        print(f"DISCOVERED control_id={cid} in_id={iid}")
        if cid is None or iid is None or cid==iid:
            print("triangle clicks still ambiguous"); b.close(); return
        clear(pg)
        found=None
        for t in ["RELAY-ON","RELAY-OFF"]:
            v=inject_check(pg,t,iid,cid); print(f"[{t} in={iid} c={cid}] eb={v['eb']} dlg={v['dlg']} tbl={v['tbl']!r} levels={v['levels']}")
            if not v["eb"]: found=(t,v,iid,cid); pg.screenshot(path=PROBE_DIR+"/PASS_verdict.png"); break
            close_popup(pg)
        if found:
            print("\n##### PASS #####", found[0],"in",found[2],"c",found[3]); print(json.dumps(found[1],indent=2))
            with open(PROBE_DIR+"/winning.json","w") as f: json.dump({"type":found[0],"in_id":found[2],"c_id":found[3]},f)
        else: print("\nno pass")
        pg.wait_for_timeout(500); b.close()

if __name__=="__main__": main()
