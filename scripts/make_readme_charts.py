"""Charts for the README, from the numbers in docs/VALIDATION.md and
kinesis/data/*/README.md. Writes SVGs to docs/img/.

python scripts/make_readme_charts.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

INK, PAPER, MINERAL, SIGNAL, SETTLED, ALARM = "#1D2A2E", "#F7F8F5", "#DCE1DD", "#F4C21B", "#2E7457", "#C5301F"
SOFT = "#4A5A5F"
OUT = Path(__file__).resolve().parents[1] / "docs" / "img"

family = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({
    "font.family": family, "font.size": 12, "svg.fonttype": "path",
    "axes.edgecolor": SOFT, "axes.labelcolor": INK, "xtick.color": SOFT, "ytick.color": SOFT,
    "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
})


def frame(title, subtitle, size=(7.2, 3.7)):
    fig, ax = plt.subplots(figsize=size)
    fig.patch.set_facecolor(PAPER)          # a solid card, so it reads on GitHub dark mode too
    ax.set_facecolor(PAPER)
    fig.text(0.035, 0.94, title, fontsize=15, fontweight="bold", va="top")
    fig.text(0.035, 0.865, subtitle, fontsize=10.5, color=SOFT, va="top")
    fig.subplots_adjust(left=0.1, right=0.97, top=0.74, bottom=0.16)
    return fig, ax


def pct(ax):
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25", "50", "75", "100%"])
    ax.grid(axis="y", color=MINERAL, linewidth=1)
    ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(OUT / name, facecolor=PAPER)
    plt.close(fig)
    print("wrote", OUT / name)


def ssvep():
    fig, ax = frame("Look to choose: 95% correct in 2 seconds",
                    "Tsinghua SSVEP benchmark, 35 people, 4 targets, only our 4 back channels at 125 Hz")
    w = ["1 s", "1.5 s", "2 s", "3 s"]
    v = [87.5, 91.8, 95.0, 97.5]
    bars = ax.bar(w, v, color=[MINERAL, MINERAL, SIGNAL, MINERAL], edgecolor=INK, linewidth=1.2, width=0.62)
    for b, x in zip(bars, v):
        ax.text(b.get_x() + b.get_width() / 2, x + 2, f"{x:.1f}%", ha="center", fontweight="bold")
    ax.axhline(25, color=ALARM, linestyle=(0, (4, 3)), linewidth=1.4)
    ax.text(-0.42, 27.5, "chance", color=ALARM, fontsize=10, ha="left")
    ax.set_xlabel("seconds of looking")
    pct(ax)
    save(fig, "ssvep-accuracy.svg")


def gestures():
    fig, ax = frame("Clench and double blink, learned per person",
                    "5 trials on our headset, each scored by a model trained on the other 4; 2 mix-ups")
    labels = ["Double blink\nfixed rules", "Double blink\nlearned model", "Clench\nlearned model"]
    v = [0, 64 / 71 * 100, 40 / 41 * 100]
    notes = ["0 caught", "64 of 71", "40 for 41"]
    bars = ax.bar(labels, v, color=[MINERAL, SETTLED, SETTLED], edgecolor=INK, linewidth=1.2, width=0.58)
    for b, x, n in zip(bars, v, notes):
        ax.text(b.get_x() + b.get_width() / 2, x + 2.5, n, ha="center", fontweight="bold")
    ax.text(0, 30, "fixed rules\nmissed every one", ha="center", fontsize=10, color=SOFT)
    pct(ax)
    save(fig, "gestures.svg")


def speech():
    fig, ax = frame("Imagined words: the limit of 6 dry electrodes",
                    "2020 BCI Competition imagined speech, 15 people, held-out trials")
    labels = ["5 words\nall 64 channels", "5 words\nour 6 electrodes", "\"Yes\" vs \"Stop\"\nour 6 electrodes"]
    v = [41.5, 26.0, 57.8]
    chance = [20, 20, 50]
    bars = ax.bar(labels, v, color=[INK, MINERAL, MINERAL], edgecolor=INK, linewidth=1.2, width=0.58)
    for b, x, c in zip(bars, v, chance):
        cx = b.get_x() + b.get_width() / 2
        ax.text(cx, x + 2.5, f"{x:.1f}%", ha="center", fontweight="bold")
        ax.plot([b.get_x() - 0.06, b.get_x() + b.get_width() + 0.06], [c, c], color=ALARM, linewidth=2)
    ax.text(2.42, 92, "red line: chance", ha="right", va="top", fontsize=10, color=ALARM)
    pct(ax)
    save(fig, "speech.svg")


def seizure():
    fig, ax = frame("Seizure-like activity, flagged from a person's own baseline",
                    "Bonn epilepsy dataset, recordings flagged after 4 windows in a row")
    groups = ["Same patients\n(intracranial)", "Against healthy\nscalp recordings"]
    caught, false = [94, 75], [3, 0]
    x = range(len(groups))
    a = ax.bar([i - 0.17 for i in x], caught, width=0.32, color=SETTLED, edgecolor=INK, linewidth=1.2, label="seizure recordings flagged")
    b = ax.bar([i + 0.17 for i in x], false, width=0.32, color=MINERAL, edgecolor=INK, linewidth=1.2, label="other recordings flagged")
    for bars in (a, b):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 2.5, f"{r.get_height():.0f}%", ha="center", fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(groups)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=10)
    fig.subplots_adjust(top=0.68)
    pct(ax)
    save(fig, "seizure.svg")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    ssvep()
    gestures()
    speech()
    seizure()
