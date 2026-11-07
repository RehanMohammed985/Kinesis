"""Rebuild a continuous recording from a file of overlapping snapshots.

Our first baseline recordings saved get_current_board_data(500) over and over
(each row block is the latest 4 s, mean removed, saved ~6 times a second), so
the file is ~350k rows for ~60 s of signal. This finds how far each snapshot
slid, keeps only the new samples, and stitches them into one continuous
signal at 125 Hz. Going forward, record with scripts/record.py (BrainFlow's
file streamer), which writes each sample once.

python scripts/reconstruct_windows.py in.csv out.csv [--win 500]
"""
import argparse

import numpy as np


def reconstruct(x, win=500, ref_ch=3, max_slide=80):
    """x: rows x channels made of stacked windows of `win` rows."""
    C = x.reshape(-1, win, x.shape[1])
    out = [C[0]]
    tail = C[0]
    slides = []
    for k in range(1, C.shape[0]):
        b = C[k]
        a_ref, b_ref = tail[:, ref_ch], b[:, ref_ch]
        best, best_d = -2, 0
        for d in range(0, max_slide):
            u = a_ref[d + 20: win - 20]
            v = b_ref[20: win - 20 - d]
            u = u - u.mean()
            v = v - v.mean()
            s = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12)
            if s > best:
                best, best_d = s, d
        d = best_d
        slides.append(d)
        if d == 0:
            continue
        # match the offset of the overlapping part, then keep the d new samples
        overlap_a = tail[d:]
        overlap_b = b[: win - d]
        offset = (overlap_a - overlap_b).mean(axis=0)
        new = b[win - d:] + offset
        out.append(new)
        tail = np.vstack([tail[d:], new])
    return np.vstack(out), np.array(slides)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--win", type=int, default=500)
    a = ap.parse_args()
    x = np.loadtxt(a.src, delimiter=",")
    y, slides = reconstruct(x, a.win)
    np.savetxt(a.dst, y, delimiter=",", fmt="%.4f")
    print(f"{a.src}: {x.shape[0]} rows -> {y.shape[0]} samples ({y.shape[0] / 125:.1f} s at 125 Hz), "
          f"median slide {np.median(slides):.0f}, zero-slide snapshots {int((slides == 0).sum())}")


if __name__ == "__main__":
    main()
