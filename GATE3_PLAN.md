# GATE 3 — REAL SKILL SYNTHESIS (plan; NO code written yet)

**Thesis being proven:** the operator OBSERVES its own referee-verified success, and CODIFIES that
behavior into a *reusable, parameterized, executable* skill = real source code generated at runtime and
written to disk — then proves the generated skill works by executing it cold and getting a referee PASS.
This is the "self-taught" claim made concrete and falsifiable.

We do NOT need the live Gemini inverter for this — we already have a **referee-verified success trajectory**
from the deterministic loop (`probe/test_semantic_wire.py`: place nand → 3 `connect_pins` → referee PASS).
Gate 3 is therefore endpoint-independent.

---

## 0. Success criteria (what must be true at the end)
A skill is REAL synthesis (not a retrieved hand-authored macro) iff ALL hold:
1. **Generated at runtime** — the skill file does not exist before the run. *Proof:* clean `git diff` on
   `operator/skills/` before; the file appears after.
2. **Executable** — it can be `importlib`-loaded from disk and called.
3. **Parameterized** — it's a function with parameters that generalize the concrete trajectory (e.g. the
   inverter's input/output terminals are arguments, not hardcoded), so it composes into bigger circuits.
4. **Verified** — it is BANKED only after we EXECUTE the generated code on a fresh NandGame instance and
   the **referee** returns a real PASS. An unverified/broken synthesis is never banked (honesty).
5. **Derived from a real trajectory** — the input is an actual referee-verified solve, not a fabrication.

---

## 0b. INTEGRITY LINE (user's non-negotiables — these define "real synthesis")
1. **Derived from the trajectory ONLY — no retrieved pre-written solution.** The synthesizer (`synth.py`)
   is solution-AGNOSTIC: it serializes whatever recorded `place`/`connect` actions earned the PASS, with
   ZERO circuit-specific code. There is NO `build_inverter()` / hand-authored solver in the synthesis or
   operator-solve path.
   - **Grep proof:** `grep -rin "build_inverter\|def solve_inv\|inverter" operator/synth.py operator/trajectory.py`
     → nothing. The only inverter-build code that exists anywhere is the RUNTIME-GENERATED `skills/skill_INV.py`.
   - **Genericity proof:** the SAME synthesizer, fed a *different* verified trajectory (RELAY_NAND), emits a
     different working skill (`skill_RELAY_NAND.py`). A circuit the agent had never solved would be skilled the
     same way. This proves it cannot be an inverter-specific macro.
2. **Written to disk at runtime on referee-verified success; empty-diff → fills (provable).** `skills/` has no
   `skill_INV.py` before a cold run (git clean); after a verified solve it appears. Provable via git, below.
3. **Parameterized by NAMED connectors** (`Input`, `nand1.a`, …) — never pixel coordinates. `NAMED_CONNECTORS_JS`
   re-resolves names to coords at *execution* time, so a banked skill survives a layout shift; it is not a
   coordinate replay.

### Where the trajectory comes from (honesty about the source)
A generic recorder (`trajectory.py`) logs every `place_component`/`connect_pins` of a referee-verified solve
through the env's semantic API. It does not matter WHO solved — the synthesizer treats all sources identically:
- **Headline (true self-taught):** the AGENT (Gemini) solves the level itself (no pre-written answer); the
  Gate-2 auto-waiter captures THIS trajectory when the endpoint clears. We then skill exactly what the agent did.
- **Endpoint-independent build/proof NOW:** a deterministic reference solve yields an equivalent verified
  trajectory (identical `place`/`connect` action format) so the machinery can be built + proven without waiting
  on the storming endpoint. This reference solve is **bootstrap scaffolding in `probe/`, NOT in the operator's
  task-solving path** — the operator never calls it to "solve"; it solves via the agent or by invoking a banked
  skill. When the Gemini trajectory lands, the identical proof re-runs on it for the headline.

---

## 1. Definitions / data shapes
- **Trajectory** (`operator/trajectories/<task>_<ts>.json`): the recorded semantic actions of a verified
  solve + the verdict. Recorded via a thin wrapper around the env's semantic API:
  ```json
  {
    "task": "INV", "start_level": "INV", "verdict": "PASS",
    "actions": [
      {"op": "place",   "component": "nand", "bound": "nand1"},
      {"op": "connect", "source": "Input",     "target": "nand1.a"},
      {"op": "connect", "source": "Input",     "target": "nand1.b"},
      {"op": "connect", "source": "nand1.out", "target": "Output"}
    ]
  }
  ```
- **Skill** (`operator/skills/skill_<name>.py`): generated standalone module exposing
  `skill_<name>(env, <params>) -> Verdict` plus a `DESCRIPTOR` dict (name, description, params, signature,
  source_trajectory, verified_at). Calls only the env's stable semantic API.
- **Banked**: skill file on disk + an entry in `operator/skills/registry.json`, written ONLY after the
  validate step passes.

## 2. Env semantic API the skills target (stable contract)
The generated skill operates the game through the SAME motor acts the agent uses — nothing privileged:
- `env.place_component(type:str) -> base_name:str` — drag toolbox→canvas, cancel armed wire, return the
  newly-placed component's base name (e.g. `"nand1"`). (New thin method; built from existing
  `toolbox_item`/`_drag`/`_cancel_armed` + a `_named_connectors` before/after diff.)
- `env.connect_pins(source:str, target:str) -> dict` — EXISTS (semantic wiring, drag-verified).
- `env.referee_check() -> Verdict` — wraps `referee.referee_check(page)`.

