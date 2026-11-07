"""Report agent: turns the day's log into a brain activity report for the
doctor (HTML file) and a summary for the app. Only measured facts and the
person's own notes. No diagnosis, no mood."""
import html
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np

from kinesis.agent import llm
from kinesis.agent.monitor import ROOT, DayLog


def _hour(t):
    return time.strftime("%I %p", time.localtime(t)).lstrip("0").lower()


def _clock(t):
    return time.strftime("%I:%M %p", time.localtime(t)).lstrip("0").lower()


def _pct(q):
    return "" if q is None else f"{q:.0%}"


def _val(v):
    return "" if v is None else str(v)


def build(profile, log=None, day=None):
    log = log or DayLog()
    rows = log.read(day)
    day = day or time.strftime("%Y-%m-%d")
    events = Counter(r["input"] for r in rows if r["kind"] == "event")
    actions = Counter(r["action"] for r in rows if r["kind"] == "action")
    minutes = [r for r in rows if r["kind"] == "minute"]
    rests = [r for r in rows if r["kind"] == "rest"]
    seizures = [r for r in rows if r["kind"] == "seizure_like"]
    alerts = [r for r in rows if r["kind"] == "alert"]
    notes = [r for r in rows if r["kind"] == "note"]
    base = next((r for r in reversed(rows) if r["kind"] == "baseline"), None)

    by_hour = {}
    for m in minutes:
        h = time.strftime("%H", time.localtime(m["t"]))
        by_hour.setdefault(h, []).append(m)
    hours = []
    for h in sorted(by_hour):
        ms = by_hour[h]
        q = [m["quality"] for m in ms if m.get("quality") is not None]
        dar = [np.mean([x for x in (m.get("dar_o1"), m.get("dar_o2")) if x is not None]) for m in ms if m.get("dar_o1") or m.get("dar_o2")]
        bsi = [m["bsi"] for m in ms if m.get("bsi") is not None]
        hours.append({"hour": _hour(ms[0]["t"]), "quality": round(float(np.mean(q)), 2) if q else None,
                      "dar": round(float(np.mean(dar)), 2) if dar else None, "bsi": round(float(np.mean(bsi)), 3) if bsi else None})

    peaks = [r["alpha_peak_hz"] for r in rests if r.get("alpha_peak_hz")]
    rep = {
        "type": "report",
        "day": day,
        "name": profile["name"],
        "doctor": profile["contacts"][profile["doctor"]]["name"],
        "facts": [
            [str(sum(events.values())), "choices made"],
            [str(actions.get("call", 0)), "calls"],
            [str(actions.get("message", 0)), "messages sent"],
            [str(actions.get("help", 0)), "help requests"],
            [str(len(seizures)), "seizure-like episodes"],
            [f"{len(minutes) // 60}:{len(minutes) % 60:02d}", "hours monitored"],
        ],
        "brain": {
            "seizure_like": [{"at": _clock(s["start"]), "duration_s": s["duration_s"]} for s in seizures],
            "rest_periods": len(rests),
            "rest_minutes": round(sum(r["duration_s"] for r in rests) / 60, 1),
            "alpha_peak_hz": round(float(np.median(peaks)), 1) if peaks else None,
            "baseline_dar": round((base["dar_o1"] + base["dar_o2"]) / 2, 2) if base else None,
            "baseline_bsi": base["bsi"] if base else None,
            "alerts": [{"kind": a["alert"], "at": _clock(a["t"])} for a in alerts],
        },
        "hours": hours,
        "notes": [[_clock(n["t"]), n["text"]] for n in notes],
    }
    rep["summary"] = _summary(rep)
    rep["file"] = str(_write_html(rep).relative_to(ROOT))
    return rep


def _summary(rep):
    b = rep["brain"]
    n = len(b["seizure_like"])
    peak = f"resting alpha peak {b['alpha_peak_hz']} Hz" if b["alpha_peak_hz"] else "resting alpha peak not measured yet"
    base = (f"{rep['name']} was monitored for {rep['facts'][5][0]} hours today. "
            f"{'No' if n == 0 else n} seizure-like episode{'' if n == 1 else 's'} flagged. "
            f"{b['rest_periods']} eyes-closed rest period{'' if b['rest_periods'] == 1 else 's'}, {peak}.")
    out = llm.ask_json(
        "Rewrite this daily EEG monitoring log as exactly 3 plain sentences for a neurologist. Only restate the "
        "measurements given. Do not diagnose, do not guess mood or causes, do not add facts. Return a JSON object "
        '{"summary": "..."}.\n' + json.dumps({k: rep[k] for k in ("facts", "brain", "notes")})
    )
    return out["summary"] if isinstance(out, dict) and isinstance(out.get("summary"), str) else base


def _write_html(rep):
    out = ROOT / "data" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"report-{rep['day']}.html"
    e = html.escape
    b = rep["brain"]
    rows = "".join(
        f"<tr><td>{e(h['hour'])}</td><td>{_pct(h['quality'])}</td>"
        f"<td>{_val(h['dar'])}</td><td>{_val(h['bsi'])}</td></tr>"
        for h in rep["hours"]
    )
    seiz = "".join(f"<li>{e(s['at'])}, about {int(s['duration_s'])} s</li>" for s in b["seizure_like"]) or "<li>None flagged</li>"
    notes = "".join(f"<li>{e(t)}: {e(n)}</li>" for t, n in rep["notes"]) or "<li>No notes</li>"
    facts = "".join(f"<div><b>{e(n)}</b><span>{e(l)}</span></div>" for n, l in rep["facts"])
    path.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kinesis report {e(rep['day'])}</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;color:#1d2a2e;background:#f7f8f5;max-width:820px;margin:32px auto;padding:0 18px}}
h1{{font-size:28px;margin:0}}h2{{font-size:19px;margin:28px 0 8px}}.facts{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.facts div{{background:#fff;border-radius:12px;padding:12px}}.facts b{{display:block;font-size:26px}}table{{border-collapse:collapse;width:100%}}
td,th{{text-align:left;padding:6px 8px;border-bottom:1px solid #dce1dd}}.fine{{color:#4a5a5f;font-size:14px}}</style></head><body>
<h1>Kinesis daily report, {e(rep['name'])}</h1><p class="fine">{e(rep['day'])}. For {e(rep['doctor'])}. Measurements from a 6-electrode consumer EEG headset; screening information, not a diagnosis.</p>
<p>{e(rep['summary'])}</p><div class="facts">{facts}</div>
<h2>Seizure-like activity</h2><ul>{seiz}</ul>
<h2>Resting rhythm</h2><p>{b['rest_periods']} eyes-closed rest periods, {b['rest_minutes']} minutes total. Resting alpha peak: {b['alpha_peak_hz'] or 'not measured'} Hz.</p>
<h2>By hour</h2><table><tr><th>Hour</th><th>Good signal</th><th>Delta/alpha ratio (O1, O2)</th><th>Left/right asymmetry (O1 vs O2)</th></tr>{rows}</table>
<p class="fine">Baseline delta/alpha ratio {b['baseline_dar']}, baseline asymmetry {b['baseline_bsi']}. Higher than baseline means slower or less even.</p>
<h2>Notes from {e(rep['name'])}</h2><ul>{notes}</ul>
<p class="fine">Never included: raw brain data, guesses about mood or causes.</p></body></html>""")
    return path
