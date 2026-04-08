#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import subprocess
import sys
import types
from pathlib import Path


ENV = {
  "HOME": "/home/kab",
  "USER": "kab",
  "LOGNAME": "kab",
  "SHELL": "/usr/bin/bash",
  "PATH": "/home/kab/.local/share/omarchy/bin:/usr/local/bin:/usr/bin:/bin",
  "XDG_RUNTIME_DIR": "/run/user/1000",
  "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
  "WAYLAND_DISPLAY": "wayland-1",
  "HYPRLAND_INSTANCE_SIGNATURE": "521ece463c4a9d3d128670688a34756805a4328f_1775507795_941347662",
}
BRIDGE_PATH = Path("/home/kab/.config/klor-bridge/klor-bridge.py")
OUT_DIR = Path("/home/kab/.cache/prompt-picker-e2e")
COMMAND_TIMEOUT_SECONDS = 8
RESULT_TIMEOUT_SECONDS = 12
PICKER_DISCOVERY_SECONDS = 4
OVERALL_TIMEOUT_SECONDS = 18


def run(cmd: list[str]) -> str:
  proc = subprocess.run(cmd, env=ENV, capture_output=True, text=True, check=True, timeout=COMMAND_TIMEOUT_SECONDS)
  return proc.stdout


def load_bridge_module():
  spec = importlib.util.spec_from_file_location("klor_bridge_live", BRIDGE_PATH)
  if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load bridge module from {BRIDGE_PATH}")
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


def set_clipboard(text: str) -> None:
  subprocess.run(["wl-copy"], env=ENV, input=text, text=True, check=True, timeout=COMMAND_TIMEOUT_SECONDS)


def get_clipboard() -> str:
  return run(["wl-paste", "--no-newline"])


def clients() -> list[dict]:
  try:
    return json.loads(run(["hyprctl", "clients", "-j"]))
  except Exception:
    return []


def cursor_pos() -> tuple[int, int]:
  raw = run(["hyprctl", "cursorpos"]).strip()
  left, right = raw.split(",", 1)
  return int(float(left.strip())), int(float(right.strip()))


def picker_client() -> dict | None:
  for client in clients():
    title = client.get("title") or client.get("initialTitle") or ""
    klass = client.get("class") or client.get("initialClass") or ""
    if title == "Prompt snippets" or klass == "org.klor.PromptPicker":
      return client
  return None


def move_cursor(x: int, y: int) -> None:
  subprocess.run(["hyprctl", "dispatch", "movecursor", str(x), str(y)], env=ENV, check=True, timeout=COMMAND_TIMEOUT_SECONDS)


def cleanup_picker() -> None:
  subprocess.run(["pkill", "-f", "prompt_picker_helper.py"], env=ENV, check=False, timeout=COMMAND_TIMEOUT_SECONDS)
  subprocess.run(["pkill", "-f", "prompt_picker_window.py"], env=ENV, check=False, timeout=COMMAND_TIMEOUT_SECONDS)
  for path in Path("/home/kab/.cache/klor-bridge").glob("picker-result-*.json"):
    path.unlink(missing_ok=True)


async def wait_for_picker(timeout: float = PICKER_DISCOVERY_SECONDS) -> dict | None:
  loop = asyncio.get_running_loop()
  deadline = loop.time() + timeout
  while loop.time() < deadline:
    client = picker_client()
    if client is not None:
      return client
    await asyncio.sleep(0.05)
  return None


async def wait_for_result_file(path: Path, timeout: float = PICKER_DISCOVERY_SECONDS) -> dict | None:
  loop = asyncio.get_running_loop()
  deadline = loop.time() + timeout
  while loop.time() < deadline:
    if path.exists():
      try:
        return json.loads(path.read_text(encoding="utf-8"))
      except Exception as exc:
        return {"error": f"invalid result json: {exc}"}
    await asyncio.sleep(0.05)
  return None


