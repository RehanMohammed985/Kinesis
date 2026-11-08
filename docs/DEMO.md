# Demo video

About 2 minutes. One person wears the headset and plays Walter. A second person sets him up and narrates. A third holds the "Linda" phone.

## The story

Walter is 72. A stroke took most of his speech and the use of his right side. The video follows one minute of his day:
- He asks for water, in his own voice.
- He reaches his wife.
- He gets an errand done.

Every choice is a jaw clench, and going back is a double blink. Nothing is sped up except the onboarding.

## Cameras

| Camera | What | How |
|---|---|---|
| A | Wide: Walter in the headset, iPad on a stand in front of him | phone on a tripod, landscape |
| B | The iPad screen | iPad screen recording (Control Center, record) |
| C | Linda's phone when messages arrive | close-up, handheld |

Cut between A and B. Use C only for the moments in scenarios 2 and 3.

## Shot list

### 0:00 to 0:12, onboarding

| Time | Picture | Words (voice-over) |
|---|---|---|
| 0:00 | A: the operator slides the headset on Walter and clips the ear clip. One 2 s shot. | "Kinesis is a $350 headset and an app." |
| 0:02 | B: Fit screen, sensors green. The operator taps **Quick check, 10 s**. | "Setup takes five minutes, once. After that, a ten-second check." |
| 0:03 | B: **Stay still** (3.5 s), then **Get ready**, **Clench now**. Walter clenches, the dot turns green and a tone plays. | |
| 0:07 | B: **Get ready**, **Blink twice now**. Walter double blinks, green, tone. | |
| 0:10 | B: **Ready.** Then Home on its own. | "That's it. He's in." |

Real time, no speed-up. Each cue waits until he does it, shows green for 0.7 s, then a short pause before the next one, so nothing looks rushed. If he misses a cue, it waits up to 2.6 s and moves on anyway: cut that take and redo it.

### 0:12 to 0:40, scenario 1: say it

| Time | Picture | Words |
|---|---|---|
| 0:12 | A then B: Home. The yellow frame rests on **Say it**. Walter clenches. | "Walter had a stroke. He cannot speak or use his right hand." |
| 0:20 | B: Say it screen. The frame starts on **I need water**. Walter clenches. | "One clench opens Say it. One more..." |
| 0:24 | A: his voice says "I need water". B: the phrase shows large. Hold 3 s. | (let the voice play, no words) |
| 0:30 | | "...and he says it out loud, in an ElevenLabs voice. Clone it from a few minutes of old videos or voicemails, and it is his own voice again." |

### 0:40 to 1:15, scenario 2: reach Linda

| Time | Picture | Words |
|---|---|---|
| 0:40 | B: Walter double blinks, back to Home. The frame steps to **Call or text**. Clench. | "No phone in his hand." |
| 0:50 | B: **Linda**, clench. Then the frame steps to **Can you come here?**, clench. The screen shows **Sent**. | |
| 1:00 | C: Linda's phone lights up with the text, then a voice message. She plays it: his voice, "Can you come here?" | "A text, and a voice message in his own voice, on her phone in seconds." |

### 1:15 to 1:50, scenario 3: get it done

| Time | Picture | Words |
|---|---|---|
| 1:15 | B: double blink twice, back to Home. The frame steps to **Get it done**, clench, then **Refill my prescription**, clench. | "AI is automating everyone's life except the people who need it most." |
| 1:25 | B: the plan appears. The frame starts on **Cancel**, then moves to **Go ahead**. Clench. | "Kinesis shows every step first and waits for his yes." |
| 1:30 | B: the four steps turn green one by one: find the prescription, call the pharmacy, confirm pickup, text Linda. | "One choice, and the whole errand runs." |
| 1:40 | C: Linda's phone: "Can you pick up my Clopidogrel at Walgreens, Hillsborough St today?" | |

### 1:50 to 2:00, close

B: Home. End card: **Kinesis. Run your day with your mind.** Then: $350 headset, 10-second check, 95% look-to-choose on the 35-person SSVEP benchmark.

## How the app is paced for video

- **Scan speed:** the frame moves every 2.4 s. A new screen holds its first tile about 4 s.
- **After each choice:** the frame rests 1.4 s on what was chosen before it moves on.
- **While Walter clenches:** the frame holds still, so the choice lands on the tile he meant.
- **Slower:** add **?dwell=3** to the address for 3 s per tile.

## Clenches per scenario

| Scenario | Inputs | About |
|---|---|---|
| 1 Say it | clench (Say it), clench (I need water) | 10 s |
| 2 Reach | double blink, wait 2 steps, clench (Call or text), clench (Linda), wait 1 step, clench (Can you come here?) | 20 s |
| 3 Get it done | double blink twice, wait 1 step, clench (Get it done), clench (Refill), wait 1 step, clench (Go ahead) | 25 s |

## Before recording (30 minutes ahead)

1. **Laptop:** on battery, with the charger unplugged (it adds electrical hum). Do Not Disturb on, on the laptop and the iPad.
2. **Voice:** with the app running, **curl -X POST http://localhost:5173/api/prewarm**. Every phrase then plays instantly.
3. **Linda's real phone:** **python scripts/set_contact.py linda +1XXXXXXXXXX --test**, using the friend's number.
   - The first time, macOS asks to let Terminal control Messages. Click OK.
   - The friend should get a test text and a voice message.
4. **Start the core with real texts.** Calls stay in practice mode, so no call window pops up:
   **KINESIS_LIVE=1 KINESIS_BACKEND=mac python -m kinesis.server --port /dev/cu.usbserial-A5069RR4**
5. **Full calibration once, before filming.** Setup, then Calibrate. This saves Walter's own model. The video then uses the quick check.
6. **Caregiver page (optional second phone):** open **http://LAPTOP-IP:5173/#/caregiver**. Each message has a "Play in Walter's voice" button.
7. **Rehearse each scenario twice.** Count the clenches from the table above.

## If something goes wrong on stage

- **Frame not moving:** a double clench paused it. Clench once to resume.
- **Text did not arrive:** check the core terminal for "FAILED text". Run the --test line again.
- **Headset misbehaves during a live pitch:** switch to the simulator and say plainly that it is the simulator.
