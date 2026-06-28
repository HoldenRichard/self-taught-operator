# DEMO PATHWAY — Self-Taught Operator (read groggy in 5 min, then execute)

**Thesis:** an AI agent that teaches itself to operate NandGame and *measurably improves* by synthesizing its
own reusable, executable skills — proven by deleting one skill and watching the capability disappear.

Everything below is grounded in what's actually built (verified against the repo). Nothing aspirational is in
the pitch. **Setup:** `source computer-use-preview/.venv/bin/activate` for the browser/Atlas commands; the
dashboard is stdlib (`python3` works alone).

> ⏱️ **TIMING REALITY (decide before stage):** `demo_dryrun.py` is **~6–8 min end-to-end** (Voyage throttle →
> reach HALFADD via 5 skills → 3 composes). It does **not** fit a 3-min slot run-from-scratch. So the revert
> climax is **pre-staged**: you pre-run it as part of pre-warm (it's deterministic + endpoint-free), and on
> stage you show the **real** verdict log driving the lamp. Real verdicts always — never echo-fake a PASS/FAIL.

---

## 1. THE 3-MINUTE DEMO SCRIPT (beat by beat, lead with the artifact)

**Before you start (pre-warm, off the clock):**
- `python operator/library.py sync` (Atlas `source` field → agent)
- `python probe/demo_dryrun.py` **once** → leaves a genuine `operator/run.log` (PASS→FAIL→PASS) and proves clean
- Pane **A** open and left running: `python operator/dashboard.py --watch`  ← your live spine (lamp green, 4 agent skills)
- Pane **B** ready for the climax (and the optional cold-solve)

| time | beat | what you say / show | command |
|---|---|---|---|
| 0:00–0:15 | **Hook + artifact** | One-liner (§2). Dashboard already on screen: **5 skills banked — ALL 5 `source:agent`** (the agent solved every one itself); lamp green. | (pane A already up) |
| 0:15–0:45 | **The loop** | "The agent solved each of these gates itself, then **wrote its own code** for them. Loop: operate → referee-verify → synthesize → bank → retrieve → compose." | — |
| 0:45–1:20 | **Synthesis is real (technical core)** | Open a generated skill on disk: it didn't exist before the agent's solve; it's **synthesized from the agent's own verified trajectory, not retrieved**. Point at the integrity proof (empty git-diff → file appears at runtime; grep forbids any hand-written solver). | `cat operator/skills/skill_XOR.py` ; (proof: `python probe/gate3_proof.py`) |
| 1:20–1:50 | **Composition is generative** | "The half-adder was **never banked.** The composer retrieves XOR + AND by similarity and wires them — the library *generates*, it doesn't look up." Show the half-adder result / retrieval scores. | (artifact: `probe/compose_halfadder.py`, already run) |
| 1:50–2:45 | **CLIMAX — freeze-mutate-revert** | "Watch the referee lamp. I **delete one skill — `skill_XOR`** — and re-run. Retrieval falls back to the next-best, `OR`, builds the wrong circuit, the referee catches it: **`sum<-OR`, FAIL, lamp RED.** Restore it → **PASS, lamp GREEN.** Delete a skill and the capability *measurably* disappears — **the library IS the capability.**" | see **CLIMAX STAGING** below |
| 2:45–3:00 | **Close** | "No human wrote these solutions or this code. The agent taught itself the whole gate ladder, and we can prove the library is load-bearing. That's measurable self-improvement." | — |

**CLIMAX STAGING — pick one (both show the REAL verdicts from your pre-run; never echo-fake):**
- **FAST / RELIABLE (recommended for a 3-min slot)** — replay the actual run's verdicts on the dashboard, instant
  green→red→green, paced by you. Narrate `sum<-OR` on the DELETED frame:
  ```
  for s in INTACT DELETED RESTORED; do clear; \
    n=$(grep -n "$s.*referee=" operator/run.log | head -1 | cut -d: -f1); \
    head -n "$n" operator/run.log > /tmp/lamp.log; \
    python3 operator/dashboard.py --log /tmp/lamp.log; sleep 3; done
  ```
  (These are the genuine PASS/FAIL/PASS verdicts from the `demo_dryrun.py` you ran in pre-warm — just played back.)
- **FULLY LIVE (the two-pane, if you pre-launch)** — pane A `python operator/dashboard.py --watch` + pane B
  `python probe/demo_dryrun.py`; the lamp flips live as it runs. ⚠️ `demo_dryrun.py` is ~6–8 min, so **launch
  pane B ~5 min before** this beat so the flip lands on cue (the `--watch` lamp only animates while the log grows).

**LIVE COLD-SOLVE — endpoint-gated, optional (slot at ~0:45 *replacing* the synthesis beat, or add ~90s):**
"Here it is happening live — a gate it has no stored skill for." The agent perceives the board, reasons
`AND = NOT(NAND)`, names the wiring, referee PASS, then synthesizes + banks.
- Command: `GEMINI_MODEL=<healthy-model> GEMINI_LADDER=AND AUTO_SAFETY=proceed python operator/gate_agent.py`
  (recommended gate **AND** ≈6 actions = reliable; **INV** safest; **XOR** showstopper only if endpoint is solid).
- ✅ **Only run this if the morning health check is a clean 5/5.** **Fallback if storming:** skip it entirely —
  show the recorded agent trajectories (`operator/trajectories/{INV,AND,OR,XOR}.json`, all `source:agent`,
  verdict PASS) and narrate. The headline demo is **100% endpoint-free** (see §6).

---

## 2. ONE-LINER + 30-SEC ELEVATOR

**One-liner:** "An AI agent that teaches itself to operate a logic-circuit game — writing its own reusable,
executable skills as it goes — and we prove the skills are real by deleting one and watching its capability vanish."

**30-second:** "We built a self-taught operator. A Gemini computer-use agent solves NandGame logic gates from
perception — it decides the circuit and names the wiring; we only make the motor act land. A deterministic,
non-LLM referee verifies each solve. On a verified solve the system **synthesizes the agent's trajectory into
real Python written to disk**, cold-executes it to re-verify, and banks it to a vector library on MongoDB Atlas.
It then **composes a half-adder out of skills that were never banked together**. The proof it's genuine learning:
delete the XOR skill and the half-adder measurably breaks — wrong circuit, referee FAIL — restore it and it
recovers. Four gates, all agent-solved. The agent teaches itself, measurably."

---

## 3. Q&A DEFENSE PREP (hostile question → tight honest answer)

**"Is this synthesized or just hardcoded / retrieved?"**
Synthesized, and we built the proof to refute exactly this. `probe/gate3_proof.py`: **empty `git status` on the
skills dir, then the skill file appears at runtime** (empty-diff→fills). An **integrity grep forbids** circuit
literals and solver defs (`def build_`, `def solve_`, `RELAY-OFF`, `Input_a`, …). **Genericity:** the *same*
synthesizer fed a different trajectory emits a *different* working skill that passes on a fresh browser — so it's
not a macro. The generated code calls only the semantic API and refers to connectors **by name**, re-resolved to
pixels at runtime — not a coordinate replay. The hand-written reference solver is **quarantined in `probe/`** and
the operator runtime imports none of it (grep-clean).

**"Did the agent really solve these, or did you script it?"**
**All five** skills are `source:"agent"` in the registry (INV/RELAY_NAND/AND/OR/XOR), each from a **recorded
trajectory** (verdict PASS), captured live via decide-and-name tools — **INV + RELAY_NAND on the prize model
`gemini-3.5-flash`**, AND/OR/XOR on 2.5-computer-use. We *started* with a reference scaffold to validate the
machinery before betting on the live model (the struggle story, §4) — then swapped in genuine agent solves,
ending with **all five** agent-sourced. A model refusal or crash is logged "couldn't attempt," **never a fake
pass** (the inverter capture even pushed through 2 mid-solve 503s via retries — real).

**"How does this scale to thousands of skills?"**
The scalable parts are already the mechanism, not the count: retrieval is **vector search** (Voyage embeddings +
Atlas `$vectorSearch`), skills are **files loaded lazily by name**, and composition is **hierarchical** (a
half-adder is built from gates; a full-adder would be built from half-adders by the same retrieve-and-invoke).
**Honest:** today it's 5 skills. Future work: dedup/prune audit, a Voyager-style growing library. We're not
claiming scale — we're showing the primitive that scales.

**"Why NandGame? Isn't this NandGame-specific?"**
The **method** is referee-as-ground-truth: a deterministic, non-LLM verifier gates every bank, so nothing enters
the library unless it provably works. NandGame is a convenient referee (its own validator + localStorage oracle),
**not** the point — any domain with a checkable success signal (tests pass, build green, form submitted) fits the
same loop. **Honest:** we proved it on one referee; cross-domain generalization is future work.

**"What is the live cold-solve actually doing?"**
A real perceive→reason→act loop. Gemini computer-use gets the board **screenshot**, reasons the construction
(`AND = NOT(NAND)`), and **names** which connectors to wire via `list_connectors`/`connect_pins`. The system makes
only the *motor act* reliable — because we measured that the model's ~150–170u coordinate error can't resolve
NandGame's ~18u-apart pins at any zoom (§4). It does **not** load the skill — it solves fresh; the referee judges.

**"Which model — and what's that 2.5 vs 3.5 thing?"**
The agent ladder was captured on **`gemini-2.5-computer-use-preview-10-2025`** because `gemini-3.5-flash` was
storming (503 "high demand") the entire build. The **thesis is model-agnostic** — the loop doesn't care which
model. **Open & disclosed:** the $5k Gemini prize names *3.5 computer-use* specifically; we're verifying
eligibility and, if 3.5 is healthy this morning, re-capturing at least the inverter on 3.5 for clean framing.

---

## 4. THE STRUGGLES NARRATIVE (the honest arc — tell it as a strength)

**1) The wiring wall → semantic tools.** Naive clicking failed and we *measured why*: Gemini emits coordinates
with ~150–170u error, NandGame's `a`/`b` pins are ~18u apart, and **zoom can't spread them** (the fraction of the
frame plateaus at ~1.8% at any zoom). Rather than fake it, we gave the agent **decide-and-name** tools: it still
does all the cognition (reads the board, reasons the circuit, names the connectors), and the system only makes the
motor act land. We even **ripped out** an earlier version that inferred the agent's intent from wire-state — it
crossed the honesty line.

