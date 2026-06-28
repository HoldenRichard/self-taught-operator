"""LIBRARY / RETRIEVAL gate for the self-taught operator.

On a referee-VERIFIED banked skill: embed its DESCRIPTION with Voyage and store
{descriptor, file, source, source_trajectory, verified_at, embedding} in MongoDB Atlas.
Retrieval: embed a task description, vector-similarity search Atlas, return the top-k banked skills.

Only skills present in operator/skills/registry.json (banked AFTER a real referee PASS) ever enter the
library — model refusals/errors never do (they were never banked). Secrets are read from the gitignored
.env at runtime; nothing is hardcoded.
"""
import os
import json
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # operator/ -> repo root


def load_env(path=None):
    path = path or os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for ln in open(path):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


load_env()

VOYAGE_MODEL = "voyage-3"          # 1024-dim (smoke-tested live)
EMBED_DIM = 1024
DB_NAME = "selftaught_operator"
COLL_NAME = "skills"
VEC_INDEX = "skill_vec"
REGISTRY = os.path.join(ROOT, "operator", "skills", "registry.json")


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


_last_embed = [0.0]
_MIN_GAP = float(os.environ.get("VOYAGE_MIN_GAP", "21"))   # free tier = 3 req/min -> keep >=20s between calls


def embed(texts, input_type="document"):
    """Voyage embeddings (BATCHED — pass a list to embed many in one call). input_type 'document' for
    stored skills, 'query' for task lookups (asymmetric). Self-throttles to the free-tier 3 req/min;
    add a Voyage payment method to lift it (the 200M free tokens still apply), then set VOYAGE_MIN_GAP=0."""
    import voyageai
    gap = _MIN_GAP - (time.time() - _last_embed[0])
    if gap > 0:
        time.sleep(gap)
    out = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"]).embed(
        list(texts), model=VOYAGE_MODEL, input_type=input_type).embeddings
    _last_embed[0] = time.time()
    return out


def _client():
    from pymongo import MongoClient
    return MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=20000)


def ensure_vector_index(coll):
    """Create the Atlas vectorSearch index on `embedding` if missing (idempotent)."""
    try:
        if VEC_INDEX in [ix["name"] for ix in coll.list_search_indexes()]:
            return "exists"
        coll.create_search_index({
            "name": VEC_INDEX, "type": "vectorSearch",
            "definition": {"fields": [{"type": "vector", "path": "embedding",
                                       "numDimensions": EMBED_DIM, "similarity": "cosine"}]}})
        return "created (building ~1 min; cosine fallback covers retrieval meanwhile)"
    except Exception as e:
        return f"index-skip ({type(e).__name__}: {str(e)[:60]})"


def add_skill(name, reg_entry, coll):
    """Embed a banked skill's DESCRIPTION and upsert its library record into Atlas."""
    desc = reg_entry["description"]
    vec = embed([desc], input_type="document")[0]
    coll.replace_one({"_id": name}, {
        "_id": name,
        "descriptor": {"name": name, "description": desc,
                       "params": reg_entry.get("params"), "signature": reg_entry.get("signature")},
        "file": reg_entry.get("file"),
        "source": reg_entry.get("source"),
        "source_trajectory": reg_entry.get("source_trajectory"),
        "verified_at": reg_entry.get("verified_at") or _now(),
        "embedding": vec,
    }, upsert=True)
    return name


def sync_registry(registry_path=REGISTRY):
    """Embed + store every banked (referee-verified) skill from the registry into Atlas (one batched embed)."""
    reg = json.load(open(registry_path))
    names = list(reg)
    vecs = embed([reg[n]["description"] for n in names], input_type="document")   # ONE batched call
    cli = _client()
    coll = cli[DB_NAME][COLL_NAME]
    for n, v in zip(names, vecs):                # upsert docs FIRST so the collection exists ...
        e = reg[n]
        coll.replace_one({"_id": n}, {
            "_id": n,
            "descriptor": {"name": n, "description": e["description"],
                           "params": e.get("params"), "signature": e.get("signature")},
            "file": e.get("file"), "source": e.get("source"),
            "source_trajectory": e.get("source_trajectory"),
            "verified_at": e.get("verified_at") or _now(), "embedding": v}, upsert=True)
    idx = ensure_vector_index(coll)              # ... THEN create the vectorSearch index on it
    count = coll.count_documents({})
    cli.close()
    return {"index": idx, "added": names, "library_size": count}


