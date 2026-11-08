"""Is the headset sending data, and which electrodes touch skin?

python scripts/check_headset.py                 # tries every USB serial port it finds
python scripts/check_headset.py --port /dev/cu.usbmodem1101

Close the EXG Visualizer and stop the Kinesis core first (only one program
can use the headset). Takes about 25 s per port: 15 s to switch the
sensors on, 8 s of recording.
"""
import argparse
import glob
import sys
import time
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfiltfilt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.board.knight import Knight  # noqa: E402
from kinesis.montage import MONTAGE  # noqa: E402


def ports():
    found = sorted(glob.glob("/dev/cu.usb*") + glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
    try:
        from serial.tools import list_ports
        found += [p.device for p in list_ports.comports() if p.device not in found and "Bluetooth" not in p.device]
    except ImportError:
        pass
    return found


def check(port, seconds=8):
    print(f"\n=== {port}")
    try:
        k = Knight(port=port)
        print("switching sensors on (about 15 s)...")
        k.start()
    except Exception as e:  # noqa: BLE001
        print(f"  could not open it: {e}")
        print("  if it says busy or permission: quit the EXG Visualizer and the Kinesis core, then try again")
        return False
    try:
        k.shim.get_board_data()  # drop what arrived while switching on
        t0 = time.time()
        time.sleep(seconds)
        data = k.shim.get_board_data()
    finally:
        k.stop()
    n = data.shape[1]
    rate = n / (time.time() - t0)
    print(f"  samples: {n} in {seconds} s ({rate:.0f} per second, expected about 125)")
    if n < 50:
        print("  NO DATA. The port opened but the board sent nothing.")
        print("  - try the other ports listed above, or unplug and replug the USB cable")
        print("  - some USB cables only charge; try another one")
        print("  - check the board's power light, and that the board type is the plain Knight (not IMU)")
        return False
    eeg = data[k.eeg_rows]
    sos = butter(2, [1, 40], btype="band", fs=125, output="sos")
    line = butter(4, [45, 60], btype="band", fs=125, output="sos")
    stds = {}
    for pin in range(1, 9):
        x = eeg[pin - 1] - eeg[pin - 1].mean()
        stds[pin] = float(np.std(sosfiltfilt(sos, x))) if np.std(x) > 0 else 0.0
    used = [stds[p] for p in MONTAGE if stds[p] > 0.5]
    typical = float(np.percentile(used, 25)) if used else 0.0
    print("  pin  site  spread 1-40 Hz (uV)  verdict")
    for pin in range(1, 9):
        site = MONTAGE.get(pin, "-")
        x = eeg[pin - 1] - eeg[pin - 1].mean()
        s = stds[pin]
        if pin not in MONTAGE:
            verdict = "not used"
        elif np.std(x) < 0.5:
            verdict = "FLAT: switched off or no signal at all"
        elif typical and s > 10 * typical:
            verdict = "FLOATING: not touching skin, re-seat it"
        elif np.mean(sosfiltfilt(line, x) ** 2) > 0.6 * np.mean(sosfiltfilt(sos, x) ** 2):
            verdict = "NOISY: mains hum, check the ear clip and unplug the charger"
        elif s > 200:
            verdict = "very large: loose contact or moving"
        else:
            verdict = "ok, touching skin"
        print(f"  {pin:>3}  {site:<4}  {s:>18.1f}  {verdict}")
    flat = [p for p in MONTAGE if np.std(eeg[p - 1]) < 0.5]
    if len(flat) == len(MONTAGE):
        print("  all sensors flat: the board streams but the channels never switched on. Restart the board (unplug, replug) and run this again.")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    a = ap.parse_args()
    found = [a.port] if a.port else ports()
    print("serial ports found:", found or "none")
    if not found:
        print("No USB serial port. Check the cable (some only charge) and that the board is powered.")
        return
    for p in found:
        if check(p):
            print(f"\nThis port works. Start Kinesis with:\n  python -m kinesis.server --port {p}")
            return
    print("\nNo port gave data. Paste this whole output to the team.")


if __name__ == "__main__":
    main()
