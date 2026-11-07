# Kinesis

Kinesis lets anyone with a motor or speech impairment run their life with their mind: talk, call people, control their phone, navigate reading and media, log what their body is doing, and send that record to their physician. One personal device, one app, a 5-minute setup.

One $350 headset (NeuroPawn Knight EEG board, 6 electrodes) plus the phone the person already owns. Three ways in, one way out.

**Inputs**
- Visual attention response: stare at one of four flickering tiles (SSVEP, occipital channels)
- Deliberate muscle activity: jaw clench (EMG, temporal channel)
- Eye-related signals: double blink (EOG, Fp1) and eyes-closed alpha burst (occipital)

**Outputs**
- Speak: a user-selected message in the user's own cloned voice
- Call: phone a chosen contact, answer or decline an incoming call
- Control: a keypress into the OS accessibility layer (Switch Control / Switch Access), so any app, e-reader, or media player works
- Share: a request sent to a caregiver, family member, or employer
- Report: a daily log (usage, calibration drift, eyes-closed rest periods, Fit quality) the user chooses to send to their physician

Only user-selected messages and user-approved reports leave the device. Never raw EEG, never inferred mental state.

**Setup (5 minutes)**: Fit (90 s contact check) then Calibration (a 2-minute set of cued actions that sets per-person thresholds and picks the cleanest input). Re-run any time; the device follows the person as their condition changes.

**Fit**: a 90-second per-electrode contact check with placement guidance, including for braids, locs, and coily hair.

## Repo layout

```
kinesis/
  board/        Knight board wrapper, synthetic fallback, recording      (nodes)
  calibration/  cued baseline + Probe (which input works for this person)  (calibration)
  signal/       detectors: ssvep, emg, blink, alpha; Fit quality scorer    (signal-processing)
  coupling/     outputs: keypress, TTS/voice, call, share, physician report (coupling)
  agent/        Gemini phrase prediction, conversation context             (ml-agent)
  data/         recorder, dataset loaders, replay harness                  (data-collection)
app/            React UI: board, tiles, calls, Fit map, setup flow, reports  (react)
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
