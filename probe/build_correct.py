# BUILD CORRECT — wire relay pins with the WORKING interaction: click the relay pin FIRST,
# then the terminal (start the wire from the relay pin). Build parallel relay-NAND by clicks,
# try RELAY-ON then RELAY-OFF, Check, capture the PASS verdict.
import json
from playwright.sync_api import sync_playwright
LS_KEY="NandGame:Levels:RELAY_NAND"; PROBE_DIR="/Users/holden/HackathonSF26/probe"
OUT=(588,190)
def conns(pg): return pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return o.connections||[]}" % LS_KEY)
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(350)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d:d.accept()); el=pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)
def drag(pg,x1,y1,x2,y2,s=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=s);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)
def cancel(pg):
    pg.keyboard.press("Escape"); pg.wait_for_timeout(70); pg.mouse.click(1250,260); pg.wait_for_timeout(110); pg.keyboard.press("Escape"); pg.wait_for_timeout(70)
def terms(pg):
    return pg.evaluate("""()=>{const t=s=>{const e=document.querySelector(s+' circle.connector-circle').getBoundingClientRect();return [Math.round(e.x+e.width/2),Math.round(e.y+e.height/2)];};
      return {a:t('.input-node .output-connector.a'), b:t('.input-node .output-connector.b'), V:t('.input-node .output-connector.V')};}""")
def relay_pins(pg):
    return pg.evaluate("""()=>{const ns=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>x.querySelector('.input-connector.c')&&x.querySelector('.input-connector.in')).filter(x=>x.getBoundingClientRect().x>460).sort((p,q)=>p.getBoundingClientRect().x-q.getBoundingClientRect().x);
      const tri=(n,w)=>{const e=n.querySelector('.input-connector.'+w+' polygon.triangle').getBoundingClientRect();return [Math.round(e.x+e.width/2),Math.round(e.y+e.height/2)];};
      const oc=(n)=>{const e=n.querySelector('.output-connector circle.connector-circle').getBoundingClientRect();return [Math.round(e.x+e.width/2),Math.round(e.y+e.height/2)];};
      return ns.map(n=>({in:tri(n,'in'), c:tri(n,'c'), out:oc(n)}));}""")
def wire_pinfirst(pg, pin, term):
    """Start wire from relay pin, then click terminal. Verify; retry reverse + offsets."""
    before=len(conns(pg))
    for (a,bp) in [(pin,term),(term,pin)]:
        for dy in [0,3,-3,6]:
            pg.keyboard.press("Escape"); pg.wait_for_timeout(40)
            pg.mouse.click(a[0],a[1]+dy); pg.wait_for_timeout(140)
            pg.mouse.click(bp[0],bp[1]); pg.wait_for_timeout(160)
            if len(conns(pg))>before: return True
    return False

def build(pg, ty):
    clear(pg)
    drag(pg,375,ty,650,400); cancel(pg)
    drag(pg,375,ty,950,400); cancel(pg)
    rp=relay_pins(pg); tm=terms(pg)
    if len(rp)<2: return {"err":"placement","rp":rp}
    A,B=rp[0],rp[1]
    r={}
    r['A.in<-V']=wire_pinfirst(pg, A["in"], tm["V"])
    r['A.c<-a']=wire_pinfirst(pg, A["c"], tm["a"])
    r['A.out->out']=wire_pinfirst(pg, A["out"], OUT)
    r['B.in<-V']=wire_pinfirst(pg, B["in"], tm["V"])
    r['B.c<-b']=wire_pinfirst(pg, B["c"], tm["b"])
    r['B.out->out']=wire_pinfirst(pg, B["out"], OUT)
    cs=conns(pg)
    pg.screenshot(path=PROBE_DIR+f"/bc_{ty}.png")
    el=pg.query_selector('button:has-text("Check solution")')
    if el: el.click(); pg.wait_for_timeout(900)
    v=pg.evaluate("()=>({eb:!!document.querySelector('.error-banner'),tbl:(document.querySelector('.test-results')||{}).textContent||null,dlg:(document.querySelector('[class*=popup-dialog]')||{}).className||null,levels:localStorage.getItem('NandGame:Levels')})")
    return {"wires":r,"nconns":len(cs),"conns":cs,"verdict":v}

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        for label,ty in [("RELAY-ON",215),("RELAY-OFF",360)]:
            print(f"\n===== {label} =====")
            r=build(pg,ty); print(json.dumps(r,indent=1))
            v=r.get("verdict")
            if v and not v["eb"]:
                print(f"\n##### PASS with {label} #####"); pg.screenshot(path=PROBE_DIR+"/PASS_verdict.png")
                with open(PROBE_DIR+"/winning.json","w") as f: json.dump({"type":label,"conns":r["conns"]},f,indent=1)
                break
            el=pg.query_selector('.popup-close, button:has-text("Close")')
            if el:
                try: el.click(); pg.wait_for_timeout(250)
                except: pass
        b.close()
if __name__=="__main__": main()
