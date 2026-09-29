#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_PATH = os.path.join(HERE, "openwhispr_elevenlabs_shim.py")
spec = importlib.util.spec_from_file_location("openwhispr_elevenlabs_shim", MODULE_PATH)
shim = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = shim
spec.loader.exec_module(shim)

CRLF = b"\r\n"


def multipart(boundary: bytes, parts) -> bytes:
    out = []
    for name, filename, content, content_type in parts:
        out.append(b"--" + boundary + CRLF)
        disp = b'Content-Disposition: form-data; name="' + name.encode() + b'"'
        if filename is not None:
            disp += b'; filename="' + filename.encode() + b'"'
        out.append(disp + CRLF)
        if content_type:
            out.append(b"Content-Type: " + content_type + CRLF)
        out.append(CRLF)
        out.append(content + CRLF)
    out.append(b"--" + boundary + b"--" + CRLF)
    return b"".join(out)


class MultipartTests(unittest.TestCase):
    def test_roundtrip(self):
        audio = b"\x00OggS\r\n\x01binary\xff"
        body = multipart(
            b"B1",
            [
                ("file", "audio.webm", audio, b"audio/webm"),
                ("model", None, b"scribe_v2", None),
                ("language", None, b"da", None),
                ("prompt", None, "ZynexGroup, OpenWhispr".encode(), None),
            ],
        )
        fields, files = shim.parse_multipart_form(body, "multipart/form-data; boundary=B1")
        self.assertEqual(files["file"], ("audio.webm", audio))
        self.assertEqual(fields["language"], "da")
        self.assertEqual(fields["prompt"], "ZynexGroup, OpenWhispr")

    def test_missing_boundary(self):
        with self.assertRaises(ValueError):
            shim.parse_multipart_form(b"x", "application/json")


class KeytermTests(unittest.TestCase):
    def test_prompt_conversion(self):
        self.assertEqual(
            shim.prompt_to_keyterms("ZynexGroup, OpenWhispr; Omarchy\nElevenLabs"),
            ["ZynexGroup", "OpenWhispr", "Omarchy", "ElevenLabs"],
        )

    def test_filters_invalid_and_duplicates(self):
        self.assertEqual(
            shim.prompt_to_keyterms("good, good, bad[term], one two three four five six"),
            ["good"],
        )


class CredentialTests(unittest.TestCase):
    def test_env_precedes_keyring(self):
        with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": "env-key"}, clear=False):
            with mock.patch.object(shim.keyring, "get_password", return_value="ring-key"):
                self.assertEqual(shim.get_api_key(), "env-key")

    def test_existing_klor_keyring_is_reused(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(shim.keyring, "get_password", return_value="ring-key") as get:
                self.assertEqual(shim.get_api_key(), "ring-key")
                get.assert_called_once_with("klor-bridge", "elevenlabs_key")


class VendorMultipartTests(unittest.TestCase):
    def test_contains_scribe_controls(self):
        body, content_type = shim.build_vendor_multipart(
            "audio.webm", b"abc", "scribe_v2", "da", ["ZynexGroup"]
        )
        self.assertIn("multipart/form-data; boundary=", content_type)
        for expected in (
            b'name="model_id"',
            b"scribe_v2",
            b'name="no_verbatim"',
            b'name="language_code"',
            b"da",
            b'name="keyterms[]"',
            b"ZynexGroup",
            b'name="file"; filename="audio.webm"',
            b"abc",
        ):
            self.assertIn(expected, body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
