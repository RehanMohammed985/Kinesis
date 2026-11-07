# Hardware setup

## What is in the box
Lattice headset with chin strap, Knight board on an Arduino, USB-C cable, dry spike recording electrodes (expect 7-8 streaming), comfort padding electrodes (foam, no signal, for tension), one ear-clip ground that plugs into both RLD and COMM, conductive paste, paper quick start. Check the box label: if it says IMU, the board is the IMU variant (BrainFlow id 66) and we get accelerometer and gyro for free.

## Wiring

| Channel pin | Lattice node | Used for |
|---|---|---|
| 1 | Oz | SSVEP tiles, alpha |
| 2 | O1 | SSVEP, alpha |
| 3 | O2 | SSVEP, alpha |
| 4 | POz | SSVEP |
| 5 | Fp1 | blinks |
| 6 | Fp2 | blinks |
| 7 | T7 (or T8) | jaw clench |
| 8 | off | spare |

- Each electrode wire goes to its channel's positive rail pin. Wrong rail or wrong pin is the number one mistake in the organizer guide.
- Slide each used channel's switch away from the header. Leave channel 8's switch toward the header.
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
1. Open the Visualizer, pick the port (top right). IMU box: choose Knight Board IMU.
2. Activate channels one at a time: Active, then Route RLD, wait for the trace.
3. Eyes closed 3 s: a clean ~10 Hz wave on channels 1-4.
4. Blink: spikes on 5 and 6. Clench: channel 7 goes wild.
5. Close the Visualizer. The serial port is exclusive; BrainFlow cannot open it while the Visualizer holds it.

## Board facts
- 8 channels, 16-bit, default 125 SPS (125/250/500 available), bandwidth 1-62.5 Hz, on-board 50/60 Hz notch, gain 12 = 0.128 uV/count, range +/-4.19 mV.
- Channels are OFF after connect. After `start_stream(450000)` wait 2 s, then per channel: wait 0.5 s, `chon_N_12`, wait 1 s, `rldadd_N`, wait 0.5 s. Commands sent faster are silently dropped. Full enable takes ~30 s.
- BrainFlow ids: NEUROPAWN_KNIGHT_BOARD = 57, NEUROPAWN_KNIGHT_BOARD_IMU = 66 (accel rows 11-13, gyro 14-16).
- Ports: Mac `/dev/cu.usbmodem*`, Linux `/dev/ttyACM0`, Windows `COMx`.
