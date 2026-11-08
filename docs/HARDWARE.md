# Hardware setup

## What is in the box
Lattice headset with chin strap, standard Knight board (not IMU, BrainFlow id 57) on an Arduino, USB-C cable, 6 dry spike recording electrodes, comfort padding electrodes (foam, no signal, for tension), one ear-clip ground that plugs into both RLD and COMM, conductive paste, paper quick start.

## Wiring

We have 6 electrodes. One forehead sensor is enough for blinks (a blink is hundreds of microvolts).

Our headset has the electrodes on **pins 2 to 7** (the recordings show pins 1 and 8 empty). The core reads the pin map from kinesis/montage.py; if the wires move to pins 1 to 6, set KINESIS_FIRST_PIN=1.

| Channel pin | Lattice node | Used for |
|---|---|---|
| 2 | Oz | look tiles (SSVEP), eyes closed (alpha) |
| 3 | O1 | look tiles, eyes closed |
| 4 | O2 | look tiles, eyes closed |
| 5 | POz | look tiles |
| 6 | Fp1 | double blink |
| 7 | T7 (or T8) | jaw clench |
| 1, 8 | off | switches toward the header |

- Each electrode wire goes to its channel's positive rail pin. Wrong rail or wrong pin is the number one mistake in the organizer guide.
- Slide the switches for the pins in use (2 to 7) away from the header. Leave 1 and 8 toward the header so they add no noise.
- Ear clip on the earlobe, leads into RLD and COMM.
- Comfort pads around the electrodes so the frame sits level and the spikes get constant pressure.

## Dry vs paste
- Start dry at gain 12.
- After the contact check, paste only the electrodes that read flat or noisy (usually the occipital four on thick hair). A pasted electrode must run at gain 4 or 6 or it clips: use `chon_N_6` for that channel and set `other_info` gain to match.

## Hair
- Braids or locs: seat each spike in a part line, not on a braid. Put comfort pads on the braids to carry tension.
- Coily hair: part a small section with a comb at each site before screwing in the spike.
- The Fit screen will flag the exact electrode to fix; do not guess.

## Contact check in the EXG Visualizer (before any code)
1. Open the Visualizer, pick the port (top right). Board type: Knight Board (not IMU).
2. Activate channels one at a time: Active, then Route RLD, wait for the trace.
3. Eyes closed 3 s: a clean ~10 Hz wave on pins 2-5 (needs good contact at the back).
4. Blink: spike on pin 6. Clench: every channel bursts, pin 7 most.
5. Close the Visualizer. The serial port is exclusive; BrainFlow cannot open it while the Visualizer holds it.

## Board facts
- 8 channels, 16-bit, default 125 SPS (125/250/500 available), bandwidth 1-62.5 Hz, on-board 50/60 Hz notch, gain 12 = 0.128 uV/count, range +/-4.19 mV.
- Channels are OFF after connect. After `start_stream(450000)` wait 2 s, then per channel: wait 0.5 s, `chon_N_12`, wait 1 s, `rldadd_N`, wait 0.5 s. Commands sent faster are silently dropped. Full enable takes ~30 s.
- BrainFlow ids: NEUROPAWN_KNIGHT_BOARD = 57, NEUROPAWN_KNIGHT_BOARD_IMU = 66 (accel rows 11-13, gyro 14-16).
- Ports: Mac `/dev/cu.usbmodem*`, Linux `/dev/ttyACM0`, Windows `COMx`.
