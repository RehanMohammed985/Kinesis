"""How messages and calls actually leave the device.

Safe by default: nothing is sent unless KINESIS_LIVE=1. Otherwise every send is
written to data/logs/outbox.jsonl and printed, so the demo shows exactly what
would have gone out.

Backends (KINESIS_BACKEND):
  dry     log only (default)
  mac     iMessage through the Messages app; calls through the iPhone
          (Continuity) or FaceTime audio. Run the core on a Mac signed into
          the user's Apple ID.
  twilio  SMS, and voice calls that speak a message. Needs TWILIO_ACCOUNT_SID,
          TWILIO_AUTH_TOKEN, TWILIO_FROM.
"""
import json
import os
import subprocess
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "data" / "logs" / "outbox.jsonl"


def _log(entry):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"at": time.time(), **entry}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[{entry['mode']}] {entry['kind']} -> {entry.get('to')}: {entry.get('text', '')}")
    return entry


def live():
    return os.environ.get("KINESIS_LIVE") == "1"


def backend():
    return os.environ.get("KINESIS_BACKEND", "dry") if live() else "dry"


# ---------- mac ----------
def _osascript(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())


def _mac_text(phone, text):
    safe = text.replace("\\", "\\\\").replace('"', '\\"')
    _osascript(
        'tell application "Messages"\n'
        "  set svc to 1st account whose service type = iMessage\n"
        f'  send "{safe}" to participant "{phone}" of svc\n'
        "end tell"
    )


def _mac_call(phone):
    subprocess.run(["open", f"tel://{phone}"], check=True)


# ---------- twilio ----------
def _twilio(path, data):
    sid = os.environ["TWILIO_ACCOUNT_SID"]
    r = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/{path}.json",
        data=data, auth=(sid, os.environ["TWILIO_AUTH_TOKEN"]), timeout=15,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Twilio {r.status_code}: {r.text[:200]}")
    return r.json()


def _twilio_text(phone, text):
    _twilio("Messages", {"To": phone, "From": os.environ["TWILIO_FROM"], "Body": text})


def _twilio_call(phone, say):
    twiml = f"<Response><Say>{say}</Say><Pause length=\"2\"/><Say>{say}</Say></Response>"
    _twilio("Calls", {"To": phone, "From": os.environ["TWILIO_FROM"], "Twiml": twiml})


# ---------- public ----------
def send_text(contact, text):
    b = backend()
    try:
        if b == "mac":
            _mac_text(contact["phone"], text)
        elif b == "twilio":
            _twilio_text(contact["phone"], text)
        return _log({"mode": b, "kind": "text", "to": contact["name"], "phone": contact.get("phone"), "text": text, "ok": True})
    except Exception as e:  # noqa: BLE001
        return _log({"mode": b, "kind": "text", "to": contact["name"], "text": text, "ok": False, "error": str(e)})


def place_call(contact, say=None):
    """mac: rings the contact through the user's phone; the app speaks replies
    out loud during the call. twilio: calls and speaks `say`.
    Calls stay in practice mode unless KINESIS_LIVE_CALLS=1 too, so texts can
    go out for real on stage without a call window popping up."""
    b = backend()
    if b != "dry" and os.environ.get("KINESIS_LIVE_CALLS") != "1":
        b = "dry"
    try:
        if b == "mac":
            _mac_call(contact["phone"])
        elif b == "twilio":
            _twilio_call(contact["phone"], say or "This is a call from Kinesis.")
        return _log({"mode": b, "kind": "call", "to": contact["name"], "phone": contact.get("phone"), "text": say or "", "ok": True})
    except Exception as e:  # noqa: BLE001
        return _log({"mode": b, "kind": "call", "to": contact["name"], "ok": False, "error": str(e)})


def _voice_file(text):
    """The phrase in the person's own voice (ElevenLabs), from the app's dev
    server, which caches every phrase. Saved where Messages can attach it."""
    app = os.environ.get("KINESIS_APP", "http://localhost:5173")
    r = requests.post(f"{app}/api/speak", json={"text": text}, timeout=30)
    if r.status_code >= 300 or not r.headers.get("Content-Type", "").startswith("audio"):
        raise RuntimeError(f"voice not available ({r.status_code}); is the app running with an ElevenLabs key?")
    folder = Path.home() / "Pictures" / "Kinesis"   # Messages attaches files from here reliably
    folder.mkdir(parents=True, exist_ok=True)
    name = "".join(ch for ch in text.lower() if ch.isalnum() or ch == " ").strip().replace(" ", "-")[:40] or "message"
    path = folder / f"{name}.mp3"
    path.write_bytes(r.content)
    return path


def _mac_file(phone, path):
    _osascript(
        'tell application "Messages"\n'
        "  set svc to 1st account whose service type = iMessage\n"
        f'  send (POSIX file "{path}") to participant "{phone}" of svc\n'
        "end tell"
    )


def send_voice(contact, text):
    """The words as a voice message in the person's own voice. Mac: an audio
    attachment in Messages. Practice mode and Twilio: logged."""
    b = backend()
    try:
        if b == "mac":
            _mac_file(contact["phone"], _voice_file(text))
        return _log({"mode": b if b == "mac" else "dry", "kind": "voice", "to": contact["name"], "phone": contact.get("phone"), "text": text, "ok": True})
    except Exception as e:  # noqa: BLE001
        return _log({"mode": b, "kind": "voice", "to": contact["name"], "text": text, "ok": False, "error": str(e)})


def send_file(contact, path, text):
    """Reports: texted as a short summary plus where the full report lives.
    A real deployment would upload to the patient portal."""
    return send_text(contact, f"{text} Full report: {Path(path).name}")
