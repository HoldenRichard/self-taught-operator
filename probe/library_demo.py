# LIBRARY / RETRIEVAL demo: embed each banked verified skill's description (Voyage), then for a task
# query embed it and rank banked skills by similarity. Proves retrieval pulls the RIGHT skill.
# (Local-backed cosine here so it runs while Atlas connectivity is sorted — identical embeddings + logic;
#  flip library.sync_registry/retrieve on once Atlas is reachable.)
import sys
sys.path.insert(0, "/Users/holden/HackathonSF26/operator")
import library

print("=== sync banked skills -> store (one batched Voyage embed call) ===")
print("  ", library.sync_local())

QUERIES = [
    ("build a NOT gate that inverts its input", "INV"),
    ("construct a NAND gate out of relay components", "RELAY_NAND"),
]
print("\n=== RETRIEVAL (Voyage-embed the task query -> rank banked skills by similarity) ===")
ok = True
for q, expect in QUERIES:
    res = library.retrieve_local(q, k=2)
    top = res[0]["name"]
    verdict = "✓" if top == expect else f"✗ (expected {expect})"
    print(f"\nquery: {q!r}\n  -> TOP: {top} {verdict}")
    for r in res:
        print(f"     {r['score']:.4f}  {r['name']:12s} [{r['source']}] — {r['description'][:62]}")
    ok = ok and top == expect

print("\nRETRIEVAL", "WORKS ✓ — each task query pulled the right banked skill by similarity" if ok
      else "MISMATCH ✗")
