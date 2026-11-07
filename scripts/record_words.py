"""Record yes/no word trials with markers, so they can be scored.

Each trial: a "+" to focus, the word for 1 s, a blank, then GO for 2 s:
say the word in your head (--mode imagine) or silently mouth it with no sound
(--mode mouth). Then rest. The word is gone before GO on purpose, so the
classifier cannot just learn what the word looked like on screen.

python scripts/record_words.py --port COM5 --name rehan --mode mouth
python scripts/record_words.py --synthetic --trials 4            # dry run
Then: python scripts/analyze_words.py data/sessions/words-rehan-mouth-*.csv

Close the EXG Visualizer first (only one program can use the headset).
Saves BrainFlow format (markers in the marker row) plus a .json with the words.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.board.knight import Knight  # noqa: E402
from kinesis.montage import MONTAGE  # noqa: E402
from kinesis.signal.words import M_CUE0, M_FIX, M_GO0, M_REST  # noqa: E402

BIG = {
    "+": "                +",
    "GO": "        >>>   GO   <<<",
}


def show(text, sub=""):
    sys.stdout.write("\033[2J\033[H\n\n\n\n")      # clear the terminal
    sys.stdout.write(f"{BIG.get(text, '            ' + text.upper())}\n\n")
    if sub:
        sys.stdout.write(f"        {sub}\n")
    sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--name", default="anon")
    ap.add_argument("--mode", choices=["imagine", "mouth"], default="mouth")
    ap.add_argument("--words", default="yes,no")
    ap.add_argument("--trials", type=int, default=25, help="per word")
    args = ap.parse_args()
    words = [w.strip() for w in args.words.split(",") if w.strip()]
    order = [i for i in range(len(words)) for _ in range(args.trials)]
    random.shuffle(order)

    k = Knight(port=args.port, synthetic=args.synthetic)
    print("Turning on channels (about 30 s)...")
    k.start()
    stem = f"words-{args.name}-{args.mode}-{time.strftime('%Y%m%d-%H%M%S')}"
    out = Path("data/sessions") / f"{stem}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    k.start_recording(str(out))
    meta = {"words": words, "mode": args.mode, "trials_per_word": args.trials, "pins": MONTAGE, "board_id": k.board_id,
            "markers": {"fix": M_FIX, "cue": f"{M_CUE0}+word", "go": f"{M_GO0}+word", "rest": M_REST}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2))
    how = "say it in your head, no movement" if args.mode == "imagine" else "mouth it silently, no sound"
    try:
        show("Sit still", f"{len(order)} trials, about {len(order) * 7 // 60 + 1} min. On GO: {how}.")
        k.mark(M_REST)
        time.sleep(8)
        for n, w in enumerate(order, 1):
            show("+", f"trial {n} of {len(order)}")
            k.mark(M_FIX)
            time.sleep(1.0 + random.random() * 0.5)
            show(words[w])
            k.mark(M_CUE0 + w)
            time.sleep(1.0)
            show(" ")
            time.sleep(0.6 + random.random() * 0.4)
            show("GO", how)
            k.mark(M_GO0 + w)
            time.sleep(2.0)
            show("rest", "blink and relax")
            k.mark(M_REST)
            time.sleep(2.0 + random.random())
    finally:
        k.stop()
    show("Done", f"Saved {out}")
    print(f"\nScore it: python scripts/analyze_words.py {out}")


if __name__ == "__main__":
    main()
