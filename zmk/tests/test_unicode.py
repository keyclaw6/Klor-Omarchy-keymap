#!/usr/bin/env python3
"""Compile and exercise the real Unicode behavior with deterministic HID stubs.

Run: python3 zmk/tests/test_unicode.py
No Zephyr SDK is needed. Firmware builds still verify the actual ZMK APIs.
"""

from pathlib import Path
import re
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "module/src/behavior_klor_unicode.c"

STUBS = r"""
#pragma once

#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define LOG_MODULE_DECLARE(...)
#define LOG_WRN(...) ((void)0)
#define BUILD_ASSERT(x, ...) _Static_assert(x, "build assertion")
#define IS_ENABLED(x) x
#define CONFIG_ZMK_HID_REPORT_TYPE_HKRO 1
#define ARG_UNUSED(x) (void)x
#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))
#define BIT(x) (1u << (x))
#define MOD_LSFT 2
#define MOD_RSFT 32
#define MOD_LCTL 1
#define HID_USAGE_KEY 7
#define HID_USAGE_KEY_KEYBOARD_U 24
#define HID_USAGE_KEY_KEYBOARD_CAPS_LOCK 57
#define HID_USAGE_KEY_KEYBOARD_0_AND_RIGHT_PARENTHESIS 39
#define HID_USAGE_KEY_KEYBOARD_1_AND_EXCLAMATION 30
#define HID_USAGE_KEY_KEYBOARD_A 4
#define HID_USAGE_KEY_KEYBOARD_SPACEBAR 44
#define ZMK_BEHAVIOR_OPAQUE 0
#define BEHAVIOR_LOCALITY_CENTRAL 0
#define DT_INST_FOREACH_STATUS_OKAY(x)
struct zmk_behavior_binding {
  uint32_t param1, param2;
};
struct zmk_behavior_binding_event {
  int ignored;
};
struct zmk_hid_keyboard_report {
  uint8_t report_id;
  struct {
    uint8_t modifiers, reserved, keys[6];
  } body;
};
struct behavior_driver_api {
  int (*binding_pressed)(struct zmk_behavior_binding *,
                         struct zmk_behavior_binding_event);
  int (*binding_released)(struct zmk_behavior_binding *,
                          struct zmk_behavior_binding_event);
  int locality;
};
static struct zmk_hid_keyboard_report report, reports[64];
static unsigned count, delay_ms;
static uint8_t indicators;
static int failed_send;
static struct zmk_hid_keyboard_report *zmk_hid_get_keyboard_report(void) {
  return &report;
}
static uint8_t zmk_hid_indicators_get_current_profile(void) {
  return indicators;
}
static int zmk_endpoint_send_report(unsigned page) {
  assert(page == 7);
  assert(count < 64);
  reports[count++] = report;
  return failed_send ? -ENODEV : 0;
}
static void k_msleep(unsigned ms) {
  assert(ms == 10);
  delay_ms += ms;
}
/* SPDX-License-Identifier: MIT */
"""

