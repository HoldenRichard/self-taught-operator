# Validate the zoom + dynamic-coord pipeline WITHOUT Gemini: solve NAND at zoom, then INV at
# zoom, via robust_wire on live-derived coordinates. Both must reach a referee PASS.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, toolbox_item, terminal, output_pin, placed_relays, conn_count, _center
from referee import referee_check, dismiss_verdict_popup

def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d:d.accept()); el=pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)
def drag(pg,x1,y1,x2,y2,s=30):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=s);pg.wait_for_timeout(140);pg.mouse.up();pg.wait_for_timeout(280)
def cancel(pg):
    pg.keyboard.press("Escape"); pg.wait_for_timeout(70); pg.mouse.click(1380,300); pg.wait_for_timeout(120); pg.keyboard.press("Escape"); pg.wait_for_timeout(70)
def rwire(pg,p,q,level):
    if not p or not q: return False
    before=conn_count(pg,level)
    for fn in [lambda:(pg.mouse.click(*p),pg.wait_for_timeout(150),pg.mouse.click(*q)),
               lambda:(pg.mouse.click(*q),pg.wait_for_timeout(150),pg.mouse.click(*p)),
               lambda:drag(pg,p[0],p[1],q[0],q[1],18),lambda:drag(pg,q[0],q[1],p[0],p[1],18)]:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(40); fn(); pg.wait_for_timeout(160)
        if conn_count(pg,level)>before: return True
    return False

def solve_nand(pg):
    clear(pg)
    on=toolbox_item(pg,"RELAY-ON"); off=toolbox_item(pg,"RELAY-OFF")
    print("  toolbox RELAY-ON:",on," RELAY-OFF:",off)
    # NOTE: CSS zoom makes NandGame place a dropped node at ~drop*zoom, so drop LOW/left to
    # land on-screen; we read actual positions afterward via placed_relays.
    drag(pg,off[0],off[1],720,480); cancel(pg)       # R1 = default-off (canvas x>650; lands on-screen)
    drag(pg,on[0],on[1],1020,480); cancel(pg)        # R2 = default-on
    import json as _j; print("  placed positions:", _j.dumps([r['box'] for r in placed_relays(pg)]))
    rs=placed_relays(pg); print("  placed relays:",len(rs))
    if len(rs)<2: return None
    R1,R2=rs[0],rs[1]
    a,b,V=terminal(pg,'a'),terminal(pg,'b'),terminal(pg,'V'); OUT=output_pin(pg)
    print("  pins a/b/V/out:",a,b,V,OUT,"| R1.in/c/out:",R1['inp'],R1['c'],R1['out'])
    res=[rwire(pg,R1['inp'],a,"RELAY_NAND"), rwire(pg,R1['c'],b,"RELAY_NAND"),
         rwire(pg,R2['inp'],V,"RELAY_NAND"), rwire(pg,R2['c'],R1['out'],"RELAY_NAND"), rwire(pg,R2['out'],OUT,"RELAY_NAND")]
    print("  wires:",res,"total conns:",conn_count(pg,"RELAY_NAND"))
    return referee_check(pg)

def main():
    with ZoomSnapComputer() as bc:
        pg=bc._page; pg.on("dialog", lambda d:d.accept())
        pg.wait_for_timeout(1500); dismiss(pg)
        pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss(pg)
        bc.apply_zoom()
        gap=pg.evaluate("""()=>{const n=document.querySelector('.diagram-node.free-node'); if(!n)return null; const c=n.querySelector('.input-connector.c').getBoundingClientRect(), i=n.querySelector('.input-connector.in').getBoundingClientRect(); return Math.round((i.x+i.width/2)-(c.x+c.width/2));}""")
        print(f"ZOOM applied. relay c-in gap = {gap}px (was 24 at 1x)")

        print("\n=== NAND at zoom ===")
        v = solve_nand(pg)
        print("NAND referee:", v.status if v else "placement-failed")
        if not (v and v.passed):
            print("!! NAND-at-zoom FAILED — stop, debug before INV");
            pg.screenshot(path="/Users/holden/HackathonSF26/probe/zoom_nand_fail.png"); return
        # click "Next level" FROM the open success popup (don't close it first)
        nl=pg.query_selector('button:has-text("Next level")')
        if nl: nl.click(); pg.wait_for_timeout(1500)
        else: print("  WARN: no Next level button")
        dismiss(pg); bc.apply_zoom()

        print("\n=== INV at zoom ===")
        clear(pg)
        nandtb=toolbox_item(pg,"nand"); print("  toolbox nand:",nandtb)
        if not nandtb:
            cand=pg.evaluate("()=>Array.from(document.querySelectorAll('.toolbox *,[class*=palette]')).map(e=>{const r=e.getBoundingClientRect();return {tag:e.tagName,cls:(e.getAttribute('class')||'').slice(0,40),txt:(e.textContent||'').trim().slice(0,18),x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width)};}).filter(e=>e.w>0&&e.x<660).slice(0,30)")
            print("  TOOLBOX candidates:", json.dumps(cand, indent=1)); return
        drag(pg,nandtb[0],nandtb[1],700,500); cancel(pg)   # drop in canvas; lands on-screen at zoom
        # nand placed: query its a/b inputs + output, and the INV single input + output terminals
        nand=pg.evaluate("""()=>{const ns=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>{const r=x.getBoundingClientRect(); return r.x>660 && r.width>0 && !x.closest('[class*=palette]') && !x.closest('.toolbox');});
          const n=ns[0]; if(!n)return null;
          const ins=Array.from(n.querySelectorAll('.input-connector')).map(c=>{const e=c.querySelector('polygon.triangle')||c; const r=e.getBoundingClientRect(); return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];});
          const oe=n.querySelector('.output-connector circle.connector-circle'); const orr=oe?oe.getBoundingClientRect():null;
          const b=n.getBoundingClientRect();
          return {ins, out: orr?[Math.round(orr.x+orr.width/2),Math.round(orr.y+orr.height/2)]:null, box:[Math.round(b.x+b.width/2),Math.round(b.y+b.height/2)]};}""")
        inp=_center(pg,'.input-node .output-connector','circle.connector-circle')
        outp=output_pin(pg)
        print("  placed nand:",json.dumps(nand)," INV input:",inp," output:",outp)
        if not nand or len(nand['ins'])<2: print("!! placed nand pins not found"); return
        # VERIFY all connectors are in-frame (Gemini can only see/click within the screenshot)
        allpts=[("INV_input",inp),("output",outp),("nand_a",nand['ins'][0]),("nand_b",nand['ins'][1]),("nand_out",nand['out'])]
        off=[name for name,p in allpts if not (p and 0<=p[0]<=1920 and 0<=p[1]<=1400)]
        pg.screenshot(path="/Users/holden/HackathonSF26/probe/zoom_inv_placed.png")
        print(f"  IN-FRAME CHECK: {len(allpts)} connectors, off-frame={off if off else 'NONE — all visible ✓'}")
        r=[rwire(pg,inp,nand['ins'][0],"INV"), rwire(pg,inp,nand['ins'][1],"INV"), rwire(pg,nand['out'],outp,"INV")]
        print("  INV wires:",r,"conns:",conn_count(pg,"INV"))
        vi=referee_check(pg)
        print("INV referee:", vi.status, "| passed:", vi.passed)
        print("raw:", repr(vi.raw_dialog)[:160])
        pg.screenshot(path="/Users/holden/HackathonSF26/probe/zoom_inv_result.png")

if __name__=="__main__": main()
