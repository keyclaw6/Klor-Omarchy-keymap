#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
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
OUT_DIR = Path.home() / ".cache" / "walker-proof-verify"


def run(cmd: list[str]) -> str:
  proc = subprocess.run(cmd, env=ENV, capture_output=True, text=True, check=True)
  return proc.stdout


def monitors() -> list[dict]:
  return json.loads(run(["hyprctl", "monitors", "-j"]))


def focus_monitor(name: str) -> None:
  run(["hyprctl", "dispatch", "focusmonitor", name])


def capture(path: Path, monitor: str) -> None:
  subprocess.run(["grim", "-o", monitor, str(path)], env=ENV, check=True)


def launch_proof() -> None:
  cmd = (
    "sh -lc 'printf \"PROMPT PICKER PROOF\\nSECOND ENTRY\\n\" | "
    "walker --dmenu -p \"PROMPT PICKER PROOF\" -t klor-proof --width 2200 --height 1200'"
  )
  run(["hyprctl", "dispatch", "exec", cmd])


def close_walker() -> None:
  subprocess.run(["walker", "--close"], env=ENV, check=False)
  time.sleep(0.8)


def compare(a: Path, b: Path) -> float:
  proc = subprocess.run(
    ["compare", "-metric", "RMSE", str(a), str(b), "null:"],
    env=ENV,
    capture_output=True,
    text=True,
    check=False,
  )
  metric = (proc.stderr or proc.stdout).strip()
  return float(metric.split("(")[-1].split(")")[0])


def verify_monitor(mon: dict) -> dict:
  close_walker()
  focus_monitor(mon["name"])
  time.sleep(0.5)

  before = OUT_DIR / f"{mon['name']}-before.png"
  during = OUT_DIR / f"{mon['name']}-during.png"
  after = OUT_DIR / f"{mon['name']}-after.png"

  capture(before, mon["name"])
  launch_proof()
  time.sleep(1.2)
  capture(during, mon["name"])
  close_walker()
  capture(after, mon["name"])

  diff_during = compare(before, during)
  diff_after = compare(before, after)

  return {
    "monitor": mon["name"],
    "during_delta": diff_during,
    "after_delta": diff_after,
    "popup_visible": diff_during > 0.02,
    "popup_cleared": diff_after < 0.01,
  }


def main() -> None:
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  report = [verify_monitor(mon) for mon in monitors()]
  out = OUT_DIR / "report.json"
  out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
  print(out)


if __name__ == "__main__":
  main()
