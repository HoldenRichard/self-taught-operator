"""NandGame operating environment for the agent: a zoomed, snap-assisted browser computer.

ZoomSnapComputer subclasses the harness PlaywrightComputer and adds, automatically at launch:
  1. ZOOM  — larger viewport + CSS zoom so pins render as fatter, well-separated targets
             (re-applied on every page load via an init script, so reloads don't wipe it).
  2. SNAP  — connector-region clicks are snapped to the nearest TRUE connector coordinate
             (read live from the DOM). The agent still DECIDES which pins to connect; we only
             make the execution land. Clicks far from any connector (buttons, empty canvas)
             pass through unchanged.

All coordinates are derived live from the DOM at the current zoom — no stale Gate-1 constants.
"""
import sys, math, json
sys.path.insert(0, "/Users/holden/HackathonSF26/computer-use-preview")
from computers import PlaywrightComputer

ZOOM = 1.4
# Virtual viewport set in code — can be LARGER than the physical screen; the screenshot is the
# full virtual viewport. Must exceed the zoomed content (~1848x1269 at zoom 1.4) so every
# connector fits in ONE frame with no scrolling (Gemini only sees/clicks within the screenshot).
VIEWPORT = (1920, 1400)
SNAP_RADIUS = 18                  # HONEST: must stay < half the pin spacing so the snap can never
                                  # reach a neighbouring pin. The agent must genuinely aim at the pin;
                                  # snap only corrects a near-miss to the exact coordinate.

# clickable point of every connector at the CURRENT zoom: the triangle handle if present, else circle
CONNECTOR_POINTS_JS = r"""
() => {
  const pts = [];
  document.querySelectorAll('.input-connector, .output-connector').forEach(c => {
    if (c.closest('.toolbox') || c.closest('[class*=palette]')) return;  // skip toolbox-icon pins
    const el = c.querySelector('polygon.triangle') || c.querySelector('circle.connector-circle') || c;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.x >= 0 && r.y >= 0)
      pts.push({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
                role: (c.getAttribute('class')||'').includes('output') ? 'out' : 'in'});
  });
  return pts;
}
"""

# Maps every connector currently on the board to a stable NAME + role, for semantic wiring.
NAMED_CONNECTORS_JS = r"""
() => {
  // working click point: input-role connectors -> the triangle handle; output-role -> the circle.
  const ctr = (el, role) => { const prefer = (role === 'output') ? 'circle.connector-circle' : 'polygon.triangle';
    const t = el.querySelector(prefer) || el.querySelector('circle.connector-circle') || el.querySelector('polygon.triangle') || el;
    const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width/2), Math.round(r.y + r.height/2)]; };
  const out = {};
  const its = Array.from(document.querySelectorAll('.input-node .output-connector')).filter(c => c.getBoundingClientRect().width > 0);
  its.forEach((c, i) => {
    const txt = (c.textContent || '').trim().replace(/[^a-zA-Z0-9]/g, '');
    out[(its.length === 1) ? 'Input' : ('Input_' + (txt || i))] = { pos: ctr(c, 'output'), role: 'output' };
  });
  const ots = Array.from(document.querySelectorAll('.output-node .input-connector')).filter(c => c.getBoundingClientRect().width > 0);
  ots.forEach((c, i) => {
    const txt = (c.textContent || '').trim().replace(/[^a-zA-Z0-9]/g, '');
    out[(ots.length === 1) ? 'Output' : ('Output_' + (txt || i))] = { pos: ctr(c, 'input'), role: 'input' };
  });
  const placed = Array.from(document.querySelectorAll('.diagram-node')).filter(n =>
    !n.closest('.toolbox') && !n.closest('[class*=palette]') &&
    !n.classList.contains('input-node') && !n.classList.contains('output-node') &&
    n.getBoundingClientRect().x > 660 && n.getBoundingClientRect().width > 0)
    .sort((a, b) => a.getBoundingClientRect().x - b.getBoundingClientRect().x);  // left->right = stable index
  const counts = {};
  placed.forEach(n => {
    const type = n.querySelector('.relay-box') ? 'relay' : 'nand';
    counts[type] = (counts[type] || 0) + 1;
    const base = type + counts[type];
    const oc = n.querySelector('.output-connector');
    if (oc) out[base + '.out'] = { pos: ctr(oc, 'output'), role: 'output' };
    Array.from(n.querySelectorAll('.input-connector'))
      .sort((a, b) => a.getBoundingClientRect().x - b.getBoundingClientRect().x)
      .forEach((c, i) => {
        let lbl = (c.textContent || '').trim().replace(/[^a-zA-Z]/g, '') || ('in' + i);
        out[base + '.' + lbl] = { pos: ctr(c, 'input'), role: 'input' };
      });
  });
  return out;
}
"""


