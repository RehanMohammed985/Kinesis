"""Live detectors, tuned on our baseline recordings (nodes branch,
kinesis/data/raw/baseline_trial1-3: eyes open 5 s, closed 15 s, open 15 s,
jaw clenches, rest). See scripts/evaluate_baseline.py for the numbers.

Montage (docs/HARDWARE.md): 1 Oz, 2 O1, 3 O2, 4 POz, 5 Fp1, 6 T7. 125 Hz.

What the recordings taught us:
- Jaw clench shows up strongest on O2, POz and Fp1, not only T7 (the clench
  tightens scalp and neck muscles), so clench uses the median across O2, POz,
  Fp1, T7. Median means one floating electrode cannot fake or hide it.
- Clenches either release fully (dips to ~1x rest) or partly (dips to 3-5x),
  so re-arming is relative to the peak, not a fixed floor.
- Clenches throw big spikes onto Fp1, so blinks are ignored while clenching.
- Eyes-closed alpha was weak with this fit; alpha uses the median across the
  occipital channels and is ignored while clenching.

These rules are the fallback. On our double-blink recordings they missed
every double blink, so clench and double blink now come from each person's
learned model (learned.py); eyes closed still comes from here.
"""
import time

import numpy as np
from scipy.signal import butter, sosfiltfilt

FS = 125
CH_CLENCH = [3, 4, 5, 6]  # O2, POz, Fp1, T7
CH_ALPHA = [1, 2, 3, 4]   # Oz, O1, O2, POz
CH_BLINK = 5              # Fp1

SOS = {
    "muscle": butter(4, [20, 55], btype="band", fs=FS, output="sos"),
    "blink": butter(2, [0.5, 10], btype="band", fs=FS, output="sos"),
    "alpha": butter(4, [8, 12], btype="band", fs=FS, output="sos"),
    "eeg": butter(2, [1, 40], btype="band", fs=FS, output="sos"),
    "line": butter(4, [45, 60], btype="band", fs=FS, output="sos"),
}

# Clench: on our 3 trials, 44 events for 43 clear clenches, 0 false triggers at rest.
CLENCH_FIRE = 8.0          # x rest muscle power (median across CH_CLENCH)
CLENCH_REARM_ABS = 2.5
CLENCH_REARM_REL = 0.35    # re-arm once below 35% of the peak just reached
CLENCH_GAP_S = 0.6
MUSCLE_VETO = 3.0          # above this, blinks and alpha are ignored

BLINK_K = 15.0             # x robust rest spread on Fp1; 0 false double blinks on our 3 trials
BLINK_MIN = 80.0           # floor, in the recording's units
BLINK_WIDTH_S = (0.04, 0.45)
DOUBLE_BLINK_S = (0.2, 0.7)

# Eyes-closed alpha was weak with our first fit (at most 2x). At 2.5x held
# 1.5 s it never misfires; it starts working once the occipital contact is good.
ALPHA_K = 2.5
ALPHA_HOLD_S = 1.5


def _row(eeg, ch):
    return eeg[ch - 1]


def _f(name, x):
    return sosfiltfilt(SOS[name], x, padlen=min(len(x) - 1, 27))


def _muscle_powers(eeg, win_s=0.4):
    n = int(win_s * FS)
    return np.array([np.mean(_f("muscle", _row(eeg, c))[-n:] ** 2) for c in CH_CLENCH])


def _alpha_powers(eeg, win_s=1.0):
    n = int(win_s * FS)
    return np.array([np.mean(_f("alpha", _row(eeg, c)[-n:]) ** 2) for c in CH_ALPHA])