**2) The "8-hour outage" that was one storming model.** `gemini-3.5-flash` 503'd all day and nearly cost us the
agent-solve window. The breakthrough: it was **model-specific** — `gemini-2.5-computer-use` (the harness's native
model) was healthy the whole time. One patch (the legacy action handler now dispatches our custom tools) and the
agent path worked. The lesson we'll tell: an infra "outage" was actually a routing/model discovery.

**3) Reference scaffold → real agent solves.** We built and validated the *entire* synthesis + library +
composition pipeline with a **quarantined reference solver first** (`source:"reference"`), so the machinery was
proven before we bet on a live preview model. Then we swapped in genuine agent solves — ending with **all five
skills `source:"agent"`** (INV + RELAY_NAND re-captured on the prize model 3.5 the morning of the demo).
The scaffold never leaks into the runtime (grep-clean) — it was the test harness, not the demo.

---

## 5. JUDGING-CRITERIA MAP

- **Technicality (40):** deterministic non-LLM referee + **runtime code synthesis** (empty-diff→fills, cold-exec
  re-verified before banking) + **vector-search skill library** (Voyage + Atlas `$vectorSearch`) + **generic
  composition** (grep-clean, zero hardcoded circuits) — integrity-checked end to end. The depth lives here.
- **Live Demo (20):** the dashboard **referee lamp** + **freeze-mutate-revert green→red→green** with the
  `sum<-OR` smoking gun — reproducible and **endpoint-free**; plus an optional genuinely-live agent cold-solve.
