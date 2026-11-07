"""Monitor agent. Runs in the background on every window of live signal:
- seizure-like activity: alert caregivers (if the person turned that on)
- slowing (delta/alpha ratio) and left/right asymmetry vs the person's baseline
- rest periods with eyes closed and the resting alpha peak frequency
- signal quality and usage
Everything is logged to data/logs/<date>.jsonl for the daily report.
Never logs or reports a mood or a diagnosis."""
import json
import time
from pathlib import Path

import numpy as np

from kinesis.agent import brain

ROOT = Path(__file__).resolve().parents[2]
SEIZURE_CHANNELS = [1, 2, 3, 4, 6]  # Oz O1 O2 POz T7 (Fp1 left out: blinks)
OCC = [1, 2, 3]
O1, O2 = 2, 3


class DayLog:
    def __init__(self, root=ROOT / "data" / "logs"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, day=None):
        return self.root / f"{day or time.strftime('%Y-%m-%d')}.jsonl"

    def write(self, kind, **data):
        entry = {"t": time.time(), "kind": kind, **data}
        with open(self.path(), "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def read(self, day=None):
        p = self.path(day)
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def _row(eeg, ch):
    return eeg[ch - 1]


class Monitor:
    def __init__(self, profile, registry, emit, log=None, fs=brain.FS):
        self.p = profile
        self.registry = registry
        self.emit = emit
        self.log = log or DayLog()
        self.fs = fs
        self.base = None
        self.last_event = 0.0
        self.run = 0
        self.quiet = 0
        self.episode = None
        self.bad_channels = set()
        self.minute = {"start": time.time(), "dar_o1": [], "dar_o2": [], "bsi": [], "q_good": 0, "q_total": 0}
        self.slow_minutes = 0
        self.rest_since = 0.0
        self.rest_peaks = []

    # ---------- inputs from the core ----------
    def set_baseline(self, eeg):
        """eeg: channels x samples of the person sitting still, eyes open (>= 4 s)."""
        n = 4 * self.fs
        seg = eeg[:, -n:]
        base = {}
        for ch in SEIZURE_CHANNELS:
            f = brain.window_features(_row(seg, ch), self.fs)
            base[ch] = {"line_length": f["line_length"], "rms": f["rms"]}
        base["dar_o1"] = brain.window_features(_row(seg, O1), self.fs)["dar"]
        base["dar_o2"] = brain.window_features(_row(seg, O2), self.fs)["dar"]
        base["bsi"] = brain.symmetry_index(_row(seg, O1), _row(seg, O2), self.fs)
        self.base = base
        self.log.write("baseline", dar_o1=round(base["dar_o1"], 3), dar_o2=round(base["dar_o2"], 3), bsi=round(base["bsi"], 3))

    def note_event(self, inp):
        self.last_event = time.time()
        self.log.write("event", input=inp)

    def note_quality(self, channels):
        self.bad_channels = {c["ch"] for c in channels if c["state"] == "bad"}
        self.minute["q_total"] += 1
        self.minute["q_good"] += int(not self.bad_channels)

    # ---------- every 2 s with the last 4 s ----------
    def feed(self, eeg, levels):
        if self.base is None:
            return
        now = time.time()
        self._rest(eeg, levels, now)
        # Seizure check runs on every window: a real seizure can produce
        # blink-like and muscle artifacts, so skipping those windows would hide
        # it. The muscle-ratio test inside seizure_like() rejects jaw clenches.
        self._seizure(eeg, now)
        # Slowing is a slow trend; skip windows around deliberate movements.
        deliberate = now - self.last_event < 3 or levels.get("clench", 0) > 0.5 or levels.get("blink", 0) > 0.8
        if not deliberate:
            self._slowing(eeg)
        if now - self.minute["start"] >= 60:
            self._close_minute(now)

    def _seizure(self, eeg, now):
        hits, detail = [], {}
        for ch in SEIZURE_CHANNELS:
            if ch in self.bad_channels:
                continue
            f = brain.window_features(_row(eeg, ch), self.fs)
            hit, ratios = brain.seizure_like(f, self.base[ch])
            if hit:
                hits.append(ch)
                detail[ch] = {**ratios, "peak_hz": round(f["peak_hz"], 1)}
        if len(hits) >= 2:
            self.run += 1
            self.quiet = 0
        else:
            self.run = 0
            self.quiet += 1
        if self.run >= brain.SEIZURE_RUN and not self.episode:
            self.episode = {"start": now - 2 * (self.run - 1) - 4, "channels": hits, "detail": detail}
            when = time.strftime("%I:%M %p", time.localtime()).lstrip("0").lower()
            text = f"Kinesis detected seizure-like brain activity on {self.p['name']} at {when}. Please check on them now."
            self.registry.execute({"action": "alert", "kind": "seizure_like", "text": text})
            self.log.write("alert", alert="seizure_like", text=text)
            self.emit({"type": "alert", "kind": "seizure_like", "text": text})
        if self.episode and self.quiet >= 3:
            ep = self.episode
            dur = round(now - ep["start"] - 6, 1)
            self.log.write("seizure_like", start=ep["start"], duration_s=dur, channels=ep["channels"], detail=ep["detail"])
            self.emit({"type": "notice", "text": f"Seizure-like activity ended after about {int(dur)} seconds. Logged for your doctor."})
            self.episode = None

    def _slowing(self, eeg):
        for ch, key in ((O1, "dar_o1"), (O2, "dar_o2")):
            if ch not in self.bad_channels:
                self.minute[key].append(brain.window_features(_row(eeg, ch), self.fs)["dar"])
        if O1 not in self.bad_channels and O2 not in self.bad_channels:
            self.minute["bsi"].append(brain.symmetry_index(_row(eeg, O1), _row(eeg, O2), self.fs))

    def _rest(self, eeg, levels, now):
        if levels.get("alpha", 0) >= 1:
            if not self.rest_since:
                self.rest_since = now
                self.rest_peaks = []
            self.rest_peaks.append(brain.alpha_peak([_row(eeg, c) for c in OCC], self.fs))
        elif self.rest_since:
            dur = now - self.rest_since
            if dur >= 10:
                self.log.write("rest", start=self.rest_since, duration_s=round(dur, 1),
                               alpha_peak_hz=round(float(np.median(self.rest_peaks)), 2))
            self.rest_since = 0.0

    def _close_minute(self, now):
        m = self.minute
        med = lambda xs: round(float(np.median(xs)), 3) if xs else None  # noqa: E731
        rec = {"dar_o1": med(m["dar_o1"]), "dar_o2": med(m["dar_o2"]), "bsi": med(m["bsi"]),
               "quality": round(m["q_good"] / m["q_total"], 2) if m["q_total"] else None}
        self.log.write("minute", **rec)
        # A sharp, sustained change vs the person's own baseline is worth a call.
        b = self.base
        dar = np.nanmean([x for x in (rec["dar_o1"], rec["dar_o2"]) if x is not None]) if (rec["dar_o1"] or rec["dar_o2"]) else None
        base_dar = (b["dar_o1"] + b["dar_o2"]) / 2
        changed = (dar is not None and dar > 2.0 * base_dar) or (rec["bsi"] is not None and rec["bsi"] > b["bsi"] + 0.15)
        self.slow_minutes = self.slow_minutes + 1 if changed else 0
        if self.slow_minutes == 5:
            text = (f"Kinesis noticed {self.p['name']}'s brain rhythm slowed or became uneven between sides "
                    "for 5 minutes compared with their usual. This is not a diagnosis. If anything else seems wrong, "
                    "such as new weakness, a drooping face, or trouble understanding, call 911.")
            self.log.write("alert", alert="slowing_change", text=text)
            self.registry.execute({"action": "alert", "kind": "slowing_change", "text": text})
            self.emit({"type": "notice", "text": "Your brain rhythm changed from your usual for 5 minutes. Logged for your doctor."})
        self.minute = {"start": now, "dar_o1": [], "dar_o2": [], "bsi": [], "q_good": 0, "q_total": 0}
