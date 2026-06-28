# BUILD BY CLICKS — consume the post-placement armed wire productively (relay.out->output),
# which clears carryover; then wire controls + power cleanly. Build parallel NAND, Check,
# capture the PASS verdict. Tries RELAY-ON then RELAY-OFF.
import json
from playwright.sync_api import sync_playwright

LS_KEY="NandGame:Levels:RELAY_NAND"; PROBE_DIR="/Users/holden/HackathonSF26/probe"
OUT_TGT=(588,190)  # empirically-validated output-terminal input hit-point

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
def conns(pg): return pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return o.connections||[]}" % LS_KEY)
def click(pg,x,y,d=150): pg.mouse.click(x,y); pg.wait_for_timeout(d)
def term(pg,which):
    sel={'a':'.input-node .output-connector.a','b':'.input-node .output-connector.b','V':'.input-node .output-connector.V'}[which]
    return pg.evaluate("(s)=>{const e=document.querySelector(s).querySelector('circle.connector-circle');const r=e.getBoundingClientRect();return[Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)]}", sel)
def relays(pg):
    return pg.evaluate("""()=>{
      const ns=Array.from(document.querySelectorAll('.diagram-node')).filter(n=>n.querySelector('.input-connector.c')&&n.querySelector('.input-connector.in')).filter(n=>n.getBoundingClientRect().x>460).sort((p,q)=>p.getBoundingClientRect().x-q.getBoundingClientRect().x);
      const tri=(n,w)=>{const e=n.querySelector('.input-connector.'+w).querySelector('polygon.triangle');const r=e.getBoundingClientRect();return[Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];};
      return ns.map(n=>({c:tri(n,'c'), in_:tri(n,'in')}));
    }""")

def wire(pg, s, t):
    before=len(conns(pg)); pg.keyboard.press("Escape"); pg.wait_for_timeout(40)
    for tdy in [0,4,-4,8]:
        click(pg,s[0],s[1],140); click(pg,t[0],t[1]+tdy,160)
        if len(conns(pg))>before: return True
        pg.keyboard.press("Escape"); pg.wait_for_timeout(40)
    return False

def build_and_check(pg, toolbox_y):
    clear(pg)
    # place A, consume armed wire -> output
    drag(pg,375,toolbox_y,650,400); pg.wait_for_timeout(200); click(pg,*OUT_TGT,250)
    # place B, consume armed wire -> output
    drag(pg,375,toolbox_y,950,400); pg.wait_for_timeout(200); click(pg,*OUT_TGT,250)
    rs=relays(pg)
    if len(rs)<2: return {"err":"relays not placed","n":len(rs)}
    A,B=rs[0],rs[1]
    a=term(pg,'a'); b=term(pg,'b'); V=term(pg,'V')
    res={}
    res['a->A.c']=wire(pg,a,A["c"]); res['V->A.in']=wire(pg,V,A["in_"])
    res['b->B.c']=wire(pg,b,B["c"]); res['V->B.in']=wire(pg,V,B["in_"])
    cs=conns(pg)
    pg.screenshot(path=PROBE_DIR+f"/build_{toolbox_y}.png")
    el=pg.query_selector('button:has-text("Check solution")')
    if el: el.click(); pg.wait_for_timeout(900)
    v=pg.evaluate("()=>({eb:!!document.querySelector('.error-banner'),tbl:(document.querySelector('.test-results')||{}).textContent||null,dlg:(document.querySelector('[class*=popup-dialog]')||{}).className||null,levels:localStorage.getItem('NandGame:Levels')})")
    return {"wires":res,"nconns":len(cs),"conns":cs,"verdict":v}

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        for label,y in [("RELAY-ON",215),("RELAY-OFF",360)]:
            print(f"\n===== build with {label} (toolbox y={y}) =====")
            r=build_and_check(pg,y)
            print(json.dumps(r, indent=1))
            if r.get("verdict") and not r["verdict"]["eb"]:
                print(f"\n##### PASS with {label} #####"); pg.screenshot(path=PROBE_DIR+"/PASS_verdict.png"); break
            # close popup
            el=pg.query_selector('.popup-close, button:has-text("Close")')
            if el:
                try: el.click(); pg.wait_for_timeout(250)
                except: pass
        b.close()

if __name__=="__main__": main()
