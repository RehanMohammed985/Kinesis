"""First-pass live detectors. Simple, explainable, tuned at runtime from a rest
baseline. The signal-processing team should replace these piece by piece; the
interface (update() -> levels, events) is what the server relies on.

Montage (docs/HARDWARE.md): 1 Oz, 2 O1, 3 O2, 4 POz, 5 Fp1, 6 T7. 125 Hz.
"""
import time

import numpy as np
from scipy.signal import butter, sosfiltfilt

FS = 125
CH_ALPHA = [1, 2, 3]
CH_BLINK = 5
CH_CLENCH = 6

SOS = {
    "clench": butter(4, [20, 55], btype="band", fs=FS, output="sos"),
    "blink": butter(2, [0.5, 10], btype="band", fs=FS, output="sos"),
    "alpha": butter(4, [8, 12], btype="band", fs=FS, output="sos"),
    "eeg": butter(2, [1, 40], btype="band", fs=FS, output="sos"),
    "line": butter(4, [45, 60], btype="band", fs=FS, output="sos"),
}

# How far above the rest baseline each input must go to fire.
CLENCH_K = 5.0      # band power ratio
BLINK_MIN_UV = 80.0  # absolute floor for a blink peak
BLINK_K = 6.0       # x robust rest std
ALPHA_K = 2.0       # alpha power ratio, eyes closed vs open
DOUBLE_BLINK_S = 0.6
ALPHA_HOLD_S = 1.0


def _row(eeg, ch):
    return eeg[ch - 1]


def _f(name, x):
    return sosfiltfilt(SOS[name], x, padlen=min(len(x) - 1, 3 * 9))


class Detectors:
    def __init__(self):
        self.base = None
        self.clench_armed = True
        self.blink_armed = True
        self.last_blink = 0.0
        self.alpha_since = 0.0
        self.alpha_fired = False

    # ---------- baseline ----------
    def calibrate_rest(self, eeg):
        """eeg: channels x samples, at least 4 s of the person sitting still, eyes open."""
        win = int(0.4 * FS)
        cl = _f("clench", _row(eeg, CH_CLENCH))
        powers = [np.mean(cl[i:i + win] ** 2) for i in range(0, len(cl) - win, win // 2)]
        bl = _f("blink", _row(eeg, CH_BLINK))
        mad = np.median(np.abs(bl - np.median(bl))) * 1.4826
        al = np.mean([np.mean(_f("alpha", _row(eeg, c)) ** 2) for c in CH_ALPHA])
        self.base = {
            "clench": max(np.median(powers), 1e-6),
            "blink_thr": max(BLINK_MIN_UV, BLINK_K * mad),
            "alpha": max(al, 1e-6),
        }
        return self.base

    # ---------- per update (call ~20x a second with the last 1.2 s) ----------
    def update(self, eeg, now=None):
        now = now or time.time()
        if self.base is None:
            return {"clench": 0, "blink": 0, "alpha": 0}, []
        events = []

        cl = _f("clench", _row(eeg, CH_CLENCH))[-int(0.4 * FS):]
        clench = float(np.mean(cl ** 2) / (self.base["clench"] * CLENCH_K))
        if clench >= 1 and self.clench_armed:
            self.clench_armed = False
            events.append({"type": "event", "input": "clench"})
        if clench < 0.45:
            self.clench_armed = True

        bl = _f("blink", _row(eeg, CH_BLINK))[-int(0.25 * FS):]
        blink = float(np.max(np.abs(bl)) / self.base["blink_thr"])
        if blink >= 1 and self.blink_armed:
            self.blink_armed = False
            gap = now - self.last_blink
            if 0.12 < gap < DOUBLE_BLINK_S:
                events.append({"type": "event", "input": "blink2"})
                self.last_blink = 0.0
            else:
                self.last_blink = now
        if blink < 0.5:
            self.blink_armed = True

        n = int(1.0 * FS)
        al = np.mean([np.mean(_f("alpha", _row(eeg, c)[-n:]) ** 2) for c in CH_ALPHA])
        alpha = float(al / (self.base["alpha"] * ALPHA_K))
        if alpha >= 1:
            if not self.alpha_since:
                self.alpha_since = now
            if not self.alpha_fired and now - self.alpha_since >= ALPHA_HOLD_S:
                self.alpha_fired = True
                events.append({"type": "event", "input": "alpha"})
        else:
            self.alpha_since = 0.0
            self.alpha_fired = False

        return {"clench": round(clench, 3), "blink": round(blink, 3), "alpha": round(alpha, 3)}, events


SITES = {1: "Oz", 2: "O1", 3: "O2", 4: "POz", 5: "Fp1", 6: "T7"}
PROMPTS = {
    "flat": "Not touching skin. Wiggle it into the hair and screw it down a little.",
    "railed": "Pressed too hard, or pasted at full gain. Back it off a quarter turn.",
    "noise": "Picking up noise. Check the ear clip and unplug the laptop charger.",
}


def quality(eeg, gain=12):
    """Per-channel contact check over the last ~2 s of raw microvolts."""
    full_scale = 4190.0 * 12 / gain  # uV
    out = []
    for ch, site in SITES.items():
        x = _row(eeg, ch)
        x = x - np.mean(x)
        std = float(np.std(x))
        if std < 0.5:
            reason = "flat"
        elif np.max(np.abs(x)) > 0.95 * full_scale:
            reason = "railed"
        else:
            sig = np.mean(_f("eeg", x) ** 2)
            hum = np.mean(_f("line", x) ** 2)
            reason = "noise" if hum > 0.6 * sig else "ok"
        state = {"ok": "good", "noise": "fair"}.get(reason, "bad")
        item = {"ch": ch, "site": site, "state": state, "reason": reason, "std_uv": round(std, 1)}
        if reason in PROMPTS:
            item["prompt"] = PROMPTS[reason]
        out.append(item)
    return out
