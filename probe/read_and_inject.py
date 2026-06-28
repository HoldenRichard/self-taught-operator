# READ SCHEMA + INJECT correct NAND -> capture the real PASS verdict.
# Place 2 relays (drag works), read the node schema, write the known-correct connection
# topology into localStorage, reload so NandGame rebuilds the circuit, then Check solution.
# connectorIds (learned from working wires): relay out=0,c=1,in=2 ; input a=0,b=1,V=2 ; output=0
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"
PROBE_DIR = "/Users/holden/HackathonSF26/probe"

VERDICT = r"""
() => {
  const pick=sel=>Array.from(document.querySelectorAll(sel)).map(e=>({cls:(e.getAttribute('class')||'').slice(0,80), txt:(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,220)}));
  return { dialogs:pick('[class*=popup-dialog]'),
    successish:pick('[class*=success],[class*=correct],[class*=solved],[class*=complete],[class*=congrat],[class*=passed],[class*=next]'),
    error_banner: !!document.querySelector('.error-banner'),
    all_classes_with_dialog: Array.from(document.querySelectorAll('[class*=dialog],[class*=popup]')).map(e=>e.getAttribute('class')).slice(0,10),
    levels: localStorage.getItem('NandGame:Levels'),
    body_text_snippet: (document.querySelector('[class*=popup-dialog]')||{}).textContent||null };
}
"""
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d:d.accept()); el=pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)
def drag(pg,x1,y1,x2,y2,steps=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=steps);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
        pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)
        drag(pg,375,215,660,400); drag(pg,375,215,940,400)

        raw = pg.evaluate("()=>localStorage.getItem('%s')" % LS_KEY)
        print("RAW circuit after placing 2 relays:\n", raw)
        circuit = json.loads(raw)
        nodes = circuit.get("nodes", [])
        for n in nodes:            # RELAY-ON parallel = OR; flip to RELAY-OFF for NAND
            n["type"] = "RELAY-OFF"
        print("\nNODE SCHEMA (keys of node[0]):", list(nodes[0].keys()) if nodes else "none")
        # ids of the two relays (preserve order)
        ids = [n.get("id") for n in nodes]
        print("node ids:", ids)
        if len(ids) < 2: print("!! need 2 relays"); b.close(); return
        A, B = ids[0], ids[1]
        conns = [
            {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":A,"connectorId":"2"}},  # V->A.in
            {"source":{"nodeId":"input","connectorId":"0"},"target":{"nodeId":A,"connectorId":"1"}},  # a->A.c
            {"source":{"nodeId":A,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}}, # A.out->output
            {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":B,"connectorId":"2"}},  # V->B.in
            {"source":{"nodeId":"input","connectorId":"1"},"target":{"nodeId":B,"connectorId":"1"}},  # b->B.c
            {"source":{"nodeId":B,"connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}}, # B.out->output
        ]
        circuit["connections"] = conns
        new_raw = json.dumps(circuit)
        pg.evaluate("(v)=>localStorage.setItem('%s', v)" % LS_KEY, new_raw)
        print("\ninjected correct connections; reloading...")
        pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss(pg)
        after = pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return {nodes:(o.nodes||[]).length,conns:(o.connections||[]).length}}" % LS_KEY)
        print("after reload:", json.dumps(after))
        pg.screenshot(path=PROBE_DIR+"/inject_built.png")

        el=pg.query_selector('button:has-text("Check solution")')
        if el: el.click(); pg.wait_for_timeout(1000)
        print("\n===== VERDICT (correct NAND?) =====\n"+json.dumps(pg.evaluate(VERDICT), indent=2))
        pg.screenshot(path=PROBE_DIR+"/inject_verdict.png")
        pg.wait_for_timeout(500); b.close()

if __name__=="__main__":
    main()
