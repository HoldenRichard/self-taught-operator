"""FREEZE-MUTATE-REVERT harness (Tier-2 revert): prove the skill LIBRARY is load-bearing.

Frozen seed: reach HALFADD the same way (deterministic banked skills), compose the half-adder by RETRIEVING
skills, and run each library configuration >=3x. The ONLY thing that changes between runs is the library:
  - intact      -> compose -> referee PASS
  - DELETE skill_XOR from the library -> retrieval returns the wrong skill for the sum -> referee FAIL
  - RESTORE skill_XOR -> compose -> referee PASS (recover)
PASS<->FAIL flips ONLY with the library mutation => the banked skill is genuinely load-bearing (measurable
improvement from the library). No live endpoint needed.

Voyage is touched twice total (embed the skills once, embed the 2 fixed sub-goals once); the loop retrieves
with cached query vectors over the local store, so delete/restore is instant and rate-limit-free.
"""
import sys, os, json, math
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from nandgame_env import ZoomSnapComputer, dismiss_popup, clear_canvas, advance_to_next_level
from referee import dismiss_verdict_popup
import synth, library, compose

SK = "/Users/holden/HackathonSF26/operator/skills"
CHAIN = ["skill_RELAY_NAND.py", "skill_INV.py", "skill_AND.py", "skill_OR.py", "skill_XOR.py"]
SPEC = {"inputs": ["Input_a", "Input_b"],
        "outputs": {"Output_l": "exclusive-or (XOR) of the two inputs",
                    "Output_h": "logical AND of the two inputs"}}
DELETE = "XOR"   # the load-bearing skill we remove/restore
CYCLES = 3


def cos(a, b):
    dot = sum(x * y for x, y in zip(a, b)); na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def main():
    print("sync_local:", library.sync_local())                      # 1 Voyage call (embed all skills)
    records = {r["name"]: r for r in json.load(open(library.LOCAL_STORE))}
    subgoals = list(SPEC["outputs"].values())
    qcache = dict(zip(subgoals, library.embed(subgoals, input_type="query")))   # 1 Voyage call (queries)
    active = dict(records)                                            # mutable library (delete/restore here)

    def retrieve(subgoal, k=1):
        qv = qcache[subgoal]
        return sorted(({"name": r["name"], "score": round(cos(qv, r["embedding"]), 4), "via": "cached"}
                       for r in active.values()), key=lambda x: -x["score"])[:k]

    with ZoomSnapComputer(viewport=(2600, 1400)) as bc:
        page = bc._page; page.on("dialog", lambda d: d.accept())
        page.wait_for_timeout(2000); dismiss_popup(page)
        page.evaluate("()=>localStorage.clear()"); page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(2500); dismiss_popup(page); bc.apply_zoom()
        print("=== frozen seed: reach HALFADD via banked skills ===")
        for s in CHAIN:
            clear_canvas(page); assert synth.run_skill(f"{SK}/{s}", bc).passed, f"{s} failed"
            advance_to_next_level(page); dismiss_popup(page); bc.apply_zoom()

        log = []
        def run(label):
            dismiss_verdict_popup(page); dismiss_popup(page); clear_canvas(page); page.wait_for_timeout(300)
            verdict, plan = compose.compose(SPEC, bc, retrieve=retrieve)
            picked = {p["output"]: p["skill"] for p in plan}
            log.append((label, verdict.status, picked))
            print(f"  [{label:13s}] referee={verdict.status:4s}  sum<-{picked.get('Output_l')}  carry<-{picked.get('Output_h')}")
            return verdict.status

        print("=== warmup compose (first-after-chain settle; discarded from the tally) ===")
        run("warmup")
        print(f"=== {CYCLES} cycles: intact / delete skill_{DELETE} / restore ===")
        for i in range(CYCLES):
            print(f"--- cycle {i + 1} ---")
            run("intact")                                            # full library -> PASS
            removed = active.pop(DELETE); run(f"{DELETE}-deleted")   # DELETE skill -> FAIL
            active[DELETE] = removed; run(f"{DELETE}-restored")      # RESTORE -> PASS (recover)

        print("\n=== RAW REFEREE LOG (frozen seed — ONLY the library changed between runs) ===")
        for label, status, picked in log:
            print(f"   {label:14s} {status}   (sum<-{picked.get('Output_l')}, carry<-{picked.get('Output_h')})")
        g = lambda lab: [s for l, s, _ in log if l == lab]
        print(f"\n   intact   : {g('intact')}   (expect PASS x{CYCLES})")
        print(f"   deleted  : {g(DELETE + '-deleted')}   (expect FAIL x{CYCLES})")
        print(f"   restored : {g(DELETE + '-restored')}   (expect PASS x{CYCLES})")
        proven = (all(s == 'PASS' for s in g('intact')) and all(s == 'FAIL' for s in g(DELETE + '-deleted'))
                  and all(s == 'PASS' for s in g(DELETE + '-restored')) and len(g('intact')) >= CYCLES)
        print("\n   REVERT:", f"PROVEN — skill_{DELETE} is load-bearing: delete -> PASS becomes FAIL, restore -> recover (x{CYCLES} each)."
              if proven else "INCONCLUSIVE — inspect the log.")


if __name__ == "__main__":
    main()
