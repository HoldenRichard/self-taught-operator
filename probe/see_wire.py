# SEE WIRE — build a single controlled relay by CLICKS, screenshot where wires attach, and
# test whether the OUTPUT responds when toggling input 'a'. Empirical truth over serialized ids.
import json
from playwright.sync_api import sync_playwright

LS_KEY="NandGame:Levels:RELAY_NAND"; PROBE_DIR="/Users/holden/HackathonSF26/probe"
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
def click(pg,x,y): pg.keyboard.press("Escape"); pg.wait_for_timeout(40); pg.mouse.click(x,y); pg.wait_for_timeout(140)
def wire(pg, sx,sy, tx,ty): pg.mouse.click(sx,sy); pg.wait_for_timeout(140); pg.mouse.click(tx,ty); pg.wait_for_timeout(180)
def read_states(pg):
    return pg.evaluate("""()=>{
      const states=Array.from(document.querySelectorAll('.state')).map(s=>(s.textContent||'').trim());
      const outNode=document.querySelector('.output-node');
      const outVal=outNode?Array.from(outNode.querySelectorAll('.state')).map(s=>s.textContent.trim()):null;
      return {all_states:states, output_node_states:outVal};
    }""")
def pts(pg):
    def cc(sel):
        return pg.evaluate("(s)=>{const e=document.querySelector(s); const c=e.querySelector('circle.connector-circle')||e; const r=c.getBoundingClientRect(); return{x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)}}", sel)
    def rtri(which):
        base="Array.from(document.querySelectorAll('.diagram-node')).filter(n=>n.querySelector('.input-connector.c')&&n.querySelector('.input-connector.in')).filter(n=>n.getBoundingClientRect().x>460)[0]"
        return pg.evaluate("()=>{const n=%s;const e=n.querySelector('.input-connector.%s').querySelector('polygon.triangle');const r=e.getBoundingClientRect();return{x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)}}" % (base,which))
    def rout():
        base="Array.from(document.querySelectorAll('.diagram-node')).filter(n=>n.querySelector('.input-connector.c')&&n.querySelector('.input-connector.in')).filter(n=>n.getBoundingClientRect().x>460)[0]"
        return pg.evaluate("()=>{const n=%s;const e=n.querySelector('.output-connector').querySelector('circle.connector-circle');const r=e.getBoundingClientRect();return{x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)}}" % base)
    return cc('.input-node .output-connector.a'), cc('.input-node .output-connector.V'), cc('.output-node .input-connector'), rtri("c"), rtri("in"), rout()

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)
        drag(pg,375,215,700,400)
        a,V,out,rc,rin,rout = pts(pg)
        print("a",a,"V",V,"out",out,"rc",rc,"rin",rin,"rout",rout)
        # build: V->relay.in, a->relay.c, relay.out->output  (click source then target)
        pg.keyboard.press("Escape"); wire(pg, V["x"],V["y"], rin["x"],rin["y"])
        pg.keyboard.press("Escape"); wire(pg, a["x"],a["y"], rc["x"],rc["y"])
        pg.keyboard.press("Escape"); wire(pg, rout["x"],rout["y"], out["x"],out["y"])
        pg.wait_for_timeout(400)
        print("CONNS:", json.dumps(pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return o.connections||[]}" % LS_KEY)))
        pg.screenshot(path=PROBE_DIR+"/see_wired.png")
        print("states (a=default):", json.dumps(read_states(pg)))
        # toggle a by clicking the input-node 'a' box body (~ below the connector)
        pg.mouse.click(582, 849); pg.wait_for_timeout(500)
        pg.screenshot(path=PROBE_DIR+"/see_a_toggled.png")
        print("states (a toggled):", json.dumps(read_states(pg)))
        b.close()

if __name__=="__main__": main()