CASES = r"""
static void test(uint32_t lo, uint32_t hi, uint8_t mods, bool caps, bool fail) {
  count = delay_ms = 0;
  indicators = caps ? 2 : 0;
  failed_send = fail;
  report = (struct zmk_hid_keyboard_report){
      .report_id = 1, .body = {.modifiers = mods, .keys = {20, 26}}};
  struct zmk_hid_keyboard_report saved = report;
  struct zmk_behavior_binding binding = {lo, hi};
  assert(on_unicode_pressed(&binding, (struct zmk_behavior_binding_event){0}) ==
         0);
  assert(!memcmp(&saved, &report, sizeof report));
  assert(!memcmp(&saved, &reports[count - 1], sizeof report));
  bool shifted = !!(mods & (2 | 32));
  uint32_t cp = shifted ^ caps ? hi : lo;
  unsigned out = 0, caps_taps = 0;
  char hex[5] = {0};
  for (unsigned i = 0; i + 1 < count; i++) {
    assert(reports[i].report_id == 1);
    assert(reports[i].body.keys[0] == 20);
    assert(reports[i].body.keys[1] == 26);
    uint8_t key = reports[i].body.keys[2];
    for (unsigned j = 3; j < 6; j++)
      assert(reports[i].body.keys[j] == 0);
    if (!key) {
      assert(reports[i].body.modifiers == 0);
      continue;
    }
    if (key == 24) {
      assert(reports[i].body.modifiers == 3);
      continue;
    }
    assert(reports[i].body.modifiers == 0);
    if (key == 57) {
      caps_taps++;
      continue;
    }
    if (key == 44) {
      assert(out == 4);
      continue;
    }
    assert(out < 4);
    hex[out++] = key == 39                ? '0'
                 : key >= 30 && key <= 38 ? '1' + key - 30
                                          : 'a' + key - 4;
  }
  char expected[5];
  snprintf(expected, sizeof expected, "%04x", cp);
  assert(!strcmp(hex, expected));
  assert(caps_taps == (caps ? 2 : 0));
  assert(delay_ms == (caps ? 170 : 130));
  assert(on_unicode_released(&binding,
                             (struct zmk_behavior_binding_event){0}) == 0);
}
int main(void) {
  unsigned cases = 0;
  const unsigned points[][2] = {{0xe5, 0xc5}, {0xe6, 0xc6}, {0xf8, 0xd8}};
  const uint8_t mods[] = {0, 2, 32, 1, 4, 8, 1 | 4 | 8 | 2, 1 | 4 | 8 | 32};
  for (unsigned p = 0; p < 3; p++)
    for (unsigned m = 0; m < 8; m++)
      for (unsigned c = 0; c < 2; c++)
        for (unsigned f = 0; f < 2; f++) {
          test(points[p][0], points[p][1], mods[m], c, f);
          cases++;
        }
  assert(cases == 96);
  /* A full report must not begin a partial Unicode sequence. */
  count = 0;
  report = (struct zmk_hid_keyboard_report){.report_id=1,
      .body={.modifiers=13, .keys={4,5,6,7,8,9}}};
  struct zmk_hid_keyboard_report full = report;
  struct zmk_behavior_binding pair = {0xe5,0xc5};
  assert(on_unicode_pressed(&pair,(struct zmk_behavior_binding_event){0}) == 0);
  assert(count == 0 && !memcmp(&report,&full,sizeof full));
  /* A physically held hex key stays down: it cannot gain a second down edge. */
  count=0; indicators=0; failed_send=0;
  report=(struct zmk_hid_keyboard_report){.report_id=1,.body={.keys={8}}};
  assert(on_unicode_pressed(&pair,(struct zmk_behavior_binding_event){0}) == 0);
  for(unsigned i=0;i<count;i++) {
    unsigned duplicates=0;
    assert(reports[i].body.keys[0]==8);
    for(unsigned k=0;k<6;k++) duplicates += reports[i].body.keys[k]==8;
    assert(duplicates==1);
  }
  pair.param1=pair.param2=0xD800; count=0;
  assert(on_unicode_pressed(&pair,(struct zmk_behavior_binding_event){0}) == -EINVAL);
  assert(count==0);

  puts(
      "PASS: 96 Unicode report sequences (three letters, Shift/Caps "
      "combinations, held mods, transport failures), exact report restoration");
  return 0;
}
"""


class UnicodeReports(unittest.TestCase):
    def test_linux_sequence_and_restoration(self):
        with tempfile.TemporaryDirectory(prefix="klor-unicode-") as directory:
            root = Path(directory)
            (root / "stubs.h").write_text(STUBS)
            for header in re.findall(r"^#include <([^>]+)>", SOURCE.read_text(), re.M):
                if "/" not in header:
                    continue
                target = root / header
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('#include "stubs.h"\n')
            harness = root / "unicode_test.c"
            harness.write_text(f'#include "{SOURCE}"\n' + CASES)
            binary = root / "unicode_test"
            subprocess.run([
                "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                "-Wno-unused-const-variable", "-I", str(root),
                str(harness), "-o", str(binary),
            ], check=True)
            result = subprocess.run([str(binary)], check=False, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("96 Unicode report sequences", result.stdout)
            print(result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
