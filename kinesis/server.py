"""Kinesis core: reads the headset, runs the detectors, and talks to the app
over ws://localhost:8765 (docs/PROTOCOL.md).

python -m kinesis.server --port /dev/cu.usbmodemXXXX
python -m kinesis.server --synthetic          # no headset
python -m kinesis.server --port ... --rules    # fixed rules, no learned gestures

Clench and double blink come from the person's learned model
(kinesis/signal/learned.py): trained in the app's calibration and saved to
data/gesture_model.json; until then the team model in kinesis/data/gestures/.

Every session is recorded to data/sessions/ for the data team.
"""
import argparse
import asyncio
import json
import time
from pathlib import Path

import numpy as np
import websockets
from scipy.signal import resample

from kinesis.agent.hub import Hub
from kinesis.board.knight import Knight
from kinesis.montage import OCCIPITAL
from kinesis.signal import learned as gl
from kinesis.signal.ssvep import Look
from kinesis.signal.live import FS, Detectors, quality

WIN = int(1.2 * FS)
PERSONAL_MODEL = Path("data/gesture_model.json")
TEAM_MODEL = Path(__file__).with_name("data") / "gestures" / "model.json"

clients = set()


async def broadcast(msg):
    if not clients:
        return
    data = json.dumps(msg)
    await asyncio.gather(*(c.send(data) for c in list(clients)), return_exceptions=True)


