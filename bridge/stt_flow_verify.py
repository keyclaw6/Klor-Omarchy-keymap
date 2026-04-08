#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
from pathlib import Path
from types import MethodType


BRIDGE_PATH = Path("/home/kab/.config/klor-bridge/klor-bridge.py")
OUT_DIR = Path.home() / ".cache" / "klor-stt-flow-verify"


def load_bridge_module():
    spec = importlib.util.spec_from_file_location("klor_bridge_live", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load bridge module from {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def run_start_failure(mod, exc: Exception):
    bridge = mod.KlorBridge()
    notifications = []

    async def fake_toggle(_self, _depth=1):
        raise exc

    async def fake_begin(_self, tag: str):
        notifications.append(("begin", tag))

    async def fake_step(_self, tag: str, title: str, body: str = "", **_kwargs):
        notifications.append(("step", tag, title, body))

    async def fake_end(_self, tag: str, delay: float = 0.0):
        notifications.append(("end", tag, delay))

    bridge.stt.toggle_recording = MethodType(fake_toggle, bridge.stt)
    bridge.platform.begin_notification_flow = MethodType(fake_begin, bridge.platform)
    bridge.platform.notify_flow_step = MethodType(fake_step, bridge.platform)
    bridge.platform.end_notification_flow = MethodType(fake_end, bridge.platform)

    await asyncio.wait_for(bridge._handle_stt_toggle(1), timeout=3.0)
    return {
        "titles": [item[2] for item in notifications if item[0] == "step"],
        "bodies": [item[3] for item in notifications if item[0] == "step"],
    }


async def run_stop_failure(mod, exc: Exception):
    bridge = mod.KlorBridge()
    bridge._stt_depth = 1
    notifications = []
    bridge.stt._recording = True

    async def fake_toggle(_self, _depth=1):
        raise exc

    async def fake_begin(_self, tag: str):
        notifications.append(("begin", tag))

    async def fake_step(_self, tag: str, title: str, body: str = "", **_kwargs):
        notifications.append(("step", tag, title, body))

    async def fake_end(_self, tag: str, delay: float = 0.0):
        notifications.append(("end", tag, delay))

    bridge.stt.toggle_recording = MethodType(fake_toggle, bridge.stt)
    bridge.platform.begin_notification_flow = MethodType(fake_begin, bridge.platform)
    bridge.platform.notify_flow_step = MethodType(fake_step, bridge.platform)
    bridge.platform.end_notification_flow = MethodType(fake_end, bridge.platform)

    await asyncio.wait_for(bridge._handle_stt_toggle(1), timeout=3.0)
    return {
        "titles": [item[2] for item in notifications if item[0] == "step"],
        "bodies": [item[3] for item in notifications if item[0] == "step"],
    }


async def main() -> None:
    os.environ["HOME"] = "/home/kab"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mod = load_bridge_module()

    start_auth = await run_start_failure(mod, RuntimeError("ElevenLabs API error 401: unauthorized"))
    stop_no_audio = await run_stop_failure(mod, mod.STTNoAudioError("No audio was captured"))
    stop_no_speech = await run_stop_failure(mod, mod.STTNoSpeechError("No speech detected in recording"))
    stop_rate_limit = await run_stop_failure(mod, RuntimeError("ElevenLabs API error 429: rate limit"))
    stop_post = await run_stop_failure(mod, mod.STTPostProcessError("STT post-process failed: Authentication failed. Check the configured OpenRouter API key."))

    report = {
        "checks": {
            "start_auth": any("Recording failed" in title for title in start_auth["titles"]) and any("authentication failed" in body.lower() for body in start_auth["bodies"]),
            "stop_no_audio": any("STT error" in title for title in stop_no_audio["titles"]) and any("No audio was captured" in body for body in stop_no_audio["bodies"]),
            "stop_no_speech": any("STT error" in title for title in stop_no_speech["titles"]) and any("No speech was detected" in body for body in stop_no_speech["bodies"]),
            "stop_rate_limit": any("STT error" in title for title in stop_rate_limit["titles"]) and any("Rate limited by ElevenLabs" in body for body in stop_rate_limit["bodies"]),
            "stop_postprocess": any("STT error" in title for title in stop_post["titles"]) and any("STT post-process failed" in body for body in stop_post["bodies"]),
        }
    }
    report["all_checks_ok"] = all(report["checks"].values())

    out = OUT_DIR / "report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    asyncio.run(main())