class ZoomSnapComputer(PlaywrightComputer):
    def __init__(self, initial_url="https://nandgame.com", highlight_mouse=True, zoom=ZOOM, viewport=VIEWPORT):
        super().__init__(screen_size=viewport, initial_url=initial_url, highlight_mouse=highlight_mouse)
        self._zoom = zoom
        self._snap_log = []

    def __enter__(self):
        res = super().__enter__()  # launches browser + navigates to initial_url
        # persist zoom across all future loads, and apply to the current page now
        self._page.add_init_script(f"document.documentElement.style.zoom = '{self._zoom}';")
        self.apply_zoom()
        return res

    def apply_zoom(self):
        self._page.evaluate(f"document.documentElement.style.zoom = '{self._zoom}';")
        self._page.wait_for_timeout(150)

    def set_zoom(self, z):
        """Change the zoom mid-session (no reload). Use a smaller zoom for many-component levels so all
        gates fit one viewport; keep the larger zoom for relay setup + any Gemini-perception steps."""
        self._zoom = z
        self.apply_zoom()

    def connector_points(self):
        try:
            return self._page.evaluate(CONNECTOR_POINTS_JS)
        except Exception:
            return []

    def _snap(self, x, y):
        """HONEST snap: move a click to the NEAREST connector within SNAP_RADIUS, else leave it.
        No intent inference, no wire-state, no role routing — it only corrects an already-near
        click to the true pin coordinate. SNAP_RADIUS must stay < half the pin spacing so it
        cannot reach a neighbouring pin (i.e. the agent must genuinely be aiming at the right pin)."""
        best, bd = None, SNAP_RADIUS * SNAP_RADIUS
        for p in self.connector_points():
            d = (p["x"] - x) ** 2 + (p["y"] - y) ** 2
            if d <= bd:
                bd, best = d, p
        if best is not None:
            self._snap_log.append({"from": [x, y], "to": [best["x"], best["y"]]})
            return best["x"], best["y"]
        return x, y

    def click_at(self, x, y):
        sx, sy = self._snap(x, y)
        return super().click_at(sx, sy)

    def _placed_bases(self):
        return set(k.split(".")[0] for k in self._named_connectors() if "." in k)

    def drag_and_drop(self, x, y, destination_x, destination_y):
        # If the AGENT drags a component onto the canvas during a recording, capture it SEMANTICALLY:
        # the component TYPE only (e.g. "nand") — never the literal drop pixels. The synthesized skill
        # then places by type and picks the position at run time, identical to the reference pipeline,
        # so the skill stays parameterized / layout-robust (not a coordinate replay).
        recording = getattr(self, "_traj", None) is not None
        before = self._placed_bases() if recording else set()
        sx, sy = self._snap(x, y)
        dx, dy = self._snap(destination_x, destination_y)
        res = super().drag_and_drop(sx, sy, dx, dy)
        if recording:
            self._page.wait_for_timeout(150)
            new = [b for b in self._placed_bases() if b not in before]
            if new:
                base = sorted(new)[0]
                self._record({"op": "place", "component": base.rstrip("0123456789"),
                              "bound": base, "via": "agent-drag"})
        return res

    # ---------- SEMANTIC WIRING (custom agent tools) ----------
    # The agent NAMES the two connectors to wire (it reads/decides which from the board); the
    # system forms exactly that connection reliably. No intent inference — the agent specifies
    # the connectors; we only execute the named connection and verify it via the game's oracle.
    def _total_conns(self):
        return self._page.evaluate("""()=>{let t=0;for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);
          if(k.indexOf('NandGame:Levels:')===0){try{t+=(JSON.parse(localStorage.getItem(k)||'{}').connections||[]).length}catch(e){}}} return t;}""")

    def _named_connectors(self):
        try:
            return self._page.evaluate(NAMED_CONNECTORS_JS)
        except Exception:
            return {}

    def _form_connection(self, p, q):
        # Same proven methods as robust_wire: click both orders AND drag both orders. Clicking the
        # tiny clustered pins often snaps to the wrong connector; the drag gesture lands the right
        # one. Verify a connection actually formed via the oracle.
        pg = self._page
        def _drag(a, b):
            pg.mouse.move(a[0], a[1]); pg.wait_for_timeout(60); pg.mouse.down(); pg.wait_for_timeout(80)
            pg.mouse.move(a[0] + 3, a[1] + 3, steps=3); pg.mouse.move(b[0], b[1], steps=18)
            pg.wait_for_timeout(120); pg.mouse.up(); pg.wait_for_timeout(160)
        before = self._total_conns()
        for fn in (lambda: (pg.mouse.click(*p), pg.wait_for_timeout(150), pg.mouse.click(*q)),
                   lambda: (pg.mouse.click(*q), pg.wait_for_timeout(150), pg.mouse.click(*p)),
                   lambda: _drag(p, q),
                   lambda: _drag(q, p)):
            pg.keyboard.press("Escape"); pg.wait_for_timeout(50); fn(); pg.wait_for_timeout(160)
            if self._total_conns() > before:
                return True
        return False

    def connect_pins(self, source: str, target: str) -> dict:
        """Create a wire between two named connectors on the board. You choose which two connectors
        to connect by name (read them from the board / list_connectors). Examples of names:
        'Input', 'Output', 'nand1.a', 'nand1.b', 'nand1.out'. Returns whether the wire was created."""
        named = self._named_connectors()
        missing = [n for n in (source, target) if n not in named]
        if missing:
            return {"success": False, "error": f"unknown connector name(s): {missing}",
                    "available_connectors": sorted(named.keys())}
        ok = self._form_connection(named[source]["pos"], named[target]["pos"])
        self._snap_log.append({"connect": [source, target], "ok": ok})
        self._record({"op": "connect", "source": source, "target": target, "ok": bool(ok)})
        return {"success": bool(ok), "connected": f"{source} -> {target}",
                "total_connections_on_board": self._total_conns(),
                "note": ("wire created (verified in the game's saved circuit)" if ok
                         else "the wire did not register; re-check the connector names against the board")}

    def list_connectors(self) -> dict:
        """List the connectors currently on the board (by name + role) that connect_pins can wire.
        Call this after placing components to learn the exact names to pass to connect_pins."""
        named = self._named_connectors()
        return {"connectors": [{"name": k, "role": v["role"]} for k, v in named.items()]}

    def place(self, component: str) -> dict:
        """Place a logic component on the board by TYPE and return its name. component is one of:
        'nand', 'inv' (inverter/NOT), 'and', 'or', 'xor'. Refer to the placed component's pins by the
        returned name (e.g. nand1.a, inv1.in0) — call list_connectors to see them. Use this to place
        components (you do not need to drag)."""
        name = self.place_component(component)
        return {"placed": component, "name": name,
                "note": (f"placed as '{name}'; its pins are '{name}.<pin>' — call list_connectors() to see them"
                         if name else "placement did not register; try again")}

    def agent_tool_callables(self):
        return [self.place, self.connect_pins, self.list_connectors]

    # ---------- semantic placement + referee (the stable API skills are generated against) ----------
    def place_component(self, component: str) -> str:
        """Drag a component (toolbox match, e.g. 'nand', 'RELAY-ON') onto the canvas, cancel the armed
        wire, and return the placed component's base NAME (e.g. 'nand1') for use with connect_pins.
        The drop position is chosen automatically (spread left->right to avoid overlap) and is NEVER
        part of the skill — the skill places by TYPE and refers to pins by NAME. Name is read back live."""
        pg = self._page
        before = self._named_connectors()
        bases_before = set(k.split(".")[0] for k in before if "." in k)
        item = toolbox_item(pg, component)
        if not item:
            self._record({"op": "place", "component": component, "bound": None})
            return None
        n = len(bases_before)
        # Positions are read back, never baked into the skill. A drop lands at ~drop*zoom (NandGame CSS-zoom
        # offset), so we target a LANDED position inside the canvas and drop at landed/zoom. Relays are wide
        # (proven 1-D positions); logic gates go in a 3-column grid with wide spacing so 5-6 wire reliably.
        Z = self._zoom
        if "relay" in component.lower():
            lx, ly = 1008 + n * 420, 700
        else:
            lx, ly = 1000 + n * 300, 560        # single row (strictly left->right for stable naming), wide spacing
        _drag(pg, item[0], item[1], lx / Z, ly / Z)
        _cancel_armed(pg)
        after = self._named_connectors()
        new = [k.split(".")[0] for k in after if "." in k and k.split(".")[0] not in bases_before]
        name = new[0] if new else None
        self._record({"op": "place", "component": component, "bound": name})
        return name

    def referee_check(self):
        """Run NandGame's own validator on the current circuit; return the Gate-1 Verdict (real PASS/FAIL)."""
        from referee import referee_check as _rc
        return _rc(self._page)

    # ---------- trajectory recording (instrumentation only; holds NO solution) ----------
    def start_recording(self, task, start_level, source="agent", goal=None):
        # source: "agent" (a genuine model solve — what we demo) or "reference" (probe scaffolding).
        # goal: the FUNCTIONAL task description the agent was given (e.g. "Inverter (NOT gate)...") — the
        # task SPEC, not the solution; used as the skill's description for semantic retrieval.
        self._traj = {"task": task, "start_level": start_level, "source": source, "goal": goal, "actions": []}

    def stop_recording(self):
        self._traj = None   # e.g. before a validation cold-execute, so it doesn't pollute the trajectory

    def _record(self, action):
        t = getattr(self, "_traj", None)
        if t is not None:
            t["actions"].append(action)

    def trajectory(self):
        return getattr(self, "_traj", None)


