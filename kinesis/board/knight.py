"""NeuroPawn Knight board wrapper.

Owns the serial port, runs the channel enable sequence NeuroPawn documents,
exposes the latest window of samples in microvolts, and can record to disk.
Use synthetic=True to develop without a headset.
"""
import json
import os
import time

import numpy as np
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from scipy.signal import filtfilt, iirnotch

# Mains hum: 60 Hz in the US, 50 Hz in most other places (KINESIS_MAINS=50).
MAINS_HZ = float(os.environ.get("KINESIS_MAINS", "60"))

from kinesis.montage import MONTAGE  # pin -> site; our electrodes are on pins 2-7


class Knight:
    def __init__(self, port=None, synthetic=False, imu=False, gains=None, sample_rate=125):
        self.synthetic = synthetic
        self.gains = gains or {ch: 12 for ch in MONTAGE}
        params = BrainFlowInputParams()
        if synthetic:
            self.board_id = BoardIds.SYNTHETIC_BOARD.value
        else:
            self.board_id = (BoardIds.NEUROPAWN_KNIGHT_BOARD_IMU if imu
                             else BoardIds.NEUROPAWN_KNIGHT_BOARD).value
            params.serial_port = port
            # Gain in other_info must match the gain used in chon_ commands or
            # microvolt scaling is wrong. We send per-channel gains below and
            # declare the most common one here.
            common = max(set(self.gains.values()), key=list(self.gains.values()).count)
            params.other_info = json.dumps({"gain": common})
        self.shim = BoardShim(self.board_id, params)
        self.fs = BoardShim.get_sampling_rate(self.board_id)
        self.eeg_rows = BoardShim.get_eeg_channels(self.board_id)
        self.ts_row = BoardShim.get_timestamp_channel(self.board_id)
        self.marker_row = BoardShim.get_marker_channel(self.board_id)
        self._recording = None

    def start(self):
        self.shim.prepare_session()
        self.shim.start_stream(450000)
        if self.synthetic:
            return
        # Channels are off after connect. Commands sent too fast are dropped,
        # and the board prints start-up bytes first ("Wrong end byte"), so wait
        # them out, switch every channel on, then check and retry any that
        # still read exactly zero.
        time.sleep(3)
        for ch, gain in self.gains.items():
            self._switch_on(ch, gain)
        self.off = self._retry_flat()

    def _switch_on(self, ch, gain, slow=1.0):
        time.sleep(0.5 * slow)
        self.shim.config_board(f"chon_{ch}_{gain}")
        time.sleep(1.0 * slow)
        self.shim.config_board(f"rldadd_{ch}")
        time.sleep(0.5 * slow)

    def _flat(self):
        time.sleep(1.5)
        data = self.shim.get_current_board_data(int(self.fs))
        eeg = data[self.eeg_rows, :]
        if eeg.shape[1] < 10:
            return list(self.gains)
        return [ch for ch in self.gains if np.std(eeg[ch - 1]) < 1e-6]

    def _retry_flat(self, tries=3):
        flat = self._flat()
        for attempt in range(1, tries + 1):
            if not flat:
                print(f"All {len(self.gains)} sensors switched on.")
                return []
            print(f"Sensors on pins {flat} did not switch on. Trying again ({attempt} of {tries})...")
            for ch in flat:
                self._switch_on(ch, self.gains[ch], slow=2.0)
            flat = self._flat()
        if flat:
            print(f"Pins {flat} still read nothing. Unplug and replug the board, then start again.")
        else:
            print(f"All {len(self.gains)} sensors switched on.")
        return flat

    def latest(self, n_samples):
        """Non-destructive read of the most recent n samples.
        Returns (eeg[channels x samples] in uV, timestamps)."""
        data = self.shim.get_current_board_data(n_samples)
        eeg = data[self.eeg_rows, :]
        if not self.synthetic and eeg.shape[1] > 30:
            eeg = self._denoise(eeg)
        return eeg, data[self.ts_row, :]

    def _denoise(self, eeg):
        """Remove mains hum, which dry electrodes pick up strongly."""
        if not hasattr(self, "_notch"):
            self._notch = iirnotch(MAINS_HZ, 30.0, fs=self.fs) if MAINS_HZ < self.fs / 2 else None
        if self._notch is None:
            return eeg
        b, a = self._notch
        return filtfilt(b, a, eeg, axis=1, padlen=min(eeg.shape[1] - 1, 30))

    def latest_seconds(self, seconds):
        return self.latest(int(seconds * self.fs))

    def channel(self, eeg, board_channel):
        """Row of a board channel number (1-based) within an eeg array."""
        return eeg[board_channel - 1]

    def mark(self, value):
        """Insert a marker (cue onset etc.) into the stream."""
        self.shim.insert_marker(float(value))

    def start_recording(self, path):
        """Stream everything to a BrainFlow-format file for replay."""
        self.shim.add_streamer(f"file://{path}:w")
        self._recording = path

    def stop(self):
        try:
            self.shim.stop_stream()
        finally:
            self.shim.release_session()