def retrieve(task_description, k=3):
    """Embed a task description, vector-search Atlas, return the top-k banked skills by similarity."""
    qv = embed([task_description], input_type="query")[0]
    cli = _client()
    coll = cli[DB_NAME][COLL_NAME]
    results = None
    try:
        results = list(coll.aggregate([
            {"$vectorSearch": {"index": VEC_INDEX, "path": "embedding",
                               "queryVector": qv, "numCandidates": 50, "limit": k}},
            {"$project": {"_id": 0, "name": "$descriptor.name", "description": "$descriptor.description",
                          "source": 1, "file": 1, "score": {"$meta": "vectorSearchScore"}}}]))
        for r in results:
            r["via"] = "atlas-vectorSearch"
    except Exception:
        results = None
    if not results:                                   # index still building, or unavailable -> cosine
        import math
        docs = list(coll.find({}, {"descriptor": 1, "source": 1, "file": 1, "embedding": 1}))
        def cos(a, b):
            dot = sum(x * y for x, y in zip(a, b)); na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
            return dot / (na * nb) if na and nb else 0.0
        results = sorted(
            ({"name": d["descriptor"]["name"], "description": d["descriptor"]["description"],
              "source": d.get("source"), "file": d.get("file"),
              "score": round(cos(qv, d["embedding"]), 4), "via": "cosine-fallback"} for d in docs),
            key=lambda r: -r["score"])[:k]
    cli.close()
    return results


# ---- LOCAL-backed mirror (same Voyage embeddings + descriptors; a JSON store + cosine) ----
# Used to demonstrate the retrieval LOGIC while Atlas connectivity is sorted. Flip to the Atlas
# functions above (sync_registry / retrieve) once the cluster's primary is reachable — same data shape.
LOCAL_STORE = os.path.join(ROOT, "operator", "skills", "library_local.json")


def _cos(a, b):
    import math
    dot = sum(x * y for x, y in zip(a, b)); na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def sync_local(registry_path=REGISTRY, store=LOCAL_STORE):
    reg = json.load(open(registry_path))
    names = list(reg)
    vecs = embed([reg[n]["description"] for n in names], input_type="document")   # ONE batched call
    recs = [{"name": n, "description": reg[n]["description"], "params": reg[n].get("params"),
             "signature": reg[n].get("signature"), "file": reg[n].get("file"), "source": reg[n].get("source"),
             "source_trajectory": reg[n].get("source_trajectory"),
             "verified_at": reg[n].get("verified_at") or _now(), "embedding": v}
            for n, v in zip(names, vecs)]
    json.dump(recs, open(store, "w"))
    return {"library_size": len(recs), "store": store}


def retrieve_local(task_description, k=3, store=LOCAL_STORE):
    qv = embed([task_description], input_type="query")[0]
    recs = json.load(open(store))
    return sorted(({"name": r["name"], "description": r["description"], "source": r.get("source"),
                    "file": r.get("file"), "score": round(_cos(qv, r["embedding"]), 4), "via": "local-cosine"}
                   for r in recs), key=lambda r: -r["score"])[:k]


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    backend_local = args and args[0] == "local"
    if backend_local:
        args = args[1:]
    _sync, _retrieve = (sync_local, retrieve_local) if backend_local else (sync_registry, retrieve)
    if args and args[0] == "sync":
        print("sync:", json.dumps(_sync(), indent=2))
    else:
        q = " ".join(args) or "build a NOT gate that inverts its input"
        print(f"query: {q!r}")
        for r in _retrieve(q):
            print(f"  {r.get('score')}  {r['name']:12s} [{r.get('source')}] via {r.get('via')} — {r['description'][:70]}")