# ---------- live (zoom-aware) coordinate helpers — query the DOM, never hardcode ----------
def _center(pg, sel, inner=None):
    return pg.evaluate("""(a)=>{const n=document.querySelector(a[0]); if(!n) return null;
      const e=a[1]?(n.querySelector(a[1])||n):n; const r=e.getBoundingClientRect();
      return r.width? [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)] : null;}""", [sel, inner])

def toolbox_item(pg, type_substr):
    """Center of a draggable toolbox component. Prefers an EXACT class-token match (gates carry a clean type
    class: NAND/INV/AND/OR — so 'and' won't grab 'nand'); falls back to a class/text substring (relays etc.)."""
    return pg.evaluate("""(t)=>{
      const T=t.toUpperCase();
      const cands = Array.from(document.querySelectorAll('.toolbox .diagram-node, .palette-nodetype, [class*=palette] .diagram-node, .diagram-node.free-node'));
      const ctr = n => { const box=n.querySelector('.relay-box')||n; const r=box.getBoundingClientRect(); return [Math.round(r.x+r.width/2), Math.round(r.y+r.height/2)]; };
      for (const n of cands){ if ((n.getAttribute('class')||'').toUpperCase().split(/\\s+/).includes(T)) return ctr(n); }
      for (const n of cands){ const c=(n.getAttribute('class')||'').toUpperCase(), x=(n.textContent||'').toUpperCase(); if (c.includes(T)||x.includes(T)) return ctr(n); }
      return null;}""", type_substr)

