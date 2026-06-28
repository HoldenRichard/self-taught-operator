"""GATE 1 confirmation — referee returns True on a REAL NandGame PASS and False on a fail.
Injects the referee-verified relay-NAND (captured from a live click-built solve; nodes
R1=RELAY-OFF, R2=RELAY-ON; connectorIds 0/1 only), confirms PASS, then breaks one wire to
confirm FAIL. Captures the exact success-verdict DOM."""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from referee import referee_check, dismiss_verdict_popup
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"

# The winning circuit (from probe/build_series.py PASS): NAND = AND(relay0) -> NOT(relay1).
WIN_NODES = [{"type": "RELAY-OFF", "x": 190.49, "y": 253, "id": "0"},
             {"type": "RELAY-ON",  "x": 470.49, "y": 253, "id": "1"}]
WIN_CONNS = [
    {"source": {"nodeId": "input", "connectorId": "1"}, "target": {"nodeId": "0", "connectorId": "0"}},
    {"source": {"nodeId": "input", "connectorId": "0"}, "target": {"nodeId": "0", "connectorId": "1"}},
    {"source": {"nodeId": "0", "connectorId": "0"}, "target": {"nodeId": "1", "connectorId": "0"}},
    {"source": {"nodeId": "input", "connectorId": "2"}, "target": {"nodeId": "1", "connectorId": "1"}},
    {"source": {"nodeId": "1", "connectorId": "0"}, "target": {"nodeId": "output", "connectorId": "0"}},
]

def dismiss(pg):
    try:
        el = pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass

def inject(pg, nodes, conns):
    pg.evaluate("(v)=>localStorage.setItem('%s', v)" % LS_KEY, json.dumps({"nodes": nodes, "connections": conns}))
    pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2300); dismiss(pg)

def show(label, v):
    print(f"\n--- {label} ---")
    print(f"  referee_check -> passed={v.passed}  status={v.status}")
    print(f"  raw_dialog    = {v.raw_dialog!r}")
    print(f"  failing_cases = {v.failing_cases}")
    print(f"  levels        = {v.levels_before} -> {v.levels_after}")

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900}); pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)

        # FULL reset so the active level returns to RELAY_NAND (a prior solve advances NandGame)
        pg.evaluate("()=>localStorage.clear()")
        pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss(pg)
        pg.evaluate("()=>localStorage.setItem('NandGame:Levels','[\"RELAY_NAND\"]')")

        inject(pg, WIN_NODES, WIN_CONNS)
        active = pg.evaluate("()=>{const t=document.querySelector('.test-results,.level-help,.popup-header'); return document.title} ")
        cols = pg.evaluate("()=>{const ths=document.querySelectorAll('table.test-results thead th'); return ths.length}")
        print(f"active level check: title={active!r} (RELAY_NAND has a,b,V inputs)")
        v_pass = referee_check(pg)
        show("REAL PASS (referee-verified NAND)", v_pass)
        # capture the success dialog class for the record
        succ = pg.evaluate("()=>{const d=document.querySelector('[class*=popup-dialog]'); return d?{cls:d.getAttribute('class'), txt:(d.textContent||'').trim().replace(/\\s+/g,' ').slice(0,90)}:null}")
        print("  success dialog:", json.dumps(succ))
        dismiss_verdict_popup(pg)

        # break it: drop the final wire (R2.out -> output) -> should now FAIL
        pg.evaluate("()=>localStorage.setItem('NandGame:Levels','[\"RELAY_NAND\"]')")
        inject(pg, WIN_NODES, WIN_CONNS[:-1])
        v_fail = referee_check(pg)
        show("BROKEN (final wire removed)", v_fail)

        print("\n=== GATE 1 RESULT ===")
        print(f"  referee True on real PASS : {v_pass.passed}")
        print(f"  referee False on broken   : {not v_fail.passed}")
        print(f"  -> {'BOTH CORRECT ✅' if (v_pass.passed and not v_fail.passed) else 'CHECK'}")
        b.close()

if __name__ == "__main__":
    main()
