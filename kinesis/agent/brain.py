"""Brain-signal features for monitoring, built on BrainFlow's DataFilter
(the same functions as the BrainFlow examples: detrend, get_psd_welch,
get_band_power).

What these flag, and what they do not:
- seizure-like activity: sustained, rhythmic, high line-length activity well
  above the person's own baseline, on more than one channel, that is not
  muscle. Flagged for review, not diagnosed. Ceribell and Epitel are the
  clinical versions of this idea.
- slowing and asymmetry: delta/alpha ratio (DAR) and left/right symmetry
  between O1 and O2, tracked against the person's own baseline. A sharp
  change is a reason to call a clinician; it is not a stroke diagnosis.
- resting alpha peak frequency: the dominant rhythm with eyes closed.
"""
import numpy as np
from brainflow.data_filter import DataFilter, DetrendOperations, WindowOperations

FS = 125
NFFT = 256  # ~0.49 Hz bins at 125 Hz

BANDS = {"delta": (1.0, 4.0), "theta": (4.0, 8.0), "alpha": (8.0, 13.0), "beta": (13.0, 30.0), "muscle": (30.0, 55.0)}


def _prep(x):
    x = np.ascontiguousarray(x, dtype=np.float64).copy()
    DataFilter.detrend(x, DetrendOperations.CONSTANT.value)
    return x


def psd(x, fs=FS):
    x = _prep(x)
    n = min(NFFT, 1 << (len(x).bit_length() - 1))
    amp, freqs = DataFilter.get_psd_welch(x, n, n // 2, fs, WindowOperations.HANNING.value)
    return amp, freqs


def band_powers(p):
    return {b: DataFilter.get_band_power(p, lo, hi) for b, (lo, hi) in BANDS.items()}


def window_features(x, fs=FS):
    """One channel, one window (about 4 s)."""
    x = np.asarray(x, dtype=np.float64)
    amp, freqs = psd(x, fs)
    bp = band_powers((amp, freqs))
    brain = bp["delta"] + bp["theta"] + bp["alpha"] + bp["beta"]
    sel = (freqs >= 2) & (freqs <= 25)
    tot = (freqs >= 1) & (freqs <= 40)
    peak_i = np.argmax(amp[sel])
    y = x - x.mean()
    return {
        "line_length": float(np.mean(np.abs(np.diff(y)))),
        "rms": float(np.std(y)),
        "rhythmicity": float(amp[sel][peak_i] / max(np.sum(amp[tot]), 1e-12)),
        "peak_hz": float(freqs[sel][peak_i]),
        "muscle_ratio": float(bp["muscle"] / max(brain, 1e-12)),
        "dar": float(bp["delta"] / max(bp["alpha"], 1e-12)),
        **{f"p_{k}": float(v) for k, v in bp.items()},
    }


# Thresholds for seizure-like windows, relative to the person's own baseline.
# Tuned on the Bonn dataset (scripts/validate_seizure.py); see that script's
# output for sensitivity and false alarms.
# Two routes to a seizure-like window: sharp (line length up 3.5x) or big
# (amplitude up 4x with line length up 2x; scalp seizures look like this).
# 4 consecutive 4 s windows at a 2 s hop = about 10 s sustained, the usual
# clinical minimum for an electrographic seizure.
# Bonn results (scripts/validate_seizure.py):
#   seizure vs interictal, same patients: 94% flagged, 3% false
#   seizure vs healthy scalp baseline:    75% flagged, 0% false
# Tuned on that same data, so expect lower on new people.
SEIZURE = {"ll_ratio": 3.5, "rms_ratio": 1.8, "rms_ratio_big": 4.0, "ll_ratio_big": 2.0, "rhythmicity": 0.035, "muscle_ratio_max": 0.6}
SEIZURE_RUN = 4


def seizure_like(f, base):
    ll = f["line_length"] / max(base["line_length"], 1e-9)
    rms = f["rms"] / max(base["rms"], 1e-9)
    sharp = ll >= SEIZURE["ll_ratio"] and rms >= SEIZURE["rms_ratio"]
    big = rms >= SEIZURE["rms_ratio_big"] and ll >= SEIZURE["ll_ratio_big"]
    hit = (
        (sharp or big)
        and f["rhythmicity"] >= SEIZURE["rhythmicity"]
        and f["muscle_ratio"] <= SEIZURE["muscle_ratio_max"]
    )
    return hit, {"ll_ratio": round(ll, 2), "rms_ratio": round(rms, 2)}


def symmetry_index(left, right, fs=FS):
    """Brain symmetry index between two homologous channels (0 = symmetric).
    Mean over 1-25 Hz of |R - L| / (R + L) on the power spectra."""
    al, f = psd(left, fs)
    ar, _ = psd(right, fs)
    sel = (f >= 1) & (f <= 25)
    return float(np.mean(np.abs(ar[sel] - al[sel]) / np.maximum(ar[sel] + al[sel], 1e-12)))


def alpha_peak(channels, fs=FS):
    """Peak frequency of the summed occipital spectrum in 7-13 Hz."""
    total = None
    for x in channels:
        a, f = psd(x, fs)
        total = a if total is None else total + a
    sel = (f >= 7) & (f <= 13)
    return float(f[sel][np.argmax(total[sel])])
