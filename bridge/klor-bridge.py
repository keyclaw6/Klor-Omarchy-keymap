#!/usr/bin/env python3
"""
KLOR Bridge — AI writing assistant daemon for the KLOR split keyboard.

Listens for Raw HID commands from the KLOR keyboard through the plain QMK
raw_hid_receive() hook, dispatches non-dictation actions to OpenRouter/helpers,
and writes results to the clipboard via wtype/wl-clipboard. OpenWhispr owns
dictation and screen-context voice actions outside this daemon.

Usage:
    python klor-bridge.py              # run in foreground
    python klor-bridge.py --verbose    # debug logging

Active dependencies (Arch):
    pacman -S python-hid python-openai python-yaml python-keyring
Active dependencies (pip):
    pip install hidapi openai pyyaml keyring

System deps:
    wtype wl-clipboard
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import os
import shlex
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path
import yaml

# ─── Constants ────────────────────────────────────────────────────────────────

CONFIG_DIR = Path.home() / ".config" / "klor-bridge"
PACKET_SIZE = 32  # QMK Raw HID packet size

# Bridge protocol command IDs (must match firmware defines)
CMD_BRIDGE_ACTION = 0x20
CMD_BRIDGE_STATUS = 0x21
CMD_BRIDGE_HEARTBEAT = 0x22
CMD_BRIDGE_CONFIG = 0x23

# Action IDs (must match firmware defines)
ACTION_BRIGHTNESS_UP = 0x11
ACTION_BRIGHTNESS_DOWN = 0x12

log = logging.getLogger("klor-bridge")


# ─── Config loading ───────────────────────────────────────────────────────────


def load_yaml(path: Path) -> dict:
    """Load a YAML file, returning empty dict if missing."""
    if not path.exists():
        log.warning("Config file not found: %s", path)
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_config() -> dict:
    return load_yaml(CONFIG_DIR / "config.yml")


def load_actions() -> dict[int, dict]:
    """Load actions.yml and index by action_id (int)."""
    raw = load_yaml(CONFIG_DIR / "actions.yml")
    actions = {}
    for name, entry in raw.get("actions", {}).items():
        aid = entry.get("action_id")
        if isinstance(aid, str):
            aid = int(aid, 0)
        entry["name"] = name
        actions[aid] = entry
    return actions


def load_prompts() -> dict[str, str]:
    return load_yaml(CONFIG_DIR / "prompts.yml") or {}


def load_snippets() -> list[dict]:
    """Load prompt snippets for the prompt picker.

    Returns a list of dicts: [{name, description, text}, ...]
    """
    raw = load_yaml(CONFIG_DIR / "snippets.yml")
    snippets = raw.get("snippets", [])
    # Validate entries
    valid = []
    for s in snippets:
        if isinstance(s, dict) and s.get("name") and s.get("text"):
            valid.append(s)
    return valid


def file_mtime_ns(path: Path) -> int | None:
    try:
        return path.stat().st_mtime_ns
    except FileNotFoundError:
        return None


# ─── Secrets ──────────────────────────────────────────────────────────────────


def get_secret(key_name: str, env_var: str) -> str | None:
    """Get secret from OS keyring, falling back to environment variable."""
    try:
        import keyring

        val = keyring.get_password("klor-bridge", key_name)
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(env_var)


# ─── Platform (clipboard + key simulation) ────────────────────────────────────


class Platform:
    """Wayland clipboard and key simulation via wl-clipboard and wtype."""

    def __init__(self, config: dict):
        plat = config.get("platform", {})
        self.clip_read = plat.get("clipboard_read", "wl-paste")
        self.clip_write = plat.get("clipboard_write", "wl-copy")
        self.key_sim = plat.get("key_simulator", "wtype")
        self.copy_delay = plat.get("copy_delay_ms", 150) / 1000.0
        self.copy_poll_interval = plat.get("copy_poll_interval_ms", 60) / 1000.0
        self.copy_timeout = plat.get("copy_timeout_ms", 1800) / 1000.0
        # Maps tag -> notification ID for tag-based replacement
        self._notif_ids: dict = {}
        # Tracks tags that represent active multi-step flows
        self._active_tags: set[str] = set()

    async def _dismiss_mako_notification(self, notif_id: int) -> None:
        """Best-effort dismissal of a specific mako notification."""
        if notif_id <= 0 or not shutil.which("makoctl"):
            return

        proc = await asyncio.create_subprocess_exec(
            "makoctl", "dismiss", "-n", str(notif_id),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

    async def _dismiss_recent_group(self) -> None:
        """Best-effort dismissal of the current mako notification group."""
        if not shutil.which("makoctl"):
            return

        proc = await asyncio.create_subprocess_exec(
            "makoctl", "dismiss", "--group",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

    async def clear_notification(self, tag: str) -> None:
        """Best-effort clear of a previously posted tagged notification."""
        self._active_tags.discard(tag)
        notif_id = self._notif_ids.pop(tag, None)
        if notif_id is not None:
            await self._dismiss_mako_notification(notif_id)
        # Group dismissal is a fallback for compositors/mako states where the
        # individual notification ID is no longer replaceable but the visual
        # banner still remains on screen.
        await self._dismiss_recent_group()

    async def begin_notification_flow(self, tag: str) -> None:
        """Start a tagged notification flow by clearing any stale prior state."""
        if not tag:
            return
        await self.clear_notification(tag)
        self._active_tags.add(tag)

    async def end_notification_flow(self, tag: str, delay: float = 0.0) -> None:
        """End a tagged notification flow, optionally after a short delay."""
        if not tag:
            return
        if delay > 0:
            await asyncio.sleep(delay)
        await self.clear_notification(tag)

    async def copy_selection(self) -> str:
        """Copy current selection with event-aware clipboard probing."""
        old_clip = await self._read_clipboard()
        sentinel = f"__klor_copy_probe__:{uuid.uuid4()}"
        sentinel_prefix = "__klor_copy_probe__:"

        await self._write_clipboard(sentinel)

        watch_task = None
        if self.clip_read == "wl-paste" and shutil.which("wl-paste"):
            watch_task = asyncio.create_task(self._watch_clipboard_change())

        proc = await asyncio.create_subprocess_exec(
            self.key_sim, "-M", "ctrl", "-k", "c", "-m", "ctrl",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(self.copy_timeout, self.copy_delay)
        last_clip = sentinel
        try:
            await asyncio.sleep(self.copy_delay)
            while loop.time() < deadline:
                if watch_task is not None and watch_task.done():
                    watched = watch_task.result()
                    if watched and watched != sentinel and not watched.startswith(sentinel_prefix):
                        return watched
                text = await self._read_clipboard()
                last_clip = text
                if text and text != sentinel and not text.startswith(sentinel_prefix):
                    return text
                await asyncio.sleep(self.copy_poll_interval)
        finally:
            if watch_task is not None:
                watch_task.cancel()
                with contextlib.suppress(BaseException):
                    await watch_task
            if last_clip.startswith(sentinel_prefix):
                await self._write_clipboard(old_clip)

        return ""

    async def _watch_clipboard_change(self) -> str:
        proc = await asyncio.create_subprocess_exec(
            self.clip_read,
            "--watch",
            self.clip_read,
            "--no-newline",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            stdout, _ = await proc.communicate()
            return stdout.decode("utf-8", errors="replace").strip()
        finally:
            if proc.returncode is None:
                proc.kill()
                with contextlib.suppress(ProcessLookupError):
                    await proc.wait()

    async def paste_text(self, text: str) -> None:
        """Write text to clipboard and paste via Ctrl+V."""
        # Write to clipboard
        proc = await asyncio.create_subprocess_exec(
            self.clip_write,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate(input=text.encode("utf-8"))

        # Small delay then paste
        await asyncio.sleep(0.05)
        proc = await asyncio.create_subprocess_exec(
            self.key_sim, "-M", "ctrl", "-k", "v", "-m", "ctrl",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

    async def type_text(self, text: str) -> None:
        """Type text directly at cursor via wtype (for STT injection)."""
        proc = await asyncio.create_subprocess_exec(
            self.key_sim, "--", text,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

    async def tap_key(self, key: str) -> bool:
        """Tap a named key via the configured Wayland key simulator."""
        if not shutil.which(self.key_sim):
            log.warning("Key simulator not found: %s", self.key_sim)
            return False

        proc = await asyncio.create_subprocess_exec(
            self.key_sim, "-k", key,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            log.warning("Key simulator failed for %s: %s", key, detail or f"rc={proc.returncode}")
            return False
        return True

    async def launch_hyprland_exec(self, command: str) -> bool:
        """Launch a command via Hyprland so layer-shell UI inherits compositor context."""
        if not shutil.which("hyprctl"):
            return False

        exec_command = command
        try:
            payload = json.loads(command)
        except Exception:
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("argv"), list):
            argv = [str(part) for part in payload["argv"] if str(part)]
            env_pairs = payload.get("env") or {}
            env_prefix = " ".join(
                f"{key}={shlex.quote(str(value))}"
                for key, value in env_pairs.items()
                if value not in (None, "")
            )
            exec_command = " ".join(shlex.quote(part) for part in argv)
            if env_prefix:
                exec_command = f"env {env_prefix} {exec_command}"

        proc = await asyncio.create_subprocess_exec(
            "hyprctl", "dispatch", "exec", exec_command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0

    async def _read_clipboard(self, primary: bool = False) -> str:
        args = [self.clip_read]
        if primary:
            args.append("--primary")
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode("utf-8", errors="replace").strip()

    async def _write_clipboard(self, text: str) -> None:
        """Write text to clipboard without pasting."""
        proc = await asyncio.create_subprocess_exec(
            self.clip_write,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate(input=text.encode("utf-8"))

    async def notify(self, title: str, body: str = "", urgent: bool = False,
                     timeout: int = 5000, tag: str = "",
                     category: str = "device") -> None:
        """Send a desktop notification via notify-send.

        Uses --replace-id so that sequential notifications with the same tag
        atomically replace each other without disturbing unrelated notifications
        (works on mako, dunst, and swaync with libnotify >= 0.7.9).

        IMPORTANT: Never uses -t 0 (infinite). Even longer state notifications
        remain finite so a bridge crash cannot leave them stuck.
        """
        try:
            if tag:
                await self.clear_notification(tag)

            # --print-id makes notify-send emit the assigned notification ID so
            # we can pass it back as --replace-id on the next call for the same
            # tag.  This replaces only our own notification, never anything else.
            cmd = ["notify-send", "--print-id"]

            # Keep urgent notifications finite and avoid compositor-specific
            # persistent critical banners for STT state changes.
            if urgent:
                cmd += ["-t", str(max(timeout, 1000)), "-u", "normal"]
            else:
                cmd += ["-t", str(max(timeout, 1000))]

            if tag:
                # Both hint styles for cross-compositor compatibility:
                #  - x-dunst-stack-tag  (dunst, mako)
                #  - x-canonical-private-synchronous (GNOME, mako)
                cmd += ["-h", f"string:x-dunst-stack-tag:{tag}"]
                cmd += ["-h", f"string:x-canonical-private-synchronous:{tag}"]

            if category:
                cmd += ["-c", category]

            # App name for consistent grouping
            cmd += ["-a", "KLOR Bridge"]

            cmd += ["--", title, body]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await proc.communicate()

            # Store the notification ID for future replacement
            if tag:
                try:
                    self._notif_ids[tag] = int(stdout.decode().strip())
                except ValueError:
                    pass
        except Exception as e:
            log.debug("Notification failed: %s", e)

    async def notify_flow_step(self, tag: str, title: str, body: str = "",
                               urgent: bool = False, timeout: int = 5000,
                               category: str = "device") -> None:
        """Post a notification belonging to an active multi-step flow."""
        if tag and tag not in self._active_tags:
            self._active_tags.add(tag)
        await self.notify(title, body, urgent=urgent, timeout=timeout, tag=tag, category=category)

# ─── LLM Client (OpenRouter) ──────────────────────────────────────────────────


class LLMClient:
    """OpenRouter API client using the OpenAI Python SDK."""

    def __init__(self, config: dict):
        llm_cfg = config.get("llm", {})
        self.base_url = llm_cfg.get("base_url", "https://openrouter.ai/api/v1")
        self.default_model = llm_cfg.get("default_model", "nvidia/nemotron-3-super-120b-a12b")
        self.provider_order = [str(p) for p in llm_cfg.get("provider_order", []) if str(p).strip()]
        self.max_tokens = llm_cfg.get("max_tokens", 4096)
        self.temperature = llm_cfg.get("temperature", 0.3)
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from openai import AsyncOpenAI

            api_key = get_secret("openrouter_key", "KLOR_OPENROUTER_KEY")
            if not api_key:
                raise RuntimeError(
                    "OpenRouter API key not found. Set via:\n"
                    "  python3 <<'EOF'\n"
                    "  import keyring\n"
                    "  keyring.set_password(\"klor-bridge\", \"openrouter_key\", \"sk-or-...\")\n"
                    "  EOF\n"
                    "or export KLOR_OPENROUTER_KEY=sk-or-..."
                )
            self._client = AsyncOpenAI(base_url=self.base_url, api_key=api_key)

    @staticmethod
    def _content_part_text(part) -> str:
        if part is None:
            return ""
        if isinstance(part, str):
            return part
        if isinstance(part, dict):
            part_type = str(part.get("type") or "").lower()
            if part_type in {"text", "output_text", "input_text"}:
                return str(part.get("text") or part.get("content") or "")
            return str(part.get("text") or "")

        part_type = str(getattr(part, "type", "") or "").lower()
        if part_type in {"text", "output_text", "input_text"}:
            return str(getattr(part, "text", None) or getattr(part, "content", "") or "")
        return str(getattr(part, "text", "") or "")

    @classmethod
    def _extract_message_text(cls, response) -> str:
        choices = getattr(response, "choices", None)
        if not choices:
            raise RuntimeError("LLM response contained no choices")

        message = getattr(choices[0], "message", None)
        if message is None:
            raise RuntimeError("LLM response contained no message")

        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text = "".join(cls._content_part_text(part) for part in content).strip()
            if text:
                return text

        refusal = getattr(message, "refusal", None)
        if refusal:
            raise RuntimeError(f"LLM refused request: {str(refusal)[:200]}")

        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            raise RuntimeError("LLM returned tool calls instead of text")

        raise RuntimeError("LLM response contained no usable text")

    async def process_text(self, text: str, prompt_template: str, **kwargs) -> str:
        """Send text through an LLM prompt and return the result."""
        self._ensure_client()
        prompt = prompt_template.replace("${text}", text)
        model = kwargs.get("model", self.default_model)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        request_kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        provider_order = kwargs.get("provider_order", self.provider_order)
        if provider_order:
            request_kwargs["extra_body"] = {"provider": {"order": provider_order, "allow_fallbacks": True}}

        log.info("LLM request: model=%s, text_len=%d", model, len(text))
        response = await self._client.chat.completions.create(**request_kwargs)
        result = self._extract_message_text(response)
        log.info("LLM response: result_len=%d", len(result))
        return result.strip()

    @staticmethod
    def classify_error(exc: Exception) -> str:
        raw_err = str(exc).strip() or exc.__class__.__name__
        err_lower = raw_err.lower()

        if isinstance(exc, asyncio.TimeoutError):
            return "Request took too long. Try shorter text, a smaller prompt, or check API connectivity."
        if "refused request" in err_lower:
            return "Model refused the request. Try different wording or less sensitive content."
        if "tool calls" in err_lower:
            return "Model returned a tool-use response instead of text. Try a different model."
        if "no usable text" in err_lower or "no choices" in err_lower or "no message" in err_lower:
            return "Model returned an invalid text response. Try again or switch model."
        if "401" in err_lower or "unauthorized" in err_lower or "invalid api key" in err_lower or "authentication" in err_lower:
            return "Authentication failed. Check the configured OpenRouter API key."
        if "429" in err_lower or "rate limit" in err_lower or "too many requests" in err_lower:
            return "Rate limited by the LLM provider. Wait a moment and try again."
        if "500" in err_lower or "502" in err_lower or "503" in err_lower or "504" in err_lower or "server error" in err_lower:
            return "The LLM provider had a server error. Try again shortly."
        if "connect" in err_lower or "network" in err_lower or "dns" in err_lower or "timed out" in err_lower:
            return "Network error while contacting the LLM provider. Check connectivity and try again."
        return raw_err[:200]


# ─── HID Connection ───────────────────────────────────────────────────────────


class HIDConnection:
    """Manages the Raw HID connection to the KLOR keyboard."""

    @staticmethod
    def _parse_hex(val, default: int) -> int:
        """Parse a value that may be int or hex string like '0x3A3C'."""
        if isinstance(val, int):
            return val
        if isinstance(val, str):
            return int(val, 0)
        return default

    def __init__(self, config: dict):
        bridge_cfg = config.get("bridge", {})
        self.vid = self._parse_hex(bridge_cfg.get("vid"), 0x3A3C)
        self.pid = self._parse_hex(bridge_cfg.get("pid"), 0x0001)
        self.usage_page = self._parse_hex(bridge_cfg.get("usage_page"), 0xFF60)
        self.usage_id = self._parse_hex(bridge_cfg.get("usage_id"), 0x61)
        self.reconnect_interval = bridge_cfg.get("reconnect_interval", 5)
        self.heartbeat_interval = bridge_cfg.get("heartbeat_interval", 5)
        self._device = None

    def connect(self) -> bool:
        """Open HID device. Returns True on success."""
        try:
            import hid

            # Support both hidapi (hid.device) and python-hid (hid.Device)
            if hasattr(hid, "device"):
                Device = hid.device
                has_open_path = True
            elif hasattr(hid, "Device"):
                Device = hid.Device
                has_open_path = False
            else:
                log.error("No hid.device or hid.Device found")
                return False

            # Enumerate to find the Raw HID interface (usage_page 0xFF60)
            for dev_info in hid.enumerate(self.vid, self.pid):
                if dev_info.get("usage_page") == self.usage_page and \
                   dev_info.get("usage") == self.usage_id:
                    if has_open_path:
                        self._device = Device()
                        self._device.open_path(dev_info["path"])
                        self._device.set_nonblocking(True)
                    else:
                        self._device = Device(path=dev_info["path"])
                        self._device.nonblocking = True
                    log.info(
                        "Connected to KLOR: %s (VID=%04x PID=%04x)",
                        dev_info.get("product_string", "unknown"),
                        self.vid,
                        self.pid,
                    )
                    return True

            # Fallback: try opening by VID/PID directly
            if has_open_path:
                self._device = Device()
                self._device.open(self.vid, self.pid)
                self._device.set_nonblocking(True)
            else:
                self._device = Device(self.vid, self.pid)
                self._device.nonblocking = True
            log.info("Connected to KLOR via VID/PID (no usage page filter)")
            return True

        except Exception as e:
            log.debug("Connection failed: %s", e)
            self._device = None
            return False

    def disconnect(self) -> None:
        if self._device:
            try:
                self._device.close()
            except Exception:
                pass
            self._device = None

    @property
    def is_connected(self) -> bool:
        return self._device is not None

    def read(self) -> bytes | None:
        """Non-blocking read. Returns 32-byte packet or None."""
        if not self._device:
            return None
        try:
            data = self._device.read(PACKET_SIZE)
            if data:
                return bytes(data)
            return None
        except Exception as e:
            log.warning("HID read error: %s", e)
            self.disconnect()
            return None

    def send(self, data: bytes) -> bool:
        """Send a 32-byte packet. Prepends 0x00 report ID as required by HID protocol."""
        if not self._device:
            return False
        try:
            # HID protocol requires report ID as first byte (0x00 for default)
            packet = b"\x00" + data.ljust(PACKET_SIZE, b"\x00")[:PACKET_SIZE]
            self._device.write(packet)
            return True
        except Exception as e:
            log.warning("HID write error: %s", e)
            self.disconnect()
            return False

    def send_heartbeat(self) -> bool:
        """Send a heartbeat ping to the keyboard."""
        data = bytes([CMD_BRIDGE_HEARTBEAT]) + b"\x00" * (PACKET_SIZE - 1)
        return self.send(data)


# ─── Bridge Daemon ────────────────────────────────────────────────────────────


class KlorBridge:
    """Main daemon: ties together HID, LLM, prompt tools, and platform helpers."""

    def __init__(self):
        self.config = load_config()
        self.actions = load_actions()
        self.prompts = load_prompts()
        self.snippets = load_snippets()
        self._prompts_path = CONFIG_DIR / "prompts.yml"
        self._snippets_path = CONFIG_DIR / "snippets.yml"
        self._prompts_mtime_ns = file_mtime_ns(self._prompts_path)
        self._snippets_mtime_ns = file_mtime_ns(self._snippets_path)

        self.hid = HIDConnection(self.config)
        self.platform = Platform(self.config)
        self.llm = LLMClient(self.config)
        self._llm_action_lock = asyncio.Lock()
        self._llm_action_active = False

        # Brightness config
        bright_cfg = self.config.get("brightness", {})
        self._brightness_step = bright_cfg.get("step_percent", 5)
        self._brightness_tool = bright_cfg.get("tool", "brightnessctl")  # or "ddcutil"
        self._ddcutil_fallback = bright_cfg.get("ddcutil_fallback", True)

    async def run(self) -> None:
        """Main event loop."""
        log.info("KLOR Bridge starting...")
        log.info("Config dir: %s", CONFIG_DIR)
        log.info("Actions loaded: %d", len(self.actions))

        # Start the test socket server for injecting simulated HID packets
        test_port = self.config.get("bridge", {}).get("test_port", 19378)
        try:
            test_server = await asyncio.start_server(
                self._handle_test_connection, "127.0.0.1", test_port)
            log.info("Test socket listening on 127.0.0.1:%d", test_port)
        except OSError as e:
            log.warning("Test socket unavailable (port %d): %s", test_port, e)
            test_server = None

        while True:
            # Connect (with retry)
            if not self.hid.is_connected:
                if self.hid.connect():
                    log.info("Keyboard connected")
                else:
                    await asyncio.sleep(self.hid.reconnect_interval)
                    continue

            # Main processing loop
            try:
                await self._process_loop()
            except Exception as e:
                log.error("Processing error: %s", e, exc_info=True)
                self.hid.disconnect()
                await asyncio.sleep(1)

    async def _handle_test_connection(self, reader: asyncio.StreamReader,
                                       writer: asyncio.StreamWriter) -> None:
        """Handle a test socket connection: read 32-byte packets and dispatch."""
        addr = writer.get_extra_info("peername")
        log.info("Test connection from %s", addr)
        try:
            while True:
                data = await reader.read(PACKET_SIZE)
                if not data:
                    break
                # Pad to 32 bytes if short
                packet = data.ljust(PACKET_SIZE, b"\x00")[:PACKET_SIZE]
                log.info("Test packet: %s", packet[:4].hex())
                await self._handle_packet(packet)
                writer.write(b"OK\n")
                await writer.drain()
        except Exception as e:
            log.debug("Test connection error: %s", e)
        finally:
            writer.close()

    async def _process_loop(self) -> None:
        """Read HID packets and dispatch actions."""
        last_heartbeat = time.monotonic()

        while self.hid.is_connected:
            # Check for incoming packets
            packet = self.hid.read()
            if packet:
                await self._handle_packet(packet)

            # Periodic heartbeat
            now = time.monotonic()
            if now - last_heartbeat >= self.hid.heartbeat_interval:
                if not self.hid.send_heartbeat():
                    log.warning("Heartbeat failed, reconnecting...")
                    break
                last_heartbeat = now

            # Small sleep to avoid busy-waiting (HID is non-blocking)
            await asyncio.sleep(0.005)  # 5ms = 200 polls/sec

    async def _handle_packet(self, packet: bytes) -> None:
        """Route an incoming HID packet to the appropriate handler."""
        if len(packet) < 1:
            return

        cmd_id = packet[0]
        log.debug("RX packet: cmd=%02x payload=%s", cmd_id, packet[1:4].hex())

        if cmd_id == CMD_BRIDGE_ACTION:
            action_id = packet[1] if len(packet) > 1 else 0
            param = packet[2] if len(packet) > 2 else 0
            await self._dispatch_action(action_id, param)

        elif cmd_id == CMD_BRIDGE_HEARTBEAT:
            log.debug("Heartbeat response received")

        else:
            log.debug("Unknown packet: cmd=%02x", cmd_id)

    def _reload_prompts_if_changed(self) -> None:
        mtime_ns = file_mtime_ns(self._prompts_path)
        if mtime_ns == self._prompts_mtime_ns:
            return

        try:
            prompts = load_prompts()
        except Exception as e:
            self._prompts_mtime_ns = mtime_ns
            log.error("Failed to reload %s: %s", self._prompts_path.name, e)
            return

        # Mutate in place so the STT pipeline sees updated templates too.
        self.prompts.clear()
        self.prompts.update(prompts)
        self._prompts_mtime_ns = mtime_ns
        log.info("Reloaded %s (%d templates)", self._prompts_path.name, len(self.prompts))

    def _reload_snippets_if_changed(self) -> None:
        mtime_ns = file_mtime_ns(self._snippets_path)
        if mtime_ns == self._snippets_mtime_ns:
            return

        try:
            snippets = load_snippets()
        except Exception as e:
            self._snippets_mtime_ns = mtime_ns
            log.error("Failed to reload %s: %s", self._snippets_path.name, e)
            return

        self.snippets[:] = snippets
        self._snippets_mtime_ns = mtime_ns
        log.info("Reloaded %s (%d snippets)", self._snippets_path.name, len(self.snippets))

    async def _dispatch_action(self, action_id: int, param: int) -> None:
        """Execute an action based on its ID."""
        # ── Brightness (direct action IDs, not in actions.yml) ──
        if action_id == ACTION_BRIGHTNESS_UP:
            await self._handle_brightness(+1)
            return
        if action_id == ACTION_BRIGHTNESS_DOWN:
            await self._handle_brightness(-1)
            return

        action = self.actions.get(action_id)

        if not action:
            log.warning("Unknown action ID: 0x%02x", action_id)
            return

        action_type = action.get("type", "")
        name = action.get("name", f"0x{action_id:02x}")
        log.info("Action: %s (type=%s, param=%d)", name, action_type, param)

        try:
            if action_type == "llm_text":
                await self._handle_llm_text(action)
            elif action_type == "prompt_picker":
                await self._handle_prompt_picker(action)
            elif action_type == "unconfigured":
                log.info("Action %s is unconfigured — assign it in actions.yml", name)
                await self.platform.notify(
                    f"Key {action.get('key', '?').upper()} — Not configured",
                    "Assign an action in actions.yml",
                    tag="klor-info",
                    timeout=3000,
                )
            else:
                log.warning("Unknown action type: %s", action_type)
                await self.platform.notify(
                    "Unknown action type",
                    f"Type '{action_type}' is not recognized",
                    tag="klor-info",
                    timeout=5000,
                )
        except Exception as e:
            log.error("Action %s failed: %s", name, e, exc_info=True)
            await self.platform.notify(
                f"Action {name} failed",
                str(e)[:200],
                tag="klor-error",
                timeout=8000,
            )

    async def _handle_llm_text(self, action: dict) -> None:
        """Copy selection → LLM transform → write result to clipboard (no auto-paste).

        Shows notifications at each stage so the user always knows what's
        happening, even when the LLM call takes several seconds.
        """
        action_name = action.get("name", "LLM")
        action_key = action.get("key", "?").upper()
        if self._llm_action_active:
            await self.platform.begin_notification_flow("klor-llm")
            await self.platform.notify_flow_step(
                "klor-llm",
                f"{action_key} — Busy",
                "Another LLM action is already running. Wait for it to finish.",
                timeout=4000,
            )
            await self.platform.end_notification_flow("klor-llm", delay=4)
            return

        async with self._llm_action_lock:
            self._llm_action_active = True
            try:
                await self._run_llm_text_action(action, action_name, action_key)
            finally:
                self._llm_action_active = False

    async def _run_llm_text_action(self, action: dict, action_name: str, action_key: str) -> None:
        await self.platform.begin_notification_flow("klor-llm")

        # Notify: starting
        await self.platform.notify_flow_step(
            "klor-llm",
            f"{action_key} — Copying selection...",
            f"Action: {action_name}",
        )

        # Copy selected text with sentinel-based clipboard probing. The copy
        # helper now safely distinguishes a real selection from stale clipboard
        # contents, even when the selected text matches the previous clipboard.
        text = ""
        copy_attempt_delays = (0.0, 0.2, 0.45, 0.8)
        for attempt, delay in enumerate(copy_attempt_delays, start=1):
            if delay > 0:
                await asyncio.sleep(delay)
            text = await self.platform.copy_selection()
            if text and not text.isspace():
                break
            if attempt < len(copy_attempt_delays):
                await self.platform.notify_flow_step(
                    "klor-llm",
                    f"{action_key} — Copying selection...",
                    f"Retrying selection copy ({attempt + 1}/{len(copy_attempt_delays)})",
                    timeout=1200,
                )

        if not text or text.isspace():
            log.warning("No fresh text selected after copy retries")
            await self.platform.notify_flow_step(
                "klor-llm",
                f"{action_key} — No text selected",
                "Selection copy did not produce new clipboard text. Select text and try again.",
                timeout=5000,
            )
            await self.platform.end_notification_flow("klor-llm", delay=5)
            return

        # Look up prompt template
        self._reload_prompts_if_changed()
        prompt_key = action.get("prompt_key", "")
        template = self.prompts.get(prompt_key)
        if not template:
            log.error("Prompt template not found: %s", prompt_key)
            await self.platform.notify_flow_step(
                "klor-llm",
                f"{action_key} — Config error",
                f"Prompt template '{prompt_key}' not found in prompts.yml",
                timeout=8000,
            )
            await self.platform.end_notification_flow("klor-llm", delay=8)
            return

        # Notify: processing with LLM
        await self.platform.notify_flow_step(
            "klor-llm",
            f"{action_key} — Processing with LLM...",
            f"{len(text)} chars selected. Please wait.",
            urgent=True,  # stays visible until replaced
        )

        # Process through LLM with timeout
        try:
            result = await asyncio.wait_for(
                self.llm.process_text(text, template),
                timeout=120,  # 2 minute max
            )
        except asyncio.TimeoutError:
            log.error("LLM request timed out after 120s")
            await self.platform.notify_flow_step(
                "klor-llm",
                f"{action_key} — LLM timeout",
                self.llm.classify_error(asyncio.TimeoutError()),
                timeout=8000,
            )
            await self.platform.end_notification_flow("klor-llm", delay=8)
            return
        except Exception as e:
            log.error("LLM request failed: %s", e, exc_info=True)
            err_msg = self.llm.classify_error(e)
            await self.platform.notify_flow_step(
                "klor-llm",
                f"{action_key} — LLM error",
                err_msg,
                timeout=8000,
            )
            await self.platform.end_notification_flow("klor-llm", delay=8)
            return

        if not result or result.isspace():
            log.warning("LLM returned empty result")
            await self.platform.notify_flow_step(
                "klor-llm",
                f"{action_key} — Empty result",
                "LLM returned nothing. Try different text.",
                timeout=5000,
            )
            await self.platform.end_notification_flow("klor-llm", delay=5)
            return

        # Write result to clipboard (no paste)
        await self.platform._write_clipboard(result)
        log.info("LLM result copied to clipboard: %d chars → %d chars", len(text), len(result))
        await self.platform.notify_flow_step(
            "klor-llm",
            f"{action_key} — Result ready",
            f"{len(result)} chars copied to clipboard. Paste with Ctrl+V.",
            timeout=5000,
        )
        await self.platform.end_notification_flow("klor-llm", delay=5)

    # ── Prompt Picker ─────────────────────────────────────────────

    async def _handle_prompt_picker(self, action: dict) -> None:
        """Show a searchable GTK prompt picker.

        Loads snippets from snippets.yml, presents them in the GTK picker,
        and copies the selected snippet's text to the clipboard.
        """
        self._reload_snippets_if_changed()

        await self.platform.begin_notification_flow("klor-picker")

        if not self.snippets:
            await self.platform.notify_flow_step(
                "klor-picker",
                "No snippets configured",
                "Add prompts to ~/.config/klor-bridge/snippets.yml",
                timeout=5000,
            )
            await self.platform.end_notification_flow("klor-picker", delay=5)
            return

        # Build a title-only list so the picker stays compact and easy to scan.
        lines = []
        line_to_snippet = {}
        for s in self.snippets:
            base_label = s["name"]
            label = base_label
            if label in line_to_snippet:
                desc = s.get("category", "")
                label = f"{base_label} ({desc})" if desc else base_label
            if label in line_to_snippet:
                index = 2
                unique_label = f"{label} #{index}"
                while unique_label in line_to_snippet:
                    index += 1
                    unique_label = f"{label} #{index}"
                label = unique_label
            lines.append(label)
            line_to_snippet[label] = s
        menu_input = "\n".join(lines)

        helper = Path(__file__).with_name("prompt_picker_helper.py")
        if not helper.exists():
            log.error("Prompt picker helper not found: %s", helper)
            await self.platform.notify_flow_step(
                "klor-picker",
                "Prompt picker unavailable",
                f"Missing helper: {helper.name}",
                timeout=5000,
            )
            await self.platform.end_notification_flow("klor-picker", delay=5)
            return

        try:
            log.info("Opening GTK prompt picker (%d snippets)", len(self.snippets))
            cache_dir = Path.home() / ".cache" / "klor-bridge"
            cache_dir.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile("w", delete=False, dir=cache_dir, suffix=".txt", encoding="utf-8") as input_file:
                input_file.write(menu_input)
                input_path = Path(input_file.name)

            result_path = cache_dir / f"picker-result-{int(time.time() * 1000)}.json"
            helper_env = os.environ.copy()
            for key in ("KLOR_PICKER_TEST_QUERY", "KLOR_PICKER_TEST_ACCEPT_MS"):
                value = os.environ.get(key)
                if value:
                    helper_env[key] = value
            helper_proc = await asyncio.create_subprocess_exec(
                sys.executable,
                str(helper),
                str(input_path),
                str(result_path),
                env=helper_env,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            try:
                loop = asyncio.get_running_loop()
                deadline = loop.time() + 28
                while not result_path.exists() and loop.time() < deadline:
                    await asyncio.sleep(0.1)

                if not result_path.exists():
                    log.warning("Prompt picker timed out waiting for result")
                    if helper_proc.returncode is None:
                        helper_proc.kill()
                        with contextlib.suppress(ProcessLookupError):
                            await helper_proc.wait()
                    await self.platform.end_notification_flow("klor-picker")
                    return

                result_data = json.loads(result_path.read_text(encoding="utf-8"))
                stdout = (result_data.get("stdout") or "").encode("utf-8")
                returncode = int(result_data.get("returncode", 1))
            finally:
                if helper_proc.returncode is None:
                    try:
                        await asyncio.wait_for(helper_proc.wait(), timeout=1.0)
                    except (asyncio.TimeoutError, ProcessLookupError):
                        helper_proc.kill()
                        with contextlib.suppress(ProcessLookupError):
                            await helper_proc.wait()
                input_path.unlink(missing_ok=True)
                result_path.unlink(missing_ok=True)

            if returncode != 0 or not stdout:
                log.info("Prompt picker cancelled by user")
                await self.platform.end_notification_flow("klor-picker")
                return

            selected = stdout.decode("utf-8").strip()
            snippet = line_to_snippet.get(selected)

            if not snippet:
                log.warning("Selected snippet not found: %s", selected)
                await self.platform.end_notification_flow("klor-picker")
                return

            text = snippet["text"]
            await self.platform._write_clipboard(text)
            log.info("Prompt snippet copied: %s (%d chars)", snippet["name"], len(text))
            await self.platform.notify_flow_step(
                "klor-picker",
                f"Snippet: {snippet['name']}",
                f"{len(text)} chars copied. Paste with Ctrl+V.",
                timeout=3000,
            )
            await self.platform.end_notification_flow("klor-picker", delay=3)
            return
        except asyncio.TimeoutError:
            log.warning("Prompt picker timed out")
            await self.platform.end_notification_flow("klor-picker")
            return
        except Exception as e:
            log.error("Prompt picker failed: %s", e)
            await self.platform.notify_flow_step(
                "klor-picker",
                "Prompt picker error",
                str(e)[:200],
                timeout=5000,
            )
            await self.platform.end_notification_flow("klor-picker", delay=5)
            return

    # ── Brightness Control ────────────────────────────────────────

    async def _handle_brightness(self, direction: int) -> None:
        """Adjust monitor brightness through the Omarchy DDC helper."""
        if await self._brightness_omarchy_ddc(direction):
            return

        key = "XF86MonBrightnessUp" if direction > 0 else "XF86MonBrightnessDown"
        if await self.platform.tap_key(key):
            log.debug("Triggered Omarchy brightness shortcut: %s", key)

    async def _brightness_omarchy_ddc(self, direction: int) -> bool:
        """Use the local Omarchy DDC brightness helper when present."""
        script = Path.home() / ".config" / "hypr" / "brightness-display-ddc.sh"
        if not script.exists():
            return False

        step = str(self._brightness_step).rstrip("%")
        if not step.isdigit():
            step = "5"
        arg = "up" if direction > 0 else "down"

        env = os.environ.copy()
        omarchy_bin = str(Path.home() / ".local" / "share" / "omarchy" / "bin")
        env["PATH"] = f"{omarchy_bin}:{env.get('PATH', '')}"

        command = [str(script), arg, step] if os.access(script, os.X_OK) else ["bash", str(script), arg, step]
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            log.warning("Omarchy DDC brightness helper failed: %s", detail or f"rc={proc.returncode}")
            return False

        log.debug("Omarchy DDC brightness: %s %s", arg, step)
        return True

    async def _brightness_brightnessctl(self, direction: int, step: int) -> None:
        """Adjust brightness via brightnessctl (works for backlight + some DDC)."""
        if not shutil.which("brightnessctl"):
            log.warning("brightnessctl not found")
            return

        arg = f"{step}%+" if direction > 0 else f"{step}%-"
        proc = await asyncio.create_subprocess_exec(
            "brightnessctl", "set", arg,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            # Parse current brightness from output for logging
            output = stdout.decode("utf-8", errors="replace")
            log.debug("brightnessctl: %s", output.strip().split("\n")[-1] if output else "ok")
        else:
            # brightnessctl failed — try ddcutil as fallback if enabled
            log.debug("brightnessctl failed (rc=%d), ddcutil_fallback=%s", proc.returncode, self._ddcutil_fallback)
            if self._ddcutil_fallback:
                await self._brightness_ddcutil(direction, step)

    async def _brightness_ddcutil(self, direction: int, step: int) -> None:
        """Adjust brightness via ddcutil (DDC/CI for external monitors).

        Adjusts ALL detected displays.  Feature code 0x10 = brightness.
        """
        if not shutil.which("ddcutil"):
            log.warning("ddcutil not found — cannot control external monitors")
            return

        sign = "+" if direction > 0 else "-"
        # Detect displays
        detect_proc = await asyncio.create_subprocess_exec(
            "ddcutil", "detect", "--brief",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        detect_out, _ = await detect_proc.communicate()

        # Parse display numbers
        displays = []
        for line in detect_out.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("Display"):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        displays.append(int(parts[1]))
                    except ValueError:
                        pass

        if not displays:
            # Try display 1 as default
            displays = [1]

        # Adjust each display
        for disp in displays:
            proc = await asyncio.create_subprocess_exec(
                "ddcutil", "setvcp", "10", f"{sign}", str(step),
                "--display", str(disp), "--noverify",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            log.debug("ddcutil display %d: brightness %s%d%%", disp, sign, step)


# ─── Entry point ──────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="KLOR Bridge AI daemon")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    bridge = KlorBridge()
    try:
        asyncio.run(bridge.run())
    except KeyboardInterrupt:
        log.info("Shutting down...")
    finally:
        bridge.hid.disconnect()


if __name__ == "__main__":
    main()
