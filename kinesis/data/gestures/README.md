# Double-blink and clench recordings, rebuilt

Three trials recorded on our headset (Nov 7). Protocol, give or take: still about 10 s, eyes closed about 10 s, still, double blinks (10 to 17 s), jaw clenches (about 11 s), still. Columns are channels 1 to 8 at 125 Hz, about 65 s each.

The originals are on the data-collection branch (kinesis/data/raw/double_trial*/). They were saved as overlapping 500-row snapshots, so these files are rebuilt with scripts/reconstruct_windows.py and each sample appears once.

## What the recordings show

- **Channels:** channel 1 recorded nothing (it was switched off). Channel 2 was floating. Channels 3 to 7 had signal, so channel 7 has an electrode on it. Check which pin each electrode is plugged into.
- **Ear clip:** channels 3 to 7 move almost identically (correlation 0.99 in trials 1 and 3). That means the ear clip, not the scalp, dominates. Re-seat it.
- **Eyes closed:** no alpha increase in any trial, so eyes-closed detection will not work with this fit.
- **Double blink:** a burst every channel shares, plus activity on channel 7 only.
- **Clench:** activity that differs channel to channel, on all of them.

## Fixed rules vs learned model

The fixed rules (kinesis/signal/live.py):
- caught 0 double blinks
- fired "clench" 43 times during the double blinks

The learned model (kinesis/signal/learned.py) uses shrinkage LDA on 22 log-power features and is trained per person during the app's calibration. Results, leave one trial out (trained on two trials, streamed through the live detector on the third):

| | trial 1 | trial 2 | trial 3 | total |
|---|---|---|---|---|
| double blink events | 8 (17 s of blinking) | 6 (10 s) | 6 (12 s) | 20 |
| double blinks read as clench | 0 | 1 | 0 | 1 |
| clench events (bursts seen offline) | 15 (14) | 9 (17) | 15 (15) | 39 (46) |
| clenches read as double blink | 0 | 0 | 0 | 0 |
| false events while still | 2 in 23 s | 0 in 30 s | 1 in 30 s | 3 in 82 s |
| frames right: rest / clench / double blink | 100 / 99 / 96% | 100 / 99 / 89% | 100 / 100 / 99% | |

Calibrating on trial 3 alone, the way the app does it, then streaming trials 1 and 2:
- 9 and 6 double blinks
- 15 and 9 clenches
- 1 mix-up

The double blinks were done back to back with almost no pause, so there is no exact count to score against. Next recording: pause about 2 s between double blinks (scripts/record.py cues one every 3 s).

`model.json` is the model trained on all three trials. The core uses it until someone calibrates in the app, which saves their own model to data/gesture_model.json.

Run: `python scripts/train_gestures.py kinesis/data/gestures/double_trial*.csv --save kinesis/data/gestures/model.json`
