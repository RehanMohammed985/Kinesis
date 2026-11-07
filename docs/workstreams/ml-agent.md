# ml-agent
Owner: AI person
- [ ] kinesis/agent/context.py: transcribe last 20 s of mic (Whisper or Gemini audio)
- [ ] kinesis/agent/predict.py: Gemini -> 4 likely replies given transcript, persona, setting; prefetch next 4
- [ ] kinesis/agent/profile.py: persona from user's own messages
- [ ] message sets: home, work, clinic, out, reading/media
- [ ] kinesis/agent/monitor.py: passive log (rest periods, EMG anomalies, Fit drift) -> report summary, no diagnoses
- [ ] stretch: cross-subject TRCA transfer from OpenBMI
Done: question into mic -> 4 good replies in < 2 s, served over the WebSocket
