# SETUP_STATUS — pre-clock environment prep

**Generated:** 2026-06-27, before the 11:30 start. No project code written (setup + smoke tests only).
**Working dir:** `/Users/holden/HackathonSF26`  •  **Harness:** `./computer-use-preview`  •  **venv:** `./computer-use-preview/.venv`

---

## TL;DR — status: 🟢 GREEN LIGHT

| Item | Status |
|---|---|
| Gemini computer-use harness cloned + installed | ✅ |
| All deps install on Python 3.14.6 (incl. greenlet/playwright/pydantic) | ✅ |
| Bundled Chromium installed + **headed window opens & navigates** (verified, screenshot) | ✅ |
| Harness imports + unit tests (13 passed) on 3.14 | ✅ |
| PyTorch 2.12.1 importable, **MPS=True**, numpy interop | ✅ |
| git identity + credential helper + default branch | ✅ |
| gh authed, `repo` scope → can create+push public repo | ✅ |
| This agent has web access | ✅ |
| Key wired into venv (gitignored, masked) | ✅ |
| **Gemini-driven smoke test** | ✅ **PASS** — browser opened, Gemini drove it, clean completion |

---

## 🟢 Paste-and-go at 11:30

The key is **already wired** into `.venv/bin/activate` (gitignored). At the clock:

```bash
cd /Users/holden/HackathonSF26/computer-use-preview
source .venv/bin/activate
echo $GEMINI_API_KEY        # confirms key is loaded

# Your NandGame probe is just a different --query:
python main.py --query "<YOUR NANDGAME PROBE>" --env playwright --highlight_mouse
```

**Verified-good smoke command (completed cleanly):**
```bash
python main.py --query "What is the main heading (the H1 text) on this page? Report it and then you are done." \
  --env playwright --initial_url "https://example.com" --highlight_mouse
# -> "Agent Loop Complete: ... The main heading (H1 text) on this page is 'Example Domain'."
```

---

## Harness flag reference (source-verified from `main.py` / `agent.py`)

| Flag | Notes |
|---|---|
| `--query "..."` | **Required.** The natural-language task. |
| `--env playwright` | ⚠️ It's `--env`, **NOT `--environment`** (your runbook had `--environment`, which argparse rejects). Default is already `playwright`. Other option: `browserbase` (do not use). |
| `--highlight_mouse` | **The cursor-highlight flag.** Injects a red circle at each action's (x,y) into the page for ~2s, so the mouse position shows up in screenshots. Visual debugging. Playwright-only. Verified working. |
| `--model <id>` | Default **`gemini-3.5-flash`** (used in the passing smoke test). Other shipped options: `gemini-2.5-computer-use-preview-10-2025`, `gemini-3-flash-preview`. |
| `--initial_url <url>` | Default `https://www.google.com`. |

- **Key env var:** `agent.py:108` reads `os.environ.get("GEMINI_API_KEY")`; `USE_VERTEXAI` defaults off → Developer API (matches your key).

---

## ⭐ Smoke-test findings that matter for the autonomous loop

These are NOT setup bugs — they're harness behaviors you'll hit when the "operator" runs unattended.

1. **The harness BLOCKS on `input()` for safety confirmations.** When Gemini returns a `safety_decision = require_confirmation` (CAPTCHAs, logins, payments, anything sensitive), `agent.py` → `_get_safety_confirmation` (~line 571) calls `input("Do you wish to proceed? [Yes]/[No]")`.
   - Interactive terminal (your manual probes): you type Yes/No — fine.
   - **Non-interactive / piped / autonomous run: `input()` raises `EOFError` and the loop crashes.** (This is exactly what happened on the first Google run.)
   - **Action for the build:** before running the operator unattended, handle `require_confirmation` programmatically — auto-decide in code, feed stdin, or patch `_get_safety_confirmation` to return a decision without `input()`. Otherwise the loop dies the first time the model proposes a gated action.

2. **Automating google.com trips a CAPTCHA** ("our systems have detected unusual traffic" → "I'm not a robot"), which then triggers finding #1. NandGame won't do this, but avoid Google for smoke tests; benign sites (example.com) complete cleanly.

3. **`Tools at indices [1] are not compatible with automatic function calling (AFC). AFC is disabled.`** — benign google-genai info line, printed every iteration. The harness drives function calls manually, so AFC is intentionally off. Not an error.

---

## Installed (versions)

**System:** Python **3.14.6** (`/opt/homebrew/bin/python3` — only Python on the box; no pyenv/3.11/3.12), pip 26.1.2, git 2.50.1, gh 2.92.0, Google Chrome.app present.

