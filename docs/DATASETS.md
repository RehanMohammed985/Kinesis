# Datasets: what the two data people should do

Kinesis does not need a trained model to work. Every detector is a threshold or a per-person template. Datasets are for three things: validating detectors before the headset is wired, cutting SSVEP calibration time, and producing the numbers on the results slide.

## Status (Nov 7)
Three baseline trials are in (see kinesis/data/baseline/README.md). Clench: 43 detected for 42 clear clenches, 0 false triggers. Five clench and double-blink trials are in (kinesis/data/gestures/README.md). The fixed rules caught 0 double blinks, so clench and double blink now come from a model each person trains in calibration, pooled with these recordings (kinesis/signal/learned.py). On a held-out trial: 64 of 71 double blinks, 31 of 41 clenches, 1 mix-up, 2 false events in 145 s still. The electrodes are on pins 2 to 7 (kinesis/montage.py). Record with scripts/record.py from now on: looping get_current_board_data() and appending saves every sample about 60 times.

## Priority 1: our own recordings (most of the value)
- Record every calibration and every demo run with `kinesis/data/recorder.py` (BrainFlow write_file + JSON sidecar with cue timestamps).
- Build `replay.py` on BrainFlow's PLAYBACK_FILE_BOARD so detectors run on recordings exactly as live.
- Metrics notebook: for each teammate and each input, detection rate on cued events, false positives per minute at rest, SSVEP accuracy and ITR (NeuroPawn's evaluate_trca.py reports both), Fit score before and after paste. Aim for 4+ people.

## Priority 2: public sets to validate detectors today, before the board is clean
- OpenBMI (Lee et al. 2019, GigaScience): 54 subjects, SSVEP 4 targets, ERP, MI, 62 ch, 1000 Hz. Use the SSVEP block: pick the occipital and parieto-occipital channels closest to ours (Oz, O1, O2, POz), downsample to 125 Hz, run our CCA and TRCA code, report accuracy at 1 s and 2 s windows. This also tests cross-subject TRCA transfer (stretch goal in ml-agent). http://gigadb.org/dataset/100542
- MOABB (Python library) wraps OpenBMI SSVEP and others with one loader: `pip install moabb`. Fastest path.
- EEG eye-blink detection: any PhysioNet EEG with EOG channels (e.g., Sleep-EDF has EOG). Use it to sanity check the blink peak threshold (~100 uV) and the 600 ms double-blink window.
- Sleep-EDF (PhysioNet): Fpz-Cz and Pz-Oz at 100 Hz. Use wake epochs with eyes closed vs open to set the alpha ratio threshold and to validate the alpha detector.
- Jaw/EMG: no good public scalp-EMG clench set; rely on our own recordings. Clench is 10-50x EEG amplitude, thresholding is enough.

## Priority 3: things that look useful but are not
- TUH EEG, CHB-MIT: seizure datasets, irrelevant to this product.
- Inner speech / imagined speech sets: at chance on dry consumer EEG; do not pursue.
- Motor imagery sets: we are not building MI.

## Deliverables from the data team by hour 12
1. `replay.py` working on our recordings
2. Threshold recommendations for EMG, blink, alpha from our data
3. OpenBMI SSVEP results table for CCA vs TRCA at 1 s / 2 s windows on Oz/O1/O2/POz
4. The results slide numbers, filled in from every teammate's run
