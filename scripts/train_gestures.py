"""Train and test the learned clench / double-blink model on our recordings.

Protocol (Nov 7, 5 trials; 4 and 5 with the ear clip tightened): still about
10 s, eyes closed about 10 s, still, then a section of jaw clenches and a
section of double blinks, still. Times are give or take, so the sections below
were marked by eye from each recording. The first 8 s of each file is the
headset settling and is left out.

Test = leave one trial out: train on the others exactly the way the app's
calibration does (rest frames + active frames inside each cued section), then
stream the third trial through the live detector every 48 ms and count events.

python scripts/train_gestures.py kinesis/data/gestures/double_trial*.csv
python scripts/train_gestures.py ... --save kinesis/data/gestures/model.json
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.signal import butter, find_peaks, sosfiltfilt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.signal import learned as L  # noqa: E402
from kinesis.signal.live import Detectors  # noqa: E402
from scripts.reconstruct_windows import reconstruct  # noqa: E402

FS = L.FS
WIN = int(1.2 * FS)
HOP = 6
META = L.team_meta()          # kinesis/data/gestures/sections.json
SETTLE = META["settle"]       # first 8 s: the headset settling
TAIL = META["tail"]           # last 2 s: reaching over to stop the recording
REST_REF = tuple(META["rest_ref"])  # the 5 s "stay still" reference, like the app's rest step
SECTIONS = {n: {k: tuple(v) for k, v in sec.items()} for n, sec in META["trials"].items()}


def load(path):
    x = np.loadtxt(path, delimiter=",")
    if x.shape[0] % 500 == 0 and x.shape[0] > 60 * FS * 5:  # stacked snapshots
        x, _ = reconstruct(x)
    return x.T


def name_of(path):
    p = Path(path)
    return p.stem if p.stem.startswith("double_trial") else p.parent.name


def frames(eeg, chans):
    ts, F = [], []
    for i in range(WIN, eeg.shape[1] + 1, HOP):
        F.append(L.raw_features(eeg[:, i - WIN:i], chans))
        ts.append(i / FS)
    return np.array(ts), np.array(F)


def training_set(trials, chans):
    X, y = [], []
    for name, eeg in trials:
        a, b = L.labelled(eeg, SECTIONS[name], chans, META, HOP)
        X += a
        y += b
    return np.array(X), np.array(y)


def bursts(eeg, chans, sec, kind):
    """Bursts seen offline with the whole recording in view, as a reference:
    clench = peaks of the muscle power every channel shares, double blink =
    peaks of the channel-specific muscle power (the two blinks of a pair are
    closer than 0.35 s, so they count once)."""
    sos = butter(4, [20, 55], btype="band", fs=FS, output="sos")
    x = eeg[[c - 1 for c in chans]]
    r0, r1 = int(REST_REF[0] * FS), int(REST_REF[1] * FS)
    a, b = sec[kind]
    if kind == "blink2":
        x = x - np.median(x, axis=0)
    env = np.median([np.convolve(sosfiltfilt(sos, r) ** 2, np.ones(40) / 40, "same") for r in x], axis=0)
    env = env / np.median(env[r0:r1])
    pk, _ = find_peaks(np.log(env), height=np.log(5), prominence=np.log(2.5), distance=int(0.35 * FS))
    return int(sum(a - 0.5 <= p / FS <= b + 0.5 for p in pk))


def stream(model, eeg):
    rules = Detectors()
    r0, r1 = int(REST_REF[0] * FS), int(REST_REF[1] * FS)
    rules.calibrate_rest(eeg[:, r0:r1])
    det = L.LearnedDetectors(model, rules)
    det.calibrate_rest(eeg[:, r0 - WIN:r1])
    ev = {"clench": [], "blink2": [], "alpha": []}
    for i in range(WIN, eeg.shape[1] + 1, HOP):
        _, es = det.update(eeg[:, i - WIN:i], now=i / FS)
        for e in es:
            ev[e["input"]].append(round(i / FS, 2))
    return ev


def score(name, eeg, ev):
    sec = SECTIONS[name]
    end = eeg.shape[1] / FS
    first = min(a for a, _ in sec.values())
    last = max(b for _, b in sec.values())
    tol = 1.0

    def count(kind, a, b):
        return sum(a <= t <= b for t in ev[kind])

    def win(kind):  # a little slack; more after the last section (detector lag)
        a, b = sec[kind]
        return a - 0.3, b + (tol if b == last else 0.3)

    return {
        "blink2_in_blinks": count("blink2", *win("blink2")),
        "clench_in_blinks": count("clench", *win("blink2")),
        "clench_in_clench": count("clench", *win("clench")),
        "blink2_in_clench": count("blink2", *win("clench")),
        "false_rest": count("clench", SETTLE, first - 1) + count("blink2", SETTLE, first - 1)
        + count("clench", last + tol, end - TAIL) + count("blink2", last + tol, end - TAIL),
        "rest_s": (first - 1 - SETTLE) + max(0.0, end - TAIL - last - tol),
        "settling": count("clench", 0, SETTLE) + count("blink2", 0, SETTLE),
        "alpha": len(ev["alpha"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--save")
    a = ap.parse_args()
    trials = [(name_of(f), load(f)) for f in a.files]
    # channels that are on and not floating in every trial
    sets = [set(L.active_channels(e[:, int(REST_REF[0] * FS):int(REST_REF[1] * FS)])) for _, e in trials]
    chans = sorted(set.intersection(*sets))
    print("channels used:", chans, " per trial:", [sorted(s) for s in sets])

    tot = {}
    print("\nLeave one trial out (train on the others, stream this one):")
    for k, (name, eeg) in enumerate(trials):
        X, y = training_set([t for j, t in enumerate(trials) if j != k], chans)
        model = L.GestureModel(chans).fit(X, y)
        ev = stream(model, eeg)
        s = score(name, eeg, ev)
        ref_c = bursts(eeg, chans, SECTIONS[name], "clench")
        ref_b = bursts(eeg, chans, SECTIONS[name], "blink2")
        # frame accuracy on the held-out trial's labelled frames
        Xt, yt = training_set([(name, eeg)], chans)
        pred = np.array(model.lda.classes)[model.lda.proba(Xt).argmax(1)]
        acc = {c: round(float(np.mean(pred[yt == i] == i)), 3) for i, c in enumerate(L.CLASSES) if (yt == i).any()}
        print(f"\n{name}  ({eeg.shape[1] / FS:.1f} s)")
        print(f"  double blink: {s['blink2_in_blinks']} events ({ref_b} bursts seen offline); read as clench: {s['clench_in_blinks']}")
        print(f"  clench: {s['clench_in_clench']} events ({ref_c} bursts seen offline); read as double blink: {s['blink2_in_clench']}")
        print(f"  false events while still: {s['false_rest']} in {s['rest_s']:.0f} s   (first {SETTLE:.0f} s settling: {s['settling']})")
        print(f"  frame accuracy: {acc}   training frames: {dict(zip(L.CLASSES, np.bincount(y, minlength=3).tolist()))}")
        print(f"  times: double blink {ev['blink2']}")
        print(f"         clench {ev['clench']}")
        for key, v in s.items():
            tot[key] = tot.get(key, 0) + v
        tot["ref_c"] = tot.get("ref_c", 0) + ref_c
        tot["ref_b"] = tot.get("ref_b", 0) + ref_b
    n = len(trials)
    print("\nTOTAL")
    print(f"  double blink: {tot['blink2_in_blinks']} events for {tot['ref_b']} bursts, read as clench: {tot['clench_in_blinks']}")
    print(f"  clench: {tot['clench_in_clench']} events for {tot['ref_c']} bursts, read as double blink: {tot['blink2_in_clench']}")
    print(f"  false events while still: {tot['false_rest']} in {tot['rest_s']:.0f} s")

    if a.save:
        X, y = training_set(trials, chans)
        model = L.GestureModel(chans).fit(X, y)
        model.save(a.save)
        print(f"\nmodel trained on all {n} trials -> {a.save}")


if __name__ == "__main__":
    main()
