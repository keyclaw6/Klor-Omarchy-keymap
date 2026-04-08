#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import subprocess
from pathlib import Path

OUT_DIR = Path.home() / ".cache" / "klor-notify-visual"
BRIDGE_PATH = Path.home() / ".config" / "klor-bridge" / "klor-bridge.py"
ENV = {
  "HOME": str(Path.home()),
  "USER": os.environ.get("USER", "kab"),
  "LOGNAME": os.environ.get("LOGNAME", "kab"),
  "SHELL": "/usr/bin/bash",
  "PATH": "/home/kab/.local/share/omarchy/bin:/usr/local/bin:/usr/bin:/bin",
  "XDG_RUNTIME_DIR": "/run/user/1000",
  "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
  "WAYLAND_DISPLAY": "wayland-1",
  "HYPRLAND_INSTANCE_SIGNATURE": "521ece463c4a9d3d128670688a34756805a4328f_1775507795_941347662",
}


def run(cmd: list[str]) -> str:
  proc = subprocess.run(cmd, env=ENV, check=True, capture_output=True, text=True)
  return proc.stdout


def load_bridge_module():
  spec = importlib.util.spec_from_file_location("klor_bridge_live", BRIDGE_PATH)
  module = importlib.util.module_from_spec(spec)
  assert spec.loader is not None
  spec.loader.exec_module(module)
  return module


def monitors() -> list[dict]:
  return json.loads(run(["hyprctl", "monitors", "-j"]))


def focus_monitor(name: str) -> None:
  run(["hyprctl", "dispatch", "focusmonitor", name])


def notification_region(mon: dict) -> str:
  reserved_top = mon.get("reserved", [0, 26, 0, 0])[1]
  width = min(900, mon["width"] // 3)
  height = min(700, mon["height"] // 2)
  x = mon["width"] - width
  y = reserved_top
  return f"{x},{y} {width}x{height}"


def capture(path: Path, mon: dict) -> None:
  raw_path = path.with_suffix(".full.png")
  geom = notification_region(mon)
  subprocess.run(["grim", "-o", mon["name"], str(raw_path)], env=ENV, check=True)
  subprocess.run(["convert", str(raw_path), "-crop", geom, "+repage", str(path)], env=ENV, check=True)
  raw_path.unlink(missing_ok=True)


def delta(a: Path, b: Path) -> float:
  proc = subprocess.run(
    ["compare", "-metric", "RMSE", str(a), str(b), "null:"],
    env=ENV,
    capture_output=True,
    text=True,
  )
  metric = (proc.stderr or proc.stdout).strip()
  if "(" in metric and ")" in metric:
    normalized = metric.split("(")[-1].split(")")[0]
    return float(normalized)
  return 1.0


async def exercise_flow(platform, tag: str, title1: str, title2: str, title3: str) -> None:
  await platform.begin_notification_flow(tag)
  await platform.notify_flow_step(tag, title1, "start", urgent=True, timeout=30000)
  await asyncio.sleep(0.6)
  await platform.notify_flow_step(tag, title2, "processing", timeout=1500)
  await asyncio.sleep(0.6)
  await platform.notify_flow_step(tag, title3, "done", timeout=1000)
  await asyncio.sleep(1.2)
  await platform.end_notification_flow(tag)
  await asyncio.sleep(1.0)


async def verify_monitor(mon: dict, platform) -> dict:
  focus_monitor(mon["name"])
  await asyncio.sleep(0.4)

  mon_dir = OUT_DIR / mon["name"]
  mon_dir.mkdir(parents=True, exist_ok=True)

  baseline = mon_dir / "baseline.png"
  capture(baseline, mon)

  tests = [
    ("stt", "Recording...", "Processing transcription...", "Transcription complete"),
    ("llm", "E - Copying selection...", "E - Processing with LLM...", "E - Result ready"),
    ("picker", "Snippet: Smoke Test", "Snippet: Smoke Test", "Snippet: Smoke Test"),
  ]

  results = []
  for name, t1, t2, t3 in tests:
    during = mon_dir / f"{name}-during.png"
    after = mon_dir / f"{name}-after.png"

    if name == "picker":
      await platform.begin_notification_flow("klor-picker")
      await platform.notify_flow_step("klor-picker", t1, "picker", timeout=1500)
      await asyncio.sleep(0.4)
      capture(during, mon)
      await asyncio.sleep(1.4)
      await platform.end_notification_flow("klor-picker")
      await asyncio.sleep(1.0)
    else:
      task = asyncio.create_task(exercise_flow(platform, f"klor-{name}", t1, t2, t3))
      await asyncio.sleep(0.5)
      capture(during, mon)
      await task

    capture(after, mon)
    d_during = delta(baseline, during)
    d_after = delta(baseline, after)
    results.append({
      "test": name,
      "during_delta": round(d_during, 4),
      "after_delta": round(d_after, 4),
      "returned_to_baseline": d_after < max(3.0, d_during * 0.35),
    })

  return {
    "monitor": mon["name"],
    "focused": mon.get("focused", False),
    "region": notification_region(mon),
    "results": results,
  }


async def main() -> None:
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  mod = load_bridge_module()
  platform = mod.Platform(mod.load_config())

  report = []
  for mon in monitors():
    report.append(await verify_monitor(mon, platform))

  report_path = OUT_DIR / "report.json"
  report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
  print(report_path)


if __name__ == "__main__":
  asyncio.run(main())
