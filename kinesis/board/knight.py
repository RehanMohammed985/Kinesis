"""NeuroPawn Knight board wrapper.

Owns the serial port, runs the channel enable sequence NeuroPawn documents,
exposes the latest window of samples in microvolts, and can record to disk.
Use synthetic=True to develop without a headset.
"""
import json
import time

import numpy as np
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams

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
        # Channels are off after connect. Commands sent too fast are dropped.
        time.sleep(2)
        for ch, gain in self.gains.items():
            time.sleep(0.5)
            self.shim.config_board(f"chon_{ch}_{gain}")
            time.sleep(1)
            self.shim.config_board(f"rldadd_{ch}")
            time.sleep(0.5)

    def latest(self, n_samples):
        """Non-destructive read of the most recent n samples.
        Returns (eeg[channels x samples] in uV, timestamps)."""
        data = self.shim.get_current_board_data(n_samples)
        eeg = data[self.eeg_rows, :]
        return eeg, data[self.ts_row, :]

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
