"""GATE 3 PROOF — real skill synthesis, end to end, on REFERENCE trajectories (pipeline validation).

Proves, in order:
  0. INTEGRITY  — synth.py / trajectory.py contain no hardcoded solver; skills/ is cold (empty).
  1. TRAJECTORY — referee-verified solves (via the QUARANTINED probe/reference_solver scaffolding)
                  are recorded as semantic trajectories and saved to disk.
  2. EMPTY-DIFF — git shows skills/ clean, then synthesis FILLS it with skill_INV.py at runtime.
  3. COLD-EXEC  — the generated skill, imported from disk, builds the inverter from an empty canvas
                  and earns a real referee PASS. Only then is it banked.
  4. REUSE      — the banked skill runs green a second time.
  5. GENERICITY — the SAME synthesizer, fed a different trajectory (RELAY_NAND), emits a different
                  working skill that passes on a brand-new browser instance (level 1, no scaffolding).

NOTE: the skills banked here are from REFERENCE (scaffolding) trajectories — this validates the
pipeline while the agent endpoint is down. The DEMO skill is re-synthesized from Gemini's own verified
trajectory when the endpoint clears (operator/gate2_runner.py captures it); that becomes the banked skill.
"""
import sys, os, subprocess
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/probe")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
from referee import dismiss_verdict_popup
from trajectory import save_trajectory, load_trajectory
import synth
from reference_solver import solve_relay_nand_reference, solve_inverter_reference  # QUARANTINED scaffolding

ROOT = "/Users/holden/HackathonSF26"
OP = os.path.join(ROOT, "operator")
SKILLS = os.path.join(OP, "skills")


def git(*a):
    return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, text=True).stdout.rstrip()

def banner(s):
    print("\n" + "=" * 80 + "\n" + s + "\n" + "=" * 80)

def fresh_env():
    bc = ZoomSnapComputer(); bc.__enter__()
    pg = bc._page; pg.on("dialog", lambda d: d.accept())
    pg.wait_for_timeout(1500); dismiss_popup(pg)
    pg.evaluate("()=>localStorage.clear()"); pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(2500); dismiss_popup(pg); bc.apply_zoom()
    return bc

def reset_canvas(pg):
    try: dismiss_verdict_popup(pg)
    except Exception: pass
    dismiss_popup(pg); clear_canvas(pg); pg.wait_for_timeout(300)


