"""Set up the user's own voice on ElevenLabs. Run it yourself; nothing here
runs on its own.

python scripts/setup_voice.py check
    Shows the credits left and the voices on the account.
python scripts/setup_voice.py clone "Walter" sample1.m4a sample2.m4a
    Instant voice clone from 1 to 3 minutes of clean speech (one speaker, no
    music). Only clone a voice with that person's permission. Saves the new
    voice id into app/.env.
python scripts/setup_voice.py use VOICE_ID
    Use an existing voice (for example a stock one for a quick demo).

Then, with the app running (cd app, npm run dev):
    curl -X POST http://localhost:5173/api/prewarm
voices every fixed phrase once, so the demo plays instantly and offline.
Reads ELEVENLABS_API_KEY from app/.env or the environment.
"""
import os
import re
import sys
from pathlib import Path

import requests

ENV = Path(__file__).resolve().parents[1] / "app" / ".env"
API = "https://api.elevenlabs.io/v1"


def key():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"]
    if ENV.exists():
        m = re.search(r"^ELEVENLABS_API_KEY=(.+)$", ENV.read_text(), re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    sys.exit("Put ELEVENLABS_API_KEY=... in app/.env first (copy app/.env.example).")


def save_voice(voice_id):
    text = ENV.read_text() if ENV.exists() else ""
    if re.search(r"^ELEVENLABS_VOICE_ID=.*$", text, re.M):
        text = re.sub(r"^ELEVENLABS_VOICE_ID=.*$", f"ELEVENLABS_VOICE_ID={voice_id}", text, flags=re.M)
    else:
        text += f"\nELEVENLABS_VOICE_ID={voice_id}\n"
    ENV.write_text(text)
    print(f"Saved ELEVENLABS_VOICE_ID={voice_id} to {ENV}. Restart the app (npm run dev) to use it.")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("check", "clone", "use"):
        sys.exit(__doc__)
    h = {"xi-api-key": key()}
    cmd = sys.argv[1]
    if cmd == "check":
        s = requests.get(f"{API}/user/subscription", headers=h, timeout=20)
        s.raise_for_status()
        s = s.json()
        print(f"Plan {s.get('tier')}: {s.get('character_count')} of {s.get('character_limit')} credits used")
        v = requests.get(f"{API}/voices", headers=h, timeout=20)
        v.raise_for_status()
        for x in v.json().get("voices", []):
            print(f"  {x['voice_id']}  {x['name']}  ({x.get('category')})")
    elif cmd == "clone":
        if len(sys.argv) < 4:
            sys.exit('usage: setup_voice.py clone "Name" sample1.m4a [sample2.m4a ...]')
        files = [("files", (Path(p).name, open(p, "rb"))) for p in sys.argv[3:]]
        r = requests.post(f"{API}/voices/add", headers=h, timeout=120,
                          data={"name": sys.argv[2], "remove_background_noise": "true",
                                "description": "Kinesis user voice"}, files=files)
        if r.status_code >= 300:
            sys.exit(f"ElevenLabs {r.status_code}: {r.text[:300]}")
        save_voice(r.json()["voice_id"])
    else:
        save_voice(sys.argv[2])


if __name__ == "__main__":
    main()
