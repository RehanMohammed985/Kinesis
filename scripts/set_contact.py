"""Put a real phone number on one of Walter's contacts, for a live demo.
Writes data/profile.json (kept out of git), starting from the example profile.

python scripts/set_contact.py linda +19195551234
python scripts/set_contact.py linda +19195551234 --test     # also sends a test text and voice message now

--test needs a Mac signed in to Messages, and the app running (cd app, npm run dev)
for the voice message. The first time, macOS asks to let Terminal control
Messages: click OK.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REAL = ROOT / "data" / "profile.json"
EXAMPLE = ROOT / "kinesis" / "agent" / "profile.example.json"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    who, phone = args[0].lower(), args[1]
    p = json.loads((REAL if REAL.exists() else EXAMPLE).read_text())
    if who not in p["contacts"]:
        sys.exit(f"No contact '{who}'. Contacts: {', '.join(p['contacts'])}")
    p["contacts"][who]["phone"] = phone
    REAL.parent.mkdir(parents=True, exist_ok=True)
    REAL.write_text(json.dumps(p, indent=2) + "\n")
    print(f"{p['contacts'][who]['name']} now texts {phone} (saved in {REAL.relative_to(ROOT)}, not pushed to git)")
    if "--test" in sys.argv:
        os.environ["KINESIS_LIVE"], os.environ["KINESIS_BACKEND"] = "1", "mac"
        from kinesis.agent import channels
        c = p["contacts"][who]
        r1 = channels.send_text(c, "Test from Kinesis. Walter's messages will come from this number.")
        r2 = channels.send_voice(c, "Can you come here?")
        for r in (r1, r2):
            print(("sent " if r.get("ok") else "FAILED ") + r["kind"] + ("" if r.get("ok") else f": {r.get('error')}"))


if __name__ == "__main__":
    main()
