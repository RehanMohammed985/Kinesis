# Kinesis build plan

Deadline: Sunday Nov 8, 11:45am. Submission: team number, team name, public repo link, downloaded .pptx, via the Google Form. No late submissions.

## The seven steps, refined

Your list: nodes, calibration, coupling, signal processing, data collection, ML/agent, React. Same seven, with what each actually means, what "done" looks like, and the order that keeps nobody blocked.

### 1. Nodes (branch `nodes`)
Hardware and the board stream. Everything else reads from this.
- Electrodes screwed into the lattice, wired to the positive rail, switches away from header (see HARDWARE.md)
- Visualizer contact check passes: eyes-closed alpha on ch 1-4, blink spike on 5, clench spike on 6
- `kinesis/board/knight.py`: opens the port, runs the enable sequence (start_stream, 2 s, per channel `chon_N_<gain>` then `rldadd_N` with the documented pauses), exposes `latest(n_samples)` and `start_recording(path)`
- `--synthetic` flag uses BrainFlow SYNTHETIC_BOARD so every other branch can code without the headset
- Done when: `python scripts/smoke_stream.py --port ...` prints 6 live channels in microvolts and writes a CSV

### 2. Calibration (branch `calibration`)
Per-person thresholds and Probe.
- Cued script: 10 s rest, 5x clench on cue, 5x double blink on cue, 10 s eyes closed, (optional) 6 SSVEP training blocks via NeuroPawn's collect_training_data flow
- Computes baselines: EMG band power at rest, blink peak amplitude, alpha power eyes open vs closed
- Probe: separability score (d') per input; ranks them; writes `profiles/<name>.json` with thresholds and the chosen SELECT and NEXT inputs
- Done when: a new teammate can be calibrated in under 3 minutes and the profile drives detectors with no code edits

### 3. Coupling (branch `coupling`)
Turning a detected event into something in the world.
- `keypress.py`: pyautogui on the demo laptop (Space = next, Enter = select) into macOS Switch Control; stretch: Raspberry Pi BLE HID keyboard for iPad
- `speak.py`: ElevenLabs instant clone (30 s sample recorded today) with pyttsx3 or system TTS fallback
- `call.py`: place a call to a chosen contact and answer/decline incoming (FaceTime or Phone via AppleScript on the demo Mac; Twilio voice as fallback)
- `notify.py`: send the selected message to a caregiver/family/employer phone (Twilio SMS or iMessage via AppleScript). Payload is the message text only.
- `report.py`: build the daily physician report (usage counts, calibration drift, Fit scores, eyes-closed rest periods, user-selected symptom messages) as PDF/JSON and send only when the user selects "send to my doctor"
- `media.py`: next page / play-pause mapped to keypresses for Kindle, iPad, Spotify
- Done when: a fake event from the CLI speaks a phrase, presses a key, places a call, sends a text, and emits a report

### 4. Signal processing (branch `signal-processing`)
The detectors and Fit. Pure functions over numpy windows, testable on synthetic and recorded data.
- `emg.py`: 20-55 Hz band power on the temporal channel, threshold = k x rest baseline, 1 s refractory
- `blink.py`: low-pass 10 Hz on Fp1/Fp2, peak over threshold, double = two peaks within 600 ms
- `alpha.py`: 8-12 Hz power on occipital channels vs eyes-open baseline, sustained 1 s
- `ssvep.py`: wrap NeuroPawn's TRCA (meegkit) with a reject margin; CCA fallback needing no training
- `quality.py` (Fit): per channel flatline (std < 0.5 uV), saturation (counts near +/-32767), residual line noise (45-62 Hz power), alpha-block test; returns red/amber/green plus a text prompt
- Done when: detectors fire correctly on the calibration recordings of every teammate, false positives under 1 per minute at rest

### 5. Data collection (branch `data-collection`)
Recording, replay, and public datasets. Two people on this.
- `recorder.py`: writes every session with BrainFlow write_file plus a JSON sidecar (who, montage, gain, task, timestamps of cues)
- `replay.py`: BrainFlow PLAYBACK_FILE_BOARD so detectors run on recordings exactly as on live data
- Public datasets (see DATASETS.md): OpenBMI SSVEP for cross-subject TRCA/CCA validation, eye-blink and EMG sets for threshold sanity, Sleep-EDF for alpha baselines
- Metrics notebook: accuracy and ITR per input per person, detection rate and false positive rate for EMG/blink/alpha, Fit score before/after paste. These numbers go on the results slide.
- Done when: `python -m kinesis.data.replay data/sessions/<file>` runs all detectors and prints metrics

### 6. ML / agent (branch `ml-agent`)
Phrase prediction, the conversation loop, and the task agent. The agent is what turns one slow selection into many actions.
- `kinesis/signal/learned.py`: per-person gesture model. The calibration steps (still, clench x5, double blink x5) train a shrinkage LDA on 22 log-power features in under a second; `scripts/train_gestures.py` tests it leave-one-trial-out on our recordings.
- `actions.py`: the action registry. The agent may only call these, each with a confirm rule:

  | Action | Params | Confirm before running |
  |---|---|---|
  | speak | text | no |
  | call | contact | yes |
  | message | contact, text | yes |
  | help | (none) | no, sends immediately to the caregiver list |
  | media | play / pause / next / prev / page_next / page_prev | no |
  | report | recipient | yes |
  | task | name, params (refill, ride, groceries, appointment, tell_family) | yes, shows the plan first |

- `tasks.py`: each task is a short plan the agent fills in from context (contacts, pharmacy, address, last order) and that the app shows as steps before the user confirms. Steps run through the registry, so a task can never do something the registry does not allow.
- `context.py`: Whisper (or Gemini audio) transcribes the last 20 s of the room mic
- `predict.py`: Gemini generates 4 likely user replies given transcript, persona, and setting (home / work / clinic / out); prefetches the next 4
- `monitor.py` ("detect stuff"): passive logging between selections: eyes-closed rest periods, unusual EMG activity, Fit degradation over the day, time since last calibration. Logged locally, summarized into the physician report. No diagnoses, no mental-state labels.
- `profile.py`: persona from the user's own past messages, name, contacts, pharmacy, doctor
- Stretch: TRCA transfer learning across subjects from OpenBMI to cut SSVEP calibration
- Done when: speak a question into the mic and four sensible replies appear in under 2 s; selecting "Refill my prescription" shows a 4-step plan, a double blink confirms, the steps tick off

### 7. React (branch `react`)
The interface the user and the caregiver see. This is the highlight of the demo; everything else feeds it. Protocol in docs/PROTOCOL.md.
- Message board: 2x2 or 1x4 scanning grid, highlight moves every 2 s, SELECT fires the highlighted item
- Tiles mode: same grid, each tile flickers at its frequency using requestAnimationFrame on a 60 Hz display (never setInterval)
- Fit view: lattice map, red/amber/green per electrode, the prompt text
- Calibration flow: the cued screens
- Contacts view: call / message a chosen person
- Caregiver view: a phone-sized page showing only incoming selected messages
- Reports view: today's log, a single "send to my doctor" action
- Transport: WebSocket from the Python core (events in, selections out)
- Done when: the whole demo runs from the UI with no terminal visible

## Integration order

1. nodes + signal-processing against synthetic, then real board (hours 0-4)
2. calibration writes a profile; detectors read it (hours 3-6)
3. coupling: keypress + TTS from CLI (hours 4-7)
4. react board + WebSocket wired to detectors (hours 6-11)
5. ml-agent replies into the board (hours 8-12)
6. SSVEP tiles added if detectors are solid by hour 10
7. full runs on every teammate, record metrics (hours 12-16)
8. video, deck, README, submission (hours 16-21), buffer after

## Cut lines (in order, if behind)
1. Pi BLE HID (demo on the Mac with Switch Control instead)
2. SSVEP tiles (keep on the slide as the third input)
3. Teacher SMS (show on a second laptop window)
4. Voice clone (system TTS)
Never cut: EMG + blink detectors, Fit map, the React board, the 90 s video.

## Positioning
AI is automating everyone's life except the people who need it most. Every assistant and agent assumes you can type or talk. Kinesis gives people who can't the input.

A personal device and app for running your life: talk, call, control, share, report, and hand off whole tasks to an agent. 5-minute setup, re-run as the condition changes.

Core idea: one selection, many actions. A BCI gives one choice every couple of seconds; the agent turns that choice into a finished task. "Refill my prescription" is one clench, then a plan the user confirms with a double blink, then the agent does the steps.

Rules we say out loud:
- We read choices, not thoughts. The user picks from options; the agent carries them out.
- Anything that contacts someone or spends money is shown as a plan and needs a confirm.
- Only what the user selects leaves the device. Never raw EEG, never inferred mental state.

## Demo script (90 s)
0. Setup: teammate puts on the headset, Fit map goes green, 2-minute calibration (sped up in the video, live if time allows)
1. Talk: judge asks a question, mic hears it, four Gemini replies appear, clench picks one, spoken in own voice
2. Call: clench on "Call Mom", the phone rings on the table, double blink answers
3. Control: blink = next page on the Kindle / iPad, alpha = play-pause music
4. Hand off a task: clench on "Refill my prescription", the plan appears (find the prescription, call the pharmacy, confirm pickup, text me), double blink confirms, the steps tick off
5. Ask for help: "I need help" goes to the caregiver's phone
6. Report: "Send to my doctor" produces the day's log and sends it
Second teammate puts it on, 5-minute setup, repeats step 1. A different input gets picked for them.

## Deck outline (.pptx)
1. AI is automating everyone's life. Every assistant assumes hands or a voice.
2. Problem: losing movement or speech means losing control of your phone, your calls, your reading, your voice, and your own medical record
3. Who: anyone with a motor or speech impairment: ALS, cerebral palsy, spinal cord injury, stroke, MS, muscular dystrophy
4. Kinesis: three inputs, one selection, many actions, $350
5. Live demo
6. How it works (board, detectors, calibration, agent registry, privacy rule)
7. Results: accuracy / ITR / false positives per input per person, Fit before/after
8. Inclusivity: calibration picks the input; Fit for every hair type; blind users via spoken scanning
9. Scalability: keypress into any OS, agent tasks reuse the same registry; $350 vs $7,450 (eye-gaze SGD) vs $16,000 (NeuroNode); 5-minute setup
10. Prior art and what's new
11. Roadmap: more agent tasks, clinical pilot, device-agnostic switch output

## Prior art to cite (be honest on slide 9)
- Cognixion Axon-R: SSVEP + LLM phrase prediction, needs Vision Pro
- Control Bionics NeuroNode: single EMG switch into Switch Control, ~$16,000
- Synchron / Augmental MouthPad: present as a Bluetooth input, let the OS scan
- WATOLINK 2022, QMind 2023: SSVEP + GPT replies on OpenBCI
- Neuralink / Apple Personal Voice: own-voice output
- Lee et al. 2019 GigaScience: no user is illiterate on all BCI paradigms
What's new: an input layer for AI agents built for people who cannot type or talk; all three inputs in one cheap device, automatic input selection, fit for textured hair, privacy-by-design message sharing.