- **Creativity (25):** "**delete a skill, watch the capability vanish**" as a *measurable* test of self-improvement;
  referee-as-ground-truth; an agent that writes its **own executable code** from its **own verified trajectory**.
- **Future Potential (15):** the loop generalizes to **any checkable domain**; hierarchical/Voyager-style library
  growth + dedup-prune is the natural next step. We show the primitive that scales, honestly scoped.

---

## 6. OPEN ITEMS FOR THE MORNING

1. **Re-poll the endpoint:** `python operator/gate2_when_ready.py` (clean **5/5** = green light; it auto-runs the
   3.5 inverter recapture on a clean poll). Last night: storming (1/5 → 0/5).
2. **If 3.5 healthy:** recapture inverter (above) and ideally the ladder
   (`GEMINI_MODEL=gemini-3.5-flash … operator/gate_agent.py`) for prize framing. **If still storming:**
   2.5-computer-use is the proven fallback — raise eligibility with a Google/sponsor organizer.
3. ✅ **DONE (AM):** agent-solved RELAY_NAND on 3.5 (`operator/relay_nand_agent.py`) → **whole library 5/5 `source:agent`**.
4. **Pre-warm (always, even if storming):** `python operator/library.py sync`; smoke
   `python probe/compose_halfadder.py` + `python probe/revert_harness.py`; pre-run `python probe/demo_dryrun.py`.

### 🛟 GRACEFUL DEGRADATION — if the endpoint is storming at demo time
**The entire headline demo is endpoint-FREE.** These all run with **no Gemini call**: the synthesis proof
(`gate3_proof.py`), library retrieval (Atlas `$vectorSearch`), composition (`compose_halfadder.py`), the
freeze-mutate-revert (`demo_dryrun.py` / `revert_harness.py`), and the dashboard. **Only** the live cold-solve
(`gate_agent.py` / `gate2_runner.py`) needs the endpoint. So if it's storming:
- **Drop the cold-solve beat**; the deterministic revert carries the climax.
- Show the **already-captured agent work** as proof the solves were real: the **five** `source:agent` trajectories
  (`operator/trajectories/*.json`), the committed 3.5 capture logs (`probe/gate2_3.5_capture.log`,
  `probe/relay_nand_3.5_capture.log`), and the ladder log (`probe/agent_gates.log`).
- **Tell the storm as the struggle story (§4)** — it's a strength, not an apology. The thesis stands entirely on
  the banked artifacts.
