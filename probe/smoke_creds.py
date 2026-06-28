# SMOKE-TEST both credentials live BEFORE building the library gate:
#   (1) Voyage: one embedding call returns a vector.
#   (2) Atlas: connect + write + read + delete round-trips (the %24 password-encoding is the known trap).
# Reads creds from gitignored .env; never prints the secrets.
import os

ROOT = "/Users/holden/HackathonSF26"
for ln in open(os.path.join(ROOT, ".env")):
    ln = ln.strip()
    if ln and not ln.startswith("#") and "=" in ln:
        k, v = ln.split("=", 1); os.environ.setdefault(k.strip(), v.strip())

print("=== (1) VOYAGE ===")
try:
    import voyageai
    r = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"]).embed(
        ["inverter: NOT(x) = nand(x, x)"], model="voyage-3", input_type="document")
    vec = r.embeddings[0]
    print(f"  VOYAGE OK — dim={len(vec)}  first3={[round(x,4) for x in vec[:3]]}")
except Exception as e:
    print("  VOYAGE FAIL —", type(e).__name__, str(e)[:140])

print("=== (2) ATLAS ===")
try:
    from pymongo import MongoClient
    cli = MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=15000)
    cli.admin.command("ping")
    coll = cli["selftaught_operator"]["_smoke"]
    coll.delete_many({"_id": "smoke"})
    coll.insert_one({"_id": "smoke", "msg": "round-trip", "n": 42})
    got = coll.find_one({"_id": "smoke"})
    coll.delete_many({"_id": "smoke"})
    cli.close()
    print(f"  ATLAS OK — connect+write+read+delete round-trip; read back: {got}")
except Exception as e:
    print("  ATLAS FAIL —", type(e).__name__, str(e)[:200])
