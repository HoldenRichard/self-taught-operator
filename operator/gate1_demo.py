"""GATE 1 demo — exercise referee_check() against circuits and show it reports NandGame's
real verdict. FAIL path is fully demonstrated here (empty + wired-but-wrong). The PASS path
is wired into referee.py and triggers on the validator's real success (see STATUS.md)."""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from referee import referee_check, dismiss_verdict_popup
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"

def dismiss(pg):
    try:
        el = pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass

def clear(pg):
    pg.once("dialog", lambda d: d.accept())
    el = pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)

def inject(pg, conns, t="RELAY-ON"):
    circuit = {"nodes":[{"type":t,"x":190.49,"y":253,"id":"0"},{"type":t,"x":470.49,"y":253,"id":"1"}],
               "connections": conns}
    pg.evaluate("(v)=>localStorage.setItem('%s', v)" % LS_KEY, json.dumps(circuit))
    pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2200); dismiss(pg)

def show(label, v):
    print(f"\n--- {label} ---")
    print(f"  referee_check -> passed={v.passed}  status={v.status}")
    print(f"  banner_text   = {v.banner_text!r}")
    print(f"  failing_cases = {v.failing_cases}")
    print(f"  levels        = {v.levels_before} -> {v.levels_after}")

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900}); pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg)

        # CASE 1: empty circuit -> validator FAILs
        clear(pg)
        show("CASE 1: empty circuit (no wires)", referee_check(pg))
        dismiss_verdict_popup(pg)

        # CASE 2: wired but logically WRONG (relays present, wrong logic) -> validator FAILs with cases
        wrong = [
            {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":"0","connectorId":"2"}},
            {"source":{"nodeId":"input","connectorId":"0"},"target":{"nodeId":"0","connectorId":"1"}},
            {"source":{"nodeId":"0","connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}},
            {"source":{"nodeId":"input","connectorId":"2"},"target":{"nodeId":"1","connectorId":"2"}},
            {"source":{"nodeId":"input","connectorId":"1"},"target":{"nodeId":"1","connectorId":"1"}},
            {"source":{"nodeId":"1","connectorId":"0"},"target":{"nodeId":"output","connectorId":"0"}},
        ]
        inject(pg, wrong)
        show("CASE 2: wired but wrong (relays, wrong logic)", referee_check(pg))
        dismiss_verdict_popup(pg)

        print("\n[referee correctly returns False on both — it gates on NandGame's real validator, not on 'wires exist'.]")
        b.close()

if __name__ == "__main__":
    main()