def main():
    # ---- PHASE 0 — INTEGRITY (cold) -------------------------------------------------------
    banner("PHASE 0 — INTEGRITY (cold, before any synthesis)")
    # A hardcoded solver would have to name specific components/connectors or define a solve_* fn.
    # synth.py gets ALL circuit knowledge from the trajectory at runtime, so it contains none of these.
    forbidden = ["RELAY-OFF", "RELAY-ON", "Input_a", "Input_b", "Input_V",
                 "nand1", "relay1", "relay2", "def build_", "def solve_"]
    for f in ("synth.py", "trajectory.py"):
        txt = open(os.path.join(OP, f)).read()
        hits = [w for w in forbidden if w in txt]   # circuit literals / solver defs, anywhere in the file
        print(f"  grep {f:14s}: {'NONE - no circuit literal or solver def ✓' if not hits else 'LEAK ' + str(hits)}")
        assert not hits, f"integrity: {f} contains {hits}"
    cold = [x for x in os.listdir(SKILLS)] if os.path.isdir(SKILLS) else []
    cold = [x for x in cold if x.startswith("skill_") and x.endswith(".py")]
    print("  skill_*.py on disk         :", cold or "NONE ✓")
    print("  git status operator/skills/:", repr(git("status", "--porcelain", "operator/skills/")) or "(clean)")
    assert not cold, "expected no generated skills before the run"

    # ---- PHASE 1 — produce referee-verified trajectories (SCAFFOLDING) ---------------------
    banner("PHASE 1 — referee-verified trajectories via probe/reference_solver (SCAFFOLDING)")
    bc = fresh_env(); pg = bc._page
    bc.start_recording("RELAY_NAND", "RELAY_NAND", source="reference",
                       goal="NAND gate built from relays: outputs NOT(a AND b).")
    v = solve_relay_nand_reference(bc); print("  RELAY_NAND solve  ->", v.status)
    assert v.passed
    print("  saved trajectory  ->", save_trajectory(bc.trajectory(), v))
    advance_to_next_level(pg); dismiss_popup(pg); bc.apply_zoom()
    bc.start_recording("INV", "INV", source="reference",
                       goal="Inverter (NOT gate): outputs the logical NOT of its input (0->1, 1->0).")
    v_inv = solve_inverter_reference(bc); print("  INV solve         ->", v_inv.status)
    assert v_inv.passed
    p_inv = save_trajectory(bc.trajectory(), v_inv)
    print("  saved trajectory  ->", p_inv)

    # ---- PHASE 2 — EMPTY-DIFF -> FILLS ----------------------------------------------------
    banner("PHASE 2 — EMPTY-DIFF -> synthesis FILLS skills/ at runtime")
    print("  BEFORE  git status operator/skills/:", repr(git("status", "--porcelain", "operator/skills/")) or "(clean)")
    inv_traj = load_trajectory(p_inv)            # the PERSISTED, referee-verified trajectory (passed=True)
    inv_path = synth.synthesize(inv_traj)
    print("  synthesized:", inv_path)
    print("  AFTER   git status operator/skills/:")
    for line in git("status", "--porcelain", "operator/skills/").splitlines():
        print("     ", line)
    print("  ---- generated skill_INV.py ----")
    for ln in open(inv_path).read().splitlines():
        print("     ", ln)

    # ---- PHASE 3 — COLD-EXEC the generated skill -> referee PASS -> BANK -------------------
    banner("PHASE 3 — COLD-EXECUTE generated skill_INV on an empty canvas")
    reset_canvas(pg)
    verdict = synth.run_skill(inv_path, bc)
    print("  skill_INV executed -> referee:", verdict.status, "| passed:", verdict.passed)
    assert verdict.passed, "generated skill_INV did not pass — NOT banking"
    synth.bank(inv_traj, inv_path); print("  banked skill_INV ✓")

    # ---- PHASE 4 — REUSE -----------------------------------------------------------------
    banner("PHASE 4 — REUSE the banked skill_INV")
    reset_canvas(pg)
    v2 = synth.run_skill(inv_path, bc)
    print("  skill_INV re-run   -> referee:", v2.status, "| passed:", v2.passed)
    assert v2.passed
    bc.__exit__(None, None, None)

    # ---- PHASE 5 — GENERICITY (different trajectory, same synthesizer, fresh instance) -----
    banner("PHASE 5 — GENERICITY: synthesize skill_RELAY_NAND, run on a BRAND-NEW browser")
    import json
    rn_traj = json.load(open(os.path.join(OP, "trajectories", "RELAY_NAND.json")))
    rn_path = synth.synthesize(rn_traj)
    print("  synthesized:", rn_path, "(same synth.py, different trajectory)")
    bc2 = fresh_env(); pg2 = bc2._page
    clear_canvas(pg2); pg2.wait_for_timeout(300)
    v_rn = synth.run_skill(rn_path, bc2)
    print("  skill_RELAY_NAND executed (fresh instance) -> referee:", v_rn.status, "| passed:", v_rn.passed)
    assert v_rn.passed
    synth.bank(rn_traj, rn_path); print("  banked skill_RELAY_NAND ✓")
    bc2.__exit__(None, None, None)

    # ---- PHASE 6 — REPORT ----------------------------------------------------------------
    banner("PHASE 6 — RESULT")
    print("  registry:", os.path.join(SKILLS, "registry.json"))
    print(open(os.path.join(SKILLS, "registry.json")).read())
    print("  git status (skills/ + trajectories/ filled at runtime):")
    for line in git("status", "--porcelain", "operator/skills/", "operator/trajectories/").splitlines():
        print("     ", line)
    print("\n  GATE 3 PIPELINE PROVEN: empty-diff -> synth -> cold-exec PASS -> reuse -> 2nd skill (generic).")
    print("  Next: re-synthesize skill_INV from Gemini's OWN trajectory when the endpoint clears (the demo skill).")


if __name__ == "__main__":
    main()
