"""Gemini, through the REST API. Reads GEMINI_API_KEY from the environment,
.env at the repo root, or app/.env (so one key file serves the app and the
core). Every caller has a non-AI fallback, so the demo never depends on it."""
import json
import os
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv

    ROOT = Path(__file__).resolve().parents[2]
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / "app" / ".env")
except ImportError:
    pass


def available():
    return bool(os.environ.get("GEMINI_API_KEY"))


def ask_json(prompt, timeout=8):
    """Returns parsed JSON, or None if no key, a network error, or bad output."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.6},
            },
            timeout=timeout,
        )
        r.raise_for_status()
        return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
    except Exception as e:  # noqa: BLE001
        print("gemini:", e)
        return None
