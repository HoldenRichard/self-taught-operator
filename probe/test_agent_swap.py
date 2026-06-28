# Validate the GEMINI-SWAP machinery WITHOUT the model: reach INV via the operator's OWN banked
# skill_RELAY_NAND, then drive the env exactly as Gemini would (placement via bc.drag_and_drop so the
# semantic placement-detection hook fires, then connect_pins), then run gate2_runner's real synthesis
# helper. Confirms: placement recorded as TYPE-only, trajectory synthesizes, validates, banks source:agent.
import sys, json, os
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
sys.path.insert(0, "/Users/holden/HackathonSF26/probe")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level, toolbox_item
from referee import referee_check
import synth, gate2_runner

SK = "/Users/holden/HackathonSF26/operator/skills"

with ZoomSnapComputer() as bc:
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()

    # SETUP: reach INV by running the operator's OWN banked skill (never the scripted solver)
    clear_canvas(pg)
    v = synth.run_skill(os.path.join(SK, "skill_RELAY_NAND.py"), bc)
    print("SETUP skill_RELAY_NAND ->", v.status); assert v.passed
    advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()

    # SIMULATE Gemini's solve: placement via the env drag action (hook should record {place, nand}),
    # then wiring via connect_pins (Escape inside connect_pins cancels the placement's armed wire).
    bc.start_recording("INV", "INV", source="agent")
    nt = toolbox_item(pg, "nand")
    bc.drag_and_drop(nt[0], nt[1], 900, 600)
    names = [c["name"] for c in bc.list_connectors()["connectors"]]
    nand_ins = sorted([x for x in names if x.startswith("nand") and not x.endswith(".out")])
    nand_out = next(x for x in names if x.startswith("nand") and x.endswith(".out"))
    print("after drag, connectors:", names)
    bc.connect_pins("Input", nand_ins[0]); bc.connect_pins("Input", nand_ins[1]); bc.connect_pins(nand_out, "Output")
    print("RECORDED TRAJECTORY:", json.dumps(bc.trajectory()))

    verdict = referee_check(pg)
    print("GEMINI(sim) referee:", verdict.status)
    assert verdict.passed, "sim solve did not pass — fix before testing swap"

    # Run the REAL swap helper (synthesize -> validate cold -> bank source:agent)
    gate2_runner._synthesize_demo_skill(bc, pg, verdict)

    reg = json.load(open(os.path.join(SK, "registry.json")))
    print("\nREGISTRY INV source:", reg.get("INV", {}).get("source"))
    print("skill_INV.py header:", open(os.path.join(SK, "skill_INV.py")).read().splitlines()[1])
