#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
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
  "KLOR_PICKER_TEST_QUERY": "review this",
  "KLOR_PICKER_TEST_ACCEPT_MS": "400",
}
OUT_DIR = Path("/home/kab/.cache/klor-prompt-picker-verify")
CACHE_DIR = Path("/home/kab/.cache/klor-bridge")
HELPER_PATH = Path("/home/kab/.config/klor-bridge/prompt_picker_helper.py")
COMMAND_TIMEOUT_SECONDS = 8
OVERALL_TIMEOUT_SECONDS = 60
PICKER_DISCOVERY_SECONDS = 4


def run(cmd: list[str]) -> str:
  proc = subprocess.run(cmd, env=ENV, capture_output=True, text=True, check=True, timeout=COMMAND_TIMEOUT_SECONDS)
  return proc.stdout


def cleanup_picker() -> None:
  subprocess.run(["pkill", "-f", "prompt_picker_helper.py"], env=ENV, check=False, timeout=COMMAND_TIMEOUT_SECONDS)
  subprocess.run(["pkill", "-f", "prompt_picker_window.py"], env=ENV, check=False, timeout=COMMAND_TIMEOUT_SECONDS)


def clients() -> list[dict]:
  try:
    return json.loads(run(["hyprctl", "clients", "-j"]))
  except Exception:
    return []


def monitors() -> list[dict]:
  try:
    return json.loads(run(["hyprctl", "monitors", "-j"]))
  except Exception:
    return []


def logical_monitor_bounds(monitor: dict) -> tuple[int, int, int, int]:
  scale = float(monitor.get("scale", 1.0) or 1.0)
  x = int(monitor.get("x", 0))
  y = int(monitor.get("y", 0))
  width = int(round(int(monitor.get("width", 0)) / scale))
  height = int(round(int(monitor.get("height", 0)) / scale))
  return x, y, width, height


def monitor_probe_point(monitor: dict) -> tuple[int, int]:
  x, y, width, height = logical_monitor_bounds(monitor)
  return x + min(32, max(0, width // 4)), y + min(32, max(0, height // 4))


def cursor_pos() -> tuple[int, int]:
  raw = run(["hyprctl", "cursorpos"]).strip()
  left, right = raw.split(",", 1)
  return int(float(left.strip())), int(float(right.strip()))


def move_cursor(x: int, y: int) -> None:
  subprocess.run(["hyprctl", "dispatch", "movecursor", str(x), str(y)], env=ENV, check=True, timeout=COMMAND_TIMEOUT_SECONDS)


def picker_clients() -> list[dict]:
  matches = []
  for client in clients():
    title = client.get("title") or client.get("initialTitle") or ""
    klass = client.get("class") or client.get("initialClass") or ""
    if title == "Prompt snippets" or klass == "org.klor.PromptPicker":
      matches.append(client)
  return matches


async def wait_for_settled_picker(timeout: float = PICKER_DISCOVERY_SECONDS) -> dict | None:
  loop = asyncio.get_running_loop()
  deadline = loop.time() + timeout
  while loop.time() < deadline:
    matches = picker_clients()
    if matches:
      return matches[0]
    await asyncio.sleep(0.05)
  matches = picker_clients()
  return matches[0] if matches else None


async def wait_for_picker(timeout: float = PICKER_DISCOVERY_SECONDS) -> dict | None:
  loop = asyncio.get_running_loop()
  deadline = loop.time() + timeout
  while loop.time() < deadline:
    matches = picker_clients()
    if matches:
      return matches[0]
    await asyncio.sleep(0.05)
  return None


async def wait_for_result(result_path: Path, timeout: float = PICKER_DISCOVERY_SECONDS) -> dict | None:
  loop = asyncio.get_running_loop()
  deadline = loop.time() + timeout
  while loop.time() < deadline:
    if result_path.exists():
      try:
        return json.loads(result_path.read_text(encoding="utf-8"))
      except Exception:
        return {"error": "invalid result json"}
    await asyncio.sleep(0.05)
  return None


async def run_case(cursor_x: int, cursor_y: int) -> dict:
  input_path = CACHE_DIR / "verify-input.txt"
  result_path = CACHE_DIR / "verify-result.json"
  input_path.write_text("Review this code\nSecond entry\n", encoding="utf-8")
  result_path.unlink(missing_ok=True)

  report = {
    "cursor_x": cursor_x,
    "cursor_y": cursor_y,
    "picker_visible": False,
    "picker_count": 0,
    "result_written": False,
    "result_returncode": None,
    "result_stdout": "",
    "error": "",
  }

  cleanup_picker()
  move_cursor(cursor_x, cursor_y)
  await asyncio.sleep(0.15)

  proc = await asyncio.create_subprocess_exec(
    sys.executable,
    str(HELPER_PATH),
    str(input_path),
    str(result_path),
    env=os.environ.copy(),
    stdout=asyncio.subprocess.DEVNULL,
    stderr=asyncio.subprocess.DEVNULL,
    start_new_session=True,
  )

  try:
    client = await wait_for_settled_picker()
    report["picker_visible"] = client is not None
    report["picker_count"] = len(picker_clients())
    payload = await wait_for_result(result_path)
    report["result_written"] = payload is not None
    if payload is not None:
      report["result_returncode"] = payload.get("returncode")
      report["result_stdout"] = (payload.get("stdout") or "").strip()

    try:
      await asyncio.wait_for(proc.wait(), timeout=2.0)
    except asyncio.TimeoutError:
      report["error"] = "helper process did not exit cleanly"
  finally:
    cleanup_picker()
    input_path.unlink(missing_ok=True)
    result_path.unlink(missing_ok=True)

  return report


async def main() -> None:
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  CACHE_DIR.mkdir(parents=True, exist_ok=True)
  os.environ.update(ENV)

  report = {
    "cases": [],
    "all_single_instance": False,
    "all_completed": False,
    "error": "",
  }
  out = OUT_DIR / "report.json"

  try:
    async with asyncio.timeout(OVERALL_TIMEOUT_SECONDS):
      for monitor in monitors():
        cursor_x, cursor_y = monitor_probe_point(monitor)
        case = await run_case(cursor_x, cursor_y)
        case["monitor_name"] = monitor.get("name")
        report["cases"].append(case)
      report["all_single_instance"] = all(case["picker_count"] == 1 for case in report["cases"])
      report["all_completed"] = all(case["result_written"] and case["result_returncode"] == 0 for case in report["cases"])
  except TimeoutError:
    report["error"] = f"overall verifier timeout after {OVERALL_TIMEOUT_SECONDS}s"
  except subprocess.TimeoutExpired as exc:
    report["error"] = f"command timeout: {' '.join(exc.cmd)}"
  except Exception as exc:
    report["error"] = str(exc)
  finally:
    cleanup_picker()
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except Exception as exc:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "report.json"
    out.write_text(json.dumps({"error": str(exc)}, indent=2) + "\n", encoding="utf-8")
    print(out)
    sys.exit(1)
