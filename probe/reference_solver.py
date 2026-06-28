"""QUARANTINED SCAFFOLDING — do NOT import from the operator runtime path.

These hand-authored reference solves exist ONLY to:
  (a) produce a referee-verified TRAJECTORY for building/proving the synthesis pipeline while the
      live agent (Gemini) endpoint is down, and
  (b) set up levels inside proof harnesses.

They are deliberately kept in probe/ and are NEVER imported by operator/synth.py, operator/trajectory.py,
or operator/gate2_runner.py (the operator's runtime task-solving loop). The operator's REAL trajectory
comes from a genuine agent solve. A judge can grep: the only hand-authored circuit solutions live here.

They solve through the env's SEMANTIC API (place_component + connect_pins by NAME), so the recorded
trajectory is identical in shape to one produced by the agent driving the same tools.
"""
import sys
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import clear_canvas


def solve_inverter_reference(bc):
    """Reference solve of the Invert level: NOT(x) = nand(x, x)."""
    clear_canvas(bc._page)
    n = bc.place_component("nand")
    bc.connect_pins("Input", f"{n}.a")
    bc.connect_pins("Input", f"{n}.b")
    bc.connect_pins(f"{n}.out", "Output")
    return bc.referee_check()


def solve_relay_nand_reference(bc):
    """Reference solve of RELAY_NAND (level 1): R1=default-off AND (in<-a, c<-b);
    R2=default-on NOT (in<-V, c<-R1.out, out->Output)."""
    clear_canvas(bc._page)
    r1 = bc.place_component("RELAY-OFF")
    r2 = bc.place_component("RELAY-ON")
    bc.connect_pins("Input_a", f"{r1}.in")
    bc.connect_pins("Input_b", f"{r1}.c")
    bc.connect_pins("Input_V", f"{r2}.in")
    bc.connect_pins(f"{r1}.out", f"{r2}.c")
    bc.connect_pins(f"{r2}.out", "Output")
    return bc.referee_check()
