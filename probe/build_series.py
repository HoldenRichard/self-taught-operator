# BUILD SERIES NAND per the game's hint: R1=AND (in<-a, c<-b), R2=NOT (in<-V, c<-R1.out),
# R2.out->output. R1=default-off, R2=default-on. Robust wiring tries pin-first/reverse/drag;
# let the REFEREE judge. Also tries pin-role and type swaps if the first build fails.
import json, sys, os
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
from referee import referee_check, dismiss_verdict_popup
from playwright.sync_api import sync_playwright
LS_KEY="NandGame:Levels:RELAY_NAND"; PROBE_DIR="/Users/holden/HackathonSF26/probe"
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
    pg.keyboard.press("Escape"); pg.wait_for_timeout(70); pg.mouse.click(1280,250); pg.wait_for_timeout(110); pg.keyboard.press("Escape"); pg.wait_for_timeout(70)
def relays(pg):
    return pg.evaluate("""()=>{const ns=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>x.querySelector('.input-connector.in')).filter(x=>x.getBoundingClientRect().x>460).sort((p,q)=>p.getBoundingClientRect().x-q.getBoundingClientRect().x);
      const t=(n,sel)=>{const e=n.querySelector(sel).getBoundingClientRect();return [Math.round(e.x+e.width/2),Math.round(e.y+e.height/2)];};
      return ns.map(n=>({inp:t(n,'.input-connector.in polygon.triangle'), c:t(n,'.input-connector.c polygon.triangle'), out:t(n,'.output-connector circle.connector-circle')}));}""")
def term(pg, w):
    return pg.evaluate("(s)=>{const e=document.querySelector(s+' circle.connector-circle').getBoundingClientRect();return[Math.round(e.x+e.width/2),Math.round(e.y+e.height/2)]}", '.input-node .output-connector.'+w)
def robust_wire(pg, p, q):
    """Try many ways to connect points p and q; return True if a new connection formed."""
    before=len(conns(pg))
    attempts=[("click p,q",lambda:(pg.mouse.click(*p),pg.wait_for_timeout(140),pg.mouse.click(*q))),
              ("click q,p",lambda:(pg.mouse.click(*q),pg.wait_for_timeout(140),pg.mouse.click(*p))),
              ("drag p->q",lambda:drag(pg,p[0],p[1],q[0],q[1],18)),
              ("drag q->p",lambda:drag(pg,q[0],q[1],p[0],p[1],18))]
    for name,fn in attempts:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(40); fn(); pg.wait_for_timeout(150)
        if len(conns(pg))>before: return True
    return False
def build(pg, t1, t2, swap1, swap2):
    clear(pg)
    drag(pg,375,t1,600,400); cancel(pg)
    drag(pg,375,t2,950,400); cancel(pg)
    rs=relays(pg)
    if len(rs)<2: return None,{"err":"placement"}
    R1,R2=rs[0],rs[1]
    a=term(pg,'a'); bb=term(pg,'b'); V=term(pg,'V'); OUT=(588,190)
    # pin role assignment (swap in/c if needed)
    r1_in,r1_c = (R1["c"],R1["inp"]) if swap1 else (R1["inp"],R1["c"])
    r2_in,r2_c = (R2["c"],R2["inp"]) if swap2 else (R2["inp"],R2["c"])
    res={}
    res['a->R1.in']=robust_wire(pg, r1_in, a)
    res['b->R1.c'] =robust_wire(pg, r1_c, bb)
    res['V->R2.in']=robust_wire(pg, r2_in, V)
    res['R1.out->R2.c']=robust_wire(pg, R2.get('c') if swap2 else r2_c, R1["out"])
    res['R2.out->output']=robust_wire(pg, R2["out"], OUT)
    return res, conns(pg)
def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        # hint solution: R1=default-off(360), R2=default-on(215). Try role/type variants.
        variants=[(360,215,False,False),(360,215,True,False),(360,215,False,True),(215,360,False,False),(215,215,False,False),(360,360,False,False)]
        for (t1,t2,s1,s2) in variants:
            res,cs=build(pg,t1,t2,s1,s2)
            if res is None: print("placement failed"); continue
            v=referee_check(pg)
            tag=f"t1={'OFF' if t1==360 else 'ON'} t2={'OFF' if t2==360 else 'ON'} swap1={s1} swap2={s2}"
            print(f"[{tag}] wires={sum(1 for x in res.values() if x)}/5 referee={v.status} fails={v.failing_cases}")
            if v.passed:
                print(f"\n##### PASS ##### {tag}\n  raw={v.raw_dialog}\n  conns={json.dumps(cs)}")
                pg.screenshot(path=PROBE_DIR+"/PASS_verdict.png")
                with open(PROBE_DIR+"/winning.json","w") as f: json.dump({"tag":tag,"conns":cs},f,indent=1)
                break
            dismiss_verdict_popup(pg)
        b.close()
if __name__=="__main__": main()