class Detectors:
    def __init__(self):
        self.base = None
        self.clench_armed = True
        self.clench_peak = 0.0
        self.last_clench = -9.0
        self.blink_armed = True
        self.blink_start = None
        self.last_blink = -9.0
        self.last_double = -9.0
        self.alpha_since = 0.0
        self.alpha_fired = False

    # ---------- baseline: >= 4 s still, eyes open ----------
    def calibrate_rest(self, eeg):
        step, win = int(0.2 * FS), int(1.2 * FS)
        mus = [_muscle_powers(eeg[:, i - win:i]) for i in range(win, eeg.shape[1] + 1, step)]
        bl = _f("blink", _row(eeg, CH_BLINK))
        mad = np.median(np.abs(bl - np.median(bl))) * 1.4826
        al = [_alpha_powers(eeg[:, i - win:i]) for i in range(win, eeg.shape[1] + 1, step)]
        self.base = {
            "muscle": np.maximum(np.median(mus, axis=0), 1e-9),
            "blink_thr": max(BLINK_MIN, BLINK_K * mad),
            "alpha": np.maximum(np.median(al, axis=0), 1e-9),
        }
        return {"muscle": float(np.median(self.base["muscle"])), "blink_thr": self.base["blink_thr"], "alpha": float(np.median(self.base["alpha"]))}

    # ---------- every ~50 ms with the last 1.2 s ----------
    def update(self, eeg, now=None):
        now = time.time() if now is None else now
        if self.base is None:
            return {"clench": 0, "blink": 0, "alpha": 0}, []
        events = []

        # clench
        muscle = float(np.median(_muscle_powers(eeg) / self.base["muscle"]))
        if self.clench_armed and muscle >= CLENCH_FIRE and now - self.last_clench >= CLENCH_GAP_S:
            events.append({"type": "event", "input": "clench"})
            self.clench_armed = False
            self.clench_peak = muscle
            self.last_clench = now
        if not self.clench_armed:
            self.clench_peak = max(self.clench_peak, muscle)
            if muscle < max(CLENCH_REARM_ABS, CLENCH_REARM_REL * self.clench_peak):
                self.clench_armed = True
        clenching = muscle >= MUSCLE_VETO or now - self.last_clench < 0.5

        # double blink (ignored while clenching)
        bl = _f("blink", _row(eeg, CH_BLINK))[-int(0.3 * FS):]
        blink = float(np.max(np.abs(bl)) / self.base["blink_thr"])
        if clenching:
            self.blink_start = None
            self.blink_armed = True
        elif blink >= 1 and self.blink_armed:
            self.blink_armed = False
            self.blink_start = now
        elif blink < 0.5 and not self.blink_armed:
            self.blink_armed = True
            width = now - (self.blink_start or now)
            if BLINK_WIDTH_S[0] <= width <= BLINK_WIDTH_S[1] + 0.3:  # +0.3 for window lag
                gap = now - self.last_blink
                if DOUBLE_BLINK_S[0] <= gap <= DOUBLE_BLINK_S[1] + 0.3 and now - self.last_double > 1.0:
                    events.append({"type": "event", "input": "blink2"})
                    self.last_double = now
                    self.last_blink = -9.0
                else:
                    self.last_blink = now
            self.blink_start = None

        # eyes closed (ignored while clenching)
        alpha = float(np.median(_alpha_powers(eeg) / self.base["alpha"]) / ALPHA_K)
        if alpha >= 1 and not clenching:
            if not self.alpha_since:
                self.alpha_since = now
            if not self.alpha_fired and now - self.alpha_since >= ALPHA_HOLD_S:
                self.alpha_fired = True
                events.append({"type": "event", "input": "alpha"})
        else:
            self.alpha_since = 0.0
            self.alpha_fired = False

        return {
            "clench": round(muscle / CLENCH_FIRE, 3),
            "blink": round(0.0 if clenching else blink, 3),
            "alpha": round(alpha, 3),
        }, events


SITES = {1: "Oz", 2: "O1", 3: "O2", 4: "POz", 5: "Fp1", 6: "T7"}
PROMPTS = {
    "flat": "Not touching skin. Wiggle it into the hair and screw it down a little.",
    "noise": "Picking up noise. Check the ear clip and unplug the laptop charger.",
    "floating": "Reading far more than the others. Re-seat it so the spike touches skin.",
}


def quality(eeg):
    """Per-channel contact check over the last ~2 s of raw signal. Relative to
    the other channels, so it works whatever the units."""
    stds = {ch: float(np.std(_f("eeg", _row(eeg, ch) - np.mean(_row(eeg, ch))))) for ch in SITES}
    typical = float(np.percentile(list(stds.values()), 25))  # the quieter channels
    out = []
    for ch, site in SITES.items():
        x = _row(eeg, ch) - np.mean(_row(eeg, ch))
        std = float(np.std(x))
        if std < 0.5:
            reason = "flat"
        elif stds[ch] > 10 * typical:
            reason = "floating"  # e.g. Oz and O1 in our baseline recordings
        else:
            sig = np.mean(_f("eeg", x) ** 2)
            hum = np.mean(_f("line", x) ** 2)
            reason = "noise" if hum > 0.6 * sig else "ok"
        state = {"ok": "good", "noise": "fair"}.get(reason, "bad")
        item = {"ch": ch, "site": site, "state": state, "reason": reason, "std": round(stds[ch], 1)}
        if reason in PROMPTS:
            item["prompt"] = PROMPTS[reason]
        out.append(item)
    return out
