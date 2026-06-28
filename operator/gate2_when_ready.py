"""Wait for the Gemini endpoint to CLEAR, then run the Gate-2 -> Gate-3 SWAP (gate2_runner.main):
Gemini solves the inverter and skill_INV is re-synthesized from GEMINI'S OWN verified trajectory
(source: agent), replacing the reference skill.

Polls health (5 quick calls); on a clean 5/5 it runs one Gemini attempt; RETRIES on API-death / non-bank
(the endpoint can flap mid-run) up to MAX_ATTEMPTS real attempts; stops the instant the agent skill is
banked. Long poll window so it survives an extended storm (capture whenever the endpoint clears)."""
import os, sys, time, json, importlib
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from google import genai
from google.genai import types

REG = "/Users/holden/HackathonSF26/operator/skills/registry.json"
POLL_ITERS = 200      # ~2-3h depending on how fast the storming calls fail
MAX_ATTEMPTS = 5      # real Gemini attempts — don't burn the endpoint forever


def health():
    c = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=15000))
    ok = 0
    for _ in range(5):
        try:
            c.models.generate_content(model="gemini-3.5-flash", contents="ok"); ok += 1
        except Exception:
            pass
        time.sleep(1)
    return ok


def swap_done():
    try:
        return json.load(open(REG)).get("INV", {}).get("source") == "agent"
    except Exception:
        return False


def main():
    if swap_done():
        print("SWAP already complete (agent skill_INV banked). Nothing to do.", flush=True); return
    attempts = 0
    for i in range(POLL_ITERS):
        ok = health()
        print(f"[health {i+1}] {ok}/5", flush=True)
        if ok >= 5:
            attempts += 1
            print(f"ENDPOINT CLEARED — launching Gate-2 swap (attempt {attempts}/{MAX_ATTEMPTS})", flush=True)
            try:
                import gate2_runner
                importlib.reload(gate2_runner)
                gate2_runner.main()
            except Exception as e:
                print(f"[gate2_runner crashed: {type(e).__name__}: {e}]", flush=True)
            if swap_done():
                print("SWAP_COMPLETE — agent-sourced skill_INV banked. Stopping.", flush=True); return
            print(f"[attempt {attempts} did not bank the agent skill]", flush=True)
            if attempts >= MAX_ATTEMPTS:
                print("max Gemini attempts reached without a banked agent skill — stopping (retry later).", flush=True); return
            time.sleep(30)
        else:
            time.sleep(40)
    print("poll window expired without a completed swap (retry later).", flush=True)


if __name__ == "__main__":
    main()
