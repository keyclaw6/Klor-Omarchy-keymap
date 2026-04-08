#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path


PICKER_TIMEOUT_SECONDS = 25
HYPR_RESULT_GRACE_SECONDS = 3
HYPR_WINDOW_GRACE_SECONDS = 1.5
ENV_PASSTHROUGH_KEYS = (
    "KLOR_PICKER_TEST_QUERY",
    "KLOR_PICKER_TEST_ACCEPT_MS",
)
def _load_picker_window_module(picker_window: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location("prompt_picker_window_mod", picker_window)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hyprctl_text(*args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["hyprctl", *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return proc.stdout.strip()
    except Exception:
        return None


def cursor_position() -> tuple[int, int] | None:
    raw = _hyprctl_text("cursorpos")
    if not raw or "," not in raw:
        return None
    left, right = raw.split(",", 1)
    try:
        return int(float(left.strip())), int(float(right.strip()))
    except ValueError:
        return None


def monitor_for_point(x: int, y: int) -> dict | None:
    monitors = _hyprctl_json("monitors") or []
    for monitor in monitors:
        mx = int(monitor.get("x", 0))
        my = int(monitor.get("y", 0))
        scale = float(monitor.get("scale", 1.0) or 1.0)
        width = int(round(int(monitor.get("width", 0)) / scale))
        height = int(round(int(monitor.get("height", 0)) / scale))
        if mx <= x < mx + width and my <= y < my + height:
            return monitor
    for monitor in monitors:
        if monitor.get("focused"):
            return monitor
    return None


def _hyprctl_json(*args: str):
    try:
        proc = subprocess.run(
            ["hyprctl", *args, "-j"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return json.loads(proc.stdout)
    except Exception:
        return None


def picker_window_visible() -> bool:
    clients = _hyprctl_json("clients") or []
    for client in clients:
        title = client.get("title") or client.get("initialTitle") or ""
        klass = client.get("class") or client.get("initialClass") or ""
        if title == "Prompt snippets" or klass == "org.klor.PromptPicker":
            return True
    return False


def main() -> int:
    if len(sys.argv) != 3:
        return 2

    input_path = Path(sys.argv[1])
    result_path = Path(sys.argv[2])
    picker_window = Path(__file__).with_name("prompt_picker_window.py")
    picker_mod = _load_picker_window_module(picker_window)
    cursor = cursor_position()
    monitor = monitor_for_point(*cursor) if cursor is not None else None
    command = [sys.executable, str(picker_window), str(input_path), str(result_path)]
    launch_env = os.environ.copy()
    def wait_for_result(deadline: float) -> int | None:
        while time.monotonic() < deadline:
            if result_path.exists():
                try:
                    payload = json.loads(result_path.read_text(encoding="utf-8"))
                    return int(payload.get("returncode", 1))
                except Exception:
                    return 1
            time.sleep(0.05)
        return None

    def wait_for_picker_window(deadline: float) -> bool:
        while time.monotonic() < deadline:
            if picker_window_visible():
                return True
            time.sleep(0.05)
        return False

    try:
        if monitor is not None and picker_mod is not None and shutil.which("hyprctl") and os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            env_values = {
                key: value
                for key in ENV_PASSTHROUGH_KEYS
                if (value := launch_env.get(key))
            }
            env_prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in env_values.items())
            exec_command = " ".join(shlex.quote(part) for part in command)
            if env_prefix:
                exec_command = f"env {env_prefix} {exec_command}"
            monitor_name = str(monitor.get("name") or "current")
            exec_rule = f"[float; noanim; monitor {monitor_name}; size {picker_mod.WINDOW_WIDTH} {picker_mod.WINDOW_HEIGHT}; centerwindow 1] {exec_command}"
            proc = subprocess.run(["hyprctl", "dispatch", "exec", exec_rule], check=False, timeout=5)
            if proc.returncode == 0:
                if wait_for_picker_window(time.monotonic() + HYPR_WINDOW_GRACE_SECONDS):
                    result = wait_for_result(time.monotonic() + PICKER_TIMEOUT_SECONDS)
                    if result is not None:
                        return result
                    return 124

        proc = subprocess.run(command, check=False, timeout=PICKER_TIMEOUT_SECONDS, env=launch_env)
        if result_path.exists():
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            returncode = int(payload.get("returncode", proc.returncode or 1))
            return returncode
        return proc.returncode
    except subprocess.TimeoutExpired:
        if not result_path.exists():
            result_path.write_text('{"returncode": 1, "stdout": "", "stderr": "timeout"}', encoding="utf-8")
        return 124


if __name__ == "__main__":
    raise SystemExit(main())
