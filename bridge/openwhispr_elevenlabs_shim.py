#!/usr/bin/env python3
"""OpenWhispr -> ElevenLabs Scribe v2 adapter.

OpenWhispr's Self-Hosted transcription mode speaks the OpenAI-compatible
/audio/transcriptions multipart contract. ElevenLabs Scribe v2 uses a different
multipart contract and xi-api-key authentication, so this tiny localhost shim
translates between them.

The ElevenLabs credential is intentionally NOT copied or stored here. Resolution:
  1. ELEVENLABS_API_KEY
  2. KLOR_ELEVENLABS_KEY
  3. Existing OS keyring entry: service="klor-bridge", username="elevenlabs_key"

That third path carries the current KLOR credential forward without exposing it.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import secrets
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import keyring

HOST = os.environ.get("OPENWHISPR_ELEVENLABS_HOST", "127.0.0.1")
PORT = int(os.environ.get("OPENWHISPR_ELEVENLABS_PORT", "8765"))
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/speech-to-text"
DEFAULT_MODEL = "scribe_v2"
MAX_BODY_BYTES = 25 * 1024 * 1024
MAX_KEYTERMS = 100
FORBIDDEN_KEYTERM_CHARS = set("<>{}[]\\\\")
KEYRING_SERVICE = "klor-bridge"
KEYRING_USERNAME = "elevenlabs_key"


def get_api_key() -> str:
    for name in ("ELEVENLABS_API_KEY", "KLOR_ELEVENLABS_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    try:
        value = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except Exception as exc:
        raise RuntimeError(f"Could not read ElevenLabs API key from OS keyring: {exc}") from exc
    if value:
        return value.strip()
    raise RuntimeError(
        "ElevenLabs API key not found. Keep the existing KLOR keyring entry or set "
        "ELEVENLABS_API_KEY."
    )


def parse_multipart_form(
    body: bytes, content_type: str
) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    """Parse the small multipart subset OpenWhispr sends, stdlib-only."""
    match = re.search(r'boundary="?([^";]+)"?', content_type)
    if not match:
        raise ValueError("missing multipart boundary in Content-Type")

    delimiter = b"--" + match.group(1).strip().encode()
    fields: dict[str, str] = {}
    files: dict[str, tuple[str, bytes]] = {}

    for chunk in body.split(delimiter):
        if not chunk or chunk.startswith(b"--"):
            continue
        if chunk.startswith(b"\r\n"):
            chunk = chunk[2:]
        if chunk.endswith(b"\r\n"):
            chunk = chunk[:-2]
        if b"\r\n\r\n" not in chunk:
            continue

        raw_headers, content = chunk.split(b"\r\n\r\n", 1)
        disposition = ""
        for line in raw_headers.decode("utf-8", "replace").split("\r\n"):
            if line.lower().startswith("content-disposition:"):
                disposition = line
                break

        name_match = re.search(r'name="([^"]*)"', disposition)
        if not name_match:
            continue
        name = name_match.group(1)

        file_match = re.search(r'filename="([^"]*)"', disposition)
        if file_match:
            files[name] = (file_match.group(1), content)
        else:
            fields[name] = content.decode("utf-8", "replace")

    return fields, files


def prompt_to_keyterms(prompt: str | None) -> list[str]:
    """Translate OpenWhispr's custom-dictionary prompt into Scribe keyterms."""
    if not prompt:
        return []

    terms: list[str] = []
    seen: set[str] = set()
    for raw in re.split(r"[,;\n]+", prompt):
        term = raw.strip().strip('"').strip("'")
        if not term or term in seen:
            continue
        if len(term) >= 50 or len(term.split()) > 5:
            continue
        if any(ch in FORBIDDEN_KEYTERM_CHARS for ch in term):
            continue
        seen.add(term)
        terms.append(term)
        if len(terms) >= MAX_KEYTERMS:
            break
    return terms


def build_vendor_multipart(
    filename: str,
    audio: bytes,
    model: str,
    language: str | None,
    keyterms: list[str],
) -> tuple[bytes, str]:
    boundary = "----klor-openwhispr-" + secrets.token_hex(12)
    boundary_bytes = boundary.encode()
    chunks: list[bytes] = []

    def field(name: str, value: str) -> None:
        chunks.extend(
            [
                b"--" + boundary_bytes + b"\r\n",
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    field("model_id", model)
    # Keep only the two dictation-specific overrides that materially help:
    # no audio-event labels in text, and no unused word timestamps in the response.
    field("tag_audio_events", "false")
    field("timestamps_granularity", "none")
    if language:
        field("language_code", language)
    for term in keyterms:
        field("keyterms", term)

    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    safe_filename = os.path.basename(filename or "audio.webm").replace('"', "")
    chunks.extend(
        [
            b"--" + boundary_bytes + b"\r\n",
            (
                f'Content-Disposition: form-data; name="file"; filename="{safe_filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode(),
            audio,
            b"\r\n",
            b"--" + boundary_bytes + b"--\r\n",
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def transcribe(
    audio: bytes,
    filename: str,
    model: str,
    language: str | None,
    prompt: str | None,
) -> str:
    api_key = get_api_key()
    selected_model = model.strip() if model and model.strip().startswith("scribe_") else DEFAULT_MODEL
    keyterms = prompt_to_keyterms(prompt)
    body, content_type = build_vendor_multipart(
        filename, audio, selected_model, language, keyterms
    )

    request = urllib.request.Request(
        ELEVENLABS_URL,
        data=body,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Content-Type": content_type,
            "Accept": "application/json",
            "User-Agent": "klor-openwhispr-elevenlabs/1",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"ElevenLabs returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach ElevenLabs: {exc.reason}") from exc

    text = payload.get("text")
    if not isinstance(text, str):
        raise RuntimeError("ElevenLabs response did not contain a text transcript")
    return text


class ShimHandler(BaseHTTPRequestHandler):
    server_version = "KlorOpenWhisprElevenLabs/1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[openwhispr-elevenlabs] {self.address_string()} - {fmt % args}", flush=True)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/health":
            self._send_json(404, {"error": "not found"})
            return
        try:
            get_api_key()
            configured = True
        except RuntimeError:
            configured = False
        self._send_json(200, {"ok": True, "elevenlabs_key_configured": configured})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") not in ("/audio/transcriptions", "/v1/audio/transcriptions"):
            self._send_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "invalid Content-Length"})
            return
        if length <= 0:
            self._send_json(400, {"error": "empty body"})
            return
        if length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "request body too large"})
            return

        try:
            fields, files = parse_multipart_form(
                self.rfile.read(length), self.headers.get("Content-Type", "")
            )
        except ValueError as exc:
            self._send_json(400, {"error": f"bad multipart: {exc}"})
            return

        if "file" not in files:
            self._send_json(400, {"error": "missing 'file' field"})
            return

        filename, audio = files["file"]
        try:
            text = transcribe(
                audio=audio,
                filename=filename,
                model=fields.get("model", ""),
                language=fields.get("language") or None,
                prompt=fields.get("prompt") or None,
            )
            self._send_json(200, {"text": text, "object": "transcription"})
        except Exception as exc:
            self._send_json(502, {"error": f"transcription failed: {exc}"})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ShimHandler)
    server.daemon_threads = True
    print(
        f"OpenWhispr ElevenLabs adapter listening on http://{HOST}:{PORT}\n"
        "Configure OpenWhispr: Speech to Text -> Self-Hosted -> "
        f"http://{HOST}:{PORT}, model {DEFAULT_MODEL}.",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
