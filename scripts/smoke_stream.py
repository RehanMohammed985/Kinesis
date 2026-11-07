"""Smoke test: stream 10 seconds, print per-channel stats, write a CSV.

python scripts/smoke_stream.py --synthetic
python scripts/smoke_stream.py --port /dev/cu.usbmodemXXXX [--imu]
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.board.knight import MONTAGE, Knight  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--imu", action="store_true")
    ap.add_argument("--seconds", type=float, default=10)
    ap.add_argument("--out", default="data/sessions/smoke.csv")
    args = ap.parse_args()
    if not args.synthetic and not args.port:
        ap.error("--port or --synthetic required")

    k = Knight(port=args.port, synthetic=args.synthetic, imu=args.imu)
    print(f"board id {k.board_id}, fs {k.fs} Hz, {len(k.eeg_rows)} eeg rows")
    k.start()
    print("streaming...")
    time.sleep(args.seconds)
    eeg, ts = k.latest_seconds(args.seconds)
    k.stop()

    print(f"{'ch':>3} {'site':>5} {'mean uV':>10} {'std uV':>10} {'p2p uV':>10}")
    for i in range(eeg.shape[0]):
        ch = i + 1
        row = eeg[i]
        print(f"{ch:>3} {MONTAGE.get(ch, '-'):>5} {row.mean():>10.1f} {row.std():>10.1f} {np.ptp(row):>10.1f}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(args.out, np.vstack([ts, eeg]).T, delimiter=",",
               header="ts," + ",".join(f"ch{i+1}" for i in range(eeg.shape[0])), comments="")
    print(f"wrote {args.out}")
    print("flat channel (std < 0.5 uV) = no contact; p2p near 8000 uV at gain 12 = railed")


if __name__ == "__main__":
    main()
