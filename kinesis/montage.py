"""Which board pin each electrode is on.

Our headset has its 6 electrodes on pins 2 to 7, in the order below. The
recordings showed it: pins 1 and 8 read nothing or floated, pins 2 to 7 had
signal. If the wires are moved to pins 1 to 6, set KINESIS_FIRST_PIN=1.
"""
import os

FIRST_PIN = int(os.environ.get("KINESIS_FIRST_PIN", "2"))
ORDER = ["Oz", "O1", "O2", "POz", "Fp1", "T7"]
MONTAGE = {FIRST_PIN + i: site for i, site in enumerate(ORDER)}  # pin -> site
PIN = {site: pin for pin, site in MONTAGE.items()}                # site -> pin
OCCIPITAL = [PIN[s] for s in ("Oz", "O1", "O2", "POz")]
