# Core to app protocol

The Python core (board, detectors, calibration, coupling, agent) runs a WebSocket server on `ws://localhost:8765`. The React app connects to it. If the app cannot connect, it runs its own simulator so the UI always demos.

All messages are JSON with a `type` field.

## Core to app

### hello
Sent once on connect.
```json
{"type": "hello", "board": "knight", "synthetic": false, "fs": 125, "profile": {"name": "Maya", "select": "clench", "back": "blink2", "rest": "alpha"}}
```

### levels (about 20 per second)
Every input normalized to its own threshold, so 1.0 means "this would fire". The app draws these live.
```json
{"type": "levels", "clench": 0.12, "blink": 0.0, "alpha": 0.4, "look": {"scores": [0.21, 0.64, 0.18, 0.2], "best": 1, "margin": 0.43}}
```

### event
A detector fired. `input` is one of `clench`, `blink2` (double blink), `alpha` (eyes closed 1 s), `look` (SSVEP, with `target` 0-3).
```json
{"type": "event", "input": "clench"}
{"type": "event", "input": "look", "target": 2}
```

### quality (once a second during Fit, every 10 s otherwise)
```json
{"type": "quality", "channels": [
  {"ch": 1, "site": "Oz", "state": "good", "reason": "ok"},
  {"ch": 2, "site": "O1", "state": "fair", "reason": "noise", "prompt": "Press O1 down a quarter turn"},
  {"ch": 5, "site": "Fp1", "state": "bad", "reason": "flat", "prompt": "Fp1 is not touching skin. Move it into a part line."}
]}
```
`state` is `good`, `fair`, or `bad`. `reason` is `ok`, `flat`, `railed`, `noise`, or `no_alpha`.

### calibration
Progress through the cued steps. The final message carries the profile.
```json
{"type": "calibration", "step": "clench", "progress": 0.6}
{"type": "calibration", "done": true, "profile": {"select": "clench", "back": "blink2", "rest": "alpha", "scores": {"clench": 3.1, "blink2": 2.4, "alpha": 1.8, "look": 1.2}}}
```

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

## App to core

```json
{"type": "calibrate", "step": "rest"}
{"type": "action", "action": "speak", "text": "Pretty well, thanks"}
{"type": "action", "action": "call", "contact": "mom"}
{"type": "action", "action": "message", "contact": "sam", "text": "I'm okay"}
{"type": "action", "action": "help"}
{"type": "action", "action": "media", "command": "page_next"}
{"type": "action", "action": "report", "recipient": "dr_patel"}
{"type": "action", "action": "task", "task": "refill"}
{"type": "confirm", "id": "t1"}
{"type": "cancel", "id": "t1"}
```

## Simulator keys (app runs without the core)
- Hold **C**: clench rises, fires at threshold
- Press **B** twice quickly: double blink
- Hold **E**: eyes closed, alpha rises
- **1 2 3 4**: look at tile
- **?**: show these keys on screen
