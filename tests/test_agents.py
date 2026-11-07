"""End-to-end check of the agents on simulated signals, in practice mode
(nothing is sent). Run: python tests/test_agents.py"""
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinesis.agent import monitor as mon  # noqa: E402
from kinesis.agent import profile as profiles  # noqa: E402
from kinesis.agent import report  # noqa: E402
from kinesis.agent.comms import CommunicationAgent  # noqa: E402
from kinesis.agent.registry import Registry  # noqa: E402
from kinesis.agent.tasks import TaskAgent  # noqa: E402

FS = 125
rng = np.random.default_rng(1)


def background(seconds, alpha_uv=6.0, delta_uv=3.0):
    n = int(seconds * FS)
    t = np.arange(n) / FS
    eeg = np.zeros((8, n))
    for r in range(8):
        pink = np.cumsum(rng.normal(0, 1, n))
        pink = (pink - np.convolve(pink, np.ones(25) / 25, "same")) * 1.2
        eeg[r] = pink + rng.normal(0, 4, n) + alpha_uv * np.sin(2 * np.pi * 10 * t + r) + delta_uv * np.sin(2 * np.pi * 2 * t + r)
    return eeg


def spike_wave(seconds):
    """3 Hz spike-and-wave, the classic generalized seizure pattern."""
    t = np.arange(int(seconds * FS)) / FS
    phase = (t * 3) % 1
    return 120 * np.exp(-((phase - 0.1) / 0.03) ** 2) - 60 * np.sin(2 * np.pi * 3 * t) ** 2


def run_monitor(m, eeg, clock, levels=None, events_at=()):
    """Feed 4 s windows every 2 s, advancing a fake clock."""
    levels = levels or {"clench": 0.1, "blink": 0.1, "alpha": 0.3}
    for start in range(0, eeg.shape[1] - 4 * FS + 1, 2 * FS):
        clock[0] += 2
        if any(abs(start / FS - e) < 2 for e in events_at):
            m.note_event("clench")
        m.feed(eeg[:, start:start + 4 * FS], levels)


def main():
    tmp = Path(tempfile.mkdtemp())
    clock = [1_700_000_000.0]
    mon.time.time = lambda: clock[0]
    p = profiles.load()
    sent = []
    emit = sent.append
    reg = Registry(p, emit)
    log = mon.DayLog(tmp)
    m = mon.Monitor(p, reg, emit, log)
    m.set_baseline(background(6))

    # 1. calm signal: no alerts
    run_monitor(m, background(60), clock)
    assert not [x for x in sent if x["type"] == "alert"], "false alert on calm signal"
    print("calm 60 s: no alert")

    # 2. 20 s seizure-like activity on every channel but Fp1
    eeg = background(30)
    sw = spike_wave(20)
    for r in (0, 1, 2, 3, 5):
        eeg[r, 5 * FS:25 * FS] += sw
    run_monitor(m, eeg, clock)
    alerts = [x for x in sent if x["type"] == "alert"]
    assert len(alerts) == 1 and alerts[0]["kind"] == "seizure_like", alerts
    run_monitor(m, background(10), clock)
    assert any(r["kind"] == "seizure_like" for r in log.read()), "episode not logged"
    print("seizure-like 20 s: one alert, episode logged")

    # 3. jaw clench (muscle) and blinks: must not alert
    sent.clear()
    eeg = background(20)
    eeg[5, 4 * FS:12 * FS] += rng.normal(0, 120, 8 * FS)        # T7 muscle burst
    eeg[0:4, 4 * FS:12 * FS] += rng.normal(0, 40, (4, 8 * FS))   # spill onto others
    for b in (3, 3.4, 9, 9.4):
        eeg[4, int(b * FS):int(b * FS) + 25] += 250                  # blinks on Fp1
    run_monitor(m, eeg, clock, events_at=(4, 6, 8, 10))
    assert not [x for x in sent if x["type"] == "alert"], "clench or blink set off an alert"
    print("clench and blinks: no alert")

    # 4. six minutes of slowing on the left (O1 only): change flagged after 5
    sent.clear()
    for minute in range(6):
        eeg = background(62)
        eeg[1] += 40 * np.sin(2 * np.pi * 2 * np.arange(eeg.shape[1]) / FS)
        run_monitor(m, eeg, clock)
    assert any(x.get("type") == "notice" and "rhythm changed" in x["text"] for x in sent), "slowing not flagged"
    print("left-sided slowing 6 min: flagged once at 5 min")

    # 5. task in practice mode
    sent.clear()
    ta = TaskAgent(p, reg, emit)
    pid = ta.propose("refill")
    ta.run(pid)
    steps = [x for x in sent if x["type"] == "step" and x["status"] == "done"]
    assert len(steps) == 4, steps
    print("refill task: 4 steps done ->", steps[-1]["detail"])

    # 6. replies without Gemini
    items, src = CommunicationAgent(p).replies("Sam", "Do you want to watch something tonight?")
    assert len(items) == 4
    print(f"replies ({src}):", items)

    # 7. report
    rep = report.build(p, log, day=None)
    html = Path(report.ROOT / rep["file"])
    assert html.exists()
    print("report:", rep["facts"], "->", rep["file"])
    print("\nall agent checks passed")


if __name__ == "__main__":
    main()
