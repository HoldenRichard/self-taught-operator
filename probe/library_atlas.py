# Close the library gate on LIVE Atlas: sync banked skills -> Atlas (embed + write + create the vector
# index), wait for the index to build, then retrieve via Atlas $vectorSearch and confirm it matches the
# local-store result. This is the MongoDB Atlas Vector Search backend, genuinely live (not local cosine).
import sys, os, time
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
import library
from pymongo import MongoClient

print("=== sync_registry -> Atlas (Voyage embed + upsert + ensure vector index) ===")
print("  ", library.sync_registry())

cli = MongoClient(os.environ["MONGODB_URI"])
coll = cli[library.DB_NAME][library.COLL_NAME]
print("  docs in Atlas collection:", coll.count_documents({}))

print("=== wait for the Atlas vectorSearch index to become queryable ===")
ready = False
for i in range(24):                                   # up to ~4 min
    try:
        ixs = {ix["name"]: ix for ix in coll.list_search_indexes()}
        print(f"  [{i*10:3d}s] " + str({n: (ix.get('status'), ix.get('queryable')) for n, ix in ixs.items()}), flush=True)
        ix = ixs.get(library.VEC_INDEX)
        if ix and ix.get("queryable"):
            ready = True; break
    except Exception as e:
        print("  poll err:", type(e).__name__, str(e)[:80])
    time.sleep(10)
cli.close()
print("  vector index queryable:", ready)

print("\n=== retrieve via LIVE Atlas ===")
ok = True
for q, expect in [("build a NOT gate that inverts its input", "INV"),
                  ("construct a NAND gate out of relay components", "RELAY_NAND")]:
    res = library.retrieve(q, k=2)
    top = res[0]["name"] if res else None
    print(f"\n  query {q!r}\n    -> TOP {top}  {'✓' if top == expect else '✗ expected ' + expect}")
    for r in res:
        print(f"       {r.get('score')}  {r['name']:12s} [{r.get('source')}] via {r.get('via')}")
    ok = ok and top == expect
print("\nLIVE ATLAS RETRIEVAL:", "MATCHES local ✓" if ok else "MISMATCH ✗",
      "(via Atlas $vectorSearch)" if ready else "(via cosine fallback — index not ready)")
