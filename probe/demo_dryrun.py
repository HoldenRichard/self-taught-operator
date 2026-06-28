"""FULL DEMO DRY-RUN — the freeze-mutate-revert exactly as presented, with the dashboard referee lamp
tracking each step via operator/run.log (the lamp flips green->red->green live).

Narrative (ONE clean cycle, as it will be presented):
  reach HALFADD via the banked skills
  -> compose the half-adder, library INTACT          -> referee PASS   (lamp GREEN)
  -> DELETE skill_XOR from the retrievable library    -> re-compose     -> referee FAIL  (lamp RED)
  -> RESTORE skill_XOR                                 -> re-compose     -> referee PASS   (lamp GREEN)

The delete is on the in-memory retrievable library (what `retrieve` searches) — the same mutation the revert
harness proved load-bearing; the on-disk skill_XOR.py is never touched, so restore is instant + Voyage-free.

Two panes for the live demo:
  pane A:  python operator/dashboard.py --watch        (lamp tracks operator/run.log; refreshes every 2s)
  pane B:  python probe/demo_dryrun.py                  (this script; writes each verdict to run.log)
"""
import sys, os, json, math, time
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
from referee import dismiss_verdict_popup
import synth, library, compose

SK = "/Users/holden/HackathonSF26/operator/skills"
RUNLOG = "/Users/holden/HackathonSF26/operator/run.log"
CHAIN = ["skill_RELAY_NAND.py", "skill_INV.py", "skill_AND.py", "skill_OR.py", "skill_XOR.py"]
SPEC = {"inputs": ["Input_a", "Input_b"],
        "outputs": {"Output_l": "exclusive-or (XOR) of the two inputs",
                    "Output_h": "logical AND of the two inputs"}}
SETTLE = 3   # seconds to let the --watch dashboard (2s refresh) settle on each lamp state


def cos(a, b):
    dot = sum(x * y for x, y in zip(a, b)); na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def main():
    # fresh run log (only a header line -> dashboard falls back to the banked invariant = GREEN until step 1)
    open(RUNLOG, "w").write("# demo run log — referee verdicts; the dashboard lamp reads the LAST one\n")

    def LOG(line):
        with open(RUNLOG, "a") as f:
            f.write(line + "\n")
        print(line, flush=True)

    print("sync_local:", library.sync_local())                      # 1 Voyage call (embed all skills)
    records = {r["name"]: r for r in json.load(open(library.LOCAL_STORE))}
    subgoals = list(SPEC["outputs"].values())
    qcache = dict(zip(subgoals, library.embed(subgoals, input_type="query")))   # 1 Voyage call (queries)
    active = dict(records)                                            # mutable retrievable library

    def retrieve(subgoal, k=1):
        qv = qcache[subgoal]
        return sorted(({"name": r["name"], "score": round(cos(qv, r["embedding"]), 4), "via": "cached"}
                       for r in active.values()), key=lambda x: -x["score"])[:k]

    with ZoomSnapComputer(viewport=(2600, 1400)) as bc:
        page = bc._page; page.on("dialog", lambda d: d.accept())
        page.wait_for_timeout(2000); dismiss_popup(page)
        page.evaluate("()=>localStorage.clear()"); page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2500); dismiss_popup(page); bc.apply_zoom()

        print("=== reach HALFADD via banked skills ===", flush=True)
        for s in CHAIN:
            clear_canvas(page); assert synth.run_skill(f"{SK}/{s}", bc).passed, f"{s} failed to reach level"
            advance_to_next_level(page); dismiss_popup(page); bc.apply_zoom()

        def compose_step(label):
            dismiss_verdict_popup(page); dismiss_popup(page); clear_canvas(page); page.wait_for_timeout(300)
            verdict, plan = compose.compose(SPEC, bc, retrieve=retrieve)
            picked = {p["output"]: p["skill"] for p in plan}
            LOG(f"[{label}] referee={verdict.status}  sum<-{picked.get('Output_l')}  carry<-{picked.get('Output_h')}")
            time.sleep(SETTLE)
            return verdict.status

        print("=== warmup compose (absorbs first-after-chain settle; NOT part of the narrative) ===", flush=True)
        compose_step("warmup (discarded)")

        seq = []
        print("\n=== STEP 1: compose half-adder · library INTACT  (expect PASS -> lamp GREEN) ===", flush=True)
        seq.append(("intact", compose_step("compose · library INTACT")))

        print("\n=== STEP 2: DELETE skill_XOR from the retrievable library · re-compose  (expect FAIL -> lamp RED) ===", flush=True)
        removed = active.pop("XOR")
        seq.append(("XOR-deleted", compose_step("skill_XOR DELETED · re-compose")))

        print("\n=== STEP 3: RESTORE skill_XOR · re-compose  (expect PASS -> lamp GREEN) ===", flush=True)
        active["XOR"] = removed
        seq.append(("XOR-restored", compose_step("skill_XOR RESTORED · re-compose")))

        print("\n=== DEMO SEQUENCE (sum<- shows which skill retrieval picked) ===", flush=True)
        for label, status in seq:
            print(f"   {label:14s} -> referee {status}", flush=True)
        clean = [s for _, s in seq] == ["PASS", "FAIL", "PASS"]
        print("\n   DRY-RUN:", "CLEAN ✅  PASS -> FAIL -> PASS  (lamp green -> red -> green)" if clean
              else f"NOT CLEAN ❌ — got {[s for _, s in seq]}, expected ['PASS','FAIL','PASS']", flush=True)


if __name__ == "__main__":
    main()
