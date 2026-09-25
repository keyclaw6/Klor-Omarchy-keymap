#!/usr/bin/env python3
"""Run the actual KLOR control C with deterministic keymap, USB and timer doubles.

python3 zmk/tests/test_control.py [--source /path/to/klor_omarchy.c]
These check port decisions and output packets; firmware builds and hardware
checks separately validate the real ZMK event ordering and USB transport.
"""
from pathlib import Path
import argparse
import re
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "module/src/klor_omarchy.c"


class ControlBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="klor-control-")
        cls.addClassCleanup(cls.directory.cleanup)
        root = Path(cls.directory.name)
        for header in re.findall(r"^#include <([^>]+)>", SOURCE.read_text(), re.M):
            if "/" not in header or header.startswith(("klor/", "dt-bindings/klor/")):
                continue
            target = root / header
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('#include "stubs.h"\n')
        cls.binary = root / "control_test"
        subprocess.run([
            "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-Wno-unused-const-variable", "-Wno-unused-function",
            "-I", str(root), "-I", str(HERE / "control"),
            "-I", str(SOURCE.parents[1] / "include"),
            f'-DKLOR_CONTROL_SOURCE="{SOURCE}"', str(HERE / "control/cases.c"),
            "-o", str(cls.binary),
        ], check=True)

    def check_case(self, name):
        result = subprocess.run([str(self.binary), name], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        print(result.stdout.strip())

    def test_training(self): self.check_case("training")
    def test_command(self): self.check_case("command")
    def test_stt(self): self.check_case("stt")
    def test_ralt(self): self.check_case("ralt")
    def test_nav(self): self.check_case("nav")
    def test_raw_hid(self): self.check_case("raw_hid")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--source", type=Path)
    options, remaining = parser.parse_known_args()
    if options.source:
        SOURCE = options.source.resolve()
    unittest.main(argv=[__file__, *remaining])
