"""Look to choose (SSVEP): which flashing square is the person looking at?

Each square on the Look screen flashes at its own rate. The visual cortex
follows the rate of whatever the eyes are on, so the back-of-head electrodes
pick up that rate and its multiples. We compare the last 2 s of the four
back channels against pure sine waves at each rate (CCA, canonical
correlation) in three frequency bands (filter-bank CCA, Chen et al. 2015).
No training needed, so it works the first time someone puts the headset on.

Rates are 60 Hz display frames per flash cycle (7, 6, 5, 4 frames), so the
browser can draw them exactly. Validated on the Tsinghua SSVEP benchmark
with only our 4 channels at our 125 Hz: scripts/validate_ssvep.py.
"""
import numpy as np
from scipy.signal import butter, sosfiltfilt

from kinesis.montage import OCCIPITAL

FS = 125
FREQS = [8.57, 10.0, 12.0, 15.0]     # must match LOOK_TILES order in app/src/data.js
HARMONICS = 3
SUBBANDS = [(6, 60), (14, 60), (22, 60)]
WEIGHTS = np.array([(m + 1) ** -1.25 + 0.25 for m in range(len(SUBBANDS))])
WIN_S = 2.0
LATENCY_S = 0.14                     # the visual cortex lags the screen by about this much

# live decision: same winner on HOLD updates in a row, clear of the runner-up.
# Tuned on benchmark people 1-10 and 100 s of our own headset with nothing
# flashing. On all 35 people: first choice right 93%, wrong 0.2%, none 7%,
# median 2.2 s; on our headset with nothing flashing, 1 false choice in 100 s.
MARGIN = 0.45                        # (best - second) / best
HOLD = 3                             # updates every 0.25 s
REFRACTORY_S = 1.5


def _sos(lo, hi, fs):
    return butter(4, [lo, min(hi, 0.45 * fs)], btype="band", fs=fs, output="sos")


def references(freqs, n, fs, harmonics=HARMONICS, phase_s=0.0):
    t = np.arange(n) / fs + phase_s
    out = []
    for f in freqs:
        cols = []
        for h in range(1, harmonics + 1):
            if h * f < fs / 2:
                cols += [np.sin(2 * np.pi * h * f * t), np.cos(2 * np.pi * h * f * t)]
        out.append(np.array(cols).T)
    return out


def cca_r(X, Y):
    """Largest canonical correlation between X (n x channels) and Y (n x refs)."""
    qx, _ = np.linalg.qr(X - X.mean(0))
    qy, _ = np.linalg.qr(Y - Y.mean(0))
    return float(np.linalg.svd(qx.T @ qy, compute_uv=False)[0])


def fbcca_scores(eeg, freqs=FREQS, fs=FS, subbands=SUBBANDS):
    """eeg: channels x samples. Returns one score per frequency."""
    refs = references(freqs, eeg.shape[1], fs)
    x = eeg - eeg.mean(axis=1, keepdims=True)
    rho = np.zeros((len(subbands), len(freqs)))
    for b, (lo, hi) in enumerate(subbands):
        xb = sosfiltfilt(_sos(lo, hi, fs), x, axis=1).T
        for k, Y in enumerate(refs):
            rho[b, k] = cca_r(xb, Y)
    return WEIGHTS @ rho ** 2


class Look:
    """Live decoder: feed the latest window every ~0.25 s."""

    def __init__(self, freqs=FREQS, chans=OCCIPITAL, fs=FS):
        self.freqs, self.chans, self.fs = freqs, list(chans), fs
        self.run = []
        self.last = -9.0

    def update(self, eeg, now):
        n = int(WIN_S * self.fs)
        x = eeg[[c - 1 for c in self.chans], -n:]
        s = fbcca_scores(x, self.freqs, self.fs)
        order = np.argsort(s)[::-1]
        best, margin = int(order[0]), float((s[order[0]] - s[order[1]]) / (s[order[0]] + 1e-12))
        self.run = (self.run + [best])[-HOLD:] if margin >= MARGIN else []
        level = {"scores": [round(float(v / (s.max() + 1e-12)), 3) for v in s], "best": best if margin >= MARGIN else -1,
                 "margin": round(margin, 3)}
        events = []
        if len(self.run) == HOLD and len(set(self.run)) == 1 and now - self.last >= REFRACTORY_S:
            events.append({"type": "event", "input": "look", "target": best})
            self.last, self.run = now, []
        return level, events
