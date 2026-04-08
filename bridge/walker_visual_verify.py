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
OUT_DIR = Path.home() / ".cache" / "walker-visual-verify"


def run(cmd: list[str]) -> str:
  proc = subprocess.run(cmd, env=ENV, capture_output=True, text=True, check=True)
  return proc.stdout


def monitors() -> list[dict]:
  return json.loads(run(["hyprctl", "monitors", "-j"]))


def focus_monitor(name: str) -> None:
  run(["hyprctl", "dispatch", "focusmonitor", name])


def layers() -> dict:
  return json.loads(run(["hyprctl", "layers", "-j"]))


def walker_count_for(monitor: str) -> int:
  data = layers().get(monitor, {}).get("levels", {})
  count = 0
  for level in data.values():
    for surf in level:
      if surf.get("namespace") == "walker":
        count += 1
  return count


def capture(path: Path, monitor: str) -> None:
  subprocess.run(["grim", "-o", monitor, str(path)], env=ENV, check=True)


def launch_walker() -> None:
  cmd = "sh -lc 'printf \"alpha\\nbeta\\n\" | walker --dmenu -p \"Prompt snippets\"'"
  run(["hyprctl", "dispatch", "exec", cmd])


def close_walker() -> None:
  subprocess.run(["walker", "--close"], env=ENV, check=False)
  time.sleep(0.5)


def verify_monitor(mon: dict) -> dict:
  close_walker()
  focus_monitor(mon["name"])
  time.sleep(0.4)

  before = OUT_DIR / f"{mon['name']}-before.png"
  during = OUT_DIR / f"{mon['name']}-during.png"
  after = OUT_DIR / f"{mon['name']}-after.png"

  before_count = walker_count_for(mon["name"])
  capture(before, mon["name"])
  launch_walker()
  time.sleep(1.0)
  during_count = walker_count_for(mon["name"])
  capture(during, mon["name"])
  close_walker()
  after_count = walker_count_for(mon["name"])
  capture(after, mon["name"])

  return {
    "monitor": mon["name"],
    "walker_before": before_count,
    "walker_during": during_count,
    "walker_after": after_count,
    "popup_detected": during_count > before_count,
    "popup_cleared": after_count <= before_count,
  }


def main() -> None:
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  results = [verify_monitor(mon) for mon in monitors()]
  report = OUT_DIR / "report.json"
  report.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
  print(report)


if __name__ == "__main__":
  main()