**venv (`computer-use-preview/.venv`):**
- google-genai 2.8.0 · playwright 1.55.0 · pydantic 2.12.0 · greenlet 3.5.3 (cp314 wheel) · browserbase 1.4.0 (installed, unused) · termcolor 3.1.0 · rich 15.0.0 · pytest 9.1.1 · python-dotenv 1.0.1
- **torch 2.12.1** (cp314 wheel) + **numpy 2.5.0** — `torch.backends.mps.is_available() == True` (Apple-Silicon GPU available for the Tier-3 value head)

**Playwright browsers** (`~/Library/Caches/ms-playwright/`): `chromium-1187` (headed — the one the harness actually uses), `chromium_headless_shell-1187`, `ffmpeg-1011`.

---

## Environment verification

- **Python 3.11+**: ✅ 3.14.6 (note: bleeding-edge; all needed wheels happened to exist — see fixes).
- **git configured**: ✅ identity set → `Holden Richard <hgrichar@uvm.edu>` (was empty — change with `git config --global user.name "..."` if you want a different display name). `init.defaultBranch=main`.
- **Create+push PUBLIC repo (plumbing)**: ✅ gh authed as `HoldenRichard`; token scopes `gist, read:org, repo, workflow`; `repo` scope grants public-repo create+push; `gh auth setup-git` wired so `git push` to github.com authenticates via the gh token.
  - Verified **non-destructively** (no throwaway repo created). A live create→push→delete round-trip was skipped because the token lacks `delete_repo` scope to self-clean. To do a live round-trip later: `gh auth refresh -s delete_repo`, then create/delete a test repo.
- **PyTorch importable**: ✅ (installed; MPS available).
- **Agent web access**: ✅ confirmed via live WebFetch of example.com.

---

## Things that failed / would have bitten at 11:30 — and the fix

1. **`playwright install chrome` is NOT enough.** The harness calls `self._playwright.chromium.launch()` with **no `channel="chrome"`** (`computers/playwright/playwright.py:103`), so it needs Playwright's **bundled Chromium**, not your system Chrome. `playwright install chrome` only detected system Chrome and downloaded nothing. → **Fix applied:** ran `playwright install chromium` (now `chromium-1187` is in the cache). Without this the smoke test would have died with "Executable doesn't exist… run playwright install".

2. **Headless footgun → invisible browser.** `playwright.py:114` is `headless=bool(os.environ.get("PLAYWRIGHT_HEADLESS", False))`. Because of the `bool()` wrapper, the **string** `"false"` is truthy → headless. So:
   - **Leave `PLAYWRIGHT_HEADLESS` UNSET** to get a visible window (current state ✅; the passing smoke test ran headed).
   - **Do NOT `cp .env.example .env`** blindly — that file sets `PLAYWRIGHT_HEADLESS=false`, which would silently run headless (no window). If you want a `.env` for the key, omit/blank that line.

3. **`--environment` flag is wrong** → use `--env` (argparse exact name; `--environment` errors as unrecognized).

4. **git identity was empty** → set (would have blocked commits).

5. **No gh credential helper wired for push** → ran `gh auth setup-git`.

6. **torch had no numpy** (`UserWarning: Failed to initialize NumPy`) → installed numpy 2.5.0.

7. **Python 3.14 wheel risk** — flagged as a risk (only 3.14 on the box); turned out fine, every dep (incl. torch cp314, greenlet cp314) had a 3.14 wheel. No fallback Python needed. If a future dep lacks a 3.14 wheel, `brew install python@3.12` and rebuild the venv with `python3.12 -m venv .venv`.

8. Minor: macOS has no `timeout` command (GNU-only) — irrelevant to the harness, just noting if any script uses it.

---

## Security note (key handling)

- Key lives **only** in `computer-use-preview/.venv/bin/activate` (plaintext export line), which is **gitignored** (`git check-ignore` confirmed via `.gitignore:132 .venv`). It cannot be committed/pushed.
- Key is **not** written into this file or any tracked file. Confirmations were masked (`prefix='AIza' suffix='e6GQ' len=39`).
- When you create the project repo at the parent folder, the harness clone keeps its own `.git` + `.gitignore`, so the venv (and key) stays out of commits. Still: never `git add` the activate file or paste the key into tracked code.

---

## What is NOT done (by design)

- Project repo NOT created, no project code written (per instructions).
- Browserbase untouched (using local Playwright).
- Codex not installed.
