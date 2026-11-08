# Setup

From nothing to the 3-minute demo. Follow the steps in order. Each step says what you should see before you move on.

Contents:

1. [What you need](#1-what-you-need)
2. [Get the code](#2-get-the-code)
3. [Keys and voice](#3-keys-and-voice)
4. [The headset](#4-the-headset)
5. [Start the core](#5-start-the-core)
6. [Start the app](#6-start-the-app)
7. [Put it on the iPad or phone](#7-put-it-on-the-ipad-or-phone)
8. [Fit and calibrate](#8-fit-and-calibrate)
9. [Live test](#9-live-test)
10. [The 3-minute demo](#10-the-3-minute-demo)
11. [Going live (real texts and calls)](#11-going-live-real-texts-and-calls)
12. [Without a headset](#12-without-a-headset)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. What you need

| Thing | Notes |
|---|---|
| Laptop | Mac, Windows or Linux. It runs the core and the app. |
| Python 3.11 or newer | `python3 --version` |
| Node.js 20.19 or newer | `node --version` (Vite 7 needs it) |
| git | `git --version` |
| NeuroPawn Knight headset | 6 dry electrodes, ear clip, USB cable |
| iPad or phone (optional) | Same wifi as the laptop. A laptop browser works too. |
| ElevenLabs account (optional) | For the person's own voice. Without it, the system voice speaks. |
| Gemini API key (optional) | For reply ideas on the Talk screen. Without it, canned replies. |

## 2. Get the code

```bash
git clone https://github.com/RehanMohammed985/Kinesis.git
cd Kinesis
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt      # BrainFlow, NumPy, SciPy, scikit-learn, pyRiemann, websockets
cd app
npm install                          # React and Vite for the app
cd ..
```

**Check:** `python tests/test_agents.py` ends with `all agent checks passed`.

## 3. Keys and voice

Copy the example env file and fill in what you have:

```bash
cp app/.env.example app/.env         # Windows: copy app\.env.example app\.env
```

| Line in `app/.env` | What it does |
|---|---|
| `ELEVENLABS_API_KEY=` | Your ElevenLabs key. Used only by the app's dev server, never sent to the browser. |
| `ELEVENLABS_VOICE_ID=` | The voice to speak in. The script below fills it in. |
| `GEMINI_API_KEY=` | Optional. Reply ideas on Talk, used by both the app and the core. |
| `KINESIS_CORE=` | Optional. Only if the core runs on a different laptop: `ws://<core-ip>:8765`. |

**Set up the voice:**

```bash
python scripts/setup_voice.py check                       # credits left and the voices on the account
python scripts/setup_voice.py clone "Walter" sample.m4a   # clone from 1 to 3 minutes of clean speech
python scripts/setup_voice.py use VOICE_ID                # or use an existing voice
```

- `clone` uploads the sample to ElevenLabs, creates the voice and writes its id into `app/.env`.
- Only clone a voice with that person's permission. For the demo, use a teammate's voice.

**Prewarm** after the app is running (step 6). This voices every fixed phrase once, so the demo plays instantly and spends no credits on stage:

```bash
curl -X POST http://localhost:5173/api/prewarm           # Windows PowerShell: curl.exe -X POST ...
```

**Check:** it returns `{"voiced": N, "failed": []}`.

**Optional, real contacts:** copy `kinesis/agent/profile.example.json` to `data/profile.json` and put in real names and phone numbers. That file stays out of git. Without it, the demo persona (Walter, his wife Linda, daughter Maria, son David) is used.

## 4. The headset

### Wiring

Our headset has the electrodes on **pins 2 to 7**. The core reads this map from `kinesis/montage.py`.

| Pin | Site | Where on the head | Used for |
|---|---|---|---|
| 2 | Oz | back of the head, center | look tiles, brain monitor |
| 3 | O1 | back of the head, left | look tiles, brain monitor |
| 4 | O2 | back of the head, right | look tiles, brain monitor |
| 5 | POz | above Oz | look tiles, brain monitor |
| 6 | Fp1 | forehead, above the left eye | double blink |
| 7 | T7 | above the left ear | clench |

- Ear clip on the earlobe, leads into **RLD** and **COMM**. A loose ear clip makes every channel move together. Clip it firmly.
- Slide the switches for pins 2 to 7 away from the header. Leave 1 and 8 toward the header.
- Seat each spike on skin. For braids or locs, use a part line, with comfort pads on the braids. For coily hair, part a small section first.
- If you move the wires to pins 1 to 6, set `KINESIS_FIRST_PIN=1` before starting the core.

### Check it in the EXG Visualizer

1. Open the Visualizer, pick the port, board type **Knight Board** (not IMU).
2. Turn on pins 2 to 7.
3. Tap each electrode one at a time.
   - **Check:** the trace that jumps is the pin in the table.
4. Blink hard.
   - **Check:** pin 6 jumps.
5. Clench.
   - **Check:** everything bursts.
6. **Close the Visualizer.** Only one program can use the headset at a time.

### Find the serial port

| System | How |
|---|---|
| Mac | `ls /dev/cu.usbmodem*`, for example `/dev/cu.usbmodem1101` |
| Windows | Device Manager, Ports (COM and LPT), for example `COM5` |
| Linux | `ls /dev/ttyACM* /dev/ttyUSB*` |

## 5. Start the core

```bash
python -m kinesis.server --port /dev/cu.usbmodem1101      # Windows: --port COM5
```

The core turns on pins 2 to 7 (about 30 s), records the session to `data/sessions/`, loads the gesture model and serves the app on port 8765.

**Check:** the terminal shows, in order:

```
Turning on channels (about 30 s on the real board)...
Recording to data/sessions/session-....csv
Gestures: learned model .../kinesis/data/gestures/model.json (channels [...])
Sit still with eyes open for 5 s to set the baseline...
Core running. On this laptop: ws://localhost:8765
iPad or phone on the same wifi: run the app on this laptop (cd app, npm run dev), then open http://<laptop-ip>:5173
Baseline set: {...}
```

Sit still with eyes open for those first 5 s.

| Option | What it does |
|---|---|
| `--synthetic` | Fake board, for building without a headset. Gestures never fire. |
| `--rules` | Fixed thresholds instead of the learned model. |
| `--model path.json` | A specific gesture model. The default is `data/gesture_model.json` after a calibration, then the team model. |
| `--ws-port 8765` | WebSocket port. |

## 6. Start the app

In a second terminal:

```bash
cd app
npm run dev
```

Open http://localhost:5173 on the laptop.

**Check:** the top bar says **Headset on**, not **Simulator**.

The dev server also forwards `/core` to the core. Any device that opens this page reaches the headset through the same address.

## 7. Put it on the iPad or phone

1. Same wifi as the laptop.
2. In Safari, open `http://<laptop-ip>:5173`. The core prints the exact address.
3. Tap Share, then **Add to Home Screen**.
4. Open **Kinesis** from the home screen. It runs full screen with its own icon.
5. **Tap once anywhere.** iPhone and iPad only play sound after the first touch. After that, phrases chosen with the headset speak too.
6. **Setup**, in the top bar, opens the Fit and Calibrate screens. On a phone held upright the top bar is shortened, so run Fit and Calibrate on the iPad or the laptop.

**Caregiver page:** on a second phone, open `http://<laptop-ip>:5173/#/caregiver`. Texts and help requests the person sends appear there live.

> The Talk screen's listening needs the microphone, which Safari only allows over https. The three demo moments do not need it.

## 8. Fit and calibrate

**Fit.** Every sensor shows its contact.

- **Pass:** at least 5 of 6 good.
- If one is flagged, follow its prompt: wiggle it through the hair, or press it down a quarter turn. POz (pin 5) has been the weakest on our headset.

**Calibrate.** About one minute:

1. Stay still for 6 s.
2. Clench 5 times, a breath apart.
3. Double blink 5 times, about 2 s apart.
4. Eyes closed: tap **Skip this step**. It does not show reliably on our current fit.

**Check:** the core prints `Gestures: learned this person's clench and double blink` and saves the model to `data/gesture_model.json`. If it prints `not enough clean attempts`, run Calibrate again and make each attempt firmer.

## 9. Live test

On **Home**, with the terminal visible:

| Do | Pass |
|---|---|
| 10 clenches, about 2 s apart | 8 or more `event: clench` |
| 10 double blinks, about 2 s apart | 8 or more `event: blink2` |
| Mix-ups between the two | 1 or fewer |
| Sit still for 1 minute | no events |

If it misses, redo Calibrate. If it fires on its own, check the ear clip and any flagged sensor, then redo Calibrate.

## 10. The 3-minute demo

Wearer: a teammate as Walter. iPad on a stand facing the judges, caregiver page open on a phone.

| Time | Do | What they see and hear |
|---|---|---|
| 0:00 | Hook: "AI is automating everyone's life except the people who need it most." Walter, 72, stroke, cannot speak or use his right side. | Home on the iPad |
| 0:30 | Clench on **Say it**, then on **I need water** | "I need water" spoken in his voice, shown large |
| 1:00 | Double blink back, clench **Get it done**, **Refill my prescription**, **Go ahead** | The plan runs step by step: call the pharmacy, text Linda |
| 1:40 | **Call or text**, **Linda**, **Can you come here?** | It arrives on the caregiver phone |
| 2:10 | Optional: on Report, **Demo: replay a recorded seizure** | About 10 s later the alarm screen opens and the caregiver phone gets the alert |
| 2:30 | Close: $350 headset, 5-minute setup, validated on public data (see the README numbers) | |

Run it end to end three times before presenting.

## 11. Going live (real texts and calls)

Nothing is sent until you turn it on. Put real numbers in `data/profile.json` first.

**Mac, through Messages and the paired iPhone:**

```bash
KINESIS_LIVE=1 KINESIS_BACKEND=mac python -m kinesis.server --port /dev/cu.usbmodem1101
```

The Mac must be signed in to Messages with iMessage. Calls open the phone dialer through the paired iPhone.

**Twilio, from anywhere:**

```bash
export TWILIO_ACCOUNT_SID=AC...
export TWILIO_AUTH_TOKEN=...
export TWILIO_FROM=+1...
KINESIS_LIVE=1 KINESIS_BACKEND=twilio python -m kinesis.server --port /dev/cu.usbmodem1101
```

A Twilio trial account can only text and call numbers you have verified in Twilio.

On Windows PowerShell, set variables with `$env:KINESIS_LIVE="1"` and so on, then run the command.

`KINESIS_KEYS=1` also lets **Read and listen** press keys on the laptop (page turns, play and pause).

## 12. Without a headset

- **App only:** `cd app` then `npm run dev`, with no core running. The app runs its simulator. Press `?` for the keys:

  | Key | Does |
  |---|---|
  | hold C | clench |
  | B B | double blink |
  | hold E | eyes closed |
  | 1 to 4 | look at a tile |
  | I | incoming call from Linda |
  | L | Look screen |
  | S | spoken scanning on or off |
  | X | replay a recorded seizure |
  | Shift H | Home |

- **Core without a board:** `python -m kinesis.server --synthetic`. Good for testing the agents and the report. Gestures do not fire on synthetic data.
- **Start on a screen:** `http://localhost:5173/?start=say` (also `home`, `fit`, `calibrate`, `talk`, `call`, `tasks`, `media`, `report`, `look`, `help`).

## 13. Troubleshooting

| Problem | Fix |
|---|---|
| Top bar says **Simulator** | The core is not running or not reachable. Start it first. If it runs on another laptop, set `KINESIS_CORE=ws://<core-ip>:8765` in `app/.env` and restart `npm run dev`. |
| Core cannot open the port | The EXG Visualizer, or another core, still holds it. Close it. Check the port name (step 4). |
| A sensor is flagged | Follow the Fit prompt. **Floating** means the spike is not on skin. **Noise** means check the ear clip and unplug the laptop charger. |
| Every channel moves together | Ear clip loose. Clip it firmly on the earlobe, leads in RLD and COMM. |
| No sound on the iPad | Tap the screen once (iPad rule). Check the silent switch and volume. With no ElevenLabs key, the system voice speaks. |
| Voice is slow the first time | Run the prewarm command (step 3). Every fixed phrase is then cached. |
| Nothing fires | Redo Calibrate with firmer, separate attempts. Check the core prints `event:` lines. |
| Fires on its own | Ear clip and flagged sensors first, then redo Calibrate sitting still. As a fallback, start the core with `--rules`. |
| Look tiles never choose | They need good contact on the back four electrodes and a 60 Hz screen. Keep the iPad brightness up and look at one tile for 2 to 3 s. |
| iPad cannot open the page | Same wifi on both? Some event networks block devices from reaching each other. Use a phone hotspot for the laptop and the iPad. |
