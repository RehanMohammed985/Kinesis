"""Guided recording for the data team. Prints a cue, inserts a marker, saves
everything to data/sessions/<name>-<time>.csv (BrainFlow format; markers are
in the last row). Close the EXG Visualizer first.

python scripts/record.py --port /dev/cu.usbmodemXXXX --name rehan

Protocol (2:30) is in PLAN below; the script prints each cue with a timestamp.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.board.knight import Knight  # noqa: E402

# (cue, marker, seconds). Markers: 1 eyes open still, 2 eyes closed,
# 3 clench, 4 double blink. Total 2:30.
PLAN = [
    ("Sit still, eyes OPEN, look at the screen", 1, 10),
    ("Eyes CLOSED, relax", 2, 10),
    ("Eyes OPEN", 1, 10),
    ("Eyes CLOSED, relax", 2, 10),
    ("Eyes OPEN", 1, 10),
    ("Eyes CLOSED, relax", 2, 10),
    ("Eyes OPEN, sit still", 1, 10),
] + [("DOUBLE BLINK now", 4, 3)] * 10 + [
    ("Sit still, eyes open", 1, 10),
] + [("CLENCH your jaw (1 s), then let go", 3, 3)] * 10 + [
    ("Sit still, eyes open", 1, 10),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--name", default="anon")
    args = ap.parse_args()
    k = Knight(port=args.port, synthetic=args.synthetic)
    print("Turning on channels (about 30 s)...")
    k.start()
    out = Path("data/sessions") / f"{args.name}-{time.strftime('%Y%m%d-%H%M%S')}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    k.start_recording(str(out))
    print(f"Recording to {out}\n")
    try:
        t0 = time.time()
        for i, (text, marker, seconds) in enumerate(PLAN):
            mm, ss = divmod(int(time.time() - t0), 60)
            print(f"[{mm}:{ss:02d}] {text}")
            k.mark(marker)
            time.sleep(seconds)
    finally:
        k.stop()
    print(f"\nDone. Saved {out}")


if __name__ == "__main__":
    main()
