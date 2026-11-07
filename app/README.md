# Kinesis app

```
cd app
npm install
cp .env.example .env        # add ElevenLabs and Gemini keys (optional)
npm run dev                 # http://localhost:5173
```

- Runs with or without the headset. With no core on ws://localhost:8765 it uses the simulator. Press ? for keys (hold C clench, B B double blink, hold E eyes closed, 1-4 look).
- Start on a specific screen: http://localhost:5173/?start=home (fit, calibrate, home, talk, call, tasks, plan, media, report, look, help)
- Caregiver view on any phone on the same wifi: run `npm run dev -- --host`, then open http://<laptop-ip>:5173/#/caregiver
- Own voice: ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID in .env. Each phrase is cached in app/.cache/tts after first use, so demo reruns cost no credits.
- Replies: GEMINI_API_KEY in .env. Without it, canned replies.
- Protocol with the Python core: docs/PROTOCOL.md. Design: docs/DESIGN.md.
