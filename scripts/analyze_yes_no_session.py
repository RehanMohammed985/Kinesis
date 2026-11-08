"""Score the team's 9-minute yes/no session (Nov 7, trial 727, Kennedy):
18 trials, each: word on screen 5 s, "+" 5 s, think the word 20 s, rest 15 s.

The EEG file has no markers, so trials are placed using file times: the
recording's name is its start (unix 1794094005) and its last-modified time is
its end; events.csv's last-modified time is its last event. That puts the
first cue 10.5 s into the recording, and the noise the team reported in the
first break lands exactly in that break, which confirms the placement.
The board ran about 1.3% fast against the laptop clock (874.8 s of samples
in 863.1 s), so times are stretched to fit.

Each 20 s "think" window is trimmed 2 s at both ends and cut into 2 s pieces.
Pieces of one trial stay together in cross-validation, and the p-value
shuffles whole-trial labels (kinesis/signal/words.evaluate).

python scripts/analyze_yes_no_session.py kinesis/data/words/yes_no_727.csv kinesis/data/words/yes_no_727_events.csv
"""
import csv
import pickle
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.signal import words as W  # noqa: E402

LEN_S = 863.1      # recording length by the laptop clock (name -> last modified)
FIRST_S = 10.51    # first cue, seconds into the recording
PINS = [3, 4, 5, 6, 7]   # pin 2 (Oz) left out: it was noisy all session


def main():
    y = np.loadtxt(sys.argv[1], delimiter=",").T
    ev = list(csv.DictReader(open(sys.argv[2])))
    t0 = int(ev[0]["host_monotonic_ns"])
    n = y.shape[1]
    x = W.bandpass(y - y.mean(1, keepdims=True), 1, 55)

    def at(rel):
        return int(round((FIRST_S + rel) / LEN_S * n))

    def pieces(stage, trim0, trim1, dur):
        P, lab, grp = [], [], []
        for e in ev:
            if e["stage"] != stage:
                continue
            rel = (int(e["host_monotonic_ns"]) - t0) / 1e9
            for k in range(int((dur - trim0 - trim1) // 2)):
                a = at(rel + trim0 + 2 * k)
                P.append(x[[p - 1 for p in PINS], a:a + 250])
                lab.append(1 if e["label"] == "yes" else 0)
                grp.append(int(e["trial_id"]))
        P = np.array(P)
        peak = np.abs(P).max(axis=(1, 2))
        keep = peak < 6 * np.median(peak)       # drop big artifacts, decided before scoring
        return P[keep], np.array(lab)[keep], np.array(grp)[keep]

    X, yl, g = pieces("imagery", 2, 2, 20)
    R, _, rg = pieces("rest", 2, 1, 15)
    print(f"{len(set(g))} trials, {len(X)} two-second pieces while thinking, {len(R)} while resting")

    res = W.evaluate(X, yl, g, n_perm=200)
    print("\nyes vs no:")
    for k, v in res.items():
        print(f"  {k:10s} {v['accuracy']:.0%} (chance {v['chance']:.0%}, p = {v['p']:.3f})")

    Xa = np.concatenate([X, R])
    ya = np.r_[np.ones(len(X), int), np.zeros(len(R), int)]
    ga = np.r_[g, rg + 1000]
    res2 = W.evaluate(Xa, ya, ga, n_perm=200)
    print("\nthinking a word vs resting:")
    for k, v in res2.items():
        print(f"  {k:10s} {v['accuracy']:.0%} (chance {v['chance']:.0%}, p = {v['p']:.3f})")

    out = Path(sys.argv[1]).parent
    for name, Xm, ym, words, r in (("yes_no_model.pkl", X, yl, ["no", "yes"], res), ("thinking_vs_rest_model.pkl", Xa, ya, ["rest", "thinking"], res2)):
        clf = W.classifiers()["covariance"].fit(Xm, ym)
        (out / name).write_bytes(pickle.dumps({"words": words, "pins": PINS, "classifier": "covariance", "model": clf, "scores": r}))
    print(f"\nsaved models to {out}")


if __name__ == "__main__":
    main()
