"""Score word recordings from scripts/record_words.py: can a classifier tell
the words apart better than chance? Several files from the same person are
pooled.

python scripts/analyze_words.py data/sessions/words-rehan-mouth-*.csv
python scripts/analyze_words.py ... --save data/words_model.pkl   # keep the best model

Prints, for each classifier: cross-validated accuracy, what shuffled labels
score (chance), and the p-value. Under p 0.05 means the words really differ.
Also checks "any word vs rest", which tells whether GO changes the signal at all.
"""
import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.signal import words as W  # noqa: E402


def load(path):
    from brainflow.board_shim import BoardShim
    from brainflow.data_filter import DataFilter
    meta = json.loads(Path(path).with_suffix(".json").read_text())
    bid = meta.get("board_id", 57)
    data = DataFilter.read_file(str(path))
    rows = BoardShim.get_eeg_channels(bid)
    pins = sorted(int(p) for p in meta["pins"])
    eeg = data[[rows[p - 1] for p in pins]]
    markers = data[BoardShim.get_marker_channel(bid)]
    fs = BoardShim.get_sampling_rate(bid)
    if fs != W.FS:  # resample, carrying markers to the nearest new sample
        idx = np.flatnonzero(markers)
        eeg = W.to_fs(eeg, fs)
        m2 = np.zeros(eeg.shape[1])
        for i in idx:
            m2[min(int(round(i * W.FS / fs)), len(m2) - 1)] = markers[i]
        markers = m2
    return eeg, markers, meta


def verdict(r):
    if r["p"] is not None and r["p"] < 0.05:
        return "above chance"
    return "not above chance"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--perm", type=int, default=200, help="label shuffles for the p-value")
    ap.add_argument("--save")
    a = ap.parse_args()
    Xs, ys, gs, Rs, words = [], [], [], [], None
    for f in a.files:
        eeg, markers, meta = load(f)
        words = words or meta["words"]
        first = int(np.concatenate(gs).max()) + 1 if gs else 0
        X, y, g, R = W.epochs_from_markers(eeg, markers, len(words), seconds=meta.get("go_seconds", W.EPOCH_S), first_trial=first)
        n_tr = len(set(g.tolist()))
        print(f"{Path(f).name}: {n_tr} trials ({', '.join(f'{w} {len(set(g[y == i].tolist()))}' for i, w in enumerate(words))}), "
              f"{len(X)} two-second pieces, {len(R)} rest")
        Xs.append(X)
        ys.append(y)
        gs.append(g)
        if len(R):
            Rs.append(R)
    X, y, g = np.concatenate(Xs), np.concatenate(ys), np.concatenate(gs)
    print(f"\n{' vs '.join(words)}: {len(set(g.tolist()))} trials, mode {meta['mode']}")
    per_word = [len(set(g[y == i].tolist())) for i in range(len(words))]
    if min(per_word) < 10:
        print(f"  only {min(per_word)} trials for one word: too few to show anything either way, record at least 15 each")
    res = W.evaluate(X, y, g, n_perm=a.perm)
    for name, r in res.items():
        print(f"  {name:10s} accuracy {r['accuracy']:.0%}   chance {r['chance']:.0%}   p = {r['p']:.3f}   -> {verdict(r)}")
    if Rs:
        R = np.concatenate(Rs)
        n = min(len(R), len(X))
        Xr = np.concatenate([X[:n], R[:n]])
        yr = np.array([1] * n + [0] * n)
        rr = W.evaluate(Xr, yr, None, n_perm=min(a.perm, 100))
        best = max(rr.values(), key=lambda r: r["accuracy"])
        print(f"\nany word vs rest: {best['accuracy']:.0%} (chance {best['chance']:.0%}, p = {best['p']:.3f}) -> {verdict(best)}")
    if a.save:
        name = max(res, key=lambda k: res[k]["accuracy"])
        clf = W.classifiers()[name].fit(X, y)  # pieces of all trials
        Path(a.save).parent.mkdir(parents=True, exist_ok=True)
        Path(a.save).write_bytes(pickle.dumps({"words": words, "classifier": name, "model": clf, "scores": res}))
        print(f"\nsaved {name} model -> {a.save}")


if __name__ == "__main__":
    main()
