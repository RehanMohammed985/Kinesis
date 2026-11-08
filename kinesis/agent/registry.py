"""The action registry: the only things Kinesis can do in the world.
The app asks for actions; tasks are built from them; the monitor uses `alert`.
Confirmation for risky actions happens in the app (the lens starts on Cancel);
the registry trusts that a request reaching it was chosen by the person."""
import os

from kinesis.agent import channels
from kinesis.agent.profile import contact


class Registry:
    def __init__(self, profile, emit):
        self.p = profile
        self.emit = emit
        self.count = {}

    def _tick(self, name):
        self.count[name] = self.count.get(name, 0) + 1

    def execute(self, a):
        kind = a.get("action")
        self._tick(kind)
        p = self.p
        if kind == "speak":
            return {"ok": True}  # the app plays it in the person's own voice
        if kind == "message":
            c = contact(p, a["contact"])
            res = channels.send_text(c, a["text"])
            if a.get("voice"):  # the same words as a voice message, in the person's own voice
                channels.send_voice(c, a["text"])
            return res
        if kind == "call":
            c = contact(p, a["contact"])
            return channels.place_call(c, say=f"{p['name']} is calling you through Kinesis and will reply with a computer voice.")
        if kind == "call_number":
            return channels.place_call({"name": a.get("name", "Number"), "phone": a.get("phone")}, say=a.get("say"))
        if kind == "help":
            res = [channels.send_text(contact(p, c), f"{p['name']} needs help now. (Kinesis)") for c in p["care_list"]]
            return {"ok": all(r.get("ok") for r in res), "mode": res[0]["mode"] if res else "dry"}
        if kind == "help_clear":
            for c in p["care_list"]:
                channels.send_text(contact(p, c), f"{p['name']} is okay now. (Kinesis)")
            return {"ok": True}
        if kind == "alert":
            # Automatic safety alerts. Only sent if the person turned them on
            # in their profile; everything else needs their selection.
            if not p.get("safety_alerts", {}).get(a.get("kind")):
                return {"ok": True, "skipped": "safety alert not enabled in profile"}
            res = [channels.send_text(contact(p, c), a["text"]) for c in p["care_list"]]
            return {"ok": all(r.get("ok") for r in res)}
        if kind == "media":
            return self._media(a.get("command"))
        if kind in ("hangup", "answer"):
            return {"ok": True}
        return {"ok": False, "error": f"unknown action {kind}"}

    def _media(self, command):
        # Optional: press keys on this computer for the e-reader or music app.
        if os.environ.get("KINESIS_KEYS") != "1":
            return {"ok": True, "mode": "dry"}
        import pyautogui

        keys = {"page_next": "right", "page_prev": "left", "play": "space", "pause": "space"}
        if command in keys:
            pyautogui.press(keys[command])
        return {"ok": True}
