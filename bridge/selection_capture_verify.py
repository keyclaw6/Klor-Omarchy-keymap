#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
from pathlib import Path
from types import MethodType


BRIDGE_PATH = Path("/home/kab/Klor-Omarchy-keymap/bridge/klor-bridge.py")
OUT_DIR = Path.home() / ".cache" / "klor-selection-verify"


def load_bridge_module():
    spec = importlib.util.spec_from_file_location("klor_bridge_repo", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load bridge module from {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def run_case(mod, name: str, old_clip: str, polled_values: list[str], watch_value: str | None = None):
    platform = mod.Platform({"platform": {"copy_delay_ms": 0, "copy_poll_interval_ms": 10, "copy_timeout_ms": 120}})
    writes = []
    polls = iter(polled_values)
    read_count = {"clipboard": 0}

    async def fake_read(_self, primary: bool = False):
        if primary:
            return old_clip
        read_count["clipboard"] += 1
        if read_count["clipboard"] == 1:
            return old_clip
        try:
            return next(polls)
        except StopIteration:
            return polled_values[-1] if polled_values else old_clip

    async def fake_write(_self, text: str):
        writes.append(text)

    class Proc:
        def __init__(self, watched: str | None = None):
            self.returncode = 0
            self._watched = watched

        async def wait(self):
            return 0

        async def communicate(self):
            if self._watched is None:
                return b"", b""
            return self._watched.encode("utf-8"), b""

        def kill(self):
            self.returncode = -9

    async def fake_create_subprocess_exec(*args, **_kwargs):
        if len(args) >= 2 and args[0] == platform.clip_read and args[1] == "--watch":
            return Proc(watch_value)
        return Proc()

    platform._read_clipboard = MethodType(fake_read, platform)
    platform._write_clipboard = MethodType(fake_write, platform)

    original_exec = asyncio.create_subprocess_exec
    asyncio.create_subprocess_exec = fake_create_subprocess_exec
    try:
        result = await asyncio.wait_for(platform.copy_selection(), timeout=2.0)
    finally:
        asyncio.create_subprocess_exec = original_exec

    sentinel = writes[0] if writes else ""
    return {
        "name": name,
        "result": result,
        "writes": writes,
        "sentinel_written": sentinel.startswith("__klor_copy_probe__:"),
    }


async def main() -> None:
    os.environ["HOME"] = "/home/kab"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mod = load_bridge_module()

    cases = []
    cases.append(await run_case(mod, "same_as_old_clipboard", "Selected text", ["Selected text"], "Selected text"))
    cases.append(await run_case(mod, "delayed_update", "old", ["__klor_copy_probe__:placeholder", "__klor_copy_probe__:placeholder", "Delayed selection"], "Delayed selection"))
    cases.append(await run_case(mod, "no_selection_restore", "old", ["__klor_copy_probe__:placeholder", "__klor_copy_probe__:placeholder", "__klor_copy_probe__:placeholder"]))

    report = {
        "cases": cases,
        "checks": {
            "same_as_old_clipboard": cases[0]["result"] == "Selected text" and cases[0]["sentinel_written"],
            "delayed_update": cases[1]["result"] == "Delayed selection" and cases[1]["sentinel_written"],
            "no_selection_restore": cases[2]["result"] == "" and len(cases[2]["writes"]) >= 2 and cases[2]["writes"][-1] == "old",
        },
    }
    report["all_checks_ok"] = all(report["checks"].values())

    out = OUT_DIR / "report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    asyncio.run(main())
