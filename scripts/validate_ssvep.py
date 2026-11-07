"""Validate the Look decoder (kinesis/signal/ssvep.py) on the Tsinghua SSVEP
benchmark (Wang et al. 2017, IEEE TNSRE, 35 people, 40 flashing targets
8 to 15.8 Hz, 6 blocks each). We use only what our headset has: Oz, O1, O2,
POz at 125 Hz, and the 4 targets closest to our tiles (8.6, 10, 12, 15 Hz).

Also streams every trial through the live decoder (kinesis/signal/ssvep.Look,
updates every 0.25 s) and, with --still, counts false choices on our own
headset recordings where nothing was flashing.

Download S1.mat.7z ... from http://bci.med.tsinghua.edu.cn/download.html and
Freq_Phase.mat, then:
python scripts/validate_ssvep.py /path/to/folder --still kinesis/data/gestures/double_trial*.csv
(.mat files, or .npz files with the 9 back channels kept, see below)
"""
import argparse
import glob
import os
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.signal import resample_poly

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.montage import PIN  # noqa: E402
from kinesis.signal import ssvep  # noqa: E402

FS_B = 250
ONSET_S = 0.5            # each epoch starts 0.5 s before the flashing
NINE = ["Pz", "PO5", "PO3", "POz", "PO4", "PO6", "O1", "Oz", "O2"]
IDX64 = [47, 53, 54, 55, 56, 57, 60, 61, 62]   # those channels in the 64-channel layout
OURS = ["Oz", "O1", "O2", "POz"]
TARGET_HZ = [8.6, 10.0, 12.0, 15.0]
WINDOWS = [1.0, 1.5, 2.0, 3.0]
GAZE_S = 0.5             # time to move the eyes to the next square, for the speed figure


def load(path):
    if path.endswith(".npz"):
        d = np.load(path)
        return d["data"], list(d["chans"])
    return sio.loadmat(path)["data"][IDX64], NINE


def itr(n, p, seconds):
    if p >= 1:
        bits = np.log2(n)
    elif p <= 1 / n:
        bits = 0.0
    else:
        bits = np.log2(n) + p * np.log2(p) + (1 - p) * np.log2((1 - p) / (n - 1))
    return bits * 60 / seconds


def live(x125, k):
    """Stream one trial through the live decoder. Returns (right, seconds) of the first choice."""
    eeg = np.zeros((8, x125.shape[1]))
    for i, c in enumerate(OURS):
        eeg[PIN[c] - 1] = x125[i]
    dec = ssvep.Look()
    for i in range(int(ssvep.WIN_S * 125), eeg.shape[1] + 1, 31):
        _, ev = dec.update(eeg[:, :i], i / 125)
        if ev:
            return ev[0]["target"] == k, i / 125 - ONSET_S
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--still", nargs="*", default=[], help="our recordings; the still part (8-30 s) is used")
    args = ap.parse_args()
    root = args.root
    fp = sio.loadmat(os.path.join(root, "Freq_Phase.mat"))
    freqs = fp["freqs"].ravel()
    targets = [int(np.argmin(abs(freqs - f))) for f in TARGET_HZ]
    files = sorted(glob.glob(os.path.join(root, "S*.npz")) + glob.glob(os.path.join(root, "S*.mat")),
                   key=lambda p: int("".join(c for c in os.path.basename(p) if c.isdigit())))
    print(f"{len(files)} people, targets {[float(freqs[t]) for t in targets]} Hz, channels {OURS}, 125 Hz\n")
    acc = {w: [] for w in WINDOWS}
    acc_ours = []      # 2 s, our tile rates (8.57 not 8.6) as references
    acc_nine = []      # 2 s, all 9 back channels at 250 Hz, as a ceiling
    decided, right = 0, 0
    first = []         # live decoder: (right or None, seconds)
    for f in files:
        data, chans = load(f)
        x = data[[chans.index(c) for c in OURS]]
        x125 = resample_poly(x, 1, 2, axis=1)
        line = []
        for w in WINDOWS:
            a = (ONSET_S + ssvep.LATENCY_S)
            hits = []
            for k, t in enumerate(targets):
                for b in range(data.shape[3]):
                    seg = x125[:, int(a * 125):int((a + w) * 125), t, b]
                    s = ssvep.fbcca_scores(seg, TARGET_HZ, 125)
                    hits.append(int(np.argmax(s)) == k)
                    if w == ssvep.WIN_S:
                        o = np.sort(s)[::-1]
                        if (o[0] - o[1]) / o[0] >= ssvep.MARGIN:
                            decided += 1
                            right += int(np.argmax(s)) == k
                        s2 = ssvep.fbcca_scores(seg, ssvep.FREQS, 125)
                        acc_ours.append(int(np.argmax(s2)) == k)
                        first.append(live(x125[:, :, t, b], k))
                        seg9 = data[:, int(a * FS_B):int((a + w) * FS_B), t, b]
                        acc_nine.append(int(np.argmax(ssvep.fbcca_scores(seg9, TARGET_HZ, FS_B))) == k)
            acc[w].append(np.mean(hits))
            line.append(f"{w:.1f}s {np.mean(hits):4.0%}")
        print(f"{os.path.basename(f):10s} " + "  ".join(line))
    print("\nMean over people (4 targets, chance 25%):")
    for w in WINDOWS:
        p = float(np.mean(acc[w]))
        print(f"  {w:.1f} s window: {p:5.1%}  (range {min(acc[w]):.0%} to {max(acc[w]):.0%}), speed {itr(4, p, w + GAZE_S):.0f} bits/min")
    print(f"\n  2 s with our exact tile rates (8.57 Hz template on 8.6 Hz data): {np.mean(acc_ours):.1%}")
    print(f"  2 s with all 9 back channels at 250 Hz (lab ceiling): {np.mean(acc_nine):.1%}")
    got = [f for f in first if f[0] is not None]
    print(f"\nLive decoder, streamed trial by trial ({len(first)} trials):")
    print(f"  first choice right: {sum(f[0] for f in got) / len(first):.1%}, wrong: {sum(not f[0] for f in got) / len(first):.1%}, "
          f"no choice in 5 s: {1 - len(got) / len(first):.1%}; median time to choose {np.median([f[1] for f in got]):.1f} s")
    if args.still:
        n_ev, secs = 0, 0.0
        for p in args.still:
            eeg = np.loadtxt(p, delimiter=",").T[:, int(8 * 125):int(30 * 125)]
            dec = ssvep.Look()
            for i in range(int(ssvep.WIN_S * 125), eeg.shape[1] + 1, 31):
                n_ev += len(dec.update(eeg[:, :i], i / 125)[1])
            secs += eeg.shape[1] / 125 - ssvep.WIN_S
        print(f"  false choices on our headset with nothing flashing: {n_ev} in {secs:.0f} s")


if __name__ == "__main__":
    main()
