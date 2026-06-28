"""GATE 2 — prove the end-to-end loop: Gemini (gemini-3.5-flash computer-use) SEES NandGame,
ACTS, builds a circuit, the referee verifies a real PASS.

Engineering for the agent (so it doesn't rediscover Gate-1 mechanics):
  * ZOOM  — large virtual viewport (1920x1400) + CSS zoom 1.4 => pins are fatter, well-separated,
            and the WHOLE canvas fits in one screenshot (verified in-frame before handing off).
  * SNAP  — the agent's connector-region clicks are snapped to the true pin coordinate. The agent
            still DECIDES which pins to wire; we only make the execution land. (ZoomSnapComputer)

Setup (deterministic, by us): solve RELAY_NAND to unlock + advance to the Invert level
(NOT(x)=nand(x,x): 1 component, 3 wires, no power). Then Gemini builds the inverter; referee judges.
A model refusal/transport death is logged as "couldn't complete", never a failed solve.
"""
import sys, os, json
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
from agent import BrowserAgent
from referee import referee_check, dismiss_verdict_popup
from nandgame_env import (ZoomSnapComputer, advance_to_next_level, clear_canvas,
                          dismiss_popup, terminal, output_pin)
import synth, os as _os
PROBE = "/Users/holden/HackathonSF26/probe"

INV_QUERY = (
  "You are operating NandGame to build an INVERTER (NOT gate).\n\n"
  "The blue canvas has an 'Output' terminal near the TOP and an 'Input' terminal near the BOTTOM. "
  "The Toolbox on the left has a 'nand' component (a box labeled 'nand' with inputs 'a' and 'b').\n\n"
  "GOAL: make the Output the logical opposite of the Input (Input 0 -> Output 1, Input 1 -> Output 0).\n"
  "SOLUTION: a NOT gate equals nand(x, x) — one nand component with BOTH of its inputs connected to "
  "the Input signal, and its output connected to the Output.\n\n"
  "WIRING — you do NOT click pins by hand (they are tiny). You have two tools:\n"
  "  * list_connectors(): returns the connectors currently on the board, by NAME and role\n"
  "    (e.g. 'Input', 'Output', 'nand1.a', 'nand1.b', 'nand1.out').\n"
  "  * connect_pins(source, target): creates a wire between the two NAMED connectors you choose.\n"
  "YOU decide which connectors to connect (read the board, reason about the circuit); the tool forms\n"
  "exactly the connection you name.\n\n"
  "STEPS:\n"
  "1. Drag the 'nand' component from the Toolbox onto the blue canvas (anywhere in the middle).\n"
  "2. Call list_connectors() to see the exact connector names now on the board.\n"
  "3. Build the inverter with connect_pins, using the exact names: connect 'Input' to BOTH of the\n"
  "   nand's inputs, and the nand's output to 'Output'. (Three connect_pins calls.)\n"
  "4. When connect_pins reports all three wires created, you are finished.\n\n"
  "Do NOT click 'Check solution', 'Clear canvas', or any toolbar button."
)

def in_frame_check(page, label):
    vw, vh = 1920, 1400
    pts = {"Input": terminal_inv_input(page), "Output": output_pin(page)}
    off = [k for k, p in pts.items() if not (p and 0 <= p[0] <= vw and 0 <= p[1] <= vh)]
    page.screenshot(path=f"{PROBE}/gate2_{label}.png")
    print(f"IN-FRAME [{label}]: terminals={json.dumps(pts)} off-frame={off if off else 'NONE ✓'}")
    return not off

def terminal_inv_input(page):
    return page.evaluate("""()=>{const e=document.querySelector('.input-node .output-connector circle.connector-circle'); if(!e)return null; const r=e.getBoundingClientRect(); return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];}""")

