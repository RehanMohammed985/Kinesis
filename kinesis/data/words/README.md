# Yes/no imagined-word session (Nov 7, trial 727)

- **What was recorded:** 9 minutes of thinking "yes" or "no", 18 trials (9 each). Each trial: the word on screen 5 s, "+" 5 s, think the word 20 s, rest 15 s.
- **Files:**
  - `yes_no_727.csv` is the recording rebuilt from snapshots (125 Hz, columns = pins 1 to 8).
  - `yes_no_727_events.csv` is the cue log.
  - The raw 286 MB file is on the team Drive.
- **Lining up the trials:** the recording has no markers, so trials were placed by file times (see `scripts/analyze_yes_no_session.py`). The noise the team reported in the first break lands exactly in that break, which confirms the placement.
- **Ear clip:** good this session. The channels no longer move together.

## Results

Scored by whole trials, with a permutation test.

| Test | Accuracy | Chance | p |
|---|---|---|---|
| yes vs no | 43 to 52% | 50% | 0.45 to 0.77 |
| thinking a word vs resting | 55 to 61% | 50% | 0.05 to 0.27 |

- **Yes vs no:** no difference. This matches the public 15-person dataset, where our 6 electrodes are near chance on imagined words (docs/VALIDATION.md).
- **Thinking vs resting:** a weak hint at best. One method reaches p 0.045 or 0.09 depending on how artifacts are dropped, which is not reliable.
- **For the demo:** yes/no goes through the Look tiles (95% on the 35-person SSVEP benchmark) or a clench.

The models are saved here as proof of the pipeline, not for live use:
- `yes_no_model.pkl`
- `thinking_vs_rest_model.pkl`
