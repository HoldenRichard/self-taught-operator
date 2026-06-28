# STATUS — Self-Taught Operator (NandGame)

**Clock:** started 11:30 Sat; target noon Sun (~24.5h). **This file is the build's source of truth — keep updated.**

---

## ✅ RESOLVED (AM 2026-06-28) — MODEL / PRIZE FRAMING
**RESOLVED two ways this morning:** (1) the official hackathon guide names **"Computer Use in Gemini 3.5 Flash"**
as a qualifying feature for the $5k prize → **`gemini-3.5-flash` computer-use IS the prize model** (no separate
variant to chase); (2) we **captured a genuine inverter solve on `gemini-3.5-flash`** this AM (endpoint briefly
cleared) → referee PASS *through 2 mid-solve 503s* → **`skill_INV` re-banked `source:"agent"` on 3.5**, and then
also captured **RELAY_NAND on `gemini-3.5-flash`** → **WHOLE LIBRARY now 5/5 `source:"agent"`** (provenance:
`probe/gate2_3.5_capture.log` + `probe/relay_nand_3.5_capture.log`, committed; both show `model=gemini-3.5-flash` + referee PASS). Theme =
**Continual Learning via toolkit expansion**; sponsors Atlas + Voyage are first-place prizes too. Organizer
confirmation of the exact prize model id stays a nice-to-have. Original open-question history kept below:
- **(a) Prize eligibility — VERIFY FIRST.** The **$5k Gemini prize names "Gemini 3.5 computer-use" specifically.**
  We captured on the **2.5** computer-use model. Before leaning on the agent-ladder story *for that prize*,
  confirm with the rules / an organizer whether 2.5-computer-use solves qualify, or whether the prize framing
  must be on 3.5. (Confirm the exact prize-named 3.5 model id too — we only had `gemini-3.5-flash` wired, which
  stormed; the prize may name a distinct `gemini-3.5-computer-use` variant.)
- **(b) Clean-framing fallback.** If `gemini-3.5-flash` (or the prize-named 3.5 computer-use model) **recovers
  before the demo, re-capture at least the inverter solve on 3.5** — one genuine 3.5 solve keeps the prize
  framing clean while the rest of the ladder stays on 2.5-computer-use. Run:
  `GEMINI_MODEL=<3.5-computer-use-id> AUTO_SAFETY=proceed python operator/gate2_runner.py` (banks `skill_INV`
  source:agent from the fresh 3.5 solve, replacing the 2.5 one). Check endpoint health first (it stormed all day).
  - **RECHECK late Sat night (~2026-06-27, venue empty):** still storming — two polls 1/5 then 0/5
    (504 DEADLINE_EXCEEDED / 503 "high demand" / 499). Did NOT burn into it (per the rule). 2.5-cu ladder
    stands. Health probe: `python <scratch>/health35.py` (5× `generate_content` ping to `gemini-3.5-flash`;
    a clean **5/5** is the green light to launch the re-capture). Re-poll tomorrow AM when traffic is lower.
- **The self-taught THESIS is model-agnostic and already proven** (operate→verify→synthesize→bank→retrieve→compose,
  + revert). This flag is *purely* about which prize track the agent-solve evidence can be framed for.

---

## 🌅 MORNING CAPTURE SESSION — do FIRST, all in ONE healthy-endpoint window
**AM PROGRESS (2026-06-28):** health re-poll **6/6 clean** on 3.5 (2.5-cu also reachable, 6/6) → **inverter +
RELAY_NAND both captured on `gemini-3.5-flash` → both banked `source:agent`** ✓✓ (inverter pushed through **2
mid-solve 503s**; RELAY_NAND clean, 7-action relay solve). **WHOLE LIBRARY is now 5/5 `source:agent`** — the
clean "agent learned every skill" story, with INV + RELAY_NAND on the prize model. Remaining: live cold-solve
wiring (item 4) + the submission-critical items (repo PUBLIC, 1-min video, rehearsal). Window is FLAPPY — the
captures are banked, so we no longer depend on the endpoint for the headline.

Every item here needs a live Gemini computer-use endpoint, so batch them into a single clean window (AM = lower
traffic). Last night the endpoint was storming (1/5 then 0/5); don't burn into anything below a clean ~5/5.

1. **Re-poll endpoint health.** `python operator/gate2_when_ready.py` is the durable gate: it polls
   `gemini-3.5-flash` health and, on a clean **5/5**, auto-runs the inverter solve on 3.5 and banks it
   `source:"agent"` (so item 1 + the inverter half of item 2 are one command). For a bare health check only,
   its `health()` fn pings 5×. **Clean 5/5 = green light; below that, wait.**
