#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
from pathlib import Path
from types import MethodType


BRIDGE_PATH = Path("/home/kab/.config/klor-bridge/klor-bridge.py")
OUT_DIR = Path.home() / ".cache" / "klor-llm-flow-verify"


def load_bridge_module():
    spec = importlib.util.spec_from_file_location("klor_bridge_live", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load bridge module from {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize_notifications(events):
    return [item[2] for item in events if item[0] == "step"]


async def run_scenario(mod, name: str, copy_results, process_behavior):
    bridge = mod.KlorBridge()
    action = bridge.actions[0x49]
    notifications = []
    clipboard = {"value": "__before__"}
    copy_iter = iter(copy_results)

    async def fake_copy_selection(_self):
        try:
            return next(copy_iter)
        except StopIteration:
            return ""

    async def fake_write_clipboard(_self, text: str):
        clipboard["value"] = text

    async def fake_begin(_self, tag: str):
        notifications.append(("begin", tag))

    async def fake_step(_self, tag: str, title: str, body: str = "", **_kwargs):
        notifications.append(("step", tag, title, body))

    async def fake_end(_self, tag: str, delay: float = 0.0):
        notifications.append(("end", tag, delay))

    async def fake_process_text(_self, text: str, template: str, **_kwargs):
        return await process_behavior(text, template)

    bridge.platform.copy_selection = MethodType(fake_copy_selection, bridge.platform)
    bridge.platform._write_clipboard = MethodType(fake_write_clipboard, bridge.platform)
    bridge.platform.begin_notification_flow = MethodType(fake_begin, bridge.platform)
    bridge.platform.notify_flow_step = MethodType(fake_step, bridge.platform)
    bridge.platform.end_notification_flow = MethodType(fake_end, bridge.platform)
    bridge.llm.process_text = MethodType(fake_process_text, bridge.llm)

    await asyncio.wait_for(bridge._handle_llm_text(action), timeout=4.0)

    return {
        "name": name,
        "clipboard": clipboard["value"],
        "notification_titles": summarize_notifications(notifications),
        "notification_bodies": [item[3] for item in notifications if item[0] == "step"],
    }


async def run_overlap_scenario(mod):
    bridge = mod.KlorBridge()
    action = bridge.actions[0x49]
    notifications = []
    clipboard = {"value": "__before__"}
    released = asyncio.Event()

    async def fake_copy_selection(_self):
        return "Selected text"

    async def fake_write_clipboard(_self, text: str):
        clipboard["value"] = text

    async def fake_begin(_self, tag: str):
        notifications.append(("begin", tag))

    async def fake_step(_self, tag: str, title: str, body: str = "", **_kwargs):
        notifications.append(("step", tag, title, body))

    async def fake_end(_self, tag: str, delay: float = 0.0):
        notifications.append(("end", tag, delay))

    async def slow_process_text(_self, text: str, template: str, **_kwargs):
        if not released.is_set():
            await asyncio.sleep(0.3)
            released.set()
            return f"FIRST::{text}"
        return f"SECOND::{text}"

    bridge.platform.copy_selection = MethodType(fake_copy_selection, bridge.platform)
    bridge.platform._write_clipboard = MethodType(fake_write_clipboard, bridge.platform)
    bridge.platform.begin_notification_flow = MethodType(fake_begin, bridge.platform)
    bridge.platform.notify_flow_step = MethodType(fake_step, bridge.platform)
    bridge.platform.end_notification_flow = MethodType(fake_end, bridge.platform)
    bridge.llm.process_text = MethodType(slow_process_text, bridge.llm)

    first = asyncio.create_task(bridge._handle_llm_text(action))
    await asyncio.sleep(0.05)
    second = asyncio.create_task(bridge._handle_llm_text(action))
    await asyncio.wait_for(asyncio.gather(first, second), timeout=4.0)

    return {
        "name": "overlap_busy",
        "clipboard": clipboard["value"],
        "notification_titles": summarize_notifications(notifications),
        "notification_bodies": [item[3] for item in notifications if item[0] == "step"],
    }


async def main() -> None:
    os.environ["HOME"] = "/home/kab"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mod = load_bridge_module()

    async def process_ok(text: str, _template: str):
        return f"OK::{text}"

    async def process_timeout(_text: str, _template: str):
        raise asyncio.TimeoutError()

    async def process_refusal(_text: str, _template: str):
        raise RuntimeError("LLM refused request: policy refusal")

    async def process_bad_shape(_text: str, _template: str):
        raise RuntimeError("LLM response contained no usable text")

    async def process_auth(_text: str, _template: str):
        raise RuntimeError("401 Unauthorized")

    async def process_rate_limit(_text: str, _template: str):
        raise RuntimeError("429 rate limit exceeded")

    async def process_network(_text: str, _template: str):
        raise RuntimeError("network connect timeout")

    scenarios = []
    scenarios.append(await run_scenario(mod, "copy_same_as_old_clipboard", ["Selected text"], process_ok))
    scenarios.append(await run_scenario(mod, "copy_retry_success", ["", "", "Selected text"], process_ok))
    scenarios.append(await run_scenario(mod, "copy_retry_failure", ["", "", ""], process_ok))
    scenarios.append(await run_scenario(mod, "llm_timeout", ["Selected text"], process_timeout))
    scenarios.append(await run_scenario(mod, "llm_refusal", ["Selected text"], process_refusal))
    scenarios.append(await run_scenario(mod, "llm_bad_shape", ["Selected text"], process_bad_shape))
    scenarios.append(await run_scenario(mod, "llm_auth", ["Selected text"], process_auth))
    scenarios.append(await run_scenario(mod, "llm_rate_limit", ["Selected text"], process_rate_limit))
    scenarios.append(await run_scenario(mod, "llm_network", ["Selected text"], process_network))
    scenarios.append(await run_overlap_scenario(mod))

    report = {
        "scenarios": scenarios,
        "checks": {
            "copy_same_as_old_clipboard": scenarios[0]["clipboard"].startswith("OK::Selected text"),
            "copy_retry_success": scenarios[1]["clipboard"].startswith("OK::Selected text"),
            "copy_retry_failure": scenarios[2]["clipboard"] == "__before__" and any("No text selected" in title for title in scenarios[2]["notification_titles"]),
            "llm_timeout": any("LLM timeout" in title for title in scenarios[3]["notification_titles"]),
            "llm_refusal": any("LLM error" in title for title in scenarios[4]["notification_titles"]) and any("Model refused the request" in body for body in scenarios[4]["notification_bodies"]),
            "llm_bad_shape": any("LLM error" in title for title in scenarios[5]["notification_titles"]) and any("invalid text response" in body for body in scenarios[5]["notification_bodies"]),
            "llm_auth": any("Authentication failed" in body for body in scenarios[6]["notification_bodies"]),
            "llm_rate_limit": any("Rate limited" in body for body in scenarios[7]["notification_bodies"]),
            "llm_network": any("Network error" in body for body in scenarios[8]["notification_bodies"]),
            "overlap_busy": any("Busy" in title for title in scenarios[9]["notification_titles"]),
        },
    }
    report["all_checks_ok"] = all(report["checks"].values())

    out = OUT_DIR / "report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    asyncio.run(main())
