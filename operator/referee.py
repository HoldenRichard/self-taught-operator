"""
GATE 1 — REFEREE READER.

The referee is NandGame's OWN "Check solution" validator. This module clicks that button
and reads the resulting DOM verdict. It is deterministic, sub-second, and contains NO LLM
anywhere in the path — the PASS/FAIL decision is NandGame's, not ours.

Verdict signals (captured empirically from nandgame.com):
  FAIL  -> a `.error-banner` ("Level is not correct.") + `.popup-dialog.error-dialog`,
           plus `.test-results tbody tr.error` rows naming the failing input combos.
  PASS  -> NO `.error-banner`; a success `.popup-dialog` (without `.error-dialog`) and the
           `NandGame:Levels` localStorage list advances to include the next level.

`referee_check(page)` returns True ONLY on NandGame's real PASS. Every call returns the raw
verdict (DOM text + classes + failing cases) so we can log it for demo rigor.
"""
from dataclasses import dataclass, field
from typing import Any

CHECK_BUTTON = 'button:has-text("Check solution")'
LEVELS_KEY = "NandGame:Levels"

_VERDICT_JS = r"""
() => {
  const txt = e => e ? (e.textContent || '').trim().replace(/\s+/g, ' ') : null;
  const banner  = document.querySelector('.error-banner');
  const dialog  = document.querySelector('[class*="popup-dialog"]');
  const errDlg  = document.querySelector('.error-dialog, .popup-dialog.error-dialog');
  // failing test-cases: rows in the result table flagged .error -> [a, b, V, output]
  const failing = Array.from(document.querySelectorAll('.test-results tbody tr.error')).map(tr =>
    Array.from(tr.querySelectorAll('td')).map(td => (td.textContent || '').trim()).filter(s => s !== ''));
  // expected value row (shown alongside the first failure)
  const expectedRow = document.querySelector('.test-results tbody tr.expected');
  return {
    error_banner: !!banner,
    banner_text: txt(banner),
    dialog_text: txt(dialog),
    dialog_class: dialog ? dialog.getAttribute('class') : null,
    is_error_dialog: !!errDlg,
    failing_cases: failing,
    expected_text: txt(expectedRow),
    levels: localStorage.getItem('NandGame:Levels'),
  };
}
"""


@dataclass
class Verdict:
    passed: bool
    status: str                       # "PASS" | "FAIL" | "AMBIGUOUS" | "NO_BUTTON"
    raw_dialog: str | None = None
    banner_text: str | None = None
    failing_cases: list = field(default_factory=list)
    levels_before: str | None = None
    levels_after: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:        # so `if referee_check(page): ...` reads naturally
        return self.passed


def referee_check(page, click_timeout_ms: int = 1500) -> Verdict:
    """Click NandGame's 'Check solution' and return its real PASS/FAIL verdict.

    True ONLY when NandGame's validator confirms the circuit (no error banner + a
    success dialog and/or the level list advances). A circuit that merely has wires
    but is logically wrong returns False (the validator raises .error-banner).
    """
    btn = page.query_selector(CHECK_BUTTON)
    if btn is None:
        return Verdict(passed=False, status="NO_BUTTON")

    levels_before = page.evaluate(f"() => localStorage.getItem('{LEVELS_KEY}')")
    btn.click()
    page.wait_for_timeout(click_timeout_ms)
    v = page.evaluate(_VERDICT_JS)

    error = bool(v["error_banner"]) or bool(v["is_error_dialog"])
    advanced = v["levels"] != levels_before
    success_dialog = (v["dialog_text"] is not None) and (not v["is_error_dialog"])

    if error:
        status, passed = "FAIL", False
    elif success_dialog or advanced:
        status, passed = "PASS", True
    else:
        status, passed = "AMBIGUOUS", False

    return Verdict(
        passed=passed,
        status=status,
        raw_dialog=v["dialog_text"],
        banner_text=v["banner_text"],
        failing_cases=v["failing_cases"],
        levels_before=levels_before,
        levels_after=v["levels"],
        detail=v,
    )


def dismiss_verdict_popup(page) -> None:
    """Close the verdict popup so the next check starts clean."""
    for sel in (".popup-close", 'button:has-text("Close")', 'button:has-text("OK")'):
        el = page.query_selector(sel)
        if el:
            try:
                el.click(); page.wait_for_timeout(200); return
            except Exception:
                pass