2. **3.5 re-capture for the $5k prize** (the prize names *Gemini 3.5 computer-use*). Inverter: handled by
   `gate2_when_ready.py` above. Then ideally the full ladder on 3.5:
   `GEMINI_MODEL=gemini-3.5-flash AUTO_SAFETY=proceed python operator/gate_agent.py` (confirm the exact
   prize-named 3.5 computer-use model id — we only had `gemini-3.5-flash` wired). **If still storming:**
   `gemini-2.5-computer-use-preview-10-2025` is the proven fallback (the ladder already ran on it) — and
   raise eligibility (2.5-cu vs 3.5) with a Google/sponsor organizer.
3. **Agent-solve RELAY_NAND** so the WHOLE library is `source:"agent"` (clean "the agent learned *every* skill"
   story; the storm/2.5-fallback mess goes in the struggles section, not the live pitch). It's the only
   `reference` skill left (it's setup). ⚠️ Needs a small runner — extend `gate_agent.py`'s `GATES` with a
   `RELAY_NAND` entry (query: *NAND from 2 relays — RELAY-OFF=AND, RELAY-ON=NOT, wire the V power terminal*;
   `place('relay')` is supported), reach level 0 on a fresh board, same referee→synth→validate→bank flow.
   Relay construction is more complex/flaky than the logic gates — budget rehearsal time; **if it won't go
   reliably, RELAY_NAND can STAY `reference`** (it's setup, not headline — the 4 agent-sourced logic gates
   already carry the story).
4. **LIVE COLD-SOLVE as a demo beat (NOT new code — the existing proven loop, run live):** on stage the agent
   solves a gate from **perceive → place → wire → referee PASS → synthesize → bank**, watched in real time.
   **Command:** `GEMINI_MODEL=<model> GEMINI_LADDER=AND AUTO_SAFETY=proceed python operator/gate_agent.py`
   — it reaches the AND level via *other* banked skills, then the agent solves AND **fresh from perception**
   (it never loads `skill_AND`, so every run is a genuine cold solve). **Gate choice:** **AND is the sweet
   spot** — shows real reasoning (AND = NOT(NAND)) but only ~6 actions, so it's reliable live; **INV** is the
   safest fallback (4 actions) if the endpoint is flaky; **XOR** is the showstopper (~10 actions) only if the
   endpoint is rock-solid. To make "hasn't seen it" airtight, optionally `rm operator/skills/skill_AND.py`
   right before (the loop re-banks it on success). **Rehearse it cold in the morning** to learn its timing +
   failure modes. **Safety net if it flakes live:** the deterministic revert demo (`probe/demo_dryrun.py`,
   no endpoint needed) is the fallback beat — green→red→green never depends on the network.

---

## ✅ PIN-DRAG PROBE — RESOLVED. DECISION: **COMMIT NANDGAME** (tap-tap wiring + drag placement)

The load-bearing risk (Gemini computer-use drag reliability on small pin targets) is **resolved**, and better than hoped: **NandGame wiring does not need drag at all** — it natively supports **click-to-wire** ("Tap or drag the triangle"). Clicks are far more reliable than drags.

### Measured reliability (vs NandGame's own localStorage oracle)
| Mechanic | Method | Result |
|---|---|---|
| Component placement | drag toolbox → canvas (interpolated `mouse.move(steps=N)`) | **6/6 = 100%** (big target) |
| Wiring | **tap-tap**: click source connector → click target connector | **11/12 = 92%** with random ±3px jitter |
| Wiring (raw single-jump drag — the harness default) | `move→down→move→up` | **0%** (never the right path; click-to-wire supersedes it) |

The single wiring miss was target y=187 (3px high → dead zone just above the connector). Centering the target at the true hit-point + **verify-and-retry** (the oracle reports success/failure instantly) → **effectively ~100%**.

**Recommendation: NandGame is GO.** No TodoMVC fallback needed. Full narrative shine + reliable mechanics + deterministic machine-readable referee.

---

## LOCKED interaction model (NandGame, level RELAY_NAND = first level)

NandGame is a **React app, 100% SVG/DOM (zero canvas)** → fully introspectable. Viewport 1440×900.

- **Place a component:** drag a toolbox node (`.palette-nodetype` / `.relay-box`, e.g. "relay (default on)" at ~(375,215)) → drop on the blue canvas (`.component-canvas.node-droptarget`, any empty point). Uses low-level mouse drag with interpolated moves (`page.mouse.move(x,y,steps=~28)`). Drop target is huge → 100%.
- **Wire two pins (TAP-TAP):** `mouse.click(source_connector)` then `mouse.click(target_connector)`. A connection is created from source→target.
  - Connectors are `.input-connector` / `.output-connector` DIVs, each with an SVG `polygon.triangle` handle.
  - ⚠️ **The clickable hit-point is the triangle handle, ~6px below the connector DIV's bbox center.** Bbox center (e.g. 588,183) MISSES; true point ~ (588,190). Build the connect primitive to click the `polygon.triangle` center (or connector-circle center + offset), then **verify via oracle and retry** on miss.
- **Reset:** "Clear canvas" button (fires a `confirm()` → auto-accept the dialog).
- **Validate:** "Check solution" button → runs NandGame's validator.

### THE REFEREE (machine-readable, non-LLM, deterministic)
1. **Circuit topology — localStorage**, key `NandGame:Levels:<LEVEL>` (e.g. `NandGame:Levels:RELAY_NAND`):
   `{"nodes":[...], "connections":[{"source":{"nodeId","connectorId"}, "target":{"nodeId","connectorId"}}, ...]}`
   - Fixed nodeIds: `"input"` (the a/b/V terminals), `"output"` (the output terminal). Placed nodes get generated ids. connectorId = `"0"`,`"1"`,…
   - Updates **live** on every place/wire. This is the per-action success oracle.
2. **Solve verdict — DOM after "Check solution":**
   - FAIL: `.error-banner` / `.popup-dialog.error-dialog` with text **"Level is not correct."**, plus `.test-results` rows with class `.error` (bg `rgb(255,182,193)`) marking failing input combos (`✗`) + expected output.
   - PASS: success dialog (no `.error-*`); level advances (`NandGame:Levels` list grows). **TODO: capture exact success class on first real solve — step 1 of build.**
   - `localStorage["NandGame:Levels"]` = list of started/cleared levels; `Nandgame:UserId` assigned on first check.

---

## Environment / harness (verified)
- Harness: `./computer-use-preview` (venv `.venv`, Python 3.14.6, key wired). Run: `source .venv/bin/activate; python main.py --query "..." --env playwright --highlight_mouse`. Default model `gemini-3.5-flash`.
- **Patched** `agent.py` `_get_safety_confirmation`: was `input()` (EOFErrors on unattended runs). Now honors `AUTO_SAFETY=proceed|deny`, else prompts, else (non-TTY) auto-proceeds + logs. Set `AUTO_SAFETY=proceed` for hands-off loops.
- torch 2.12.1 (MPS=True) + numpy for Tier-3. MongoDB Atlas M10 ready (conn string → gitignored `.env`, URL-encode `$`→`%24`, `pip install "pymongo[srv]"`). Voyage embeddings (key pending).

## Probe artifacts (read-only, in `./probe/`)
`recon_nandgame.py` (SVG/canvas), `recon_connectors.py` (connector coords + localStorage), `event_probe.py` (event model: custom pointer, no native DnD), `watch_wire.py` (elementFromPoint maps, mid-drag), `find_and_wire.py` (**discovered tap-tap works**), `reliability.py` (the rates above), `check_solution_probe.py` (referee DOM verdict). Screenshots alongside.

---

## ✅ GATE 1 — REFEREE READER: COMPLETE (referee True on real PASS, False on fail)
- **`operator/referee.py`** — `referee_check(page) -> Verdict`. Clicks NandGame's "Check solution",
  reads the DOM verdict, returns `passed=True` ONLY on the validator's real PASS. No LLM in the path.
  - FAIL signal: `.error-banner` "Level is not correct." + `.error-dialog` + `.test-results tr.error`.
  - PASS signal: **"Level successfully completed!"** dialog (non-error), all test rows ✔, and
    `NandGame:Levels` advances to the next level.
- **`operator/gate1_demo.py`** — empty → False; 6-wire-but-wrong → False (gates on validator, not "wires exist").
- **`operator/gate1_live_demo.py`** — the canonical proof: builds relay-NAND by REAL clicks; with one
  wire missing → referee **False** ("Level is not correct."); complete → referee **True**
  ("Level successfully completed! ... 2 components used. This is the simplest possible solution!"). ✅✅
- Captured PASS verdict / winning circuit: `probe/winning.json`, screenshot `probe/gate1_pass.png`.

### Relay model (CORRECTED — the "control pin / connectorId 2" was a phantom; only 0 and 1 exist)
- Each relay exposes **connectorId 0 and connectorId 1** only. The two bottom pins + top output map to
  these; there is NO id 2. Clicking the triangle handles + `robust_wire` (try click-orders AND drags,
  verify via the localStorage oracle, retry) reliably wires every pin. This is the reusable wire primitive.
- **relay-NAND solution** (from the game's own Hint #1 = AND then NOT, "simplest 2-component solution"):
  - R1 = `RELAY-OFF` (AND): `in←a`, `c←b`
  - R2 = `RELAY-ON` (NOT/invert): `in←V`, `c←R1.out`, `R2.out→output`
  - Verified-correct connections (connectorIds 0/1 only) in `probe/winning.json`.
- Build mechanic to reuse in Gate 2: place via drag (toolbox→canvas), wire via `robust_wire` on the
  triangle-handle coords, after each placement `cancel()` the armed-wire carryover (Esc + click empty).

## GATE 2 — end-to-end loop: ENGINEERING VALIDATED (deterministic referee PASS); live Gemini pass endpoint-gated
**The loop is proven and the honesty line holds: the agent's perception + reasoning + decisions drive it;
the system only makes the motor act reliable. The ONLY thing left for Gate 2 is the live Gemini run, and it
is blocked solely by the gemini-3.5-flash endpoint storming (503/504 "high demand"). A background auto-waiter
captures it when the endpoint clears — do NOT freeze the build on it.**

### What the loop is
`operator/gate2_runner.py` — opens the harness browser, deterministically solves RELAY_NAND to unlock +
advance to the **Invert** level (easy win: `NOT(x)=nand(x,x)`, 1 nand, 3 wires, no power source needed),
verifies the level is fully in-frame, then hands off to **Gemini** (gemini-3.5-flash) to build the inverter.
The **referee** (`operator/referee.py`, Gate 1) judges the real PASS. A model refusal / transport death is
logged "couldn't complete", NEVER a failed solve (non-negotiable #3). Attempt-1 (pre-semantic) already
confirmed Gemini places the nand fine via drag; only the wiring precision was the blocker.

### The pin-precision boundary (why naive clicking can't work) — MEASURED, settled, do not re-litigate
Gemini emits 0–1000 normalized coords with ~150–170u error on NandGame's tiny clustered pins. The nand
`a`/`b` pins are only ~18 normalized units apart, and **zoom cannot spread them**: measured pin gap as a
fraction of the screenshot frame plateaus at ~1.8% at ANY zoom (uniform zoom scales the whole in-frame
level together; once content fills the viewport the fraction caps):
| zoom | pin gap px | frac of frame | norm units |
|---|---|---|---|
| 1.0 | 24 | 0.71% | 7u |
| 1.4 | 34 | 1.00% | 10u |
| 2.0 | 48 | 1.41% | 14u |
| 2.8 | 67 | 1.81% | 18u |
| 3.5 | 84 | 1.82% | 18u |
~18u (max) ≪ ~170u error → an honest nearest-pin snap CANNOT resolve `a` vs `b`. Raw-click wiring is a dead
end on NandGame's clustered pins. This is a real capability boundary of the preview model, not an engineering gap.

### RESOLUTION — SEMANTIC WIRING (the agent names connectors; the system lands the motor act)
Implemented in `operator/nandgame_env.py` (class `ZoomSnapComputer`, constant `NAMED_CONNECTORS_JS`) +
harness registration. Two custom agent tools are declared to Gemini and dispatched to the computer:
- **`list_connectors()`** → the connectors currently on the board, by NAME + role (e.g. `Input`, `Output`,
  `nand1.a`, `nand1.b`, `nand1.out`). Built by `NAMED_CONNECTORS_JS`: input-role → triangle-handle coord,
  output-role → circle coord; placed components auto-named `<type><idx>.<pinlabel>` (sorted left→right).
- **`connect_pins(source, target)`** → forms EXACTLY that named connection via `_form_connection`
  (Esc + click-both-orders + **drag-both-orders**, verified by the localStorage oracle `_total_conns`),
  returns a success dict. The DRAG is essential — clicking the clustered pins snaps to the wrong connector;
  the drag gesture lands the right one. (Earlier click-only version built a feedback cycle → "unstable".)
- Registered: `agent.py` `__init__` adds `browser_computer.agent_tool_callables()` declarations via
  `FunctionDeclaration.from_callable`; `handle_action` else-branch dispatches the call to the bound method.
  The harness wraps a dict return as the function response, so the agent sees the success/availability info.

**Honesty line (HELD — this is the user's hard rule):** the agent does ALL cognition — reads the board,
reasons the circuit (`NOT(x)=nand(x,x)`), decides + NAMES which connectors to wire and in what order, and
referee-verifies + iterates. The system makes ONLY the motor act reliable. It does NOT infer which pin the
agent "meant" from wire-state. (An earlier wire-state-inference snap was RIPPED OUT for crossing this line.)
The honest 18px nearest-connector snap (`SNAP_RADIUS`, `_snap`) remains only for raw clicks (e.g. placement).

### Validated deterministically (no Gemini needed) — THIS is the Gate-3 input
`probe/test_semantic_wire.py` — solve NAND → advance INV → drop a nand → `list_connectors()` returns the 5
names → `connect_pins("Input","nand1.a")`, `("Input","nand1.b")`, `("nand1.out","Output")` → **referee
PASS**: "Level successfully completed! ... 1 nand gate. This is optimal!". This run IS a referee-verified
success trajectory (placement + 3 named connections + PASS verdict) — the raw material Gate-3 synthesis turns into a skill.

### Harness patches (all applied; needed for the agent path)
`computer-use-preview/agent.py`: (1) `drag_and_drop` accepts `start_x/start_y/end_x/end_y` OR
`x/destination_x` (gemini-3.5-flash uses the former) — BOTH handlers; (2) genai client
`http_options=HttpOptions(timeout=90000)`; (3) `get_model_response` retries 5→9, capped backoff
`min(base*2^a, 8)`; (4) custom-tool registration + dispatch (above).
`computer-use-preview/computers/playwright/playwright.py`: initial `goto` uses
`wait_until="domcontentloaded", timeout=60000` (nandgame.com sometimes hangs the full `load` event).

### HOW TO RUN / RESUME the live Gemini pass (the only thing left for Gate 2)
- Endpoint health is the gate. Auto-wait + run:
  `source .venv/bin/activate && AUTO_SAFETY=proceed python -u operator/gate2_when_ready.py`
  (polls health 5×; runs `gate2_runner.main()` on a clean 5/5; time-boxed ~25 min; log `probe/gate2_run4.log`).
  Direct (if endpoint already healthy): `... python -u operator/gate2_runner.py`.
- Success = `Outcome: PASS ✅` + referee "Level successfully completed!". Gemini's expected action sequence:
  `drag_and_drop` (place nand) → `list_connectors` → 3× `connect_pins` → done; then the referee checks.
- If the loop ends without a final answer (503/504) → `COULD-NOT-COMPLETE`, NOT a fail; rerun when calm.

## ✅ GATE 3 — REAL SKILL SYNTHESIS: PIPELINE PROVEN (reference trajectories; agent-derived demo pending endpoint)
The operator records a referee-verified solve as a semantic TRAJECTORY and SYNTHESIZES it into a reusable,
parameterized, EXECUTABLE skill (generated Python written to disk at runtime), then validates the generated
code by executing it and requiring a real referee PASS before banking. Proven end-to-end by
`probe/gate3_proof.py` (endpoint-independent — no Gemini needed):
  0. **INTEGRITY** — `operator/synth.py` + `operator/trajectory.py` contain no circuit literals / solver
     defs (grep-clean); `operator/skills/` cold (only `.gitkeep`); `git status operator/skills/` empty.
  1. **TRAJECTORY** — referee-verified RELAY_NAND + INV solves (via QUARANTINED `probe/reference_solver.py`)
     recorded as semantic trajectories → `operator/trajectories/<task>.json`.
  2. **EMPTY-DIFF → FILLS** — `git status operator/skills/` empty, then `synth.synthesize()` writes
     `operator/skills/skill_INV.py` at runtime (`?? operator/skills/skill_INV.py`).
  3. **COLD-EXEC** — the generated skill, imported from disk, builds the inverter on an empty canvas →
     real referee PASS → only THEN banked.
  4. **REUSE** — banked skill re-run → PASS.
  5. **GENERICITY** — the SAME synthesizer fed the RELAY_NAND trajectory emits a different working skill
     that PASSES on a BRAND-NEW browser instance. Different skill, same generic synth ⇒ not a macro.
- **Machinery (operator runtime):** `operator/trajectory.py` (record + save-on-PASS), `operator/synth.py`
  (`_abstract`→`render`→`synthesize`→`run_skill`→`bank`; solution-AGNOSTIC), env additions
  `place_component()` / `referee_check()` / `start_recording()` (instrumentation, holds no solution). The
  generated skill calls ONLY the env semantic API and refers to connectors by NAME (re-resolved to pixels
  at run time via `NAMED_CONNECTORS_JS` ⇒ survives a layout shift; not a coordinate replay).
- **Generated skill_INV.py (verbatim shape):** `def skill_INV(env, Input, Output): n0 = env.place_component("nand");
  env.connect_pins(Input, f"{n0}.a"); env.connect_pins(Input, f"{n0}.b"); env.connect_pins(f"{n0}.out", Output);
  return env.referee_check()`.
- **Honesty / integrity (HELD):** hand-authored solves are QUARANTINED in `probe/reference_solver.py`; the
  operator runtime (`gate2_runner`/`synth`/`trajectory`/`nandgame_env`) imports NONE of them (grep-clean).
  The two skills banked by this run are `source: "reference"` (pipeline validation only).
- **✅ AGENT SWAP — DONE: `skill_INV` is `source:"agent"` (FIRST genuine agent solve, captured live).**
  `gate2_runner` records Gemini's OWN INV solve (placement captured as component TYPE via a drag hook — never
  pixels) and, on referee PASS, synthesizes → cold-execute validates → banks `skill_INV` as `source:"agent"`,
  replacing the reference one (synth to a temp dir + validate first, so a bad recording never clobbers the
  working skill). Setup reaches INV by running the operator's OWN banked `skill_RELAY_NAND` (never the scripted
  solver). Live trace: Gemini saw the board → placed the nand → `list_connectors()` → `connect_pins("Input",
  "nand1.a")`, `("Input","nand1.b")`, `("nand1.out","Output")` → referee PASS → banked. Trajectory in
  `operator/trajectories/INV.json` (`source:agent`).
- **THE GEMINI STORM WAS MODEL-SPECIFIC** (key finding): only `gemini-3.5-flash` (+ `gemini-flash-latest`,
  which routes to it) 503'd the entire session. Healthy: `gemini-2.5-computer-use-preview-10-2025` (the
  harness's NATIVE computer-use model — a bare ping returns 400 "wrong format", i.e. reachable),
  `gemini-3-flash-preview`, `gemini-3.1-flash-lite`, `gemini-2.5-flash`, `gemini-2.5-pro`. `gate2_runner`'s
  model is now configurable: `GEMINI_MODEL=gemini-2.5-computer-use-preview-10-2025 python operator/gate2_runner.py`
  (default still 3.5-flash). HARNESS PATCH (vendored/gitignored `agent.py`): the LEGACY action handler now
  also dispatches the browser-computer custom tools — `gemini-2.5-computer-use` uses the legacy path, so
  without this `list_connectors`/`connect_pins` raised "Unsupported function".
- **✅ AGENT LADDER DONE — INV/AND/OR/XOR ALL `source:"agent"`** (RELAY_NAND stays reference = setup). Captured
  live on `gemini-2.5-computer-use-preview-10-2025` in one ladder run (`probe/agent_gates.log`): each gate
  referee-PASS → cold-execute validated → banked. Agent trajectories: INV 1 place/3 connect, AND 2/4, OR 3/5,
  XOR 3/7 — increasing complexity, all genuinely agent-solved (`operator/trajectories/<gate>.json`, source:agent).
  `operator/gate_agent.py` — generic runner:
  reach each gate level via banked skills → hand to Gemini with a per-gate query (the construction +
  decide-and-name) → agent solves via the `place`/`list_connectors`/`connect_pins` tools → referee PASS →
  record its OWN trajectory → synthesize → cold-execute validate → bank `source:"agent"` (replacing the
  reference) → advance. Stops on the first failure (partial capture is fine — every real agent solve counts).
  Added a **`place(component)` agent tool** (the agent NAMES the type — the drag hook can't distinguish
  nand/inv/and/or since NAMED_CONNECTORS_JS calls every non-relay "nandN"; `place` records the correct type).
  Run: `GEMINI_MODEL=gemini-2.5-computer-use-preview-10-2025 python operator/gate_agent.py` (log
  `probe/agent_gates.log`). **Check sources:** `python -c "import json;print({k:v['source'] for k,v in
  json.load(open('operator/skills/registry.json')).items()})"`. RELAY_NAND can stay reference (setup).
  To re-bank a gate from a fresh agent solve, just re-run; to re-bank the whole ladder, delete the gate
  `skill_*.py` first. Goal: INV/AND/OR/XOR all `source:"agent"` so the half-adder + revert run on agent skills.
- **Secrets:** `VOYAGE_API_KEY` stored in gitignored `.env` (verified absent from every tracked file + commit;
  `voyageai` not yet installed — do that at the library gate). Mongo Atlas conn string still needed
  (`mongodb+srv://<user>:<URL-ENCODED-PASSWORD>@<cluster>.mongodb.net/?appName=Cluster0`, `$`→`%24`).
- **Run it:** `computer-use-preview/.venv/bin/python probe/gate3_proof.py` (to re-run, first delete
  `operator/skills/skill_*.py` so PHASE 0's cold check holds).

## ✅ LIBRARY / RETRIEVAL gate — CLOSED, live on MongoDB Atlas Vector Search
`operator/library.py` — on a referee-VERIFIED banked skill: embed its DESCRIPTION (Voyage `voyage-3`, 1024-dim,
batched + self-throttled for the free tier) and store `{descriptor, file, source, verified_at, embedding}` in
Atlas; retrieve by embedding a task description + Atlas `$vectorSearch` (cosine fallback if the index is building).
- **Retrieval PROVEN** (`probe/library_demo.py`; local-backed store = identical embeddings + ranking):
  "build a NOT gate that inverts its input" → **INV** (0.66 vs 0.52); "construct a NAND gate out of relay
  components" → **RELAY_NAND** (0.67 vs 0.49). Right skill each time, clean margin.
- **Functional descriptions are load-bearing:** the skill description is the TASK GOAL ("Inverter (NOT gate):
  outputs the logical NOT...", "NAND gate built from relays...") threaded `start_recording(goal=)` → trajectory
  → `synth.render`. Mechanical-only descriptions ("places N components") retrieved WRONG — this was the fix.
- **LIVE ATLAS (`probe/library_atlas.py`):** `sync_registry` upserts skills to Atlas + creates a `vectorSearch`
  index (`skill_vec`, 1024-dim, cosine; builds in ~50s: PENDING→READY), then `retrieve` runs Atlas
  **`$vectorSearch`** — "NOT gate"→INV (0.83 vs 0.76), "NAND from relays"→RELAY_NAND (0.84 vs 0.75); same
  ranking as local cosine ✓. IP `<dev-public-IP>` allowlisted + active; all 3 nodes reachable (primary + 2
  secondaries). NOTE: the index must be created AFTER the first upsert (the collection must exist) — handled.
- **Smoke test (`probe/smoke_creds.py`):** Voyage ✓ (1024-dim); Atlas ✓ (round-trip). The `%24` password
  encoding was correct throughout (the earlier failure was the IP allowlist, never auth).
- **Voyage free tier = 3 req/min** (no payment method); handled by batching all skills into one embed call +
  a 21s throttle (`VOYAGE_MIN_GAP`). Add a Voyage payment method to lift it (200M free tokens still apply),
  then run with `VOYAGE_MIN_GAP=0`.
- **Secrets:** `VOYAGE_API_KEY` + `MONGODB_URI` (password `$`→`%24`) in gitignored `.env`; verified absent from
  every tracked file + commit. `pymongo` + `voyageai` installed in the harness venv.

## ✅ COMPOSITION gate — PROVEN: half-adder composed from retrieved banked skills (library is GENERATIVE)
`operator/compose.py` — GENERIC composer: given a task spec `{inputs, outputs:{connector: sub-goal}}` (the
logical DEFINITION of the task), for each output it RETRIEVES the best banked skill by Atlas vector similarity
to the sub-goal (DISCOVERS it — is not told which skill) and INVOKES it on the inputs + that output. There is
NO hardcoded circuit for any task: compose.py has zero `place_component`/`connect_pins` calls (those live only
inside the skills; the docstring mentions them only to explain). The construction comes entirely from the
retrieved skills.
- **Sub-skills banked (`probe/build_gates.py`, source:reference):** reach each level via banked skills, solve
  adaptively (place gates by TYPE, discover pins, wire), record → synth → validate (cold-exec) → bank.
  AND=invert(nand(a,b)); OR=nand(¬a,¬b); XOR=and(or(a,b), nand(a,b)). Library now: INV, RELAY_NAND, AND, OR, XOR.
- **Half-adder (`probe/compose_halfadder.py`):** reach HALFADD via the 5 banked skills; compose the spec
  `{Output_l:"XOR of the inputs", Output_h:"AND of the inputs"}` → retrieved **skill_XOR** (0.79) + **skill_AND**
  (0.79) from Atlas `$vectorSearch` → invoked → **referee PASS** (5 components; truth table a,b→h,l: 00→00,
  01→01, 10→01, 11→10). The half-adder was NEVER banked ⇒ the library GENERATES, it doesn't look up.
- **Layout (the hard part, solved):** `place_component` targets a LANDED position and drops at `landed/zoom`
  (robust to the CSS-zoom offset + any zoom), strictly left→right so the left-to-right naming stays stable
  (a grid breaks it — two gates share an x). 5 gates need a wider canvas: the droptarget extends with the
  viewport, so the gate/composition env uses `viewport=(2600,1400)` (5 gates fit one row, wide 300px spacing,
  reliable wiring). Relays keep their proven 1-D placement. `toolbox_item` matches the exact class token
  (`AND` ≠ `NAND`); multi-output terminals named `Output_h`/`Output_l`.
- **Honesty:** AND/OR/XOR are `source:"reference"` (machinery validation) — they flip to agent-sourced in the
  disclosed pre-warm (same swap as skill_INV). The retrieve+invoke COMPOSITION mechanism is the generative proof.
- **Run it:** `python probe/build_gates.py` (bank AND/OR/XOR), then `python probe/compose_halfadder.py`.

## ✅ FREEZE-MUTATE-REVERT — PROVEN: the skill library is load-bearing (Tier-2 revert)
`probe/revert_harness.py` — FROZEN SEED (reach HALFADD the same way via the agent-taught skills; deterministic
composition), run each library configuration ≥3×; ONLY the library changes between runs:
  - intact → compose the half-adder → referee **PASS ×3**
  - DELETE `skill_XOR` from the library → retrieval returns the next-best (`OR`) for the sum → wrong circuit
    → referee **FAIL ×3**  (raw log shows `sum<-OR` instead of `sum<-XOR` — the smoking gun)
  - RESTORE `skill_XOR` → compose → referee **PASS ×3** (recover)
PASS↔FAIL flips ONLY with the library mutation ⇒ the banked skill measurably IS the operator's capability.
Cached query vectors + the local store (`operator/skills/library_local.json`) make delete/restore instant +
Voyage-free in the loop (2 Voyage calls total). Raw log: `probe/revert.log`. Run: `python probe/revert_harness.py`.
A discarded "warmup" compose absorbs a one-off first-compose-after-chain settle flake (tally is then clean 3/3/3).

## CURRENT STATE (one-glance, for resume)
- **All gates DONE & committed.** Technical project complete; only the dashboard + demo polish remain (below).
- **Library (`operator/skills/registry.json`):** ALL 5 — INV, RELAY_NAND, AND, OR, XOR = `source:"agent"`
  (genuinely Gemini-solved, verified in registry; INV + RELAY_NAND on the prize model `gemini-3.5-flash`,
  AND/OR/XOR on 2.5-cu). All also embedded in Atlas
  (`selftaught_operator.skills`, `skill_vec` index) + the local store. **Re-sync Atlas to the agent skills before
  a live Atlas demo:** `python operator/library.py sync` (descriptions unchanged so retrieval already returns the
  right names, but the stored `source` field is otherwise stale).
- **Endpoint:** `gemini-3.5-flash` stormed all day (503); USE `gemini-2.5-computer-use-preview-10-2025` (set
  `GEMINI_MODEL`). **See the ⚠️ OPEN DECISION at the top** — the $5k Gemini prize names 3.5 computer-use, so the
  prize framing is unresolved until verified tomorrow.
- **Proven gates:** Gate-1 referee, Gate-2 semantic wiring, Gate-3 synthesis (empty-diff→fills), library/Atlas
  $vectorSearch, composition (half-adder generative), agent ladder (INV/AND/OR/XOR), revert (load-bearing 3/3/3).
- **Git (9 commits tonight):** `466c7f9` baseline → `64958d5` Gate-3 swap → `a4d1f39` library → `4c648dd` Atlas
  live → `4ca0c9a`/`1a5af9a` composition → `0eaccec` first agent solve → `b42b865` gate-ladder runner →
  `9f05f02` full ladder agent-taught → `fb206e1` revert PROVEN + STATUS finalized. Secrets clean (`.env`
  gitignored, verified absent from every tracked file).

## NEXT — DEMO PREP (tomorrow AM = EXECUTION, not rediscovery)
All gates ✅ (Gate-1 referee, Gate-2 semantic wiring, Gate-3 synthesis, library/Atlas, composition, agent
ladder, revert). **Status: dashboard ✅ · full dry-run ✅ · morning-capture [AM, endpoint-gated] · 1-min video
[pending AM] · rehearsal [AM].** In order:

0. **⚠️ MORNING CAPTURE SESSION FIRST** — see the **🌅 block at the top**: re-poll endpoint health → 3.5 prize
   re-capture (or 2.5 fallback + raise eligibility with an organizer) → agent-solve RELAY_NAND → wire the live
   cold-solve beat. All endpoint-gated; do them together in one healthy window. Settle the model/prize framing
   before rehearsing the pitch.

1. ✅ **Minimal 3-readout dashboard — BUILT** (`operator/dashboard.py`, stdlib-only, BARE). Three readouts:
   (1) skills-banked counter split agent/reference (**4 agent / 1 reference**); (2) STEPS-TO-SUCCESS — actions
   per solve from each trajectory (INV 4 → AND 6 → OR 8 → XOR 10), framed HONESTLY as "ordered by GATE COMPLEXITY,
   not a time series" / "scaling to harder problems, NOT rising efficiency" (the learning story is composition +
   revert, NOT step counts — do not let this read as an efficiency curve); (3) referee lamp — reads a run log's
   last STRUCTURED verdict (`referee/outcome/verdict: PASS|FAIL`, ignores prose), else the banked invariant
   (all PASS → green). Default log = `operator/run.log`. Run: `python operator/dashboard.py` (`--watch` refreshes
   every 2s; `--log <file>` points at a specific run).

2. **Pre-warm verification (do RIGHT BEFORE demoing — nothing cold on stage):**
   - Endpoint health check (it stormed all day) — confirm the chosen `GEMINI_MODEL` is reachable before any live solve.
   - `python operator/library.py sync` — refresh Atlas so the stored `source` field shows agent (descriptions
     already retrieve correctly; this just makes the live Atlas view match the agent story).
   - Smoke the two load-bearing demos so they're hot, not rediscovered: `python probe/compose_halfadder.py`
     (half-adder → referee PASS) and `python probe/revert_harness.py` (PASS→FAIL→PASS 3/3/3). Both endpoint-free.

3. **1-minute video:** the self-taught arc — Gemini decides-and-names → referee PASS → skill synthesized to disk
   (empty-diff→fills) → banked to Atlas → retrieved → half-adder composed from skills never banked together →
   revert (delete skill_XOR ⇒ PASS becomes FAIL). Lead with the thesis: *the agent teaches itself, measurably.*

4. ✅ **Full demo dry-run — RAN CLEAN end-to-end** (`probe/demo_dryrun.py`, the canonical "as presented" flow):
   reach HALFADD via the 5 banked skills → compose intact **PASS** (`sum<-XOR`) → DELETE `skill_XOR` from the
   retrievable library → re-compose **FAIL** (`sum<-OR`, the smoking gun) → RESTORE → re-compose **PASS**
   (`sum<-XOR`). Sequence **PASS→FAIL→PASS**, clean. It writes each verdict to `operator/run.log`, so the
   dashboard **referee lamp flips green→red→green** live (verified by replaying cumulative slices). The XOR
   delete is the in-memory retrievable-library mutation (on-disk `skill_XOR.py` untouched → instant restore).
   **DEMO = two panes:** A `python operator/dashboard.py --watch`  +  B `python probe/demo_dryrun.py`. Log:
   `probe/demo_dryrun.log`. Still to do: time it on the clock + rehearse the model-framing answer (#0).

- **Optional polish (not headline):** agent-source RELAY_NAND too (currently reference; it's only setup).
- **Guards (still binding):** never log a model refusal/error as a task failure; only referee-verified skills get
  banked; secrets only in gitignored `.env`; the honesty line (agent operates; system only makes motor acts land).
