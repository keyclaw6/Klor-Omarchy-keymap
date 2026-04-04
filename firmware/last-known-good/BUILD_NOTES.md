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

## Build validation (2026-04-04)

Re-validated compilation of the last known good keymap against latest QMK master.

- **QMK CLI**: 1.2.0
- **ARM toolchain**: arm-none-eabi-gcc 13.2.1 20231009
- **Build command**: `qmk compile -kb geigeigeist/klor/2040 -km zynex`
- **Result**: Success — no changes required beyond the two callback renames already present.
- **Artifact**: `firmware/last-known-good/geigeigeist_klor_2040_zynex.uf2` (131072 bytes)

## Latency fix (2026-04-04)

### Symptom
3–4 second delay between keypress and character appearing on screen.

### Root cause
The upstream KLOR keyboard.json enables `haptic: true` with driver `drv2605l` (I2C).
The DRV2605L chip is **not physically present** on this Polydactyl board. Every I2C
transaction to the missing device blocks for its timeout duration, stalling the matrix
scan loop and causing massive input latency on every keypress.

Additionally, `rgb_matrix: true` (WS2812) and `audio: true` (from 2040/rules.mk
overriding keyboard.json) were enabled for hardware not installed on this board.

### Fix applied
Added three lines to keymap-level `rules.mk`:
```
HAPTIC_ENABLE = no     # DRV2605L not present → I2C timeout elimination (primary fix)
RGB_MATRIX_ENABLE = no # WS2812 LEDs not installed
AUDIO_ENABLE = no      # Buzzer not installed
```

No layout, layer, or key behavior changes were made.

### Result
- Firmware size reduced from 131,072 → 100,352 bytes (~30KB of unused driver code removed)
- DRV2605L, RGB matrix, and audio drivers confirmed excluded from compiled binary

## Flashing

Put the KLOR into bootloader mode (hold BOOT while plugging in USB, or press QK_BOOT from the ADJUST layer), then copy the `.uf2` file to the RP2040 mass storage device.

## Minimal Omarchy adaptation (2026-04-04)

### Baseline used
- `keyboards/geigeigeist/klor/keymaps/zynex/keymap.c` (last known good with `_user` callback fixes)
- `keyboards/geigeigeist/klor/keymaps/zynex/rules.mk` (with haptic/RGB/audio disabled)
- `keyboards/geigeigeist/klor/keymaps/zynex/config.h` (unchanged)

### Omarchy changes applied
1. **Added `_OMARCHY` layer enum** (index 4, after `_ADJUST`) — required to define the new layer.
2. **Replaced `KC_RSFT` with `MO(_OMARCHY)`** on the base layer right-bottom position — this is the Omarchy layer trigger key (hold to access Omarchy shortcuts).
3. **Added `_OMARCHY` layer definition** with 17 Omarchy utility shortcuts mapped to the top two rows, matching the design in `KLOR_OMARCHY_REVISION.md`:
   - Top row: launcher, system menu, capture menu, toggle menu, keybindings, waybar toggle, dismiss notification, dismiss all, invoke notification, restore notification
   - Home row: audio controls, bluetooth, wifi, activity monitor, nightlight toggle, idle toggle
4. **Added OLED case** for layer 4 → displays "OMARCHY" on the primary OLED.

### Intentionally NOT changed
- LOWER, RAISE, ADJUST layers — untouched
- Numpad keycodes (`KC_P*`) — working with NumLock-on-boot, not worth the risk
- Timing settings, tapping term, combos, key overrides — untouched
- Encoder behavior — untouched
- rules.mk, config.h — untouched
- Haptic/RGB/Audio disable lines — untouched (the latency fix)
- SNAP2 screenshot macro — untouched
- Trackball / pointing device code — untouched

### Build command
```
qmk compile -kb geigeigeist/klor/2040 -km zynex
```

### Build result
- **Status**: Success
- **Artifact**: `artifacts/geigeigeist_klor_2040_zynex.uf2` (100,864 bytes)
