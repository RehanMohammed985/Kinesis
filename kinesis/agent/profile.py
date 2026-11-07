"""The person's profile: name, contacts, care list, doctor, pharmacy, consent
for safety alerts. Real values live in data/profile.json (gitignored, it has
phone numbers). profile.example.json is the template."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REAL = ROOT / "data" / "profile.json"
EXAMPLE = Path(__file__).with_name("profile.example.json")


def load():
    path = REAL if REAL.exists() else EXAMPLE
    with open(path) as f:
        p = json.load(f)
    p["_source"] = str(path.relative_to(ROOT))
    return p


def contact(profile, cid):
    c = profile["contacts"].get(cid)
    if not c:
        raise KeyError(f"No contact '{cid}' in {profile['_source']}")
    return {"id": cid, **c}