## 3. Synthesis: trajectory → generated source (the abstraction)
A deterministic **abstraction pass** (genuine runtime codegen — the output did not exist before and is
derived from the observed trajectory, NOT hand-authored):
1. Split actions into placements `P` and connections `C`.
2. Allocate a local var per placement; map its bound name → var (`nand1` → `n0`).
3. Rewrite every connector endpoint in `C`:
   - endpoint on a placed component (`nand1.a`) → component-relative `f"{n0}.a"`.
   - endpoint NOT placed by this skill (`Input`, `Output`) → a **parameter** (deduped, ordered).
4. Emit the function source + DESCRIPTOR, write to `operator/skills/skill_<name>.py`.

**Worked output for INV** (what the synthesizer will emit, verbatim shape):
```python
# AUTO-GENERATED at runtime by operator/synth.py — DO NOT hand-edit.
# source_trajectory: trajectories/INV_<ts>.json | verified_at: <ts>
DESCRIPTOR = {
    "name": "INV", "description": "Inverter NOT(x)=nand(x,x): wire one input to both nand inputs, nand output to one output.",
    "params": ["Input", "Output"], "signature": "skill_INV(env, Input, Output)",
}
def skill_INV(env, Input, Output):
    n0 = env.place_component("nand")
    env.connect_pins(Input, f"{n0}.a")
    env.connect_pins(Input, f"{n0}.b")
    env.connect_pins(f"{n0}.out", Output)
    return env.referee_check()
```
This is parameterized (any input/output signal, so it composes — e.g. `skill_INV(env, "and1.out", "Output")`)
and not a fixed replay.

**Optional headline upgrade (model-authored), if the endpoint is healthy and time allows:** feed the
trajectory + the env API contract to an LLM and have IT write `skill_<name>` source; then run the SAME
validate step. Same artifact (generated code on disk), stronger "the AI wrote its own skill" narrative.
The deterministic pass is the reliable spine; the LLM pass is a swappable front-end. (Decision for user.)

## 4. Validate-before-bank (closed loop — this is also the live demo)
After writing `skill_<name>.py`:
1. Open a FRESH NandGame instance at `start_level` (clean state).
2. `importlib` the generated module from disk.
3. Execute `skill_<name>(env, **defaults)`.
4. `referee_check()` → must be a real PASS.
5. PASS → bank (keep file + add to `registry.json`). FAIL → discard the file, do NOT bank; (LLM path:
   regenerate up to N times, else report "synthesis failed for this trajectory" — never fake a skill).

## 5. The empty-diff → it-fills proof (`probe/gate3_proof.py`)
Requires the project to be a git repo (it is not yet — `git init` + baseline commit with an EMPTY
`operator/skills/` (a `.gitkeep`); this is pre-authorized in the brief but I'll confirm before running it).
Exact proof sequence (all logged):
0. **Integrity (grep) — COLD:** `grep -rin "build_inverter\|def solve_inv\|inverter" operator/synth.py
   operator/trajectory.py` → nothing. The synth path contains no pre-written solution.
1. `git status --porcelain operator/skills/` → **empty**; assert `skill_INV.py` absent on disk. (COLD.)
2. Run pipeline: record verified INV trajectory → synthesize → write `skill_INV.py` → validate (execute the
   generated code on a fresh instance) → referee PASS → bank.
3. `git status --porcelain operator/skills/` → now shows **`?? operator/skills/skill_INV.py`** (+ registry).
   `git diff --stat` after `git add` shows the new file "filling in."
4. `cat operator/skills/skill_INV.py` → real generated, parameterized, executable code.
5. **Independent reuse check:** in a brand-new process + fresh NandGame, `import` the banked skill and run
   it → referee PASS again. Proves it's a genuine reusable artifact, not a one-shot fluke.
6. **Genericity:** feed the SAME synthesizer the verified RELAY_NAND trajectory → it emits a *different*
   working `skill_RELAY_NAND.py` (executes cold → PASS). Same generic code, different skill ⇒ not a macro.

The diff going from empty → a working generated file, that file running green twice cold, the grep showing no
pre-written solver, and a second distinct skill from the same synthesizer — together that IS the proof.

## 6. Files Gate 3 will add (for reference; none written yet)
- `operator/trajectory.py` — recorder wrapper (logs place/connect; saves on PASS).
- `operator/synth.py` — abstraction → source emit → write → validate → bank.
- `operator/skills/` — generated skills + `registry.json` (+ `.gitkeep` for the empty baseline).
- `operator/trajectories/` — recorded verified trajectories.
- `probe/gate3_proof.py` — the empty-diff → fills → cold-reuse proof harness.
- (env) `place_component` thin method on `ZoomSnapComputer`.

## 7. Guardrails (non-negotiables preserved)
- Honesty line from Gate 2 holds: the skill operates via the same semantic motor API; no privileged state writes.
- Never bank an unverified skill; never count a failed synthesis as a success.
- No hand-authored macro masquerading as synthesis — the empty-diff proof structurally forbids it.
- Endpoint-independent: deterministic synthesis spine means the flaky Gemini endpoint cannot block Gate 3.

## 8. Open decisions for the user (before building)
- **Synthesis author:** deterministic abstraction spine (reliable, recommended) vs also wiring the
  LLM-authored upgrade now vs deterministic-only.
- **`git init` + baseline commit** to enable the empty-diff proof — confirm OK.
- **Scope of the first skill:** just `skill_INV` from the verified trajectory (recommended), or immediately
  also synthesize from the RELAY_NAND trajectory (we have that verified solve too) to bank a second skill.
