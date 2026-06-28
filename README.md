# Self-Taught Operator

An AI agent that teaches itself to operate **[NandGame](https://nandgame.com)** (a browser logic-circuit game) and **writes its own reusable, executable skills** as it goes — getting more capable the more it plays, with no human in the loop. We prove the skills are real by **deleting one and watching the agent's capability measurably disappear.**

> **AI Engineer World's Fair Hackathon 2026** (June 27–28, San Francisco) · Solo: Holden Richard
> **Theme — Continual Learning** via *toolkit expansion*: the agent grows its own skill library from real use.
> **Prize track — Best Usage of Gemini 3.5:** uses **Computer Use in Gemini 3.5 Flash** (native screenshot perception + UI actions).

## The loop — `operate → verify → synthesize → bank → retrieve → compose`
1. **Operate.** Gemini 3.5 Flash (computer use) sees the board and reasons the circuit; it *names* the wiring (`list_connectors` / `connect_pins`). The agent does all the thinking — the system only makes the motor act land reliably.
2. **Verify.** A deterministic, **non-LLM referee** runs NandGame's own validator. Nothing is trusted without a real PASS.
3. **Synthesize.** On a verified solve, the agent's trajectory is turned into **real Python written to disk at runtime** — a parameterized, executable skill, not a hand-written macro.
4. **Bank.** The generated skill is cold-executed to re-verify, then stored in a **MongoDB Atlas Vector Search** library (descriptions embedded with **Voyage AI**).
5. **Retrieve + Compose.** New tasks retrieve skills by similarity and invoke them — a **half-adder** is composed from skills that were *never banked together*. The library generates; it doesn't look up.

## Proven (all during the hackathon)
- **5/5 logic-gate skills solved by the agent itself** (`source: agent`): NAND-from-relays, INV, AND, OR, XOR — captured live (INV + RELAY_NAND on Gemini 3.5 Flash; AND/OR/XOR on Gemini 2.5 computer-use).
- **Half-adder composed** from retrieved `XOR` + `AND` → referee PASS (truth table correct), though it was never banked.
- **Freeze-mutate-revert:** intact library → half-adder PASSes; **delete `skill_XOR` → retrieval falls back to the wrong skill → referee FAIL** (`sum<-OR`); restore → PASS. The banked library *is* the capability.

## Tech & sponsors
- **Gemini 3.5 Flash — Computer Use** — the agent's eyes + hands.
- **MongoDB Atlas Vector Search** — the skill library (`$vectorSearch` retrieval).
- **Voyage AI** (`voyage-3`) embeddings — semantic skill retrieval.

## What we built vs. dependencies (hackathon disclosure)
- **Original work, built June 27–28, 2026 — everything in `operator/` and `probe/`:** the referee, the runtime skill synthesizer, the semantic-wiring layer, the Atlas + Voyage library, the generic composer, the freeze-mutate-revert harness, and the agent runners.
- **One dependency, NOT our work and NOT in this repo:** Google's **Gemini `computer-use-preview`** harness (Apache-2.0) — the browser runtime that feeds screenshots to the model and executes its actions. It is vendored locally, **gitignored**, and we patched it only to dispatch our custom semantic tools (changes documented in `STATUS.md`).

## Layout
- `operator/` — runtime: `referee.py`, `synth.py`, `trajectory.py`, `library.py`, `compose.py`, `nandgame_env.py`; agent runners (`gate2_runner.py`, `gate_agent.py`, `relay_nand_agent.py`); `dashboard.py`; banked `skills/` + `trajectories/`.
- `probe/` — proofs & experiments: `gate3_proof.py` (synthesis integrity), `compose_halfadder.py`, `revert_harness.py`, `demo_dryrun.py`, plus the genuine Gemini 3.5 capture logs.
- `STATUS.md` / `DEMO_PATHWAY.md` — full build log + demo script.

## Run it
1. Provide the gitignored dependencies: Google's `computer-use-preview` harness alongside this repo (with a Gemini API key), and a `.env` with `MONGODB_URI` + `VOYAGE_API_KEY`.
2. `source computer-use-preview/.venv/bin/activate`
3. Endpoint-free proofs: `python probe/gate3_proof.py` · `python probe/demo_dryrun.py` (compose + revert) · `python operator/dashboard.py`
4. Live agent solve: `GEMINI_MODEL=gemini-3.5-flash AUTO_SAFETY=proceed python operator/gate2_runner.py`

## License
MIT — see [LICENSE](LICENSE). (The vendored Google `computer-use-preview` harness is Apache-2.0 and is **not** included in this repository.)
