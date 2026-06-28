"""GATE 1 live demo (authentic): build NandGame's relay-NAND by real clicks; show the referee
return False while a wire is missing, then True once the circuit is complete and NandGame's
validator confirms it. No injection (a correct injected circuit auto-advances the game)."""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from referee import referee_check, dismiss_verdict_popup
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"

def conns(pg): return pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return o.connections||[]}" % LS_KEY)
def dismiss(pg):
    try:
        el = pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d: d.accept()); el = pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)
def drag(pg, x1, y1, x2, y2, s=28):
    pg.mouse.move(x1, y1); pg.wait_for_timeout(60); pg.mouse.down(); pg.wait_for_timeout(90)
    pg.mouse.move(x1+4, y1+4, steps=4); pg.wait_for_timeout(30); pg.mouse.move(x2, y2, steps=s); pg.wait_for_timeout(120); pg.mouse.up(); pg.wait_for_timeout(250)
def cancel(pg):
    pg.keyboard.press("Escape"); pg.wait_for_timeout(70); pg.mouse.click(1280, 250); pg.wait_for_timeout(110); pg.keyboard.press("Escape"); pg.wait_for_timeout(70)
def relays(pg):
    return pg.evaluate("""()=>{const ns=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>x.querySelector('.input-connector.in')).filter(x=>x.getBoundingClientRect().x>460).sort((p,q)=>p.getBoundingClientRect().x-q.getBoundingClientRect().x);
      const t=(n,sel)=>{const e=n.querySelector(sel).getBoundingClientRect();return [Math.round(e.x+e.width/2),Math.round(e.y+e.height/2)];};
      return ns.map(n=>({inp:t(n,'.input-connector.in polygon.triangle'), c:t(n,'.input-connector.c polygon.triangle'), out:t(n,'.output-connector circle.connector-circle')}));}""")
def term(pg, w):
    return pg.evaluate("(s)=>{const e=document.querySelector(s+' circle.connector-circle').getBoundingClientRect();return[Math.round(e.x+e.width/2),Math.round(e.y+e.height/2)]}", '.input-node .output-connector.'+w)
def robust_wire(pg, p, q):
    before = len(conns(pg))
    for fn in [lambda:(pg.mouse.click(*p),pg.wait_for_timeout(140),pg.mouse.click(*q)),
               lambda:(pg.mouse.click(*q),pg.wait_for_timeout(140),pg.mouse.click(*p)),
               lambda:drag(pg,p[0],p[1],q[0],q[1],18),
               lambda:drag(pg,q[0],q[1],p[0],p[1],18)]:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(40); fn(); pg.wait_for_timeout(150)
        if len(conns(pg)) > before: return True
    return False

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900}); pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)
        pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss(pg)
        clear(pg)
        # build the hint solution: R1=AND(default-off), R2=NOT(default-on)
        drag(pg, 375, 360, 600, 400); cancel(pg)   # R1 default-off
        drag(pg, 375, 215, 950, 400); cancel(pg)   # R2 default-on
        rs = relays(pg); R1, R2 = rs[0], rs[1]
        a, bb, V, OUT = term(pg,'a'), term(pg,'b'), term(pg,'V'), (588,190)
        # wire 4 of 5 (omit R2.out->output)
        robust_wire(pg, R1["inp"], a); robust_wire(pg, R1["c"], bb)
        robust_wire(pg, R2["inp"], V); robust_wire(pg, R2["c"], R1["out"])
        print("INCOMPLETE (R2.out->output missing): connections =", len(conns(pg)))
        v_fail = referee_check(pg)
        print(f"  referee -> passed={v_fail.passed} status={v_fail.status} banner={v_fail.banner_text!r}")
        dismiss_verdict_popup(pg)
        # add the final wire -> complete NAND
        robust_wire(pg, R2["out"], OUT)
        print("\nCOMPLETE: connections =", len(conns(pg)))
        v_pass = referee_check(pg)
        print(f"  referee -> passed={v_pass.passed} status={v_pass.status}")
        print(f"  raw verdict: {v_pass.raw_dialog!r}")
        print(f"\n=== GATE 1: referee False-then-True on the real build ===")
        print(f"  False on incomplete : {not v_fail.passed}")
        print(f"  True  on real PASS  : {v_pass.passed}")
        print(f"  -> {'BOTH CORRECT ✅' if (not v_fail.passed and v_pass.passed) else 'CHECK'}")
        pg.screenshot(path="/Users/holden/HackathonSF26/probe/gate1_pass.png")
        b.close()

if __name__ == "__main__":
    main()
