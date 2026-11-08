# Datasets

Kinesis is built and scored on **public, labeled EEG datasets**, using only what our headset has (its channels and 125 Hz). Our own recordings are the **baseline**: contact checks, each person's rest level, and the seed for the gesture model.

Download the public sets and see their labels: `python scripts/get_datasets.py` (saves to `data/external/`, kept out of git).

## Primary: public labeled datasets

### Tsinghua SSVEP benchmark
- **Source:** http://bci.med.tsinghua.edu.cn/download.html
- **Citation:** Wang Y, Chen X, Gao X, Gao S. A benchmark dataset for SSVEP-based brain-computer interfaces. IEEE TNSRE 25(10), 2017.
- **People and recording:** 35 people, 64 channels, 250 Hz. 40 targets on a screen, each flashing at its own rate from 8 to 15.8 Hz in 0.2 Hz steps, with its own phase. 6 blocks.
- **Labels:**
  - Each `S<n>.mat` holds `data[64 channels, 1500 samples, 40 targets, 6 blocks]`, so the label is the target index.
  - `Freq_Phase.mat` gives each target's rate and phase.
  - Each epoch starts 0.5 s before the flashing.
- **Our use:** design, tuning and validation of the Look decoder (`kinesis/signal/ssvep.py`).
  - Only Oz, O1, O2, POz, resampled to 125 Hz.
  - The 4 targets closest to our tiles: 8.6, 10, 12, 15 Hz.
  - Tuned on people 1 to 10, checked on all 35.
- **Result:** 95.0% at 2 s, and 93.1% right first choice when streamed live. Script: `scripts/validate_ssvep.py`.

### 2020 BCI Competition, track 3: imagined speech (NEMAR nm000113)
- **Source:** https://nemar.org/dataset/nm000113 (original: https://osf.io/pq7vb)
- **Citation:** 2020 International Brain-Computer Interface Competition, track 3. BIDS conversion on NEMAR.
- **People and recording:** 15 people, 64 channels, 256 Hz. Each imagines saying one of 5 phrases without moving.
- **Labels:**
  - In each run's `events.tsv`, `trial_type` is one of Hello, Help me, Stop, Thank you, Yes.
  - Each trial is 3.1 s, with its start given by `onset`.
  - run-00 is training (300 trials), run-01 is validation (50), run-02 is test (50).
- **Our use:** training and held-out scoring of the words pipeline (`kinesis/signal/words.py`), all 64 channels vs only our 6 sites at 125 Hz.
- **Result:**
  - 41.5% on 5 words with 64 channels (chance 20%, all 15 people above chance).
  - 26.0% with our 6 electrodes.
  - Script: `scripts/eval_imagined_speech.py`.

### Bonn epilepsy dataset
- **Source:** https://www.ukbonn.de/epileptologie/arbeitsgruppen/ag-lehnertz-neurophysik/downloads/
- **Citation:** Andrzejak RG, Lehnertz K, Mormann F, Rieke C, David P, Elger CE. Indications of nonlinear deterministic and finite-dimensional structures in time series of brain electrical activity. Physical Review E 64, 061907, 2001.
- **People and recording:** 10 people: 5 healthy volunteers and 5 people with epilepsy. 500 single-channel recordings, 23.6 s each, 173.61 Hz.
- **Labels by set (100 recordings each):**

  | Set | Label | Recorded from |
  |---|---|---|
  | Z | healthy, eyes open | scalp |
  | O | healthy, eyes closed | scalp |
  | N | between seizures, opposite side to the seizure focus | intracranial |
  | F | between seizures, at the seizure focus | intracranial |
  | S | seizure | intracranial |

- **Our use:** the brain monitor's seizure-like rule (`kinesis/agent/brain.py`), resampled to 125 Hz, 4 s windows.
- **Result:**
  - Seizure vs non-seizure from the same patients: 94% of seizure recordings flagged, 3% false.
  - Against healthy scalp: 75% flagged, 0% false.
  - Script: `scripts/validate_seizure.py`.

## Baseline: our own headset

No public dataset has jaw clenches and double blinks on a NeuroPawn Knight with dry electrodes, so these are ours. They are labeled by protocol: each section is marked in the file next to it.

| Folder | What | Labels | Use |
|---|---|---|---|
| `kinesis/data/baseline/` | 3 trials, about 65 s each | eyes open, eyes closed, jaw clenches (README) | contact check, rest baseline, first detector tuning |
| `kinesis/data/gestures/` | 5 trials, about 65 s each | clench and double-blink sections in `sections.json` | seed for the per-person gesture model; leave-one-trial-out test |
| `kinesis/data/words/` | 18 imagined yes/no trials, 9 minutes | `yes_no_727_events.csv` | checks the imagined-speech result on our own headset |

How a person's model is built: their 1-minute calibration (stay still, 5 clenches, 5 double blinks), pooled with `kinesis/data/gestures/` (`kinesis/signal/learned.py`).

New baseline recordings: `python scripts/record.py` (cued protocol) or `python kinesis/stimulus/recording_task.py` (cued word trials). Both write BrainFlow files with the cues marked inside, to `data/sessions/`.
