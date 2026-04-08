/* SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/* ── Vial UID (unique per keyboard model) ── */
#define VIAL_KEYBOARD_UID {0xEA, 0x0C, 0x5B, 0x83, 0xDC, 0xA3, 0x5C, 0x35}

/* ── Vial unlock combo: Q (0,1) + P (4,1) ── */
#define VIAL_UNLOCK_COMBO_ROWS { 0, 4 }
#define VIAL_UNLOCK_COMBO_COLS { 1, 1 }

/* ── Split: left half is USB master ── */
#define MASTER_LEFT

/* ── Encoders ── */
#define ENCODER_RESOLUTION 2

/* ── Tap-hold: Home Row Mods (Flow Tap + Chordal Hold + HOOKE) ── */
#define TAPPING_TERM 200
#define QUICK_TAP_TERM 0
#ifndef CHORDAL_HOLD
#    define CHORDAL_HOLD
#endif
#define HOLD_ON_OTHER_KEY_PRESS
#ifndef FLOW_TAP_TERM
#    define FLOW_TAP_TERM 150
#endif

/* ── Auto Shift (not enabled in rules.mk — retained for future use) ── */
#define NO_AUTO_SHIFT_ALPHA
#define AUTO_SHIFT_TIMEOUT TAPPING_TERM
#ifndef AUTO_SHIFT_NO_SETUP
#    define AUTO_SHIFT_NO_SETUP
#endif

/* ── Save space ── */
#undef LOCKING_SUPPORT_ENABLE
#undef LOCKING_RESYNC_ENABLE

/* ── One-shot keys (OSM/OSL) ── */
#define ONESHOT_TIMEOUT 3000       // Cancel if no key pressed within 3s
#define ONESHOT_TAP_TOGGLE 2       // Double-tap OSM = toggle (caps lock)

/* ── Unicode (Danish æ ø å via Ctrl+Shift+U on Linux/GTK) ── */
#define UNICODE_SELECTED_MODES UNICODE_MODE_LINUX
#define UNICODE_TYPE_DELAY 10      // Safety margin for Wayland apps

/* ── Vial dynamic feature slots ── */
#define DYNAMIC_KEYMAP_LAYER_COUNT 5
#define VIAL_COMBO_ENTRIES 8
#define VIAL_TAP_DANCE_ENTRIES 8
#define VIAL_KEY_OVERRIDE_ENTRIES 4

/* ── Vial manages combos/key overrides dynamically ── */
/* VIAL_COMBO_ENABLE and VIAL_KEY_OVERRIDE_ENABLE are auto-defined
   by vial.h when COMBO_ENABLE / KEY_OVERRIDE_ENABLE are set in rules.mk.
   No manual defines needed here. */

/* ── Pointing device (not installed — guarded so it compiles cleanly) ── */
#ifdef POINTING_DEVICE_ENABLE
#    define SPLIT_POINTING_ENABLE
#    define POINTING_DEVICE_RIGHT
#    define POINTING_DEVICE_ROTATION_270
#endif
