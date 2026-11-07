"""Yes/no trials with your full-screen cues, recorded with markers.

Same flow as the team's first version (word cue, prepare, imagery, rest,
breaks between blocks), but this one also runs the headset, so every stage
is marked inside the recording itself. Without that, the trials cannot be
lined up with the EEG afterwards.

Run it on the laptop the headset is plugged into, with the EXG Visualizer closed:
python kinesis/stimulus/recording_task.py --port COM5 --name kennedy --mode mouth
python kinesis/stimulus/recording_task.py --synthetic --blocks 1                 # dry run
Then: python scripts/analyze_words.py data/sessions/words-kennedy-mouth-*.csv

Default: 4 blocks x 10 trials (5 yes, 5 no) = 40 trials, 16 s each, about 12 min.
Imagery is 6 s, scored as three 2 s pieces per trial.
"""
import argparse
import json
import random
import sys
import time
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kinesis.board.knight import Knight  # noqa: E402
from kinesis.montage import MONTAGE  # noqa: E402
from kinesis.signal.words import M_CUE0, M_FIX, M_GO0, M_REST  # noqa: E402

WORDS = ["yes", "no"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--name", default="anon")
    ap.add_argument("--mode", choices=["imagine", "mouth"], default="mouth")
    ap.add_argument("--blocks", type=int, default=4)
    ap.add_argument("--per-word", type=int, default=5, help="trials per word per block")
    ap.add_argument("--cue", type=float, default=2.0)
    ap.add_argument("--prepare", type=float, default=2.0)
    ap.add_argument("--imagery", type=float, default=6.0)
    ap.add_argument("--rest", type=float, default=6.0)
    a = ap.parse_args()

    rng = random.Random()
    schedule = []
    for block in range(1, a.blocks + 1):
        labels = [w for w in range(len(WORDS)) for _ in range(a.per_word)]
        rng.shuffle(labels)
        schedule += [(block, w) for w in labels]

    k = Knight(port=a.port, synthetic=a.synthetic)
    print("Turning on channels (about 30 s)...")
    k.start()
    stem = f"words-{a.name}-{a.mode}-{time.strftime('%Y%m%d-%H%M%S')}"
    out = Path("data/sessions") / f"{stem}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    k.start_recording(str(out))
    meta = {"words": WORDS, "mode": a.mode, "trials": len(schedule), "pins": MONTAGE, "board_id": k.board_id,
            "go_seconds": a.imagery, "timing": {"cue": a.cue, "prepare": a.prepare, "imagery": a.imagery, "rest": a.rest},
            "markers": {"prepare": M_FIX, "cue": f"{M_CUE0}+word", "imagery": f"{M_GO0}+word", "rest": M_REST}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2))
    print(f"Recording to {out}")

    how = "say it in your head, no movement" if a.mode == "imagine" else "mouth it silently, no sound"
    root = tk.Tk()
    root.title("Kinesis Recording")
    root.geometry("1000x700")
    root.configure(bg="black")
    screen = tk.Label(root, text=f"On the + : {how}.\n\nPress SPACE to begin.", font=("Arial", 32), fg="white", bg="black")
    screen.pack(expand=True)
    state = {"i": 0, "waiting": True}

    def stage(text, marker, seconds, then, tone=False):
        screen.config(text=text)
        k.mark(marker)
        if tone:
            root.bell()
        root.after(int(seconds * 1000), then)

    def start_trial():
        state["waiting"] = False
        w = schedule[state["i"]][1]
        stage(WORDS[w].upper(), M_CUE0 + w, a.cue, prepare)

    def prepare():
        stage("", M_FIX, a.prepare + rng.random() * 0.5, imagery)   # blank, so the word is gone

    def imagery():
        w = schedule[state["i"]][1]
        stage("+", M_GO0 + w, a.imagery, rest, tone=True)

    def rest():
        stage("Rest", M_REST, a.rest + rng.random(), finish)

    def finish():
        block = schedule[state["i"]][0]
        state["i"] += 1
        if state["i"] >= len(schedule):
            screen.config(text=f"Recording complete.\n\n{len(schedule)} trials saved.")
            root.after(1500, close)
        elif schedule[state["i"]][0] != block:
            state["waiting"] = True
            screen.config(text=f"Take a break. Block {block} of {a.blocks} done.\n\nPress SPACE when ready.")
        else:
            start_trial()

    def close(*_):
        try:
            k.stop()
        finally:
            root.destroy()
            print(f"Saved {out}\nScore it: python scripts/analyze_words.py {out}")

    root.bind("<space>", lambda e: start_trial() if state["waiting"] and state["i"] < len(schedule) else None)
    root.bind("<Escape>", close)
    root.protocol("WM_DELETE_WINDOW", close)
    root.mainloop()


if __name__ == "__main__":
    main()
