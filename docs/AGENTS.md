# Agents

All in kinesis/agent/. The core server (kinesis/server.py) owns one Hub that routes app messages and feeds live signal to the monitor.

| Agent | File | Does |
|---|---|---|
| Registry | registry.py | The only actions Kinesis can take: speak, message, call, help, alert, media, note, report |
| Channels | channels.py | How messages and calls leave: practice mode (default), Mac iMessage and phone, or Twilio |
| Communication | comms.py | Four replies to what someone just said, with conversation memory (Gemini, fallback without) |
| Tasks | tasks.py | One selection, many actions: builds a plan from the profile, runs it step by step after confirm |
| Monitor | monitor.py + brain.py | Seizure-like activity, slowing and left/right asymmetry vs baseline, resting alpha peak, rest periods, signal quality |
| Report | report.py | Daily brain activity report for the doctor (HTML in data/reports) and the app's Report screen |

## Safety and honesty rules
- Practice mode by default. Nothing is texted or called unless KINESIS_LIVE=1.
- Automatic alerts (seizure-like, slowing change) only go out if the person turned them on in their profile (`safety_alerts`). Everything else needs their selection.
- Monitoring flags patterns for a clinician. It never diagnoses, never labels mood.
- Seizure-like: sharp (line length 3.5x baseline) or big (amplitude 4x with line length 2x), rhythmic, not muscle, on 2+ channels, sustained about 10 s.
- Slowing / asymmetry: delta/alpha ratio over 2x baseline or O1 vs O2 symmetry index up 0.15, for 5 minutes. A reason to call a clinician, not a stroke diagnosis.

## Validation
`python scripts/validate_seizure.py <folder with Bonn sets Z O N F S>`

Bonn epilepsy dataset (Andrzejak et al. 2001), resampled to 125 Hz:
- seizure vs non-seizure recordings from the same patients: 94% of seizure recordings flagged, 3% false
- seizure vs healthy scalp: 75% flagged, 0% false on 200 healthy recordings

Thresholds were tuned on this data, so expect lower on new people. Bonn seizure recordings are intracranial; our headset is scalp.

`python tests/test_agents.py` runs every agent on simulated signals in practice mode.

## Going live
1. Copy kinesis/agent/profile.example.json to data/profile.json and put in real names and numbers (data/profile.json is gitignored).
2. Mac: the core laptop must be signed in to Messages with the user's Apple ID. `KINESIS_LIVE=1 KINESIS_BACKEND=mac python -m kinesis.server --port ...`
3. Twilio: set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, then `KINESIS_LIVE=1 KINESIS_BACKEND=twilio ...`
4. Gemini: GEMINI_API_KEY in .env or app/.env.
