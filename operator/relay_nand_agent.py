"""Capture a GENUINE agent solve of RELAY_NAND (level 0) so the WHOLE library is source:"agent".
No setup skills — a fresh board IS the RELAY_NAND level. The agent places two relay TYPES and wires the
NAND-from-relays construction via decide-and-name (place / list_connectors / connect_pins). On referee PASS
we reuse the proven bank_agent_gate (synth -> cold-validate -> bank source:agent; never clobbers the working
reference skill unless the agent skill itself re-validates). A refusal/transport death is "couldn't attempt".

Run: GEMINI_MODEL=gemini-3.5-flash AUTO_SAFETY=proceed python operator/relay_nand_agent.py
"""
import sys, os
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
from agent import BrowserAgent
from referee import referee_check
from nandgame_env import ZoomSnapComputer, dismiss_popup
from gate_agent import bank_agent_gate

QUERY = (
  "You are operating NandGame to build a NAND gate from two RELAYS (this is the first level).\n\n"
  "The board has input terminals named 'Input_a', 'Input_b', and a POWER terminal 'Input_V', plus an "
  "'Output' terminal. The Toolbox on the left has two relay types: 'RELAY-OFF' (default off) and "
  "'RELAY-ON' (default on).\n\n"
  "GOAL: Output = NOT(a AND b)  (a NAND gate).\n"
  "CONSTRUCTION: a NAND = an AND relay feeding a NOT/inverter relay.\n"
  "  - A 'RELAY-OFF' relay acts as the AND.\n"
  "  - A 'RELAY-ON' relay (powered from Input_V) acts as the NOT/inverter.\n\n"
  "TOOLS (you wire by NAME — you do NOT click tiny pins):\n"
  "  * place(component): place a component by type. Call place('RELAY-OFF') then place('RELAY-ON'). "
  "It RETURNS the placed name (e.g. 'relay1', 'relay2') — remember which is which.\n"
  "  * list_connectors(): returns every connector now on the board by NAME (e.g. 'Input_a', 'relay1.in', "
  "'relay1.c', 'relay1.out', ...).\n"
  "  * connect_pins(source, target): wires the two NAMED connectors.\n\n"
  "STEPS:\n"
  "1. place('RELAY-OFF')  -> this is your AND relay (remember its name, e.g. relay1).\n"
  "2. place('RELAY-ON')   -> this is your NOT relay (remember its name, e.g. relay2).\n"
  "3. Call list_connectors() to confirm the exact names.\n"
  "4. Wire it (AND relay = the RELAY-OFF you placed, NOT relay = the RELAY-ON you placed):\n"
  "   connect_pins('Input_a', '<AND relay>.in')\n"
  "   connect_pins('Input_b', '<AND relay>.c')\n"
  "   connect_pins('Input_V', '<NOT relay>.in')\n"
  "   connect_pins('<AND relay>.out', '<NOT relay>.c')\n"
  "   connect_pins('<NOT relay>.out', 'Output')\n"
  "5. When all five wires are created, you are finished.\n\n"
  "Do NOT click 'Check solution', 'Clear canvas', or any toolbar button."
)


def main():
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    with ZoomSnapComputer(highlight_mouse=True) as bc:
        page = bc._page
        page.on("dialog", lambda d: d.accept())
        page.wait_for_timeout(2000); dismiss_popup(page)
        page.evaluate("()=>localStorage.clear()"); page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2500); dismiss_popup(page); bc.apply_zoom()
        print("level set:", page.evaluate("()=>localStorage.getItem('NandGame:Levels')"))

        bc.start_recording("RELAY_NAND", "RELAY_NAND", source="agent",
                           goal="NAND gate built from relays: outputs NOT(a AND b).")
        print(f"\n=== GEMINI AGENT START (RELAY_NAND)  model={model} ===")
        agent = BrowserAgent(browser_computer=bc, query=QUERY, model_name=model)
        try:
            agent.agent_loop(); attempted = True
        except Exception as e:
            print(f"[agent error — couldn't attempt, NOT a failed solve]: {type(e).__name__}: {e}"); attempted = False
        print("=== GEMINI AGENT END ===\n")

        verdict = referee_check(page)
        print("REFEREE:", verdict.status, "| passed =", verdict.passed, "| attempted =", attempted)
        if attempted and verdict.passed:
            ok = bank_agent_gate(bc, page, "RELAY_NAND", verdict)
            print("RELAY_NAND BANK:", "source:agent ✅ — WHOLE LIBRARY now agent-sourced" if ok
                  else "did not validate — reference skill_RELAY_NAND left intact")
        elif not attempted:
            print("Outcome: COULD-NOT-ATTEMPT (error before/with loop) — NOT a failed solve; reference stays.")
        else:
            print("Outcome: agent did not produce a passing circuit — NOT banked; reference skill_RELAY_NAND stays.")


if __name__ == "__main__":
    main()
