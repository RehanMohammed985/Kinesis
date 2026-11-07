"""Guided recording for the data team. Prints a cue, inserts a marker, saves
everything to data/sessions/<name>-<time>.csv (BrainFlow format; markers are
in the last row). Close the EXG Visualizer first.

python scripts/record.py --port /dev/cu.usbmodemXXXX --name rehan

Markers: 1 rest eyes open, 2 eyes closed, 3 clench cue, 4 double blink cue,
5 look at tile (SSVEP done separately with NeuroPawn's repo).
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.board.knight import Knight  # noqa: E402

PLAN = [
    ("Sit still, eyes open, look at the screen", 1, 30, 1),
    ("Close your eyes and relax", 2, 20, 1),
    ("Eyes open, relax", 1, 10, 1),
    ("CLENCH your jaw now, then let go", 3, 3, 10),
    ("DOUBLE BLINK now", 4, 3, 10),
    ("Close your eyes until the beep", 2, 6, 4),
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
        for text, marker, seconds, reps in PLAN:
            for r in range(reps):
                label = f"{text}" + (f"  ({r + 1}/{reps})" if reps > 1 else "")
                print(f"\n>>> {label}")
                k.mark(marker)
                time.sleep(seconds)
                if marker == 2 and reps > 1:
                    print("\a beep, open your eyes")
                    time.sleep(3)
    finally:
        k.stop()
    print(f"\nDone. Saved {out}")


if __name__ == "__main__":
    main()
