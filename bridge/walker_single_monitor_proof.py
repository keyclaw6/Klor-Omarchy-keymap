#!/usr/bin/env python3
from __future__ import annotations

import json
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
OUT_DIR = Path.home() / ".cache" / "walker-single-proof"


def run(cmd: list[str]) -> str:
  proc = subprocess.run(cmd, env=ENV, capture_output=True, text=True, check=True)
  return proc.stdout


def capture(path: Path, monitor: str) -> None:
  subprocess.run(["grim", "-o", monitor, str(path)], env=ENV, check=True)


def compare(a: Path, b: Path) -> float:
  proc = subprocess.run(["compare", "-metric", "RMSE", str(a), str(b), "null:"], env=ENV, capture_output=True, text=True, check=False)
  metric = (proc.stderr or proc.stdout).strip()
  return float(metric.split("(")[-1].split(")")[0])


def launch_proof() -> None:
    cmd = (
        "sh -lc 'printf \"PROMPT PICKER PROOF\\nSECOND ENTRY\\n\" | "
        "walker --dmenu -p \"PROMPT PICKER PROOF\" --theme klor-proof --width 2200 --height 1200 "
        "--config /home/kab/.config/walker/config-proof-window.toml'"
    )
    run(["hyprctl", "dispatch", "exec", cmd])


def close_walker() -> None:
  subprocess.run(["walker", "--close"], env=ENV, check=False)
  time.sleep(0.8)


def main() -> None:
  if len(sys.argv) != 2:
    raise SystemExit("usage: walker_single_monitor_proof.py <MONITOR>")

  monitor = sys.argv[1]
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  before = OUT_DIR / f"{monitor}-before.png"
  during = OUT_DIR / f"{monitor}-during.png"
  after = OUT_DIR / f"{monitor}-after.png"

  close_walker()
  capture(before, monitor)
  launch_proof()
  time.sleep(1.2)
  capture(during, monitor)
  close_walker()
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
