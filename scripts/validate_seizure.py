"""Validate the seizure-like detector on the Bonn epilepsy dataset
(Andrzejak et al. 2001). Single channel, 23.6 s per recording, 173.61 Hz.
Sets: Z healthy eyes open, O healthy eyes closed (scalp); N, F interictal and
S seizure (intracranial, same patients).

The fair test is S vs N+F: same patients, same electrodes, seizure vs not.
S vs Z+O is shown too but overstates performance (intracranial vs scalp).

Each recording is resampled to 125 Hz (our board), cut into 4 s windows with
a 2 s hop, and scored against a baseline taken from non-seizure recordings,
the way the live monitor uses the person's own rest baseline. A recording is
flagged when SEIZURE_RUN (4) or more consecutive windows are seizure-like, which mirrors the
live rule of a sustained run before alerting.

python scripts/validate_seizure.py /path/to/folder/with/Z,O,N,F,S
"""
import glob
import os
import sys
from pathlib import Path

import numpy as np
from scipy.signal import resample

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.agent.brain import SEIZURE, SEIZURE_RUN, seizure_like, window_features  # noqa: E402

FS_BONN = 173.61
FS = 125
WIN, HOP = 4 * FS, 2 * FS


def load(root, s):
    files = sorted(glob.glob(os.path.join(root, "**", f"{s}[0-9][0-9][0-9].[tT][xX][tT]"), recursive=True))
    seen, out = set(), []
    for f in files:
        name = os.path.basename(f).upper()
        if name in seen:
            continue
        seen.add(name)
        x = np.loadtxt(f)
        out.append(resample(x, int(round(len(x) * FS / FS_BONN))))
    return out


def windows(x):
    return [x[i:i + WIN] for i in range(0, len(x) - WIN + 1, HOP)]


def score(recs, base):
    flags, win_hits, n_win = [], 0, 0
    for x in recs:
        hits = [seizure_like(window_features(w), base)[0] for w in windows(x)]
        win_hits += sum(hits)
        n_win += len(hits)
        run = best = 0
        for h in hits:
            run = run + 1 if h else 0
            best = max(best, run)
        flags.append(best >= SEIZURE_RUN)
    return np.mean(flags), win_hits / max(n_win, 1), len(recs)


def baseline_from(recs):
    feats = [window_features(w) for x in recs for w in windows(x)]
    return {k: float(np.median([f[k] for f in feats])) for k in ("line_length", "rms")}


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    sets = {s: load(root, s) for s in "ZONFS"}
    print("recordings per set:", {s: len(v) for s, v in sets.items()})
    print("thresholds:", SEIZURE, "run:", SEIZURE_RUN)

    # Fair test: baseline from interictal recordings of the same patients.
    # Half of N+F builds the baseline, the other half measures false alarms.
    inter = sets["N"] + sets["F"]
    rng = np.random.default_rng(0)
    idx = rng.permutation(len(inter))
    base_part = [inter[i] for i in idx[: len(idx) // 2]]
    test_part = [inter[i] for i in idx[len(idx) // 2:]]
    base = baseline_from(base_part)
    sens, sw, ns = score(sets["S"], base)
    fa, fw, nf = score(test_part, base)
    print("\nSeizure vs interictal (same patients, intracranial)")
    print(f"  seizure recordings flagged:      {sens:6.1%}  ({ns} recordings, {sw:.1%} of windows)")
    print(f"  non-seizure recordings flagged:  {fa:6.1%}  ({nf} recordings, {fw:.1%} of windows)")

    base_scalp = baseline_from(sets["Z"] + sets["O"])
    sens2, _, _ = score(sets["S"], base_scalp)
    fa2, _, n2 = score(sets["Z"] + sets["O"], base_scalp)
    print("\nSeizure vs healthy scalp (overstates performance, different electrodes)")
    print(f"  seizure recordings flagged:      {sens2:6.1%}")
    print(f"  healthy recordings flagged:      {fa2:6.1%}  ({n2} recordings)")


if __name__ == "__main__":
    main()
