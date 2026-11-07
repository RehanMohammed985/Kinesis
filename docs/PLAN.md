# Kinesis build plan

Deadline: Sunday Nov 8, 11:45am. Submission: team number, team name, public repo link, downloaded .pptx, via the Google Form. No late submissions.

## The seven steps, refined

Your list: nodes, calibration, coupling, signal processing, data collection, ML/agent, React. Same seven, with what each actually means, what "done" looks like, and the order that keeps nobody blocked.

### 1. Nodes (branch `nodes`)
Hardware and the board stream. Everything else reads from this.
- Electrodes screwed into the lattice, wired to the positive rail, switches away from header (see HARDWARE.md)
- Visualizer contact check passes: eyes-closed alpha on ch 1-4, blink spikes on 5-6, clench spike on 7
- `kinesis/board/knight.py`: opens the port, runs the enable sequence (start_stream, 2 s, per channel `chon_N_<gain>` then `rldadd_N` with the documented pauses), exposes `latest(n_samples)` and `start_recording(path)`
- `--synthetic` flag uses BrainFlow SYNTHETIC_BOARD so every other branch can code without the headset
- If the box is the IMU variant: board id 66, expose accel rows for motion gating
- Done when: `python scripts/smoke_stream.py --port ...` prints 8 live channels in microvolts and writes a CSV

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
- `notify.py`: send the selected message to a teacher/manager phone (SMS via Twilio or iMessage via AppleScript on the demo Mac). Payload is the message text only.
- `media.py`: next page / play-pause mapped to keypresses for Kindle, iPad, Spotify
- Done when: a fake event from the CLI speaks a phrase, presses a key, and sends a text

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
Phrase prediction and the conversation loop.
- `context.py`: Whisper (or Gemini audio) transcribes the last 20 s of the room mic
- `predict.py`: Gemini generates 4 likely user replies given transcript, persona, and setting (classroom / workplace / home); prefetches the next 4
- `profile.py`: persona from the user's own past messages, name, school/work context
- Stretch: TRCA transfer learning across subjects from OpenBMI to cut SSVEP calibration
- Done when: speak a question into the mic and four sensible replies appear in under 2 s

### 7. React (branch `react`)
The interface the user and the teacher see.
- Message board: 2x2 or 1x4 scanning grid, highlight moves every 2 s, SELECT fires the highlighted item
- Tiles mode: same grid, each tile flickers at its frequency using requestAnimationFrame on a 60 Hz display (never setInterval)
- Fit view: lattice map, red/amber/green per electrode, the prompt text
- Calibration flow: the cued screens
- Teacher view: a phone-sized page showing only incoming selected messages
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

## Demo script (60 s, maps to the five problems)
1. Answer a question: teacher asks, double blink = "Yes" in own voice
2. Request assistance: clench on "I need help", teacher's phone buzzes
3. Participate: mic hears the question, four Gemini replies appear, clench picks one
4. Workplace: same board, workplace message set
5. Pages and media: blink = next page on the Kindle / iPad, alpha = play-pause
Fit map stays green on the side screen the whole time. Second teammate puts it on, calibrates in 2 minutes, repeats step 1.

## Deck outline (.pptx)
1. Problem (the five)
2. Who: motor and speech impairments, ALS, CP, SCI, stroke, students like those at Hilltop Home
3. Kinesis: three inputs, one output, $350
4. Live demo
5. How it works (board, detectors, calibration, privacy rule)
6. Results: accuracy / ITR / false positives per input per person, Fit before/after
7. Inclusivity: Probe picks the input; Fit for every hair type; blind users via audio scanning
8. Scalability: keypress into any OS; $350 vs $7,450 (eye-gaze SGD) vs $16,000 (NeuroNode); calibration is 2 min
9. Prior art and what's new
10. Roadmap: gaze mode, clinical pilot, device-agnostic switch output

## Prior art to cite (be honest on slide 9)
- Cognixion Axon-R: SSVEP + LLM phrase prediction, needs Vision Pro
- Control Bionics NeuroNode: single EMG switch into Switch Control, ~$16,000
- Synchron / Augmental MouthPad: present as a Bluetooth input, let the OS scan
- WATOLINK 2022, QMind 2023: SSVEP + GPT replies on OpenBCI
- Neuralink / Apple Personal Voice: own-voice output
- Lee et al. 2019 GigaScience: no user is illiterate on all BCI paradigms
What's new: all three inputs in one cheap device, automatic input selection, fit for textured hair, privacy-by-design message sharing.