def terminal(pg, which):
    return _center(pg, f'.input-node .output-connector.{which}', 'circle.connector-circle')

def output_pin(pg):
    return _center(pg, '.output-node .input-connector', 'polygon.triangle')

def placed_relays(pg):
    return pg.evaluate("""()=>{const ns=Array.from(document.querySelectorAll('.diagram-node')).filter(x=>x.querySelector('.input-connector.in')).filter(x=>!x.closest('[class*=palette]')&&!x.closest('.toolbox'));
      // toolbox items have small x; placed are to the right of the toolbox column (~ x>450 at zoom)
      const placed = ns.filter(n=>n.getBoundingClientRect().x>430).sort((p,q)=>p.getBoundingClientRect().x-q.getBoundingClientRect().x);
      const tri=(n,w)=>{const e=n.querySelector('.input-connector.'+w+' polygon.triangle'); if(!e)return null; const r=e.getBoundingClientRect(); return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];};
      const oc=(n)=>{const e=n.querySelector('.output-connector circle.connector-circle'); const r=e.getBoundingClientRect(); return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];};
      return placed.map(n=>({inp:tri(n,'in'), c:tri(n,'c'), out:oc(n), box:(()=>{const r=n.getBoundingClientRect();return[Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];})()}));}""")

def conn_count(pg, level):
    return pg.evaluate("(k)=>{let o={};try{o=JSON.parse(localStorage.getItem('NandGame:Levels:'+k)||'{}')}catch(e){};return (o.connections||[]).length}", level)

