# Baseline recordings, rebuilt

Three trials recorded on our headset (Nov 7). Protocol, give or take: eyes open 5 s, eyes closed 15 s, eyes open 15 s, about 15 jaw clenches, 10 s rest. Columns are channels 1 to 8 (1 Oz, 2 O1, 3 O2, 4 POz, 5 Fp1, 6 T7, 7 and 8 unused). 125 Hz, about 64.5 s each.

The originals (data-collection branch, kinesis/data/raw/baseline_trial*/) were saved as overlapping 500-row snapshots, about 350k rows each. These files are rebuilt with scripts/reconstruct_windows.py so each sample appears once. Units are not BrainFlow microvolts (likely a gain mismatch); the detectors only use ratios to each person's rest, so units do not matter.

Evaluate: `python scripts/evaluate_baseline.py kinesis/data/baseline/trial*.csv`

Results with the tuned detectors (kinesis/signal/live.py):
- jaw clench: 43 detected for 42 clear clenches, 0 false triggers in 86 s of rest
- double blink: 0 false triggers (no deliberate blinks were recorded, so detection rate is untested)
- eyes closed: no hits and no misfires; alpha barely changed with eyes closed because Oz and O1 were floating
- contact: Oz floating in all three trials, O1 in trial 2; channel 8 floating (switch it off)

Next recording: re-seat Oz and O1, switch channel 8 off, then record 10 deliberate double blinks and 3 rounds of eyes closed for 10 s, with scripts/record.py.
