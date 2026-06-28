"""Capture GENUINE agent solves for the gate ladder (AND -> OR -> XOR) on a healthy Gemini computer-use
model. Same discipline as the inverter: Gemini drives via place()/list_connectors()/connect_pins()
(decide-and-name), referee PASS -> record its OWN trajectory -> synthesize -> cold-execute validate ->
bank as source:"agent", replacing the reference version. A refusal/harness error is "couldn't attempt",
never banked (ledger stays clean). Reaches each level by running the operator's OWN banked skills, then
advances level-to-level as the agent solves each (no re-running the chain).

Run: GEMINI_MODEL=gemini-2.5-computer-use-preview-10-2025 python operator/gate_agent.py
"""
import sys, os, json, shutil, tempfile
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
from agent import BrowserAgent
from referee import referee_check, dismiss_verdict_popup
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
from trajectory import save_trajectory, load_trajectory
import synth

SK = "/Users/holden/HackathonSF26/operator/skills"
TOOLS = ("You have tools: place(component) places a logic component by type ('nand','inv','and','or') and "
         "returns its name; list_connectors() lists every connector name on the board; "
         "connect_pins(source, target) wires two connectors BY NAME. You decide which connectors to wire and "
         "name them — you do not click pixels. Do NOT click toolbar buttons.")

GATES = {
    "AND": ("Logical AND of two inputs: outputs 1 only when both a and b are 1.",
            "Build an AND gate. AND(a,b) = NOT(NAND(a,b)).\n" + TOOLS + "\nSteps:\n"
            "1. place('nand')  (this computes nand(a,b))\n2. place('inv')  (this is the NOT)\n"
            "3. list_connectors() to read the names (board has Input_a, Input_b, Output plus your components' pins).\n"
            "4. connect_pins: wire Input_a and Input_b to the nand's two inputs; the nand's output to the "
            "inverter's input; the inverter's output to Output."),
    "OR": ("Logical OR of two inputs: outputs 1 when a or b (or both) is 1.",
           "Build an OR gate. OR(a,b) = NAND(NOT a, NOT b).\n" + TOOLS + "\nSteps:\n"
           "1. place('inv')  (inverts a)\n2. place('inv')  (inverts b)\n3. place('nand')\n"
           "4. list_connectors() to read the names.\n"
           "5. connect_pins: Input_a to the first inverter's input; Input_b to the second inverter's input; "
           "each inverter's output to one of the nand's two inputs; the nand's output to Output."),
    "XOR": ("Exclusive-OR (XOR) of two inputs: outputs 1 when exactly one of a, b is 1.",
            "Build an XOR gate. XOR(a,b) = AND( OR(a,b), NAND(a,b) ).\n" + TOOLS + "\nSteps:\n"
            "1. place('or')\n2. place('nand')\n3. place('and')\n4. list_connectors() to read the names.\n"
            "5. connect_pins: Input_a and Input_b to the OR's two inputs; Input_a and Input_b ALSO to the "
            "nand's two inputs; the OR's output to one of the AND's inputs; the nand's output to the AND's "
            "other input; the AND's output to Output."),
}


def bank_agent_gate(bc, page, gate, verdict):
    traj = bc.trajectory()
    print(f"=== AGENT TRAJECTORY ({gate}) ===\n{json.dumps(traj)}")
    bc.stop_recording()
    acts = (traj or {}).get("actions", [])
    if not [a for a in acts if a["op"] == "place"] or not [a for a in acts if a["op"] == "connect" and a.get("ok")]:
        print(f"  incomplete {gate} trajectory — NOT banked"); return False
    traj["passed"] = True; traj["verdict"] = verdict.status
    tmp = tempfile.mkdtemp(); tskill = synth.synthesize(traj, skills_dir=tmp)
    dismiss_verdict_popup(page); dismiss_popup(page); clear_canvas(page); page.wait_for_timeout(300)
    vv = synth.run_skill(tskill, bc)
    print(f"  VALIDATE agent skill_{gate} -> {vv.status}")
    if not vv.passed:
        print(f"  agent skill_{gate} did NOT validate — NOT banked"); return False
    final = os.path.join(SK, f"skill_{gate}.py"); shutil.copyfile(tskill, final)
    save_trajectory(traj, verdict); synth.bank(traj, final)
    print(f"  BANKED agent-sourced skill_{gate} (source: agent) ✅")
    return True


def main():
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-computer-use-preview-10-2025")
    ladder = os.environ.get("GEMINI_LADDER", "AND,OR,XOR").split(",")
    with ZoomSnapComputer(viewport=(2600, 1400), highlight_mouse=True) as bc:
        page = bc._page; page.on("dialog", lambda d: d.accept())
        page.wait_for_timeout(2000); dismiss_popup(page)
        page.evaluate("()=>localStorage.clear()"); page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(2500); dismiss_popup(page); bc.apply_zoom()
        for skill in ("skill_RELAY_NAND.py", "skill_INV.py"):   # reach AND via banked skills
            clear_canvas(page); assert synth.run_skill(f"{SK}/{skill}", bc).passed, f"setup {skill} failed"
            advance_to_next_level(page); dismiss_popup(page); bc.apply_zoom()

        for gate in ladder:
            goal, query = GATES[gate]
            print(f"\n=== AGENT SOLVE {gate}  (model={model}, level={page.evaluate(chr(39)+'()=>localStorage.getItem(\"NandGame:Levels\")'+chr(39))}) ===")
            bc.start_recording(gate, gate, source="agent", goal=goal)
            agent = BrowserAgent(browser_computer=bc, query=query, model_name=model)
            try:
                agent.agent_loop(); attempted = True
            except Exception as e:
                print(f"[agent error — couldn't attempt, NOT a failed solve]: {type(e).__name__}: {e}"); attempted = False
            verdict = referee_check(page)
            print(f"{gate} REFEREE: {verdict.status} | passed={verdict.passed} | attempted={attempted}")
            if not (attempted and verdict.passed):
                print(f"{gate} not agent-solved — stopping ladder (partial capture is fine)."); break
            if not bank_agent_gate(bc, page, gate, verdict):
                print(f"{gate} bank failed — stopping ladder."); break
            advance_to_next_level(page); dismiss_popup(page); bc.apply_zoom()

        reg = json.load(open(f"{SK}/registry.json"))
        print("\nLADDER RESULT — sources:", {k: v["source"] for k, v in reg.items()})


if __name__ == "__main__":
    main()
