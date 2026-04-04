#pragma once

/* The way how "handedness" is decided (which half is which),
see https://docs.qmk.fm/#/feature_split_keyboard?id=setting-handedness
for more options.
*/

#define MASTER_LEFT
// #define MASTER_RIGHT


// ── Tap-hold: Home Row Mods (Flow Tap + Chordal Hold + HOOKE) ──
#define TAPPING_TERM 200
#define QUICK_TAP_TERM 0        // Disable auto-repeat on mod-taps (fixes camelCase)
#define CHORDAL_HOLD             // Same-hand tap-then-tap = typing; opposite-hand = defer to HOOKE
#define HOLD_ON_OTHER_KEY_PRESS  // Instant modifier activation (safe with Chordal Hold guard)
#define FLOW_TAP_TERM 150        // Fast typing bypass: alpha within 150ms of previous = always tap

// Auto Shift
#define NO_AUTO_SHIFT_ALPHA
#define AUTO_SHIFT_TIMEOUT TAPPING_TERM
#define AUTO_SHIFT_NO_SETUP

#undef LOCKING_SUPPORT_ENABLE
#undef LOCKING_RESYNC_ENABLE
#define NO_ACTION_ONESHOT
//#define NO_ACTION_TAPPING
//#define NO_MUSIC_MODE

#define COMBO_COUNT 1


#ifdef POINTING_DEVICE_ENABLE
//#    define POINTING_DEVICE_ROTATION_90
#    define SPLIT_POINTING_ENABLE
#    define POINTING_DEVICE_RIGHT
#    define POINTING_DEVICE_ROTATION_270
#endif



