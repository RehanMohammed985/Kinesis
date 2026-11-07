"""Learned gestures: the app learns what each person's clench and double blink
look like during calibration, instead of using one fixed rule for everyone.

Why: on our double-blink recordings (kinesis/data/gestures/) the fixed rules
missed every double blink and fired "clench" on them, because with this
headset fit both gestures show up as muscle noise. But the two look different:
- double blink: a burst shared by every channel (it comes in through the ear
  clip) plus activity on one channel only
- clench: activity that differs channel to channel, on all of them
A small linear model (shrinkage LDA, a few lines of numpy) separates them.
People differ (weak jaw, eyes only, a different fit), so each person trains
their own in the calibration steps the app already has: stay still, clench,
double blink. Training takes well under a second.

Features, every 50 ms on the last 0.5 s, relative to the person's rest:
per channel: muscle power (20-55 Hz) and slow power (0.5-8 Hz), each on the
raw channel and on the channel minus the median of all channels; plus the
two powers of the median itself (what every channel shares). All log ratios.
"""
import json
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfiltfilt

FS = 125
FEAT_S = 0.5
SOS = {
    "muscle": butter(4, [20, 55], btype="band", fs=FS, output="sos"),
    "slow": butter(2, [0.5, 8], btype="band", fs=FS, output="sos"),
    "eeg": butter(2, [1, 40], btype="band", fs=FS, output="sos"),
}
CLASSES = ["rest", "clench", "blink2"]

# Gesture-agnostic activity, used to label calibration frames and count
# attempts before any model exists: median muscle power across channels, x rest.
ACT_ON = 4.0
ACT_OFF = 2.0

# Turning frame probabilities into events.
P_FIRE = 0.8      # gesture probability needed
HOLD_S = 0.2      # held this long (a stray twitch is shorter)
GAP_S = {"clench": 0.5, "blink2": 0.8}
REARM_REL = 0.45  # clench re-arms once activity falls below 45% of its peak
P_REARM = 0.5     # double blink re-arms once the model says rest (the dip
                  # between the two blinks of one double blink is not rest)


def _f(name, x):
    return sosfiltfilt(SOS[name], x, padlen=min(x.shape[-1] - 1, 27))


def active_channels(rest):
    """Channels that are switched on and not floating, from a rest window
    (8 x samples). Floating = far noisier than the quieter channels."""
    stds = np.array([float(np.std(_f("eeg", r - r.mean()))) for r in rest])
    on = stds > 0.5
    if on.sum() < 2:
        return [i + 1 for i in range(len(stds)) if on[i]]
    typical = float(np.percentile(stds[on], 25))
    return [i + 1 for i in range(len(stds)) if on[i] and stds[i] <= 10 * typical]


def raw_features(eeg, chans):
    """eeg: 8 x n (n >= 0.5 s, the server passes 1.2 s). Returns log powers."""
    x = eeg[[c - 1 for c in chans]].astype(float)
    x = x - x.mean(axis=1, keepdims=True)
    med = np.median(x, axis=0)
    n = int(FEAT_S * FS)
    out = []
    for band in ("muscle", "slow"):
        fx = _f(band, x)[:, -n:]
        fd = _f(band, x - med)[:, -n:]
        fm = _f(band, med)[-n:]
        out += list(np.log(np.mean(fx ** 2, axis=1) + 1e-6))
        out += list(np.log(np.mean(fd ** 2, axis=1) + 1e-6))
        out.append(float(np.log(np.mean(fm ** 2) + 1e-6)))
    return np.array(out)


def activity(feat, n_ch):
    """Median raw muscle power across channels, x rest (feat already relative)."""
    return float(np.exp(np.median(feat[:n_ch])))


class LDA:
    """Shrinkage linear discriminant analysis on standardized features."""

    def fit(self, X, y, shrink=0.2):
        self.mu_x, self.sd_x = X.mean(0), X.std(0) + 1e-6
        Z = (X - self.mu_x) / self.sd_x
        ks = sorted(set(y))
        mu = np.array([Z[y == k].mean(0) for k in ks])
        Zc = np.vstack([Z[y == k] - mu[i] for i, k in enumerate(ks)])
        S = Zc.T @ Zc / max(len(Z) - len(ks), 1)
        S = (1 - shrink) * S + shrink * np.trace(S) / S.shape[0] * np.eye(S.shape[0])
        self.W = np.linalg.solve(S, mu.T)
        self.b = -0.5 * np.sum(mu * self.W.T, axis=1)
        self.classes = [int(k) for k in ks]
        return self

    def proba(self, X):
        Z = (np.atleast_2d(X) - self.mu_x) / self.sd_x
        s = Z @ self.W + self.b
        s = s - s.max(axis=1, keepdims=True)
        e = np.exp(s)
        return e / e.sum(axis=1, keepdims=True)

    def to_dict(self):
        return {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d):
        m = cls()
        for k, v in d.items():
            setattr(m, k, np.array(v) if isinstance(v, list) and k != "classes" else v)
        return m