def find_port():
    """The first USB serial port: /dev/cu.usb* on a Mac, ttyACM/ttyUSB on Linux, COM on Windows."""
    import glob
    found = sorted(glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*") + glob.glob("/dev/cu.usb*")
                   + glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
    if not found:
        try:
            from serial.tools import list_ports
            found = [p.device for p in list_ports.comports() if "Bluetooth" not in p.device]
        except ImportError:
            pass
    return found[0] if found else None


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", help="serial port; leave out to find the headset automatically")
    ap.add_argument("--synthetic", action="store_true")
    # 0.0.0.0 so the app can run on a different laptop on the same wifi:
    # open http://<app-laptop>:5173/?core=ws://<this-laptop-ip>:8765
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--ws-port", type=int, default=8765)
    ap.add_argument("--model", help="gesture model json (default: data/gesture_model.json, then the team model)")
    ap.add_argument("--rules", action="store_true", help="fixed rules only, no learned gestures")
    args = ap.parse_args()
    if not args.synthetic and not args.port:
        args.port = find_port()
        if not args.port:
            ap.error("no headset found on USB. Check the cable (some only charge), or pass --port")
        print(f"Headset port: {args.port}")

    board = Knight(port=args.port, synthetic=args.synthetic)
    print("Turning on channels (about 30 s on the real board)...")
    board.start()
    sessions = Path("data/sessions")
    sessions.mkdir(parents=True, exist_ok=True)
    rec = sessions / f"session-{time.strftime('%Y%m%d-%H%M%S')}.csv"
    board.start_recording(str(rec))
    print(f"Recording to {rec}")

    det = Detectors()
    gest = {"det": None, "source": "rules"}
    if not args.rules:
        for path in (args.model, PERSONAL_MODEL, TEAM_MODEL):
            if path and Path(path).exists():
                gest["det"] = gl.LearnedDetectors(gl.GestureModel.load(path), det)
                gest["source"] = str(path)
                print(f"Gestures: learned model {path} (channels {gest['det'].model.chans})")
                break
    cal = {"step": None, "c": None}
    look = {"on": False, "dec": Look(), "last": 0.0, "level": None}
    loop = asyncio.get_running_loop()

    def emit(msg):
        # Agents run in worker threads; hand their messages back to the loop.
        loop.call_soon_threadsafe(lambda: asyncio.ensure_future(broadcast(msg)))

    hub = Hub(emit)
    state = {"rest_until": time.time() + 5, "fit": True, "inject": None}

    # Demo only: mix a real recorded seizure (Bonn dataset, recording S001,
    # Andrzejak et al. 2001) into the live signal so the real detector can be
    # shown working. The app labels this as a replay.
    demo = np.loadtxt(Path(__file__).with_name("agent") / "demo_seizure.txt")
    demo = resample(demo, int(round(len(demo) * FS / 173.61)))
    demo = demo / np.std(demo)

    def read(n):
        eeg, ts = board.latest(n)
        inj = state["inject"]
        if inj and eeg.shape[1]:
            idx = ((ts - inj["start"]) * FS).astype(int)
            ok = (idx >= 0) & (idx < len(demo))
            if ok.any():
                eeg = eeg.copy()
                for ch in OCCIPITAL:  # back of the head only, so the switch detectors never fire
                    eeg[ch - 1, ok] += demo[idx[ok]] * inj["scale"]
            elif ts[-1] - inj["start"] > len(demo) / FS:
                state["inject"] = None
        return eeg, ts
    profile = {"select": "clench", "back": "blink2", "rest": "alpha"}
    print("Sit still with eyes open for 5 s to set the baseline...")

    async def handler(ws):
        clients.add(ws)
        await ws.send(json.dumps({"type": "hello", "board": "knight", "synthetic": args.synthetic, "fs": FS, "profile": profile, "gestures": gest["source"]}))
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                kind = msg.get("type")
                if kind == "calibrate":
                    step = msg.get("step")
                    if step == "rest":
                        state["rest_until"] = time.time() + 5
                        board.mark(1)
                        cal["step"], cal["c"] = "rest", None
                    elif step in ("clench", "blink2"):
                        board.mark(2 if step == "clench" else 3)
                        cal["step"] = step
                    else:  # the switch steps are over: learn this person's gestures
                        cal["step"] = None
                        await train_gestures()
                elif kind == "look":  # the app's Look screen is open
                    look["on"] = bool(msg.get("on"))
                    look["dec"] = Look()
                    look["level"] = None
                elif kind == "fit":
                    state["fit"] = True
                elif kind == "demo_seizure":
                    base = hub.monitor.base or {}
                    rms = float(np.median([base[c]["rms"] for c in OCCIPITAL if c in base] or [10.0]))
                    state["inject"] = {"start": time.time() + 1, "scale": 5 * rms}
                    print("demo: replaying a recorded seizure into the live signal for 23 s")
                elif kind in ("action", "confirm", "cancel", "heard", "report_request"):
                    print("app:", {k: v for k, v in msg.items() if k != "type"} or kind)
                    loop.run_in_executor(None, hub.handle, msg)
        finally:
            clients.discard(ws)

    async def train_gestures():
        c = cal["c"]
        if c is None or args.rules:
            return
        model, info = c.train()
        if model is None:
            print("Gestures: not enough clean attempts to learn from", info)
            await broadcast({"type": "calibration", "step": "model", "ok": False, **info})
            return
        model.save(PERSONAL_MODEL)
        gest["det"] = gl.LearnedDetectors(model, det)
        gest["source"] = str(PERSONAL_MODEL)
        print("Gestures: learned this person's clench and double blink", info)
        await broadcast({"type": "calibration", "step": "model", "ok": True, **info})

    async with websockets.serve(handler, args.host, args.ws_port):
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except OSError:
            ip = "localhost"
        print(f"Core running. On this laptop: ws://localhost:{args.ws_port}")
        print(f"iPad or phone on the same wifi: run the app on this laptop (cd app, npm run dev), then open http://{ip}:5173")
        print(f"App on another laptop: set KINESIS_CORE=ws://{ip}:{args.ws_port} in app/.env")
        last_q = 0.0
        last_m = 0.0
        # Is the headset actually sending? The app shows this instead of
        # "Headset on" whenever it is connected to the core.
        feed = {"newest": 0.0, "seen": time.time(), "told": 0.0, "warned": 0.0, "start": time.time()}
        while True:
            await asyncio.sleep(0.05)
            now = time.time()
            eeg, ts = board.latest(int(2.0 * FS))  # detectors see the raw signal only
            newest = float(ts[-1]) if ts.size else 0.0
            if newest > feed["newest"]:
                feed["newest"], feed["seen"] = newest, now
            streaming = now - feed["seen"] < 2.0 and ts.size > 0
            if now - feed["told"] >= 1.0:
                feed["told"] = now
                rate = int((ts > newest - 1.0).sum()) if streaming else 0
                await broadcast({"type": "status", "streaming": streaming, "rate": rate})
                if not streaming and now - feed["start"] > 8 and now - feed["warned"] > 5:
                    feed["warned"] = now
                    print("No data from the headset. Check the USB cable and the port, close the EXG Visualizer, "
                          "then run: python scripts/check_headset.py")
            if eeg.shape[1] < int(1.2 * FS) or not streaming:
                continue
            if state["rest_until"] and now >= state["rest_until"]:
                rest = read(int(4.5 * FS))[0]
                base = det.calibrate_rest(rest)
                if gest["det"]:
                    gest["det"].calibrate_rest(rest)
                if cal["step"] == "rest":  # calibration: start collecting this person's gestures
                    c = gl.Calibrator(gl.active_channels(rest))
                    for i in range(WIN, rest.shape[1] + 1, 6):
                        c.add_rest(gl.raw_features(rest[:, i - WIN:i], c.model.chans))
                    cal["c"] = c
                hub.monitor.set_baseline(rest)
                state["rest_until"] = 0
                print("Baseline set:", {k: round(float(v), 2) for k, v in base.items()})
                await broadcast({"type": "calibration", "step": "rest", "progress": 1})
            levels, events = (gest["det"] or det).update(eeg[:, -WIN:], now)
            if cal["step"] in ("clench", "blink2") and cal["c"] is not None:
                # calibration: count attempts for the app, keep frames to learn from
                events = []
                f = gl.raw_features(eeg[:, -WIN:], cal["c"].model.chans)
                if cal["c"].add(f, cal["step"]):
                    events = [{"type": "event", "input": cal["step"]}]
            if args.synthetic:
                events = []  # synthetic data is meaningless for switches
            look_events = []
            if look["on"] and now - look["last"] >= 0.25 and eeg.shape[1] >= int(2.0 * FS):
                look["last"] = now
                look["level"], look_events = look["dec"].update(eeg, now)
                if args.synthetic:
                    look_events = []
            if look["on"] and look["level"]:
                levels["look"] = look["level"]
            events = events + look_events
            await broadcast({"type": "levels", **levels})
            for ev in events:
                print("event:", ev["input"])
                hub.monitor.note_event(ev["input"])
                await broadcast(ev)
            if now - last_q >= 1.0:
                last_q = now
                q = quality(eeg)
                hub.monitor.note_quality(q)
                await broadcast({"type": "quality", "channels": q})
            if now - last_m >= 2.0:
                last_m = now
                window = read(int(4.0 * FS))[0]
                if window.shape[1] >= int(4.0 * FS):
                    loop.run_in_executor(None, hub.monitor.feed, window, levels)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
