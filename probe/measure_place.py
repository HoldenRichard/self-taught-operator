# Measure, at zoom 1.4 on the AND level, the canvas droptarget bounds and where dropped components actually
# land (drop -> landed-center transform), so place_component can spread N gates WITHIN the canvas.
import sys, json
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level, toolbox_item, _drag, _cancel_armed
import synth

SK = "/Users/holden/HackathonSF26/operator/skills"
with ZoomSnapComputer() as bc:
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
    for skill in ("skill_RELAY_NAND.py", "skill_INV.py"):
        clear_canvas(pg); assert synth.run_skill(f"{SK}/{skill}", bc).passed
        advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()

    def canvas():
        return pg.evaluate("""()=>{const c=document.querySelector('.component-canvas')||document.querySelector('[class*=droptarget]')||document.querySelector('svg');
          const r=c.getBoundingClientRect(); return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),cls:c.getAttribute('class')};}""")
    def placed():
        return pg.evaluate("""()=>Array.from(document.querySelectorAll('.diagram-node')).filter(n=>!n.closest('.toolbox')
          &&!n.classList.contains('input-node')&&!n.classList.contains('output-node')&&n.getBoundingClientRect().x>150)
          .map(n=>{const r=n.getBoundingClientRect();return {cx:Math.round(r.x+r.width/2),left:Math.round(r.x),right:Math.round(r.x+r.width),w:Math.round(r.width)};})""")

    for Z in (1.4, 1.0):
        bc.set_zoom(Z); clear_canvas(pg)
        print(f"\n=== zoom {Z} ===  canvas droptarget: {json.dumps(canvas())}")
        nt = toolbox_item(pg, "nand")
        drops = [600, 850, 1100, 1350, 1600]
        for d in drops:
            _drag(pg, nt[0], nt[1], d, 450); _cancel_armed(pg)
        pos = placed()
        print(f"  dropped at {drops}")
        print(f"  landed ({len(pos)} placed): {json.dumps(pos)}")
