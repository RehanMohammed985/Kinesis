# Core to app protocol

The Python core (board, detectors, calibration, coupling, agent) runs a WebSocket server on `ws://localhost:8765`. The React app connects to it. If the app cannot connect, it runs its own simulator so the UI always demos.

All messages are JSON with a `type` field.

## Core to app

### hello
Sent once on connect.
```json
{"type": "hello", "board": "knight", "synthetic": false, "fs": 125, "profile": {"name": "Walter", "select": "clench", "back": "blink2", "rest": "alpha"}}
```

### levels (about 20 per second)
Every input normalized to its own threshold, so 1.0 means "this would fire". The app draws these live.
```json
{"type": "levels", "clench": 0.12, "blink": 0.0, "alpha": 0.4, "look": {"scores": [0.21, 0.64, 0.18, 0.2], "best": 1, "margin": 0.43}}
```

### event
A detector fired. `input` is one of `clench`, `clench2` (double clench: two clenches within 0.7 s), `blink2` (double blink), `alpha` (eyes closed 1 s, not used on our headset), `look` (SSVEP, with `target` 0-3). While a clench waits to see if a second follows, `levels` carries `"pending": true`.
```json
{"type": "event", "input": "clench"}
{"type": "event", "input": "look", "target": 2}
```

### quality (once a second during Fit, every 10 s otherwise)
```json
{"type": "quality", "channels": [
  {"ch": 1, "site": "Oz", "state": "good", "reason": "ok"},
  {"ch": 2, "site": "O1", "state": "fair", "reason": "noise", "prompt": "Press O1 down a quarter turn"},
  {"ch": 6, "site": "T7", "state": "bad", "reason": "flat", "prompt": "T7 is not touching skin. Move it into a part line."}
]}
```
`state` is `good`, `fair`, or `bad`. `reason` is `ok`, `flat`, `railed`, `noise`, or `no_alpha`.

### calibration
Progress through the cued steps. The final message carries the profile.
```json
{"type": "calibration", "step": "clench", "progress": 0.6}
{"type": "calibration", "done": true, "profile": {"select": "clench", "back": "blink2", "rest": "alpha", "scores": {"clench": 3.1, "blink2": 2.4, "alpha": 1.8, "look": 1.2}}}
{"type": "calibration", "step": "model", "ok": true, "frames": {"rest": 180, "clench": 95, "blink2": 88}, "accuracy": {"rest": 1.0, "clench": 0.97, "blink2": 0.95}, "channels": [3, 4, 6, 7], "pooled_with_team_frames": 1402}
```
During the clench and double-blink steps the core counts each attempt and sends it as an `event` with that step's input, so the app's counter moves. When the app moves past those steps, the core trains this person's gesture model (`step: model`), saves it to data/gesture_model.json and uses it from then on. `ok: false` means too few clean attempts; the previous model stays.

### heard
The room mic transcript for conversation mode.
```json
{"type": "heard", "speaker": "Dr. Patel", "text": "How did you sleep last night?"}
```

### replies
Four predicted replies from the agent.
```json
{"type": "replies", "items": ["Not great, I woke up a lot", "Pretty well, thanks", "My back hurt", "Can we talk about it later?"]}
```

### plan / step
A task plan for confirmation, then progress as it runs.
```json
{"type": "plan", "id": "t1", "task": "refill", "title": "Refill my prescription", "steps": ["Find the prescription", "Call the pharmacy", "Confirm pickup time", "Text me when it's ready"]}
{"type": "step", "id": "t1", "index": 1, "status": "done", "detail": "Walgreens on Hillsborough St, ready at 4:30"}
```

### alert / notice
From the monitor agent. `alert` opens the alarm screen; `notice` is a toast.
```json
{"type": "alert", "kind": "seizure_like", "text": "Kinesis detected seizure-like brain activity on Walter at 3:21 pm. Please check on them now."}
{"type": "notice", "text": "Seizure-like activity ended after about 26 seconds. Logged for your doctor."}
```

### report
From the report agent, in answer to `report_request` or `action: report`. `file` is the HTML report for the doctor.
```json
{"type": "report", "day": "2026-11-07", "facts": [["143", "choices made"]], "brain": {"seizure_like": [{"at": "3:21 pm", "duration_s": 26}], "rest_periods": 3, "alpha_peak_hz": 9.8}, "hours": [{"hour": "3 pm", "quality": 0.92, "dar": 1.4, "bsi": 0.08}], "notes": [["9:12 am", "My back hurt"]], "summary": "...", "file": "data/reports/report-2026-11-07.html"}
```

## App to core

```json
{"type": "calibrate", "step": "rest"}
{"type": "calibrate", "step": "clench"}
{"type": "look", "on": true}
{"type": "action", "action": "speak", "text": "Pretty well, thanks"}
{"type": "action", "action": "call", "contact": "linda"}
{"type": "action", "action": "message", "contact": "maria", "text": "I'm okay"}
{"type": "action", "action": "help"}
{"type": "action", "action": "media", "command": "page_next"}
{"type": "action", "action": "report", "recipient": "dr_patel"}
{"type": "action", "action": "task", "task": "refill"}
{"type": "action", "action": "note", "text": "My back hurt"}
{"type": "confirm", "id": "t1"}
{"type": "cancel", "id": "t1"}
{"type": "heard", "speaker": "Linda", "text": "Do you want to watch the game tonight?"}
{"type": "report_request"}
{"type": "demo_seizure"}
```
`calibrate` marks each cued step (rest, clench, blink2, then anything else ends the gesture steps and trains the model). `look` turns the SSVEP decoder on while the Look screen is open; the core then adds `look` to `levels` and sends `event` with `input: look, target: 0-3`. `heard` asks the communication agent for replies. `demo_seizure` mixes a real recorded seizure (Bonn dataset) into the live signal for 23 s so the real detector can be shown; the app labels it as a replay.

## Simulator keys (app runs without the core)
- Hold **C**: clench rises, fires at threshold
- Press **B** twice quickly: double blink
- Hold **E**: eyes closed, alpha rises
- **D**: double clench
- **1 2 3 4**: look at tile
- **X**: replay a recorded seizure
- **?**: show these keys on screen
