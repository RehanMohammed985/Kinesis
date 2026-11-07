import csv
import random
import time
from pathlib import Path
import tkinter as tk

# ---------- Configuration ----------
SESSION_DIR = Path("kinesis_session_001")
N_BLOCKS = 5
TRIALS_PER_CLASS_PER_BLOCK = 3

# 3 + 5 + 10 + 12 = 30 seconds
CUE_SECONDS = 5
PREPARE_SECONDS = 5
IMAGERY_SECONDS = 20
REST_SECONDS = 15

RANDOM_SEED = 42
# -----------------------------------

SESSION_DIR.mkdir(exist_ok=True)

rng = random.Random(RANDOM_SEED)

schedule = []
trial_id = 1

for block_id in range(1, N_BLOCKS + 1):
    labels = (
        ["yes"] * TRIALS_PER_CLASS_PER_BLOCK
        + ["no"] * TRIALS_PER_CLASS_PER_BLOCK
    )
    rng.shuffle(labels)

    for label in labels:
        schedule.append({
            "trial_id": trial_id,
            "block_id": block_id,
            "label": label
        })
        trial_id += 1

with open(SESSION_DIR / "schedule.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=["trial_id", "block_id", "label"]
    )
    writer.writeheader()
    writer.writerows(schedule)

event_file = open(
    SESSION_DIR / "events.csv", "w", newline="", buffering=1
)
event_writer = csv.writer(event_file)
event_writer.writerow([
    "trial_id", "block_id", "label",
    "stage", "host_monotonic_ns"
])

root = tk.Tk()
root.title("Kinesis Recording")
root.geometry("1000x700")
root.configure(bg="black")

screen = tk.Label(
    root,
    text="Start EEG acquisition first.\n\nPress SPACE to begin.",
    font=("Arial", 32),
    fg="white",
    bg="black"
)
screen.pack(expand=True)

index = 0
waiting = True
closed = False

def log_event(stage):
    trial = schedule[index]
    event_writer.writerow([
        trial["trial_id"],
        trial["block_id"],
        trial["label"],
        stage,
        time.monotonic_ns()
    ])

def show_stage(text, stage, seconds, next_function, tone=False):
    screen.config(text=text)
    log_event(stage)

    if tone:
        root.bell()  # Verify the tone is audible before recording.

    root.after(int(seconds * 1000), next_function)

def start_trial():
    global waiting
    waiting = False

    trial = schedule[index]
    show_stage(
        trial["label"].upper(),
        "cue",
        CUE_SECONDS,
        preparation
    )

def preparation():
    show_stage("+", "prepare", PREPARE_SECONDS, imagery)

def imagery():
    show_stage(
        "+",
        "imagery",
        IMAGERY_SECONDS,
        rest,
        tone=True
    )

def rest():
    show_stage("Rest", "rest", REST_SECONDS, finish_trial)

def finish_trial():
    global index, waiting

    log_event("end")
    previous_block = schedule[index]["block_id"]
    index += 1

    if index >= len(schedule):
        screen.config(text="Recording complete.\nStop EEG acquisition.")
        return

    if schedule[index]["block_id"] != previous_block:
        waiting = True
        screen.config(
            text="Take a break.\n\nPress SPACE when ready."
        )
    else:
        start_trial()

def on_space(event):
    if waiting and index < len(schedule):
        start_trial()

def close():
    global closed
    if not closed:
        closed = True
        event_file.close()
        root.destroy()

root.bind("<space>", on_space)
root.bind("<Escape>", lambda event: close())
root.protocol("WM_DELETE_WINDOW", close)

try:
    root.mainloop()
finally:
    if not event_file.closed:
        event_file.close()
