# What we tested, on what data

Every number here comes from a script in this repo, so anyone can rerun it.

## Look to choose (SSVEP): validated on 35 people

- **Data:** Tsinghua SSVEP benchmark (Wang et al. 2017, IEEE TNSRE, PubMed 27849543). 35 people, 40 flashing targets from 8 to 15.8 Hz, 6 blocks each. http://bci.med.tsinghua.edu.cn/download.html
- **Setup:** only what our headset has, which is 4 back-of-head channels (Oz, O1, O2, POz) at 125 Hz, and the 4 targets closest to our tiles (8.6, 10, 12, 15 Hz). Filter-bank CCA, so no training is needed.

| Window | Accuracy (chance 25%) | Speed |
|---|---|---|
| 1 s | 87.5% | 50 bits/min |
| 2 s | 95.0% | 39 bits/min |
| 3 s | 97.5% | 31 bits/min |

- **Live decoder,** streamed trial by trial (840 trials):
  - first choice right 93.1%, wrong 0.2%, no choice 6.7%
  - median 2.2 s to choose
- **False choices on our own headset with nothing flashing:** 1 in 100 s.
- **Our tile rates** (8.57 Hz template on 8.6 Hz data): 95.4%, so the small rate difference does not matter.
- **Ceiling:** all 9 back channels at 250 Hz reach 96.5%. Our 4 channels lose almost nothing.
- **Caveat:** the benchmark used gel electrodes in a lab. Our headset's back electrodes need good contact first.
- **Run:** `python scripts/validate_ssvep.py <folder> --still kinesis/data/gestures/double_trial*.csv`

## Imagined words: proof of concept, and its limit

- **Data:** 2020 BCI Competition track 3 on NEMAR (nm000113). 15 people, 64 channels, imagining "Hello", "Help me", "Stop", "Thank you", "Yes". Trained on 300 trials per person, scored on 100 held-out trials. https://nemar.org/dataset/nm000113
- **Pipeline:** kinesis/signal/words.py (Riemannian covariance + logistic regression, or band power + LDA), the same one that scores our own word trials.

| Condition | Accuracy | Chance | People above chance |
|---|---|---|---|
| 5 words, all 64 channels | 41.5% | 20% | 15 of 15 |
| 5 words, our 6 electrodes | 26.0% | 20% | 7 of 15 |
| "Yes" vs "Stop", our 6 electrodes | 57.8% | 50% | 3 of 15 |

- **What this shows:** the pipeline works, since it decodes imagined words on full-cap EEG. With 6 electrodes it falls to near chance.
- **For yes/no today:** the Look tiles (95%), or silently mouthed words, which the temple electrode and ear clip can pick up. Score those with `scripts/record_words.py --mode mouth`, then `scripts/analyze_words.py`.
- **Run:** `python scripts/eval_imagined_speech.py <nm000113 folder>`

## Clench and double blink: our own headset, 5 trials

- **Leave one trial out:**
  - double blink: 64 of 71 caught
  - clench: 40 events for 41 bursts (31 before clench re-armed on release)
  - 2 mix-ups between the two
  - 2 false events in 145 s still
- **Fixed rules, for comparison:** caught 0 double blinks.
- Details are in kinesis/data/gestures/README.md.
- **Run:** `python scripts/train_gestures.py kinesis/data/gestures/double_trial*.csv`

## Seizure-like activity: Bonn epilepsy dataset

- **Same patients, intracranial:** 94% of seizure recordings flagged, 3% of non-seizure recordings flagged.
- **Against healthy scalp recordings:** 75% flagged, 0% false.
- Details are in scripts/validate_seizure.py.
