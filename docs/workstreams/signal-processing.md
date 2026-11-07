# signal-processing
Owner: signal person 1
- [ ] kinesis/signal/filters.py: detrend, butter bandpass, notch, window helpers (125 Hz)
- [ ] kinesis/signal/emg.py: 20-55 Hz power on ch 7, k x baseline, 1 s refractory
- [ ] kinesis/signal/blink.py: lowpass 10 Hz Fp1/Fp2, peak threshold, double within 600 ms
- [ ] kinesis/signal/alpha.py: 8-12 Hz on ch 1-3 vs baseline, sustained 1 s
- [ ] kinesis/signal/ssvep.py: NeuroPawn TRCA wrapper + CCA fallback + reject margin
- [ ] kinesis/signal/quality.py (Fit): flatline, saturation, line noise, alpha block -> color + prompt
Done: all detectors pass on every teammate's calibration recording; < 1 false positive / min at rest
