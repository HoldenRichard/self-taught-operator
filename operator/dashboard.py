"""Minimal 3-readout dashboard for the Self-Taught Operator. BARE by design (the self-taught LOOP is the
feature, not this). Reads only `operator/skills/registry.json` + each skill's recorded trajectory, plus an
OPTIONAL run log for the live referee lamp. Stdlib only; no server, no deps.

Three readouts:
  1. SKILLS BANKED  — counter, split agent vs reference (the self-taught yield).
  2. STEPS TO SUCCESS — actions per banked skill (the agent ladder: harder tasks as the library grows).
  3. REFEREE LAMP — last verdict (from the run log if present, else the banked-state invariant: all PASS).

Run:  python operator/dashboard.py            # live terminal readout
      python operator/dashboard.py --log probe/revert.log   # lamp reflects that run's last verdict
      python operator/dashboard.py --watch     # refresh every 2s (Ctrl-C to stop)
"""
import os, sys, json, re, time

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "skills")
REG = os.path.join(SKILLS, "registry.json")
DEFAULT_LOG = os.path.join(HERE, "run.log")
LADDER = ["RELAY_NAND", "INV", "AND", "OR", "XOR"]   # display order (reference baseline, then the agent ladder)

_TTY = sys.stdout.isatty()
def _c(code, s):  # color only on a real terminal
    return f"\033[{code}m{s}\033[0m" if _TTY else s
GREEN = lambda s: _c("32", s); RED = lambda s: _c("31", s); DIM = lambda s: _c("2", s)
BOLD = lambda s: _c("1", s);   CYAN = lambda s: _c("36", s); YEL = lambda s: _c("33", s)


def load():
    reg = json.load(open(REG))
    rows = []
    for name in LADDER + [k for k in reg if k not in LADDER]:
        if name not in reg:
            continue
        r = reg[name]
        steps, verdict = None, None
        tpath = os.path.join(SKILLS, "..", r.get("source_trajectory", ""))
        if r.get("source_trajectory") and os.path.exists(tpath):
            t = json.load(open(tpath))
            acts = t.get("actions", [])
            steps = sum(1 for a in acts if a.get("op") in ("place", "connect"))
            verdict = t.get("verdict")
        rows.append({"name": name, "source": r.get("source", "?"), "steps": steps, "verdict": verdict})
    return rows


def read_lamp(rows, log_path):
    """Live referee state: last STRUCTURED verdict in the run log (referee/outcome/verdict: PASS|FAIL — not
    prose), else the banked invariant (every banked skill passed the referee, so the lamp is green)."""
    if log_path and os.path.exists(log_path):
        last = None
        for line in open(log_path, errors="ignore"):
            m = re.search(r"(?:referee|outcome|verdict)\s*[=:]?\s*(PASS|FAIL)", line, re.I)
            if m:
                last = (m.group(1).upper(), line.strip())
        if last:
            return last[0], f"run log: …{last[1][-56:]}"
    verdicts = [r["verdict"] for r in rows if r["verdict"]]
    if verdicts and all(v == "PASS" for v in verdicts):
        return "PASS", f"all {len(verdicts)} banked skills verified PASS (banking requires a real referee PASS)"
    if any(v == "FAIL" for v in verdicts):
        return "FAIL", "a banked trajectory carries a FAIL verdict (should never happen)"
    return "—", "no verdict on record"


def render(rows, log_path):
    agent = [r for r in rows if r["source"] == "agent"]
    ref = [r for r in rows if r["source"] == "reference"]
    pad = lambda s, w: f"{s:<{w}}"            # pad the PLAIN string, THEN color (keeps columns aligned under ANSI)
    L = ["",
         "  " + BOLD("SELF-TAUGHT OPERATOR") + DIM("  ·  live readout  ·  registry.json + trajectories"),
         "  " + DIM("─" * 64)]

    # 1) SKILLS BANKED — split agent vs reference
    L.append("")
    L.append("  " + BOLD("SKILLS BANKED") + "   " + BOLD(str(len(rows))))
    def srcrow(label, items, color):
        names = " ".join(r["name"] for r in items)
        return (f"    {color(pad(label, 10))} {color(pad('█' * (3 * len(items)), 18))} "
                f"{len(items)}   {DIM('(' + names + ')')}")
    L.append(srcrow("agent", agent, GREEN))
    L.append(srcrow("reference", ref, YEL))

    # 2) STEPS TO SUCCESS — actions per banked skill (the ladder)
    L.append("")
    L.append("  " + BOLD("STEPS TO SUCCESS") + DIM("   actions per solve · ordered by GATE COMPLEXITY (not a time series)"))
    mx = max((r["steps"] or 0) for r in rows) or 1
    for r in rows:
        s = r["steps"]
        if s is None:
            continue
        color = GREEN if r["source"] == "agent" else YEL
        tag = "agent" if r["source"] == "agent" else " ref "
        bar = pad("█" * int(round(s * 18 / mx)), 19)
        L.append(f"    {pad(r['name'], 11)} {color(tag)}  {color(bar)} {BOLD(str(s))}")
    L.append("    " + DIM("└─ taller = a HARDER gate (INV→XOR) — scaling to harder problems, NOT rising efficiency."))
    L.append("    " + DIM("   the learning/improvement story is COMPOSITION + REVERT (the library is load-bearing), not step counts."))

    # 3) REFEREE LAMP
    state, detail = read_lamp(rows, log_path)
    lamp = GREEN("●") if state == "PASS" else (RED("●") if state == "FAIL" else DIM("○"))
    word = GREEN("PASS") if state == "PASS" else (RED("FAIL") if state == "FAIL" else DIM(state))
    L.append("")
    L.append(f"  {BOLD('REFEREE')}   {lamp} {word}   " + DIM(detail))
    L.append("")
    return "\n".join(L)


def main():
    log_path = DEFAULT_LOG
    if "--log" in sys.argv:
        log_path = sys.argv[sys.argv.index("--log") + 1]
    watch = "--watch" in sys.argv
    if watch:
        try:
            while True:
                sys.stdout.write("\033[2J\033[H")  # clear
                print(render(load(), log_path), flush=True)
                time.sleep(2)
        except KeyboardInterrupt:
            pass
    else:
        print(render(load(), log_path))


if __name__ == "__main__":
    main()
