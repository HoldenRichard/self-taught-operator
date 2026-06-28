# Solve NAND programmatically (proven recipe), advance to the INVERT level, inspect what it
# requires (toolbox components, spec, connectors) so we can point Gemini at an EASY win.
import json, sys
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
from referee import referee_check, dismiss_verdict_popup
from playwright.sync_api import sync_playwright
PROBE_DIR="/Users/holden/HackathonSF26/probe"
def LS(level): return f"NandGame:Levels:{level}"
def conns(pg, level="RELAY_NAND"): return pg.evaluate("(k)=>{let o={};try{o=JSON.parse(localStorage.getItem(k)||'{}')}catch(e){};return o.connections||[]}", LS(level))
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
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
def term(pg,w):
    return pg.evaluate("(s)=>{const e=document.querySelector(s+' circle.connector-circle').getBoundingClientRect();return[Math.round(e.x+e.width/2),Math.round(e.y+e.height/2)]}", '.input-node .output-connector.'+w)
def robust_wire(pg,p,q,level="RELAY_NAND"):
    before=len(conns(pg,level))
    for fn in [lambda:(pg.mouse.click(*p),pg.wait_for_timeout(140),pg.mouse.click(*q)),
               lambda:(pg.mouse.click(*q),pg.wait_for_timeout(140),pg.mouse.click(*p)),
               lambda:drag(pg,p[0],p[1],q[0],q[1],18),lambda:drag(pg,q[0],q[1],p[0],p[1],18)]:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(40); fn(); pg.wait_for_timeout(150)
        if len(conns(pg,level))>before: return True
    return False
def solve_nand(pg):
    clear(pg)
    drag(pg,375,360,600,400); cancel(pg); drag(pg,375,215,950,400); cancel(pg)
    rs=relays(pg); R1,R2=rs[0],rs[1]
    a,bb,V,OUT=term(pg,'a'),term(pg,'b'),term(pg,'V'),(588,190)
    robust_wire(pg,R1["inp"],a); robust_wire(pg,R1["c"],bb)
    robust_wire(pg,R2["inp"],V); robust_wire(pg,R2["c"],R1["out"]); robust_wire(pg,R2["out"],OUT)
    return referee_check(pg)

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(3000); dismiss(pg)
        pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss(pg)
        v=solve_nand(pg)
        print("NAND solve:", v.status, "| levels:", v.levels_after)
        # click Next level -> INV
        nl=pg.query_selector('button:has-text("Next level")')
        if nl: nl.click(); pg.wait_for_timeout(1500)
        else: print("no Next level button; dialog:", v.raw_dialog)
        # inspect current level
        info=pg.evaluate("""()=>{
          const title=document.title;
          const spec=(document.querySelector('.level-help, .sidebar, [class*=help]')||{}).textContent||'';
          const toolbox=Array.from(document.querySelectorAll('.palette-label, .palette-nodetype')).map(e=>(e.textContent||'').trim()).filter(Boolean).slice(0,10);
          const lsKeys=Object.keys(localStorage).filter(k=>k.startsWith('NandGame:Levels'));
          const inputs=Array.from(document.querySelectorAll('.input-node .output-connector')).map(e=>(e.getAttribute('class')||'').match(/output-connector connector (\\w+)/)||[]).map(m=>m[1]).filter(Boolean);
          const truth=(document.querySelector('table, .specification, .level-help table')||{}).textContent||'';
          return {title, levelsKeys:lsKeys, levelsVal:localStorage.getItem('NandGame:Levels'), toolbox, inputs, spec:spec.replace(/\\s+/g,' ').slice(0,300)};
        }""")
        print("\nCURRENT LEVEL after Next:", json.dumps(info, indent=1))
        pg.screenshot(path=PROBE_DIR+"/inv_level.png")
        b.close()
if __name__=="__main__": main()
