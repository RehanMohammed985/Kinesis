"""Kinesis core: reads the headset, runs the detectors, and talks to the app
over ws://localhost:8765 (docs/PROTOCOL.md).

python -m kinesis.server --port /dev/cu.usbmodemXXXX
python -m kinesis.server --synthetic          # no headset

Every session is recorded to data/sessions/ for the data team.
"""
import argparse
import asyncio
import json
import time
from pathlib import Path

import websockets

from kinesis.board.knight import Knight
from kinesis.signal.live import FS, Detectors, quality

clients = set()


async def broadcast(msg):
    if not clients:
        return
    data = json.dumps(msg)
    await asyncio.gather(*(c.send(data) for c in list(clients)), return_exceptions=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    ap.add_argument("--synthetic", action="store_true")
    # 0.0.0.0 so the app can run on a different laptop on the same wifi:
    # open http://<app-laptop>:5173/?core=ws://<this-laptop-ip>:8765
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--ws-port", type=int, default=8765)
    args = ap.parse_args()
    if not args.synthetic and not args.port:
        ap.error("--port or --synthetic required")

    board = Knight(port=args.port, synthetic=args.synthetic)
    print("Turning on channels (about 30 s on the real board)...")
    board.start()
    sessions = Path("data/sessions")
    sessions.mkdir(parents=True, exist_ok=True)
    rec = sessions / f"session-{time.strftime('%Y%m%d-%H%M%S')}.csv"
    board.start_recording(str(rec))
    print(f"Recording to {rec}")

    det = Detectors()
    state = {"rest_until": time.time() + 5, "fit": True}
    profile = {"select": "clench", "back": "blink2", "rest": "alpha"}
    print("Sit still with eyes open for 5 s to set the baseline...")

    async def handler(ws):
        clients.add(ws)
        await ws.send(json.dumps({"type": "hello", "board": "knight", "synthetic": args.synthetic, "fs": FS, "profile": profile}))
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                kind = msg.get("type")
                if kind == "calibrate" and msg.get("step") == "rest":
                    state["rest_until"] = time.time() + 5
                    board.mark(1)
                elif kind == "fit":
                    state["fit"] = True
                elif kind in ("action", "confirm", "cancel"):
                    # Coupling and agent teams hook in here (call, message, task, media).
                    print("app:", msg)
        finally:
            clients.discard(ws)

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
        print(f"From another laptop on the same wifi, open the app with ?core=ws://{ip}:{args.ws_port}")
        last_q = 0.0
        while True:
            await asyncio.sleep(0.05)
            now = time.time()
            eeg, _ = board.latest(int(2.0 * FS))
            if eeg.shape[1] < int(1.2 * FS):
                continue
            if state["rest_until"] and now >= state["rest_until"]:
                base = det.calibrate_rest(board.latest(int(4.5 * FS))[0])
                state["rest_until"] = 0
                print("Baseline set:", {k: round(float(v), 2) for k, v in base.items()})
                await broadcast({"type": "calibration", "step": "rest", "progress": 1})
            levels, events = det.update(eeg[:, -int(1.2 * FS):])
            await broadcast({"type": "levels", **levels})
            for ev in events:
                print("event:", ev["input"])
                await broadcast(ev)
            if now - last_q >= 1.0:
                last_q = now
                await broadcast({"type": "quality", "channels": quality(eeg)})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
