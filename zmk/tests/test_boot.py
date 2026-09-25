#!/usr/bin/env python3
"""Exercise the real per-half boot listener with host stubs, without Zephyr."""

from pathlib import Path
import re
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "module/src/klor_boot.c"

STUBS = r"""
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <stdio.h>
#define ZMK_EV_EVENT_BUBBLE 0
#define ZMK_POSITION_STATE_CHANGE_SOURCE_LOCAL 255
#define BOOT_MODE_TYPE_BOOTLOADER 1
#define SYS_REBOOT_WARM 0
#define LOG_ERR(...) ((void)0)
#define LOG_MODULE_REGISTER(...)
#define ZMK_LISTENER(...)
#define ZMK_SUBSCRIPTION(...)
struct zmk_position_state_changed {
    uint8_t source;
    uint32_t position;
    bool state;
    int64_t timestamp;
};
typedef struct zmk_position_state_changed zmk_event_t;
static const struct zmk_position_state_changed *as_zmk_position_state_changed(const zmk_event_t *ev) {
    return ev;
}
static int reboots, boot_error;
static int bootmode_set(int mode) {
    assert(mode == BOOT_MODE_TYPE_BOOTLOADER);
    return boot_error;
}
static void sys_reboot(int mode) {
    assert(mode == SYS_REBOOT_WARM);
    reboots++;
}
"""

CASES = r"""
static void reset(void) {
    for (int i = 0; i < 8; i++) boot_thumb_down[i] = false;
    boot_combo_held = false;
    boot_combo_count = 0;
    boot_combo_started = 0;
    reboots = 0;
    boot_error = 0;
}
static void thumbs(int first, bool down, int64_t at, uint8_t source) {
    for (int i = first; i < first + 4; i++) {
        zmk_event_t ev = {.source=source, .position=i, .state=down, .timestamp=at};
        assert(boot_combo_listener(&ev) == ZMK_EV_EVENT_BUBBLE);
    }
}
int main(void) {
    /* The central transform maps left thumbs to 36..39; the peripheral's
     * row-offset maps its own four physical thumbs to 40..43. */
    for (int half = 36; half <= 40; half += 4) {
        reset();
        for (int i = 0; i < 5; i++) {
            thumbs(half, true, i * 750, 255);
            assert(reboots == (i == 4));
            thumbs(half, false, i * 750 + 1, 255);
        }
        assert(reboots == 1); /* Exactly 3000 ms is inside the QMK window. */

        reset();
        for (int i = 0; i < 5; i++) {
            thumbs(half, true, i * 751, 255);
            thumbs(half, false, i * 751 + 1, 255);
        }
        assert(reboots == 0);
        assert(boot_combo_count == 1); /* Expired window starts over. */

        reset();
        for (int i = 0; i < 10; i++) thumbs(half, true, i, 255);
        assert(boot_combo_count == 1); /* Held repeats cannot count as taps. */
        assert(!reboots);

        reset();
        for (int i = 0; i < 5; i++) {
            thumbs(half, true, i * 10, 0);
            thumbs(half, false, i * 10 + 1, 0);
        }
        assert(!boot_combo_count); /* Split source 0 cannot reboot central. */
        assert(!reboots);

        reset();
        boot_error = -1;
        for (int i = 0; i < 5; i++) {
            thumbs(half, true, i * 10, 255);
            thumbs(half, false, i * 10 + 1, 255);
        }
        assert(!reboots);
        assert(!boot_combo_count); /* Failed boot-mode request is retryable. */

        reset();
        for (int i = 0; i < 4; i++) {
            thumbs(half, true, i * 10, 255);
            thumbs(half, false, i * 10 + 1, 255);
        }
        thumbs(half, true, 40, 0);
        assert(!reboots);
        thumbs(half, true, 41, 255);
        assert(reboots == 1); /* Only a local fifth gesture completes it. */
    }
    puts("both halves: window boundary, expiry, held repeats, remote sources, boot failure passed");
}
"""


class BootTests(unittest.TestCase):
    def test_actual_listener(self):
        source = re.sub(r"^#include[^\n]*\n", "", SOURCE.read_text(), flags=re.MULTILINE)
        with tempfile.TemporaryDirectory(prefix="klor-boot-") as directory:
            root = Path(directory)
            c_file = root / "test.c"
            binary = root / "test"
            c_file.write_text(STUBS + source + CASES)
            subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            str(c_file), "-o", str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    unittest.main()
