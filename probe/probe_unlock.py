# Can we reach the Invert level (nand available) by setting the progression state only — NO scripted
# circuit solve? If yes, gate2_runner's setup can be honest (env config, not a hardcoded answer).
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
sys.path.insert(0, "/Users/holden/HackathonSF26/probe")
from nandgame_env import ZoomSnapComputer, dismiss_popup, advance_to_next_level, toolbox_item
from reference_solver import solve_relay_nand_reference

with ZoomSnapComputer() as bc:
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()

    # Reach INV the known-good way (scaffolding) and capture the progression state.
    solve_relay_nand_reference(bc)
    advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()
    keys = pg.evaluate("()=>Object.keys(localStorage).filter(k=>k.startsWith('NandGame'))")
    levels = pg.evaluate("()=>localStorage.getItem('NandGame:Levels')")
    cur = pg.evaluate("()=>localStorage.getItem('NandGame:CurrentLevel')")
    print("AT-INV  keys:", keys)
    print("AT-INV  NandGame:Levels =", levels, "| CurrentLevel =", cur)
    print("AT-INV  nand in toolbox:", toolbox_item(pg, "nand") is not None)

    # NOW the honest unlock test: wipe everything, set ONLY the progression list (no circuits), reload.
    pg.evaluate("(lv)=>{localStorage.clear(); localStorage.setItem('NandGame:Levels', lv);}", levels)
    pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
    nand2 = toolbox_item(pg, "nand")
    one_input = pg.evaluate("()=>document.querySelectorAll('.input-node .output-connector').length")
    has_relay = toolbox_item(pg, "RELAY-OFF") is not None
    print("UNLOCK-SET  Levels =", pg.evaluate("()=>localStorage.getItem('NandGame:Levels')"))
    print("UNLOCK-SET  nand in toolbox:", nand2 is not None, "| #input terminals:", one_input,
          "| relay still in toolbox:", has_relay)
    print("=> Invert reachable by progression-set alone:", nand2 is not None and one_input == 1)