async def main() -> None:
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  os.environ.update(ENV)
  cleanup_picker()

  report = {
    "picker_visible": False,
    "task_completed": False,
    "matched": False,
    "error": "",
    "clipboard_prefix": "",
    "expected_prefix": "",
    "placement": None,
  }
  out = OUT_DIR / "report.json"

  bridge = None
  task = None
  original_launch = None
  original_notify_step = None
  original_begin = None
  original_end = None
  old_query = os.environ.get("KLOR_PICKER_TEST_QUERY")
  old_accept = os.environ.get("KLOR_PICKER_TEST_ACCEPT_MS")

  try:
    async with asyncio.timeout(OVERALL_TIMEOUT_SECONDS):
      mod = load_bridge_module()
      bridge = mod.KlorBridge()
      action = bridge.actions[0x50]
      expected_name = "Review this code"
      expected_text = next(snippet["text"].strip() for snippet in bridge.snippets if snippet["name"] == expected_name)
      report["expected_prefix"] = expected_text.splitlines()[0]

      original_launch = bridge.platform.launch_hyprland_exec
      original_notify_step = bridge.platform.notify_flow_step
      original_begin = bridge.platform.begin_notification_flow
      original_end = bridge.platform.end_notification_flow

      async def no_delay(_self, *args, **kwargs) -> None:
        return None

      bridge.platform.notify_flow_step = types.MethodType(no_delay, bridge.platform)
      bridge.platform.begin_notification_flow = types.MethodType(no_delay, bridge.platform)
      bridge.platform.end_notification_flow = types.MethodType(no_delay, bridge.platform)

      original_cursor = cursor_pos()
      moved_cursor = (original_cursor[0] + 120, original_cursor[1] + 40)
      move_cursor(*moved_cursor)
      await asyncio.sleep(0.15)

      set_clipboard("__before__")
      os.environ["KLOR_PICKER_TEST_QUERY"] = "review this"
      os.environ["KLOR_PICKER_TEST_ACCEPT_MS"] = "700"

      task = asyncio.create_task(bridge._handle_prompt_picker(action))
      client = await wait_for_picker()
      report["picker_visible"] = client is not None
      if client is not None:
        at = client.get("at") or [0, 0]
        report["placement"] = {
          "window_x": at[0],
          "window_y": at[1],
          "cursor_x": moved_cursor[0],
          "cursor_y": moved_cursor[1],
          "monitor": client.get("monitor"),
        }

      helper_result_path = next(
        (path for path in Path("/home/kab/.cache/klor-bridge").glob("picker-result-*.json")),
        None,
      )
      if helper_result_path is not None:
        helper_result = await wait_for_result_file(helper_result_path, timeout=RESULT_TIMEOUT_SECONDS)
        report["task_completed"] = helper_result is not None
        if helper_result is None:
          report["error"] = f"picker result not written after {RESULT_TIMEOUT_SECONDS}s"
      else:
        await asyncio.sleep(1.0)

      clipboard = get_clipboard().strip()
      report["clipboard_prefix"] = clipboard.splitlines()[0] if clipboard else ""
      report["matched"] = clipboard == expected_text
      if not report["matched"] and not report["error"]:
        report["error"] = "clipboard did not receive selected snippet"
  except TimeoutError:
    report["error"] = f"overall verifier timeout after {OVERALL_TIMEOUT_SECONDS}s"
  except subprocess.TimeoutExpired as exc:
    report["error"] = f"command timeout: {' '.join(exc.cmd)}"
  except Exception as exc:
    report["error"] = str(exc)
  finally:
    if task is not None and not task.done():
      task.cancel()
    if bridge is not None and original_launch is not None:
      bridge.platform.launch_hyprland_exec = original_launch
      bridge.platform.notify_flow_step = original_notify_step
      bridge.platform.begin_notification_flow = original_begin
      bridge.platform.end_notification_flow = original_end
    if old_query is None:
      os.environ.pop("KLOR_PICKER_TEST_QUERY", None)
    else:
      os.environ["KLOR_PICKER_TEST_QUERY"] = old_query
    if old_accept is None:
      os.environ.pop("KLOR_PICKER_TEST_ACCEPT_MS", None)
    else:
      os.environ["KLOR_PICKER_TEST_ACCEPT_MS"] = old_accept
    cleanup_picker()
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)
    sys.stdout.flush()


if __name__ == "__main__":
  try:
    asyncio.run(main())
    os._exit(0)
  except Exception as exc:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "report.json"
    out.write_text(json.dumps({"error": str(exc)}, indent=2) + "\n", encoding="utf-8")
    print(out)
    sys.stdout.flush()
    os._exit(1)
