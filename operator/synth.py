"""Skill synthesis — turn a referee-verified TRAJECTORY into a reusable, parameterized, EXECUTABLE
skill (real Python source) written to disk at runtime, then VALIDATE it by executing the generated
code and requiring a real referee PASS before it is banked.

INTEGRITY (the whole point): this module is solution-AGNOSTIC. It contains NO circuit-specific code —
no build_inverter, no hardcoded answer, no per-task branch. It mechanically serializes whatever
place/connect actions a trajectory recorded, abstracting:
  * each PLACED component  -> a fresh `env.place_component(<type>)` call bound to a local var
  * a pin on a placed part -> a component-relative f-string  (e.g. f"{n0}.a")
  * any other connector     -> a function PARAMETER (named, e.g. Input/Output) resolved to pixels at
                               RUN time, so the skill survives a layout shift (not a coordinate replay)
Feed it a different verified trajectory and it emits a different working skill. That is what makes the
result genuine synthesis rather than a retrieved macro.
"""
import os
import json
import importlib.util

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")
REGISTRY = os.path.join(SKILLS_DIR, "registry.json")


def _abstract(traj):
    """Trajectory -> (ordered params, placement body, rewritten connections). Pure serialization."""
    actions = traj["actions"]
    placements = [a for a in actions if a["op"] == "place"]
    connects = [a for a in actions if a["op"] == "connect" and a.get("ok", True)]

    var_of, body = {}, []
    for i, p in enumerate(placements):
        var = f"n{i}"
        var_of[p["bound"]] = var
        body.append((var, p["component"]))
    placed = set(var_of)

    params = []
    def endpoint(name):
        if "." in name:
            base, pin = name.split(".", 1)
            if base in placed:
                return ("rel", var_of[base], pin)        # component-relative -> f"{var}.pin"
        if name not in params:
            params.append(name)                          # external connector -> a parameter
        return ("param", name)

    conns = [(endpoint(c["source"]), endpoint(c["target"])) for c in connects]
    return params, body, conns


def _expr(e):
    return f'f"{{{e[1]}}}.{e[2]}"' if e[0] == "rel" else e[1]   # f"{n0}.a"   |   bare param identifier


def render(traj):
    """Render the generated skill module source. Returns (source_text, descriptor_dict)."""
    name = traj["task"]
    params, body, conns = _abstract(traj)
    sig = f"skill_{name}(env, " + ", ".join(params) + ")"
    desc = (f"Reproduces a referee-verified {name} solve: places {len(body)} component(s) and makes "
            f"{len(conns)} named connection(s). Parameterized by external connectors {params}.")
    descriptor = {"name": name, "params": params, "description": desc, "signature": sig}

    L = []
    L.append("# AUTO-GENERATED at runtime by operator/synth.py from a referee-verified trajectory.")
    L.append(f"# task: {name}  |  source_trajectory: trajectories/{name}.json")
    L.append("# This file did not exist before the verified solve — it IS the synthesized skill. Do not hand-edit.")
    L.append("DESCRIPTOR = " + json.dumps(descriptor, indent=4))
    L.append("")
    L.append("")
    L.append(f"def skill_{name}(" + ", ".join(["env"] + params) + "):")
    for var, comp in body:
        L.append(f"    {var} = env.place_component({json.dumps(comp)})")
    for s, t in conns:
        L.append(f"    env.connect_pins({_expr(s)}, {_expr(t)})")
    L.append("    return env.referee_check()")
    L.append("")
    return "\n".join(L), descriptor


def synthesize(traj, skills_dir=SKILLS_DIR):
    """Generate skill source from a VERIFIED trajectory and write it to disk at runtime. Returns the path."""
    if not (traj.get("passed") or traj.get("verdict") == "PASS"):
        raise ValueError("refusing to synthesize from an unverified trajectory")
    src, descriptor = render(traj)
    os.makedirs(skills_dir, exist_ok=True)
    path = os.path.join(skills_dir, f"skill_{traj['task']}.py")
    with open(path, "w") as f:
        f.write(src)
    return path


def load_skill(path):
    """Import a generated skill module from disk (it became real at runtime)."""
    modname = "genskill_" + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_skill(path, env, param_values=None):
    """Execute the generated skill against an env already at the right level. Returns the referee Verdict."""
    mod = load_skill(path)
    fn = getattr(mod, "skill_" + mod.DESCRIPTOR["name"])
    pv = param_values if param_values is not None else {p: p for p in mod.DESCRIPTOR["params"]}
    return fn(env, **pv)


def bank(traj, path, registry=REGISTRY):
    """Record a VALIDATED skill in the registry. Call ONLY after run_skill returned a real PASS."""
    mod = load_skill(path)
    d = mod.DESCRIPTOR
    os.makedirs(os.path.dirname(registry), exist_ok=True)
    reg = json.load(open(registry)) if os.path.exists(registry) else {}
    reg[d["name"]] = {
        "file": os.path.basename(path),
        "params": d["params"],
        "description": d["description"],
        "signature": d["signature"],
        "source": traj.get("source", "agent"),
        "source_trajectory": f"trajectories/{traj['task']}.json",
    }
    with open(registry, "w") as f:
        json.dump(reg, f, indent=2)
    return registry
