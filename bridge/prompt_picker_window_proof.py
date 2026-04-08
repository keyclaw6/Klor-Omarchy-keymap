#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
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
OUT_DIR = Path.home() / ".cache" / "prompt-picker-window-proof"
DWELL_SECONDS = float(os.environ.get("PROMPT_PICKER_PROOF_DWELL", "3.5"))
COMMAND_TIMEOUT_SECONDS = 8


def run(cmd: list[str]) -> str:
  proc = subprocess.run(cmd, env=ENV, capture_output=True, text=True, check=True, timeout=COMMAND_TIMEOUT_SECONDS)
  return proc.stdout


def capture(path: Path, monitor: str) -> None:
  subprocess.run(["grim", "-o", monitor, str(path)], env=ENV, check=True, timeout=COMMAND_TIMEOUT_SECONDS)


def compare(a: Path, b: Path) -> float:
  proc = subprocess.run(["compare", "-metric", "RMSE", str(a), str(b), "null:"], env=ENV, capture_output=True, text=True, check=False, timeout=COMMAND_TIMEOUT_SECONDS)
  metric = (proc.stderr or proc.stdout).strip()
  return float(metric.split("(")[-1].split(")")[0])


def focus_monitor(name: str) -> None:
  run(["hyprctl", "dispatch", "focusmonitor", name])


def move_cursor(x: int, y: int) -> None:
  run(["hyprctl", "dispatch", "movecursor", str(x), str(y)])


def close_picker() -> None:
  subprocess.run(["pkill", "-f", "prompt_picker_window.py"], env=ENV, check=False, timeout=COMMAND_TIMEOUT_SECONDS)
  time.sleep(0.6)


def launch_picker() -> None:
  cache_dir = Path.home() / ".cache" / "klor-bridge"
  cache_dir.mkdir(parents=True, exist_ok=True)
  input_path = cache_dir / "proof-input.txt"
  result_path = cache_dir / "proof-result.json"
  input_path.write_text("PROMPT PICKER PROOF\nSECOND ENTRY\n", encoding="utf-8")
  cmd = f'/usr/bin/python3 /home/kab/.config/klor-bridge/prompt_picker_window.py "{input_path}" "{result_path}"'
  run(["hyprctl", "dispatch", "exec", cmd])


def main() -> None:
  if len(sys.argv) != 4:
    raise SystemExit("usage: prompt_picker_window_proof.py <MONITOR> <X> <Y>")

  monitor = sys.argv[1]
  x = int(sys.argv[2])
  y = int(sys.argv[3])
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  before = OUT_DIR / f"{monitor}-before.png"
  during = OUT_DIR / f"{monitor}-during.png"
  after = OUT_DIR / f"{monitor}-after.png"

  close_picker()
  focus_monitor(monitor)
  move_cursor(x, y)
  time.sleep(0.6)

  capture(before, monitor)
  launch_picker()
  time.sleep(DWELL_SECONDS)
  capture(during, monitor)
  close_picker()
  capture(after, monitor)

  report = {
    "monitor": monitor,
    "during_delta": compare(before, during),
    "after_delta": compare(before, after),
  }
  out = OUT_DIR / f"{monitor}-report.json"
  out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
  print(out)


if __name__ == "__main__":
  main()
