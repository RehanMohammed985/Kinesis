"""Run the live detectors on baseline recordings, the same way the server does
(every ~50 ms on the last 1.2 s), and report what fired when.

Protocol: eyes open 0-5 s, eyes closed 5-20 s, open 20-35 s, jaw clenches
~35-56 s, rest. Times are give or take, so windows are padded.

python scripts/evaluate_baseline.py kinesis/data/raw/baseline_trial*/recording_*.csv
Files saved as stacked 500-row snapshots are rebuilt first (see
scripts/reconstruct_windows.py).
"""
import sys
from pathlib import Path

import numpy as np
from scipy.signal import butter, find_peaks, sosfiltfilt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.signal.live import CH_CLENCH, FS, Detectors, quality  # noqa: E402
from scripts.reconstruct_windows import reconstruct  # noqa: E402

CLENCH_WIN = (33, 56)
CLOSED_WIN = (5, 22)


def load(path):
    x = np.loadtxt(path, delimiter=",")
    if x.shape[0] % 500 == 0 and x.shape[0] > 60 * FS * 5:  # stacked snapshots
        x, _ = reconstruct(x)
    return x.T  # channels x samples


def reference_clenches(eeg):
    """Clear clench bursts found offline with the whole recording in view."""
    sos = butter(4, [20, 55], btype="band", fs=FS, output="sos")
    env = []
    for c in CH_CLENCH:
        y = sosfiltfilt(sos, eeg[c - 1]) ** 2
        sm = np.convolve(y, np.ones(int(0.4 * FS)) / int(0.4 * FS), "same")
        env.append(sm / np.median(sm[: int(4.5 * FS)]))
    med = np.median(env, axis=0)
    pk, _ = find_peaks(np.log(med), height=np.log(6), prominence=np.log(2.2), distance=int(0.5 * FS))
    return [p / FS for p in pk]


def run(eeg):
    d = Detectors()
    d.calibrate_rest(eeg[:, : int(4.5 * FS)])
    ev = {"clench": [], "blink2": [], "alpha": []}
    for i in range(int(1.2 * FS), eeg.shape[1], 6):
        _, es = d.update(eeg[:, i - int(1.2 * FS): i], now=i / FS)
        for e in es:
            ev[e["input"]].append(round(i / FS, 1))
    return ev


def inside(ts, win):
    return [t for t in ts if win[0] <= t <= win[1]]


def main(paths):
    tot = {"ref": 0, "caught": 0, "false_rest": 0, "rest_s": 0.0, "blink2": 0, "alpha_in": 0, "alpha_out": 0}
    for p in paths:
        eeg = load(p)
        dur = eeg.shape[1] / FS
        ref = reference_clenches(eeg)
        ev = run(eeg)
        rest_s = CLENCH_WIN[0] - 4.5
        false_rest = [t for t in ev["clench"] if t < CLENCH_WIN[0]]
        q = quality(eeg[:, int(1 * FS): int(3 * FS)])
        tot["ref"] += len(inside(ref, CLENCH_WIN))
        tot["caught"] += len(inside(ev["clench"], CLENCH_WIN))
        tot["false_rest"] += len(false_rest)
        tot["rest_s"] += rest_s
        tot["blink2"] += len(ev["blink2"])
        tot["alpha_in"] += len(inside(ev["alpha"], CLOSED_WIN))
        tot["alpha_out"] += len(ev["alpha"]) - len(inside(ev["alpha"], CLOSED_WIN))
        print(f"\n{Path(p).parent.name}/{Path(p).name}  ({dur:.1f} s)")
        print(f"  clench: {len(inside(ev['clench'], CLENCH_WIN))} detected for {len(inside(ref, CLENCH_WIN))} clear clenches; "
              f"false triggers before the clench section: {len(false_rest)}; after it: {[t for t in ev['clench'] if t > CLENCH_WIN[1]]}")
        print(f"  double blink (none asked for): {ev['blink2']}")
        print(f"  eyes closed: during 5-22 s {inside(ev['alpha'], CLOSED_WIN)}, elsewhere {[t for t in ev['alpha'] if t not in inside(ev['alpha'], CLOSED_WIN)]}")
        print("  contact: " + ", ".join(f"{c['site']} {c['state']}" + (f" ({c['reason']})" if c['reason'] != 'ok' else "") for c in q))
    print("\nTOTAL")
    print(f"  clench: {tot['caught']} detected for {tot['ref']} clear clenches, {tot['false_rest']} false triggers in {tot['rest_s']:.0f} s of rest")
    print(f"  double blink false triggers: {tot['blink2']}")
    print(f"  eyes closed: {tot['alpha_in']} during eyes-closed, {tot['alpha_out']} elsewhere")


if __name__ == "__main__":
    main(sys.argv[1:])