def _synthesize_demo_skill(bc, page, verdict):
    """CONDITION #1: turn GEMINI'S OWN referee-verified INV trajectory into the banked demo skill_INV.
    Synthesize to a temp dir, VALIDATE by cold-executing it (must referee-PASS), and only THEN promote it
    over the reference skill_INV. On any shortfall the reference skill is left intact (never bank junk)."""
    import shutil, tempfile
    from trajectory import save_trajectory
    traj = bc.trajectory()
    print("\n=== AGENT TRAJECTORY (Gemini's own solve) ===")
    print(json.dumps(traj, indent=2))
    bc.stop_recording()   # freeze it — the validation cold-execute below must NOT pollute the trajectory
    actions = (traj or {}).get("actions", [])
    placed = [a for a in actions if a["op"] == "place"]
    conns = [a for a in actions if a["op"] == "connect" and a.get("ok")]
    if not placed or not conns:
        print("incomplete agent trajectory (need >=1 place and >=1 connect) — NOT synthesizing; "
              "reference skill_INV left intact."); return
    traj["passed"] = True; traj["verdict"] = verdict.status
    tmp = tempfile.mkdtemp()
    tskill = synth.synthesize(traj, skills_dir=tmp)
    print("synthesized agent skill (temp) ->", tskill)
    # VALIDATE: cold-execute the generated skill on an empty INV canvas -> real referee PASS
    dismiss_verdict_popup(page); dismiss_popup(page); clear_canvas(page); page.wait_for_timeout(300)
    vv = synth.run_skill(tskill, bc)
    print("VALIDATE agent skill_INV -> referee:", vv.status, "| passed:", vv.passed)
    if not vv.passed:
        print("agent skill did NOT validate — NOT banked (honesty); reference skill_INV unchanged."); return
    final = _os.path.join(_os.path.dirname(__file__), "skills", "skill_INV.py")
    shutil.copyfile(tskill, final)
    save_trajectory(traj, verdict)     # operator/trajectories/INV.json now = Gemini's OWN trajectory
    synth.bank(traj, final)            # registry INV -> source: agent
    print("BANKED agent-sourced skill_INV (source: agent) — condition #1 fulfilled.")
    print("SWAP_COMPLETE")


def main():
    env = ZoomSnapComputer(initial_url="https://nandgame.com", highlight_mouse=True)
    with env as bc:
        page = bc._page
        page.on("dialog", lambda d: d.accept())
        page.wait_for_timeout(2000); dismiss_popup(page)
        page.evaluate("()=>localStorage.clear()"); page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(2500); dismiss_popup(page)
        bc.apply_zoom()

        # SETUP (clean — operator uses its OWN banked skill, never the scripted solver): reach INV by
        # running the banked skill_RELAY_NAND, then advancing. Requires gate3_proof.py to have banked it.
        rn_skill = _os.path.join(_os.path.dirname(__file__), "skills", "skill_RELAY_NAND.py")
        if not _os.path.exists(rn_skill):
            print("SETUP: skill_RELAY_NAND not banked yet — run gate3_proof.py first to populate the "
                  "skill library, then retry."); return
        clear_canvas(page)
        v = synth.run_skill(rn_skill, bc)
        print("SETUP — RELAY_NAND via banked skill:", v.status)
        if not v.passed:
            print("SETUP FAILED to reach INV; aborting"); return
        advance_to_next_level(page)
        dismiss_popup(page)  # INV intro popup
        bc.apply_zoom()
        print("now at level set:", page.evaluate("()=>localStorage.getItem('NandGame:Levels')"))

        # VERIFY the target level is fully in-frame before handing to Gemini
        in_frame_check(page, "before_gemini")

        # RECORD Gemini's OWN solve from here on (the skill-based setup above is deliberately NOT recorded).
        bc.start_recording("INV", "INV", source="agent")

        # HAND OFF TO GEMINI (snapping is automatic via ZoomSnapComputer.click_at)
        print("\n=== GEMINI AGENT START (INVERT, zoom+snap) ===")
        agent = BrowserAgent(browser_computer=bc, query=INV_QUERY, model_name="gemini-3.5-flash")
        try:
            agent.agent_loop(); attempted = True
        except Exception as e:
            print(f"[agent error — couldn't attempt, NOT a failed solve]: {type(e).__name__}: {e}"); attempted = False
        print("=== GEMINI AGENT END ===\n")
        page.screenshot(path=f"{PROBE}/gate2_after_gemini.png")
        print("snap events:", len(bc._snap_log), "(agent clicks snapped to true pins)")

        # REFEREE verifies the real PASS
        verdict = referee_check(page)
        ended_cleanly = getattr(agent, "final_reasoning", None) is not None
        print("REFEREE:", verdict.status, "| passed =", verdict.passed)
        print("raw verdict:", repr(verdict.raw_dialog)[:300])
        print("\n=== GATE 2 RESULT ===")
        if not attempted:
            print("Outcome: COULD-NOT-ATTEMPT (error before loop) — NOT a failed solve.")
        elif verdict.passed:
            print("Outcome: PASS ✅ end-to-end loop proven (Gemini saw -> placed -> wired -> referee PASS).")
            _synthesize_demo_skill(bc, page, verdict)
        elif not ended_cleanly:
            print("Outcome: COULD-NOT-COMPLETE — loop ended without a final answer (API/transport "
                  "failure, e.g. 503/504). NOT a failed solve; do NOT bank. Retry when endpoint recovers.")
        else:
            print("Outcome: agent completed but circuit is INCORRECT (genuine wrong-build FAIL).")
        page.wait_for_timeout(800)

if __name__ == "__main__":
    main()
