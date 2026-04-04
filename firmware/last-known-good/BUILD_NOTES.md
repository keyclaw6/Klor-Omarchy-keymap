# Last Known Good Build

## Source of truth

- **File used**: `known-good-klor/zynex/keymap.c` (and accompanying `config.h`, `rules.mk`, `zynex_logo.h`)
- **Why**: This is the original 4-layer keymap (QWERTY, LOWER, RAISE, ADJUST) archived from the user's Downloads folder — the version that was previously flashed and confirmed working on the physical KLOR keyboard.

## Changes made for compilation

Two minimal callback renames were required because `klor.c` already defines `_kb` versions of these functions, causing "multiple definition" linker errors:

1. `layer_state_set_kb` → `layer_state_set_user` (line ~280)
2. `oled_task_kb` → `oled_task_user` (line ~307), and removed the inner `oled_task_user()` delegation wrapper (since this function now *is* the user callback)

No layout, layer, or key behavior changes were made.

## Build command

```
qmk compile -kb geigeigeist/klor/2040 -km zynex
```

## Build result

- **Status**: Success
- **Artifact**: `firmware/last-known-good/geigeigeist_klor_2040_zynex.uf2`

## Flashing

Put the KLOR into bootloader mode (hold BOOT while plugging in USB, or press QK_BOOT from the ADJUST layer), then copy the `.uf2` file to the RP2040 mass storage device.