class GestureModel:
    """Rest reference + classifier for one person and one fit."""

    def __init__(self, chans):
        self.chans = list(chans)
        self.rest = None
        self.lda = None

    def set_rest(self, feats):
        self.rest = np.median(np.array(feats), axis=0)

    def rel(self, eeg):
        return raw_features(eeg, self.chans) - self.rest

    def fit(self, X, y):
        self.lda = LDA().fit(np.array(X), np.array(y))
        return self

    def proba(self, feat):
        p = self.lda.proba(feat)[0]
        return {CLASSES[k]: float(p[i]) for i, k in enumerate(self.lda.classes)}

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps({"chans": self.chans, "lda": self.lda.to_dict()}))

    @classmethod
    def load(cls, path):
        d = json.loads(Path(path).read_text())
        m = cls(d["chans"])
        m.lda = LDA.from_dict(d["lda"])
        return m


class GestureEvents:
    """Frame probabilities -> clench / blink2 events, one per gesture.
    Re-arming is relative to the peak, like the rule-based clench: people
    often clench again before fully relaxing, and do double blinks back to
    back, so waiting for full rest would miss most of them."""

    def __init__(self):
        self.armed = True
        self.cand = None
        self.since = 0.0
        self.peak = 0.0
        self.last = -9.0
        self.fired = None

    def step(self, p, act, now):
        events = []
        if not self.armed:
            self.peak = max(self.peak, act)
            rest = p.get("rest", 0) >= P_REARM
            if rest or (self.fired == "clench" and act < max(ACT_OFF, REARM_REL * self.peak)):
                self.armed = True
                self.cand = None
            return events
        g = max(("clench", "blink2"), key=lambda k: p.get(k, 0))
        if p.get(g, 0) >= P_FIRE and act >= ACT_OFF:
            if self.cand != g:
                self.cand, self.since = g, now
            elif now - self.since >= HOLD_S and now - self.last >= GAP_S[g]:
                events.append({"type": "event", "input": g})
                self.armed, self.cand, self.last, self.peak, self.fired = False, None, now, act, g
        else:
            self.cand = None
        return events


class Calibrator:
    """Collects labelled frames during the app's calibration steps and trains.
    Rest frames come from the rest step and the quiet moments between
    attempts; gesture frames are the active moments during that gesture's step."""

    def __init__(self, chans):
        self.model = GestureModel(chans)
        self.rest_feats = []
        self.frames = []          # (raw feature, step)
        self.armed = True
        self.peak = 0.0

    def add_rest(self, feat_raw):
        self.rest_feats.append(feat_raw)

    def add(self, feat_raw, step):
        """Returns True when this frame starts a new attempt (for the app's counter)."""
        self.frames.append((feat_raw, step))
        if not self.rest_feats:
            return False
        a = activity(feat_raw - np.median(self.rest_feats, axis=0), len(self.model.chans))
        if self.armed and a >= ACT_ON:
            self.armed, self.peak = False, a
            return True
        self.peak = max(self.peak, a)
        if a < max(ACT_OFF, REARM_REL * self.peak):
            self.armed = True
        return False

    def train(self):
        self.model.set_rest(self.rest_feats)
        n = len(self.model.chans)
        X, y = [], []
        for f in self.rest_feats:
            X.append(f - self.model.rest)
            y.append(0)
        for f, step in self.frames:
            r = f - self.model.rest
            a = activity(r, n)
            if a >= ACT_ON and step in ("clench", "blink2"):
                X.append(r)
                y.append(CLASSES.index(step))
            elif a < ACT_OFF:
                X.append(r)
                y.append(0)
        y = np.array(y)
        counts = {c: int((y == i).sum()) for i, c in enumerate(CLASSES)}
        if counts["clench"] < 5 or counts["blink2"] < 5:
            return None, counts
        self.model.fit(X, y)
        # how cleanly each class is told apart, on the training frames
        P = self.model.lda.proba(np.array(X))
        pred = np.array(self.model.lda.classes)[P.argmax(1)]
        scores = {c: float(np.mean(pred[y == i] == i)) for i, c in enumerate(CLASSES) if (y == i).any()}
        return self.model, {"frames": counts, "accuracy": scores}


class LearnedDetectors:
    """Same interface as live.Detectors.update(). Clench and double blink
    from the person's model; eyes-closed stays with the rule-based detector."""

    def __init__(self, model, rules):
        self.model = model
        self.rules = rules
        self.events = GestureEvents()

    def calibrate_rest(self, rest, step=6):
        n = int(1.2 * FS)
        feats = [raw_features(rest[:, i - n:i], self.model.chans) for i in range(n, rest.shape[1] + 1, step)]
        self.model.set_rest(feats)

    def update(self, eeg, now):
        lv, ev = self.rules.update(eeg, now)
        if self.model.rest is None:
            return lv, [e for e in ev if e["input"] == "alpha"]
        rel = self.model.rel(eeg)
        p = self.model.proba(rel)
        gest = self.events.step(p, activity(rel, len(self.model.chans)), now)
        lv["clench"] = round(p.get("clench", 0) / P_FIRE, 3)
        lv["blink"] = round(p.get("blink2", 0) / P_FIRE, 3)
        busy = p.get("rest", 1) < 0.5
        return lv, gest + [e for e in ev if e["input"] == "alpha" and not busy]
