# Kinesis app

```
cd app
npm install
cp .env.example .env        # add ElevenLabs and Gemini keys (optional)
npm run dev                 # http://localhost:5173
```

- Runs with or without the headset. The dev server forwards /core to the core (ws://localhost:8765, or KINESIS_CORE in .env); with no core it uses the simulator. Press ? for keys (hold C clench, B B double blink, hold E eyes closed, 1-4 look).
- Start on a specific screen: http://localhost:5173/?start=home (fit, calibrate, home, talk, call, tasks, plan, media, report, look, help)
- Caregiver view on any phone on the same wifi: `npm run dev` already listens on the wifi; open http://<laptop-ip>:5173/#/caregiver
- Own voice: ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID in .env. Each phrase is cached in app/.cache/tts after first use, so demo reruns cost no credits.
- Replies: GEMINI_API_KEY in .env. Without it, canned replies.
- Protocol with the Python core: docs/PROTOCOL.md. Design: docs/DESIGN.md.

## Demo on an iPad or phone (home screen)

1. Laptop with the headset: `python -m kinesis.server --port <port>`, then in `app/`: `npm run dev`.
2. The core prints `open http://<laptop-ip>:5173`. Open that in Safari on the iPad, on the same wifi.
3. Share button, Add to Home Screen. Open Kinesis from the home screen: full screen, no browser bars.
4. Tap once anywhere (Power on). iPad only plays sound after a first touch; after that, phrases chosen with the headset speak too.

The page reaches the headset through the same address (`/core` is forwarded to the core), so nothing else needs setting up. If the core runs on a different laptop, put `KINESIS_CORE=ws://<core-ip>:8765` in `app/.env`.

The listening part of Talk needs the microphone, which Safari only allows over https; the three demo moments do not need it.

## The three demo moments

1. **Say it** → "I need water", spoken in the user's voice.
2. **Get it done** → "Refill my prescription": the agent shows its plan, calls the pharmacy, texts Linda.
3. **Call or text** → Linda → "Can you come here?" (shows up live on the caregiver page on a phone) or **Call Linda**.

Voice: `python scripts/setup_voice.py check`, then `clone` or `use`, then `curl -X POST http://localhost:5173/api/prewarm`. Full guide: docs/SETUP.md.
