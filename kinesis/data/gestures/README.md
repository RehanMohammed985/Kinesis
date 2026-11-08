# Clench and double-blink recordings, rebuilt

Five trials recorded on our headset (Nov 7). Trials 4 and 5 were recorded with the ear clip tightened. Protocol, give or take: still about 10 s, eyes closed about 10 s, still, a section of jaw clenches, a section of double blinks, still. Columns are channels 1 to 8 at 125 Hz, about 65 s each.

The originals are on the data-collection branch (kinesis/data/raw/double_trial*/). They were saved as overlapping 500-row snapshots, so these files are rebuilt with scripts/reconstruct_windows.py and each sample appears once. `sections.json` marks each section.

## What the recordings show

- **Wiring:** the electrodes are on pins 2 to 7, not 1 to 6. Pin 1 read nothing and pin 8 was off; in the baseline recordings both floated. The core now reads pins 2 to 7 (kinesis/montage.py).
- **Ear clip:** tightening it lowered the noise on every channel (1 to 40 Hz spread: 1,300 to 2,100 in trials 4 and 5 vs 2,700 to 23,000 in trials 1 to 3). Pin 5 (POz) floated in trials 4 and 5, so re-seat it.
- **Eyes closed:** trial 4 showed a small alpha rise (about 1.6x), trial 5 none. Not usable yet.
- **Which section is which:** the notes said double blinks came first, but the signal says the first section is clenches:
  - It looks like the clench-only baseline: one burst every channel shares, because the ear clip sits next to the jaw muscle.
  - It also shows up at the temple (pin 7) or the back of the head (pin 2, neck muscle). Blinks never reach the back of the head.
  - The second section is the forehead channel alone (pin 6), with two spikes about 0.2 s apart, roughly once a second. That is a double blink.
  - Labels follow the signal. In the app this never matters, because calibration labels each step by what the person was asked to do.

## Results

The fixed rules (kinesis/signal/live.py) caught 0 double blinks and called them clenches.

The learned model (kinesis/signal/learned.py) uses shrinkage LDA on log-power features. It was tested leave one trial out: trained on 4 trials, then streamed through the live detector on the 5th.

| | 1 | 2 | 3 | 4 | 5 | total |
|---|---|---|---|---|---|---|
| double blinks caught (bursts seen offline) | 14 (14) | 9 (17) | 14 (15) | 13 (13) | 14 (12) | 64 (71) |
| clench events (bursts seen offline) | 14 (10) | 6 (8) | 9 (9) | 5 (8) | 6 (6) | 40 (41) |
| mix-ups | 0 | 0 | 1 | 1 | 0 | 2 |
| false events while still | 2 in 23 s | 0 in 30 s | 0 in 30 s | 0 in 32 s | 0 in 31 s | 2 in 145 s |

A clench re-arms once the jaw lets go (activity under 25% of its peak), so quick repeated clenches each count; two within 0.7 s are read as a double clench. Before this change clench re-armed only at full rest and caught 31 of 41. Trial 1 shows a few extra events (14 for 10 bursts) where clenches wobbled.

**In-app calibration** (still, 5 clenches, 5 double blinks) pools the person's attempts, weighted 3x, with these recordings. Calibrating on one trial and testing on another:
- pooled never did worse than calibration alone
- calibrate on trial 5, test on trial 4: alone, 1 clench caught and 4 mix-ups; pooled, 2 and 2
- calibrate on trial 1, test on trial 2: alone, 1 clench caught; pooled, 6

`model.json` is trained on all five trials. The core uses it until someone calibrates, which saves their own model to data/gesture_model.json.

Run: `python scripts/train_gestures.py kinesis/data/gestures/double_trial*.csv --save kinesis/data/gestures/model.json`
