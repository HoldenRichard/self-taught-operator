# RELAY FUNCTION — read NandGame's own level/relay text, then empirically learn what the relay
# does using ONLY reachable pins (out=0, in=1): wire a->in, out->output, toggle a, read output.
import json
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
    if el: el.click(); pg.wait_for_timeout(420)
def drag(pg,x1,y1,x2,y2,s=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=s);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)
def cancel(pg):
    pg.keyboard.press("Escape"); pg.wait_for_timeout(70); pg.mouse.click(1250,260); pg.wait_for_timeout(110); pg.keyboard.press("Escape"); pg.wait_for_timeout(70)
def wire(pg, pin, term):
    before=len(conns(pg))
    for (x,y) in [pin,term]:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(40)
    pg.mouse.click(pin[0],pin[1]); pg.wait_for_timeout(150); pg.mouse.click(term[0],term[1]); pg.wait_for_timeout(170)
    return len(conns(pg))>before
def pins(pg):
    return pg.evaluate("""()=>{const n=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>x.querySelector('.input-connector.in')).filter(x=>x.getBoundingClientRect().x>460)[0];
      const tri=document.querySelector('.diagram-node .input-connector.in polygon.triangle');
      const inT=n.querySelector('.input-connector.in polygon.triangle').getBoundingClientRect();
      const outC=n.querySelector('.output-connector circle.connector-circle').getBoundingClientRect();
      return {in:[Math.round(inT.x+inT.width/2),Math.round(inT.y+inT.height/2)], out:[Math.round(outC.x+outC.width/2),Math.round(outC.y+outC.height/2)]};}""")
def output_state(pg):
    return pg.evaluate("""()=>{const o=document.querySelector('.output-node'); const st=o?Array.from(o.querySelectorAll('.state, .dec')).map(s=>s.textContent.trim()):null;
      const aNode=Array.from(document.querySelectorAll('.input-node'))[0]; const aSt=aNode?Array.from(aNode.querySelectorAll('.state,.dec')).map(s=>s.textContent.trim()):null;
      return {output:st, a:aSt};}""")
def hint(pg):
    return pg.evaluate("""()=>{const els=Array.from(document.querySelectorAll('div,p,section')).filter(d=>/your task|relay|specification|current|represents/i.test(d.textContent||'')).map(d=>(d.textContent||'').trim().replace(/\\s+/g,' ')).filter(t=>t.length>30&&t.length<700);
      // dedup by shortest containing
      const uniq=[...new Set(els)].sort((a,b)=>a.length-b.length).slice(0,4); return uniq;}""")
def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        print("=== LEVEL HINT TEXT ===");
        for h in hint(pg): print("  •", h)
        # Level Help popup
        lh=pg.query_selector('button:has-text("Level Help")')
        if lh:
            lh.click(); pg.wait_for_timeout(600)
            pop=pg.evaluate("()=>{const d=document.querySelector('[class*=popup-dialog],[class*=modal]'); return d?(d.textContent||'').trim().replace(/\\s+/g,' ').slice(0,800):null}")
            print("\n=== LEVEL HELP POPUP ===\n ", pop)
            cl=pg.query_selector('.popup-close, button:has-text("Close")')
            if cl: cl.click(); pg.wait_for_timeout(300)

        for ty,label in [(215,"RELAY-ON"),(360,"RELAY-OFF")]:
            clear(pg); drag(pg,375,ty,700,400); cancel(pg)
            pn=pins(pg)
            # a connector + a toggle box
            a_conn=pg.evaluate("()=>{const e=document.querySelector('.input-node .output-connector.a circle.connector-circle').getBoundingClientRect();return[Math.round(e.x+e.width/2),Math.round(e.y+e.height/2)]}")
            out_term=(588,190)
            w1=wire(pg, pn["in"], a_conn)       # a -> relay.in (pin-first)
            w2=wire(pg, pn["out"], out_term)     # relay.out -> output (pin-first)
            print(f"\n=== {label}: wired in<-a={w1} out->output={w2} | conns={json.dumps(conns(pg))}")
            print(f"   a=0 (default): {json.dumps(output_state(pg))}")
            # toggle a -> click the 'a' input node box body
            pg.mouse.click(582, 849); pg.wait_for_timeout(500)
            print(f"   a=toggled:     {json.dumps(output_state(pg))}")
            pg.screenshot(path=PROBE_DIR+f"/relayfn_{label}.png")
        b.close()
if __name__=="__main__": main()
