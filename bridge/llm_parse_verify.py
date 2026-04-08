#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
from pathlib import Path
from types import MethodType, SimpleNamespace


BRIDGE_PATH = Path("/home/kab/.config/klor-bridge/klor-bridge.py")
OUT_DIR = Path.home() / ".cache" / "klor-llm-verify"


def load_bridge_module():
    spec = importlib.util.spec_from_file_location("klor_bridge_live", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load bridge module from {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def response_with_content(content, *, refusal=None, tool_calls=None):
    message = SimpleNamespace(content=content, refusal=refusal, tool_calls=tool_calls)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def response_without_choices():
    return SimpleNamespace(choices=[])


class FakeCompletions:
    def __init__(self, response):
        self.response = response

    async def create(self, **_kwargs):
        return self.response


class FakeChat:
    def __init__(self, response):
        self.completions = FakeCompletions(response)


class FakeClient:
    def __init__(self, response):
        self.chat = FakeChat(response)


async def verify_extraction(mod):
    client = mod.LLMClient({})
    cases = []

    async def run_case(name, response, expected=None, error_substr=None):
        client._client = FakeClient(response)
        ok = False
        detail = ""
        try:
            result = await asyncio.wait_for(client.process_text("hello", "Text:\n${text}"), timeout=2.0)
            ok = expected is not None and result == expected
            detail = result
        except Exception as exc:
            detail = str(exc)
            ok = error_substr is not None and error_substr in detail
        cases.append({"name": name, "ok": ok, "detail": detail})

    await run_case("plain_string", response_with_content(" hello "), expected="hello")
    await run_case(
        "content_parts_dict",
        response_with_content([
            {"type": "output_text", "text": "Hello "},
            {"type": "output_text", "text": "world"},
        ]),
        expected="Hello world",
    )
    await run_case(
        "content_parts_object",
        response_with_content([
            SimpleNamespace(type="text", text="Alpha "),
            SimpleNamespace(type="output_text", text="Beta"),
        ]),
        expected="Alpha Beta",
    )
    await run_case("refusal", response_with_content(None, refusal="policy refusal"), error_substr="refused request")
    await run_case("tool_calls", response_with_content(None, tool_calls=[{"id": "1"}]), error_substr="tool calls")
    await run_case("no_choices", response_without_choices(), error_substr="no choices")

    return cases


async def verify_llm_action_flow(mod):
    bridge = mod.KlorBridge()
    action = bridge.actions[0x49]
    clipboard = {"value": "__before__"}
    notifications = []

    async def fake_copy_selection(_self):
        return "Selected sample text"

    async def fake_write_clipboard(_self, text: str):
        clipboard["value"] = text

    async def fake_begin(_self, tag: str):
        notifications.append(("begin", tag))

    async def fake_step(_self, tag: str, title: str, body: str = "", **_kwargs):
        notifications.append(("step", tag, title, body))

    async def fake_end(_self, tag: str, delay: float = 0.0):
        notifications.append(("end", tag, delay))

    async def fake_process_text(_self, text: str, template: str, **_kwargs):
        return f"PROCESSED::{text}::{template.splitlines()[0]}"

    bridge.platform.copy_selection = MethodType(fake_copy_selection, bridge.platform)
    bridge.platform._write_clipboard = MethodType(fake_write_clipboard, bridge.platform)
    bridge.platform.begin_notification_flow = MethodType(fake_begin, bridge.platform)
    bridge.platform.notify_flow_step = MethodType(fake_step, bridge.platform)
    bridge.platform.end_notification_flow = MethodType(fake_end, bridge.platform)
    bridge.llm.process_text = MethodType(fake_process_text, bridge.llm)

    await asyncio.wait_for(bridge._handle_llm_text(action), timeout=3.0)

    return {
        "clipboard_prefix": clipboard["value"].splitlines()[0],
        "clipboard_ok": clipboard["value"].startswith("PROCESSED::Selected sample text::"),
        "notification_titles": [item[2] for item in notifications if item[0] == "step"],
    }


async def main() -> None:
    os.environ["HOME"] = "/home/kab"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mod = load_bridge_module()

    extraction_cases = await verify_extraction(mod)
    action_flow = await verify_llm_action_flow(mod)

    report = {
        "extraction_cases": extraction_cases,
        "all_extraction_cases_ok": all(case["ok"] for case in extraction_cases),
        "action_flow": action_flow,
        "action_flow_ok": bool(action_flow["clipboard_ok"]),
    }

    out = OUT_DIR / "report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    asyncio.run(main())
