"""How far can imagined speech go, and how much do we lose with our 6
electrodes? Tested on the 2020 BCI Competition track 3 dataset (NEMAR
nm000113): 15 people, 64 channels, imagining "Hello", "Help me", "Stop",
"Thank you", "Yes", 60 trials each for training plus 20 each held out.

Same pipeline as our own word trials (kinesis/signal/words.py). Trained on
the training run, scored on the held-out runs, the way the competition did.
Compared: all 64 channels vs only our 6 sites (Oz, O1, O2, POz, Fp1, T7) at
our 125 Hz, for all 5 words and for "Yes" vs "Stop" (the closest pair to
yes/no in the set).

Download: https://data.nemar.org/nm000113/v1.0.0.zip, unzip, then
python scripts/eval_imagined_speech.py /path/to/nm000113
"""
import glob
import os
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.signal import words as W  # noqa: E402

OURS = ["Oz", "O1", "O2", "POz", "Fp1", "T7"]
EPOCH_S = 3.0


def load(root, sub, run, picks):
    import mne
    base = os.path.join(root, sub, "eeg", f"{sub}_task-imaginedSpeech_run-{run:02d}")
    raw = mne.io.read_raw_edf(base + "_eeg.edf", preload=True, verbose="error")
    fs = raw.info["sfreq"]
    x = raw.get_data(picks=picks) * 1e6 if picks else raw.get_data() * 1e6
    x = W.to_fs(x, fs)
    ev = np.genfromtxt(base + "_events.tsv", delimiter="\t", names=True, dtype=None, encoding="utf-8-sig")
    X, y = [], []
    n = int(EPOCH_S * W.FS)
    xf = W.bandpass(x - x.mean(axis=1, keepdims=True), 1, 55)
    for e in np.atleast_1d(ev):
        i = int(round(float(e["onset"]) * W.FS))
        if i + n <= xf.shape[1]:
            X.append(xf[:, i:i + n])
            y.append(str(e["trial_type"]))
    return np.array(X), np.array(y)


def score(Xtr, ytr, Xte, yte):
    out = {}
    for name, clf in W.classifiers().items():
        clf.fit(Xtr, ytr)
        out[name] = float(np.mean(clf.predict(Xte) == yte))
    return out


def main():
    root = sys.argv[1]
    subs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(root, "sub-*")))
    rows = []
    for sub in subs:
        r = {}
        for label, picks in (("64", None), ("ours", OURS)):
            Xtr, ytr = load(root, sub, 0, picks)
            Xa, ya = load(root, sub, 1, picks)
            Xb, yb = load(root, sub, 2, picks)
            Xte, yte = np.concatenate([Xa, Xb]), np.concatenate([ya, yb])
            r[label + "_5"] = score(Xtr, ytr, Xte, yte)
            if label == "ours":
                m, mt = np.isin(ytr, ["Yes", "Stop"]), np.isin(yte, ["Yes", "Stop"])
                r["ours_2"] = score(Xtr[m], ytr[m], Xte[mt], yte[mt])
                r["n2"] = int(mt.sum())
            r["n5"] = len(yte)
        rows.append(r)
        print(f"{sub}: 5 words, 64 ch {max(r['64_5'].values()):.0%} | 5 words, our 6 {max(r['ours_5'].values()):.0%} | "
              f"Yes vs Stop, our 6 {max(r['ours_2'].values()):.0%}", flush=True)

    print("\nMean over people, held-out trials (best of the two classifiers per condition):")
    for key, chance, label in (("64_5", 0.2, "5 words, all 64 channels"), ("ours_5", 0.2, "5 words, our 6 electrodes"),
                               ("ours_2", 0.5, "Yes vs Stop, our 6 electrodes")):
        for clf in ("covariance", "bandpower"):
            accs = [r[key][clf] for r in rows]
            n = rows[0]["n2" if key == "ours_2" else "n5"]
            sig = sum(binomtest(int(round(a * n)), n, chance, alternative="greater").pvalue < 0.05 for a in accs)
            print(f"  {label:32s} {clf:10s} {np.mean(accs):5.1%}  (chance {chance:.0%}; above chance in {sig} of {len(accs)} people)")


if __name__ == "__main__":
    main()
