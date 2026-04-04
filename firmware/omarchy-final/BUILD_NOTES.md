# Full Omarchy Implementation — Final Build

## Baseline used

- **Source**: `keyboards/geigeigeist/klor/keymaps/zynex/` (post-minimal Omarchy adaptation)
- **Why**: This was the successfully compiled keymap from the minimal Omarchy adaptation pass, which added the `_OMARCHY` layer, fixed `_user` callbacks, and included the latency fix (haptic/RGB/audio disabled).

## Changes from minimal pass

### 1. Keypad digits → standard number keycodes (LOWER layer)

Replaced all numpad keycodes with their standard equivalents:

| Position | Before | After |
|----------|--------|-------|
| Row 1 | `KC_P7`, `KC_P8`, `KC_P9` | `KC_7`, `KC_8`, `KC_9` |
| Row 2 | `KC_P4`, `KC_P5`, `KC_P6` | `KC_4`, `KC_5`, `KC_6` |
| Row 3 | `KC_P1`, `KC_P2`, `KC_P3` | `KC_1`, `KC_2`, `KC_3` |
| Thumb | `KC_P0` | `KC_0` |

`KC_PPLS` (keypad +) and `KC_PAST` (keypad *) were kept — these operator keys are **not** affected by NumLock state and work consistently across all platforms.

**Why**: Standard number keycodes work identically on Omarchy/Hyprland, Ubuntu, and Windows regardless of NumLock state. Keypad digits become navigation keys when NumLock is off. Standard digits also enable `SUPER + 1-9` workspace switching via Hyprland when holding Super on the host side.

### 2. Removed NumLock-on-boot hack

Removed the `keyboard_post_init_user()` function that forced NumLock ON at startup. This was only needed because the old keypad digits required NumLock to function as numbers. With standard keycodes, this is no longer necessary.

### 3. Disabled OLED support

- Changed `OLED_ENABLE = yes` → `OLED_ENABLE = no` in `rules.mk`
- Removed `OLED_DRIVER = ssd1306` line from `rules.mk`
- Wrapped `#include "zynex_logo.h"` in `#ifdef OLED_ENABLE` guard in `keymap.c`

All OLED rendering code in `keymap.c` was already behind `#ifdef OLED_ENABLE` preprocessor guards, so it is automatically excluded from compilation. The keyboard-level OLED code in `klor.c` is similarly guarded.

**Why**: The user does not use the OLED display. Disabling it reduces firmware size and removes unnecessary I2C traffic.

## What was NOT changed

- **QWERTY base layer**: Unchanged (including `MO(_OMARCHY)` at right Shift)
- **RAISE layer**: Unchanged (symbols and international characters)
- **ADJUST layer**: Unchanged (function keys and QK_BOOT)
- **OMARCHY layer**: Unchanged (17 utility shortcuts from minimal pass)
- **Encoder behavior**: Unchanged (volume control on both encoders)
- **Combos**: Unchanged (TAB + Q = ESC)
- **Key overrides**: Unchanged (GUI + S = CTRL + S)
- **SNAP2 macro**: Unchanged (SHIFT + WIN + S screenshot)
- **Trackball/pointing device code**: Unchanged
- **Latency fix**: Unchanged (HAPTIC_ENABLE, RGB_MATRIX_ENABLE, AUDIO_ENABLE all remain `no`)
- **config.h**: Unchanged
- **Tapping term / auto-shift settings**: Unchanged

## Build

```
qmk compile -kb geigeigeist/klor/2040 -km zynex
```

- **QMK CLI**: 1.2.0
- **ARM toolchain**: arm-none-eabi-gcc 13.2.1
- **Result**: Success
- **Artifact**: `firmware/omarchy-final/geigeigeist_klor_2040_zynex.uf2` (86,528 bytes)

### Firmware size comparison

| Version | Size |
|---------|------|
| Last known good (4-layer, OLED enabled) | 131,072 bytes |
| Minimal Omarchy pass (5-layer, OLED enabled) | 100,864 bytes |
| **Full Omarchy final (5-layer, OLED disabled)** | **86,528 bytes** |

## Flashing

1. Put the KLOR into bootloader mode:
   - Hold BOOT while plugging in USB, **or**
   - Press QK_BOOT from the ADJUST layer (hold LOWER + RAISE, then press bottom-left key)
2. Copy `geigeigeist_klor_2040_zynex.uf2` to the RP2040 mass storage device
3. The keyboard will reboot automatically

## Flash/test checklist

- [ ] Numbers 0-9 work on LOWER layer (no NumLock dependency)
- [ ] SUPER + 1-9 switches Omarchy workspaces (hold SUPER on host, press LOWER + number position)
- [ ] Omarchy layer activates when holding right-bottom key (old right Shift position)
- [ ] Launcher opens (Omarchy layer + Q position = SUPER + SPACE)
- [ ] System menu opens (Omarchy layer + W position = SUPER + ESC)
- [ ] Base layer typing works normally
- [ ] Encoders control volume
- [ ] TAB + Q combo sends ESC
- [ ] No input latency (haptic driver still disabled)
- [ ] OLED is off (expected — disabled in firmware)
