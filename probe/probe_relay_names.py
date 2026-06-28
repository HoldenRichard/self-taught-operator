# Discover the named connectors for a relay (for the RELAY_NAND genericity skill) + test place_component.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas

with ZoomSnapComputer() as bc:
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
    print("level set:", pg.evaluate("()=>localStorage.getItem('NandGame:Levels')"))
    clear_canvas(pg)
    r1 = bc.place_component("RELAY-OFF")
    r2 = bc.place_component("RELAY-ON")
    print("placed bases:", r1, r2)
    print("connectors:", json.dumps([ (c['name'], c['role']) for c in bc.list_connectors()['connectors'] ]))
