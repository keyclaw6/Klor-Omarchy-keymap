#!/usr/bin/env python3
"""
KLOR Bridge — AI writing assistant daemon for the KLOR split keyboard.

Listens for Raw HID commands from the KLOR keyboard (via raw_hid_receive_kb() hook),
dispatches actions to OpenRouter LLM and ElevenLabs STT, and injects results
back at the cursor via wtype/wl-clipboard.

Usage:
    python klor-bridge.py              # run in foreground
    python klor-bridge.py --verbose    # debug logging

Dependencies (Arch):
    pacman -S python-hid python-openai python-yaml python-keyring python-sounddevice python-numpy python-aiohttp
Dependencies (pip):
    pip install hidapi openai pyyaml keyring sounddevice numpy aiohttp

System deps:
    wtype wl-clipboard
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import sys
import time
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
ACTION_STT = 0x10

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


def load_lexicon() -> list[str]:
    """Flatten all lexicon categories into a single list of terms."""
    raw = load_yaml(CONFIG_DIR / "lexicon.yml")
    terms = []
    for category in raw.values():
        if isinstance(category, list):
            terms.extend(category)
    return terms


def load_corrections() -> list[dict]:
    raw = load_yaml(CONFIG_DIR / "corrections.yml")
    return raw.get("corrections", [])


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

    async def copy_selection(self) -> str:
        """Copy currently selected text to clipboard via Ctrl+C, then read it."""
        # Save current clipboard
        old_clip = await self._read_clipboard()

        # Send Ctrl+C
        proc = await asyncio.create_subprocess_exec(
            self.key_sim, "-M", "ctrl", "-k", "c", "-m", "ctrl",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

        # Wait for clipboard to update
        await asyncio.sleep(self.copy_delay)

        # Read new clipboard content
        text = await self._read_clipboard()

        return text if text else old_clip or ""

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

    async def _read_clipboard(self) -> str:
        proc = await asyncio.create_subprocess_exec(
            self.clip_read,
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
                     timeout: int = 3000, tag: str = "") -> None:
        """Send a desktop notification via notify-send.

        If tag is set, subsequent notifications with the same tag replace
        the previous one (uses dunst/mako-compatible hint).
        """
        try:
            cmd = ["notify-send"]
            if urgent:
                cmd += ["-t", "0", "-u", "critical"]
            else:
                cmd += ["-t", str(timeout)]
            if tag:
                cmd += ["-h", f"string:x-dunst-stack-tag:{tag}"]
            cmd += ["--", title, body]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
        except Exception as e:
            log.debug("Notification failed: %s", e)


# ─── LLM Client (OpenRouter) ──────────────────────────────────────────────────


class LLMClient:
    """OpenRouter API client using the OpenAI Python SDK."""

    def __init__(self, config: dict):
        llm_cfg = config.get("llm", {})
        self.base_url = llm_cfg.get("base_url", "https://openrouter.ai/api/v1")
        self.default_model = llm_cfg.get("default_model", "nvidia/nemotron-3-super-120b-a12b")
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

    async def process_text(self, text: str, prompt_template: str, **kwargs) -> str:
        """Send text through an LLM prompt and return the result."""
        self._ensure_client()
        prompt = prompt_template.replace("${text}", text)
        model = kwargs.get("model", self.default_model)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)

        log.info("LLM request: model=%s, text_len=%d", model, len(text))
        response = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        result = response.choices[0].message.content or ""
        log.info("LLM response: result_len=%d", len(result))
        return result.strip()


# ─── STT Pipeline ─────────────────────────────────────────────────────────────


class STTPipeline:
    """Speech-to-text with 3-layer correction pipeline."""

    def __init__(self, config: dict, llm: LLMClient, prompts: dict):
        stt_cfg = config.get("stt", {})
        self.language = stt_cfg.get("language")  # None = auto-detect (ElevenLabs default)
        self.sample_rate = stt_cfg.get("sample_rate", 16000)
        self.channels = stt_cfg.get("channels", 1)
        self.audio_device = stt_cfg.get("audio_device", "default")

        self.el_cfg = stt_cfg.get("elevenlabs", {})

        self.llm = llm
        self.prompts = prompts
        self.lexicon = load_lexicon()
        self.corrections = load_corrections()

        # Recording state
        self._recording = False
        self._audio_buffer: list = []
        self._stream = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    async def toggle_recording(self, depth: int = 1) -> str | None:
        """Toggle STT recording. Returns transcribed text when stopping, None when starting."""
        if self._recording:
            return await self._stop_and_process(depth)
        else:
            self._start_recording()
            return None

    def _start_recording(self) -> None:
        """Start capturing audio from microphone."""
        import sounddevice as sd

        self._audio_buffer = []
        self._recording = True

        device = None if self.audio_device == "default" else self.audio_device

        def callback(indata, frames, time_info, status):
            if status:
                log.warning("Audio callback status: %s", status)
            self._audio_buffer.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            device=device,
            callback=callback,
        )
        self._stream.start()
        log.info("STT recording started")

    async def _stop_and_process(self, depth: int) -> str:
        """Stop recording and run the correction pipeline."""
        import numpy as np

        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._audio_buffer:
            log.warning("No audio captured")
            return ""

        audio = np.concatenate(self._audio_buffer, axis=0)
        self._audio_buffer = []
        log.info("STT recording stopped: %.1f seconds", len(audio) / self.sample_rate)

        # Layer 1: Transcription
        transcript = await self._transcribe(audio)
        log.info("L1 transcript: %s", transcript[:100])

        if depth >= 2 and transcript:
            # Layer 2: Domain corrector
            transcript = self._domain_correct(transcript)
            log.info("L2 corrected: %s", transcript[:100])

        if depth >= 3 and transcript:
            # Layer 3: LLM post-processing
            template = self.prompts.get("stt_postprocess", "Fix errors:\n${text}")
            transcript = await self.llm.process_text(transcript, template)
            log.info("L3 post-processed: %s", transcript[:100])

        return transcript

    async def _transcribe(self, audio) -> str:
        """Run Layer 1 transcription via ElevenLabs Scribe v2."""
        return await self._transcribe_elevenlabs(audio)

    async def _transcribe_elevenlabs(self, audio) -> str:
        """Transcribe using ElevenLabs Scribe v2 REST API.

        Sends raw PCM (int16, 16kHz, mono) instead of WAV to avoid container
        overhead and reduce latency for short dictation clips.
        """
        import numpy as np

        api_key = get_secret("elevenlabs_key", "KLOR_ELEVENLABS_KEY")
        if not api_key:
            raise RuntimeError("ElevenLabs API key not configured")

        # Convert float32 audio to raw PCM int16 bytes (no WAV header)
        pcm_bytes = self._audio_to_pcm(audio)

        # Build multipart form data
        import aiohttp

        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {"xi-api-key": api_key}

        data = aiohttp.FormData()
        data.add_field("file", pcm_bytes, filename="audio.pcm", content_type="audio/pcm")
        data.add_field("model_id", self.el_cfg.get("model_id", "scribe_v2"))

        # Language: auto-detect if not explicitly set
        if self.language:
            data.add_field("language_code", self.language)

        # Dictation-optimized settings
        if self.el_cfg.get("no_verbatim", True):
            data.add_field("no_verbatim", "true")

        data.add_field("diarize", str(self.el_cfg.get("diarize", False)).lower())
        data.add_field("timestamps_granularity", self.el_cfg.get("timestamps_granularity", "none"))

        if not self.el_cfg.get("tag_audio_events", False):
            data.add_field("tag_audio_events", "false")

        # Tell ElevenLabs the audio format (raw PCM int16, 16kHz, mono)
        data.add_field("file_format", "pcm_s16le_16")

        # Add keyterms for vocabulary biasing — each term as a separate field
        if self.lexicon:
            keyterms = self.lexicon[:1000]  # max 1000
            # Send each keyterm as a repeated form field (not a JSON string)
            for term in keyterms:
                data.add_field("keyterms[]", term)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(f"ElevenLabs API error {resp.status}: {body}")
                result = await resp.json()
                return result.get("text", "")

    def _domain_correct(self, text: str) -> str:
        """Layer 2: Apply regex exact corrections then fuzzy matching."""
        # Exact regex corrections
        for rule in self.corrections:
            pattern = rule.get("pattern", "")
            replace = rule.get("replace", "")
            flags = re.IGNORECASE if rule.get("ignorecase") else 0
            text = re.sub(pattern, replace, text, flags=flags)

        # Fuzzy matching against lexicon (simple Levenshtein for known terms)
        # This is intentionally lightweight — heavy correction is L3's job
        if self.lexicon:
            words = text.split()
            corrected = []
            for word in words:
                match = self._fuzzy_match(word)
                corrected.append(match if match else word)
            text = " ".join(corrected)

        return text

    def _fuzzy_match(self, word: str, threshold: int = 2) -> str | None:
        """Find closest lexicon term within Levenshtein distance threshold."""
        if len(word) < 4:
            return None  # don't fuzzy-match short words

        best_term = None
        best_dist = threshold + 1

        for term in self.lexicon:
            if abs(len(word) - len(term)) > threshold:
                continue
            dist = self._levenshtein(word.lower(), term.lower())
            if dist < best_dist and dist <= threshold:
                best_dist = dist
                best_term = term

        return best_term

    @staticmethod
    def _levenshtein(s: str, t: str) -> int:
        """Compute Levenshtein edit distance between two strings."""
        if len(s) < len(t):
            return STTPipeline._levenshtein(t, s)
        if len(t) == 0:
            return len(s)

        prev_row = list(range(len(t) + 1))
        for i, c1 in enumerate(s):
            curr_row = [i + 1]
            for j, c2 in enumerate(t):
                cost = 0 if c1 == c2 else 1
                curr_row.append(min(
                    curr_row[j] + 1,
                    prev_row[j + 1] + 1,
                    prev_row[j] + cost,
                ))
            prev_row = curr_row
        return prev_row[-1]

    def _audio_to_pcm(self, audio) -> bytes:
        """Convert numpy float32 audio array to raw PCM int16 bytes.

        Output: signed 16-bit little-endian, 16kHz, mono — no WAV header.
        ElevenLabs Scribe v2 accepts this as pcm_s16le_16 format.
        """
        import numpy as np

        # Normalize and convert to int16
        audio_int16 = (audio * 32767).astype(np.int16)
        if audio_int16.ndim > 1:
            audio_int16 = audio_int16[:, 0]

        return audio_int16.tobytes()


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
    """Main daemon: ties together HID, LLM, STT, and platform layers."""

    def __init__(self):
        self.config = load_config()
        self.actions = load_actions()
        self.prompts = load_prompts()

        self.hid = HIDConnection(self.config)
        self.platform = Platform(self.config)
        self.llm = LLMClient(self.config)
        self.stt = STTPipeline(self.config, self.llm, self.prompts)

        # STT state
        self._stt_depth = 1

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

    async def _dispatch_action(self, action_id: int, param: int) -> None:
        """Execute an action based on its ID."""
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
            elif action_type == "stt_toggle":
                await self._handle_stt_toggle(param)
            elif action_type == "unconfigured":
                log.info("Action %s is unconfigured — assign it in actions.yml", name)
            else:
                log.warning("Unknown action type: %s", action_type)
        except Exception as e:
            log.error("Action %s failed: %s", name, e, exc_info=True)

    async def _handle_llm_text(self, action: dict) -> None:
        """Copy selection → LLM transform → write result to clipboard (no auto-paste)."""
        # Copy selected text
        text = await self.platform.copy_selection()
        if not text:
            log.warning("No text selected (clipboard empty)")
            await self.platform.notify("No text selected", "Select some text and try again", tag="klor-llm")
            return

        # Look up prompt template
        prompt_key = action.get("prompt_key", "")
        template = self.prompts.get(prompt_key)
        if not template:
            log.error("Prompt template not found: %s", prompt_key)
            return

        # Process through LLM
        result = await self.llm.process_text(text, template)
        if not result:
            log.warning("LLM returned empty result")
            await self.platform.notify("LLM returned empty", "Try again or select different text", tag="klor-llm")
            return

        # Write result to clipboard (no paste)
        await self.platform._write_clipboard(result)
        log.info("LLM result copied to clipboard: %d chars → %d chars", len(text), len(result))
        await self.platform.notify(
            f"{action.get('key', '').upper()} — LLM result copied",
            f"{len(result)} chars ready to paste",
            tag="klor-llm"
        )

    async def _handle_stt_toggle(self, depth: int) -> None:
        """Toggle speech-to-text recording."""
        depth = max(1, min(3, depth))  # clamp to 1-3

        if self.stt.is_recording:
            # Use the depth stored at recording start (not the stop packet's param)
            log.info("STT stop → processing with depth=%d", self._stt_depth)
            await self.platform.notify(
                "Processing transcription...", "Please wait",
                tag="klor-stt"
            )
            result = await self.stt.toggle_recording(self._stt_depth)
            if result:
                await self.platform._write_clipboard(result)
                log.info("STT copied to clipboard: %d chars", len(result))
                await self.platform.notify(
                    "Transcription complete",
                    f"{len(result)} chars copied to clipboard (depth={self._stt_depth})",
                    tag="klor-stt"
                )
            else:
                log.warning("STT produced no text")
                await self.platform.notify(
                    "No speech detected", "Try again and speak clearly",
                    tag="klor-stt"
                )
        else:
            self._stt_depth = depth
            await self.stt.toggle_recording(depth)
            log.info("STT recording started (depth=%d)", depth)
            await self.platform.notify(
                "Recording...",
                f"Speak now. Depth {depth}/3. Press RALT or T to stop.",
                urgent=True,
                tag="klor-stt"
            )


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
        # Ensure audio stream is cleaned up
        if bridge.stt.is_recording:
            if bridge.stt._stream:
                bridge.stt._stream.stop()
                bridge.stt._stream.close()
        bridge.hid.disconnect()


if __name__ == "__main__":
    main()
