"""Download the public labeled datasets Kinesis is built and scored on, into
data/external/ (kept out of git), and print what each label means.

python scripts/get_datasets.py                 # all, Tsinghua people 1-10
python scripts/get_datasets.py --tsinghua 35   # all 35 people (about 3.7 GB)
python scripts/get_datasets.py --only speech

Details and citations: docs/DATASETS.md.
"""
import argparse
import sys
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1] / "data" / "external"
THU = "https://bci.med.tsinghua.edu.cn/upload/yijun"
NEMAR = "https://data.nemar.org/nm000113/v1.0.0.zip"
BONN_PAGE = "https://www.ukbonn.de/epileptologie/arbeitsgruppen/ag-lehnertz-neurophysik/downloads/"

LABELS = {
    "tsinghua_ssvep": "S<n>.mat: data[64 ch, 1500 samples, 40 targets, 6 blocks] at 250 Hz; the label is the target index. "
                      "Freq_Phase.mat: each target's flash rate (8 to 15.8 Hz) and phase. Epochs start 0.5 s before the flashing.",
    "bci2020_imagined_speech": "BIDS. sub-XX/eeg/*_events.tsv: trial_type is Hello, Help me, Stop, Thank you or Yes; 3.1 s per trial. "
                               "run-00 train (300), run-01 validation (50), run-02 test (50). 64 ch, 256 Hz.",
    "bonn_epilepsy": "Sets of 100 single-channel recordings, 23.6 s at 173.61 Hz. Z healthy eyes open (scalp), O healthy eyes closed "
                     "(scalp), N between seizures away from the focus, F between seizures at the focus, S seizure (intracranial).",
}


def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  have {dest.name}")
        return dest
    print(f"  downloading {url}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        tmp.rename(dest)
    return dest


def tsinghua(n):
    d = ROOT / "tsinghua_ssvep"
    d.mkdir(parents=True, exist_ok=True)
    fetch(f"{THU}/Freq_Phase.mat", d / "Freq_Phase.mat")
    for i in range(1, n + 1):
        fetch(f"{THU}/S{i}.mat.7z", d / f"S{i}.mat.7z")
    print("  unpack each S<n>.mat.7z with 7-Zip (or: pip install py7zr), then:")
    print(f"  python scripts/validate_ssvep.py {d} --still kinesis/data/gestures/double_trial*.csv")
    return d


def speech():
    d = ROOT / "bci2020_imagined_speech"
    d.mkdir(parents=True, exist_ok=True)
    z = fetch(NEMAR, ROOT / "nm000113_v1.0.0.zip")
    if not (d / "participants.tsv").exists():
        print("  unzipping")
        zipfile.ZipFile(z).extractall(d)
    print(f"  then: python scripts/eval_imagined_speech.py {d}")
    return d


def bonn():
    d = ROOT / "bonn_epilepsy"
    d.mkdir(parents=True, exist_ok=True)
    print(f"  the Bonn group hosts the sets on their page; download Z, O, N, F, S from\n  {BONN_PAGE}")
    print(f"  and unzip them into {d}, then: python scripts/validate_seizure.py {d}")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsinghua", type=int, default=10, help="how many people (1-35)")
    ap.add_argument("--only", choices=["ssvep", "speech", "seizure"])
    a = ap.parse_args()
    jobs = {"ssvep": ("tsinghua_ssvep", lambda: tsinghua(max(1, min(35, a.tsinghua)))),
            "speech": ("bci2020_imagined_speech", speech),
            "seizure": ("bonn_epilepsy", bonn)}
    for key, (name, run) in jobs.items():
        if a.only and a.only != key:
            continue
        print(f"\n{name}")
        d = run()
        (d / "LABELS.txt").write_text(LABELS[name] + "\n")
        print(f"  labels: {LABELS[name]}")


if __name__ == "__main__":
    sys.exit(main())