# ---------- browser-action helpers (deterministic SETUP only; the agent drives via the harness) ----------
def dismiss_popup(pg):
    try:
        el = pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass

def clear_canvas(pg):
    pg.once("dialog", lambda d: d.accept())
    el = pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)

def _drag(pg, x1, y1, x2, y2, steps=30):
    pg.mouse.move(x1, y1); pg.wait_for_timeout(60); pg.mouse.down(); pg.wait_for_timeout(90)
    pg.mouse.move(x1+4, y1+4, steps=4); pg.wait_for_timeout(30)
    pg.mouse.move(x2, y2, steps=steps); pg.wait_for_timeout(140); pg.mouse.up(); pg.wait_for_timeout(280)

def _cancel_armed(pg):
    pg.keyboard.press("Escape"); pg.wait_for_timeout(70)
    pg.mouse.click(1750, 320); pg.wait_for_timeout(120)        # click empty far-right canvas
    pg.keyboard.press("Escape"); pg.wait_for_timeout(70)

def robust_wire(pg, p, q, level):
    """Connect points p,q (live coords) trying click-orders + drags; verify via the LS oracle."""
    if not p or not q: return False
    before = conn_count(pg, level)
    for fn in [lambda: (pg.mouse.click(*p), pg.wait_for_timeout(150), pg.mouse.click(*q)),
               lambda: (pg.mouse.click(*q), pg.wait_for_timeout(150), pg.mouse.click(*p)),
               lambda: _drag(pg, p[0], p[1], q[0], q[1], 18),
               lambda: _drag(pg, q[0], q[1], p[0], p[1], 18)]:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(40); fn(); pg.wait_for_timeout(160)
        if conn_count(pg, level) > before: return True
    return False

# NOTE: hand-authored circuit SOLVES live in probe/reference_solver.py (quarantined scaffolding),
# never here in the operator env. The operator reaches a level by running its OWN banked skills
# (operator/skills/) or by a genuine agent solve — never a scripted answer. (Gate-3 integrity line.)

def advance_to_next_level(pg):
    """Click 'Next level' FROM the open success popup (don't close it first)."""
    nl = pg.query_selector('button:has-text("Next level")')
    if nl:
        nl.click(); pg.wait_for_timeout(1500); return True
    return False

