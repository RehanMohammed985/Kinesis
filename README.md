# Kinesis

Kinesis helps people with limited movement or speech communicate, participate in classrooms and workplaces, and navigate digital content through an affordable headset and interface.

One $350 headset (NeuroPawn Knight, 8-channel EEG) plus the phone or laptop the person already owns. Three ways in, one way out.

**Inputs**
- Visual attention response: stare at one of four flickering tiles (SSVEP, occipital channels)
- Deliberate muscle activity: jaw clench (EMG, temporal channel)
- Eye-related signals: double blink (EOG, Fp1/Fp2) and eyes-closed alpha burst (occipital)

**Outputs**
- A user-selected message, spoken in the user's own cloned voice
- A keypress into the OS accessibility layer (Switch Control / Switch Access), so any app, e-reader, or media player works
- A request shared with a teacher or manager. Only the selected message leaves the device. Never raw EEG, never inferred mental state.

**Calibration**: a 2-minute set of cued actions sets per-person thresholds and picks the cleanest input. Re-run any time.

**Fit**: a 90-second per-electrode contact check with placement guidance, including for braids, locs, and coily hair.

## Repo layout

```
kinesis/
  board/        Knight board wrapper, synthetic fallback, recording      (nodes)
  calibration/  cued baseline + Probe (which input works for this person)  (calibration)
  signal/       detectors: ssvep, emg, blink, alpha; Fit quality scorer    (signal-processing)
  coupling/     outputs: keypress, TTS/voice, message to teacher           (coupling)
  agent/        Gemini phrase prediction, conversation context             (ml-agent)
  data/         recorder, dataset loaders, replay harness                  (data-collection)
app/            React UI: message board, tiles, Fit map, calibration flow  (react)
scripts/        smoke tests and run scripts
docs/           PLAN.md (the report), HARDWARE.md, DATASETS.md, workstreams/
data/           raw recordings (gitignored except .gitkeep)
```

## Branches

One branch per workstream, all cut from `main`:
`nodes`, `calibration`, `coupling`, `signal-processing`, `data-collection`, `ml-agent`, `react`

Merge to `main` through PRs. `main` must always run the synthetic-board smoke test.

## Quick start

```
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/smoke_stream.py --synthetic      # no headset needed
python scripts/smoke_stream.py --port /dev/cu.usbmodemXXXX   # real board
```

See docs/PLAN.md for the full plan, owners, hours, and cut lines.
