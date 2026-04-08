#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path


BRIDGE_PATH = Path.home() / ".config" / "klor-bridge" / "klor-bridge.py"
LOG_PATH = Path.home() / ".cache" / "klor-bridge-notification-smoke.log"


def load_bridge_module():
    spec = importlib.util.spec_from_file_location("klor_bridge_live", BRIDGE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


async def run() -> None:
    mod = load_bridge_module()
    platform = mod.Platform(mod.load_config())
    lines: list[str] = []

    async def mark(msg: str) -> None:
        lines.append(msg)

    await mark("TEST 1: STT start -> processing -> complete -> clear")
    await platform.begin_notification_flow("klor-stt")
    await platform.notify_flow_step("klor-stt", "Recording...", "Smoke test STT start", urgent=True, timeout=30000)
    await asyncio.sleep(0.5)
    await platform.notify_flow_step("klor-stt", "Processing transcription...", "Smoke test STT processing", timeout=2000)
    await asyncio.sleep(0.5)
    await platform.notify_flow_step("klor-stt", "Transcription complete", "Smoke test STT complete", timeout=1500)
    await asyncio.sleep(1.5)
    await platform.end_notification_flow("klor-stt")
    await mark("PASS 1")

    await mark("TEST 2: LLM copy -> processing -> ready -> clear")
    await platform.begin_notification_flow("klor-llm")
    await platform.notify_flow_step("klor-llm", "E - Copying selection...", "Smoke test LLM copy")
    await asyncio.sleep(0.5)
    await platform.notify_flow_step("klor-llm", "E - Processing with LLM...", "Smoke test LLM processing", urgent=True, timeout=30000)
    await asyncio.sleep(0.5)
    await platform.notify_flow_step("klor-llm", "E - Result ready", "Smoke test LLM ready", timeout=1500)
    await asyncio.sleep(1.5)
    await platform.end_notification_flow("klor-llm")
    await mark("PASS 2")

    await mark("TEST 3: Prompt picker result -> clear")
    await platform.begin_notification_flow("klor-picker")
    await platform.notify_flow_step("klor-picker", "Snippet: Smoke Test", "Smoke test picker result", timeout=1500)
    await asyncio.sleep(1.5)
    await platform.end_notification_flow("klor-picker")
    await mark("PASS 3")

    await mark("TEST 4: Repeated STT lifecycle twice")
    for idx in range(2):
        await platform.begin_notification_flow("klor-stt")
        await platform.notify_flow_step("klor-stt", "Recording...", f"Repeat {idx + 1}", urgent=True, timeout=30000)
        await asyncio.sleep(0.3)
        await platform.notify_flow_step("klor-stt", "Processing transcription...", f"Repeat {idx + 1}", timeout=1000)
        await asyncio.sleep(0.3)
        await platform.notify_flow_step("klor-stt", "Transcription complete", f"Repeat {idx + 1}", timeout=1000)
        await asyncio.sleep(1.0)
        await platform.end_notification_flow("klor-stt")
    await mark("PASS 4")

    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(LOG_PATH)


if __name__ == "__main__":
    asyncio.run(run())
