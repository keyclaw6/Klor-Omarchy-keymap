/* SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/* ── Split: left half is USB master ── */
#define MASTER_LEFT

/* ── Encoders ── */
#define ENCODER_RESOLUTION 2

/* ── Tap-hold: Home Row Mods (canonical article baseline) ── */
#define TAPPING_TERM 250
#ifndef PERMISSIVE_HOLD
#    define PERMISSIVE_HOLD
#endif
#define QUICK_TAP_TERM 0
#ifndef CHORDAL_HOLD
#    define CHORDAL_HOLD
#endif
#ifndef FLOW_TAP_TERM
#    define FLOW_TAP_TERM 150
#endif
#ifndef SPECULATIVE_HOLD
#    define SPECULATIVE_HOLD
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

/* ── Pointing device (not installed — guarded so it compiles cleanly) ── */
#ifdef POINTING_DEVICE_ENABLE
#    define SPLIT_POINTING_ENABLE
#    define POINTING_DEVICE_RIGHT
#    define POINTING_DEVICE_ROTATION_270
#endif
