"""Wait for the Gemini endpoint to CLEAR (stop flapping 503/504), then run Gate 2 once.
Polls health (5 quick calls) every ~40s; launches gate2_runner.main() when a clean 5/5 lands.
Time-boxed to ~25 min of polling so it can't wait forever."""
import os, sys, time
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from google import genai
from google.genai import types

def health():
    c = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=20000))
    ok = 0
    for _ in range(5):
        try:
            c.models.generate_content(model="gemini-3.5-flash", contents="ok"); ok += 1
        except Exception:
            pass
        time.sleep(1)
    return ok

def main():
    cleared = False
    for i in range(35):
        ok = health()
        print(f"[health {i+1}] {ok}/5", flush=True)
        if ok >= 5:
            print("ENDPOINT CLEARED — launching Gate 2", flush=True); cleared = True; break
        time.sleep(40)
    if not cleared:
        print("ENDPOINT DID NOT CLEAR within the polling window — stopping (retry later).", flush=True)
        return
    import gate2_runner
    gate2_runner.main()

if __name__ == "__main__":
    main()
