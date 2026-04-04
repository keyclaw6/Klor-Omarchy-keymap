# Klor-Omarchy-keymap

QMK keymap for a KLOR split keyboard (42-key Polydactyl layout, RP2040) running on [Omarchy](https://omarchy.com) (Arch Linux + Hyprland).

## Hardware

- **Board:** KLOR by geigeigeist, Polydactyl variant (42 keys)
- **Controller:** RP2040
- **Encoders:** 2 (left = mute, right = play/pause; both scroll volume)

## Layers

| # | Name | Activation |
|---|------|-----------|
| 0 | `_QWERTY` | Default base layer |
| 1 | `_LOWER` | Hold left thumb `LOWER` key |
| 2 | `_RAISE` | Hold right thumb `RAISE` key |
| 3 | `_ADJUST` | Hold `LOWER` + `RAISE` together |
| 4 | `_NAV` | Hold bottom-right key (replaces right Shift) |

The **NAV layer** wraps every mapped key in `LGUI()`, so pressing a key on NAV sends `SUPER + keycode`. This gives direct access to Omarchy workspace switching (`SUPER+1`-`SUPER+0`), directional focus/swap (`SUPER+arrows`), and workspace cycling (`SUPER+TAB`) from a single held key. Add Shift/Alt/Ctrl for Omarchy's variant shortcuts (move-to-workspace, grouped windows, etc.).

## Build

### Standard QMK (zynex keymap)

```
qmk compile -kb geigeigeist/klor/2040 -km zynex
```

Output: `geigeigeist_klor_2040_zynex.uf2` (~85 KB)

### Vial (vial keymap)

Vial requires the [vial-qmk fork](https://github.com/vial-kb/vial-qmk), not stock QMK:

```bash
# Clone vial-qmk (separate from qmk_firmware — do NOT nest them)
git clone https://github.com/vial-kb/vial-qmk ~/vial-qmk
cd ~/vial-qmk && make git-submodule

# Copy this repo's keyboard definition into the vial-qmk tree
cp -r /path/to/this/repo/keyboards/geigeigeist ~/vial-qmk/keyboards/

# Build the Vial firmware (use make, not qmk compile)
make geigeigeist/klor/2040:vial
```

Output: `geigeigeist_klor_2040_vial.uf2` (~110 KB)

### Flashing

Flash by holding BOOT + tapping RESET on the keyboard, then copying the UF2 to the mounted `RPI-RP2` drive.

### Using Vial

After flashing the Vial firmware, open [Vial](https://get.vial.today/) (desktop app or [vial.rocks](https://vial.rocks) web app). The keyboard will be auto-detected. You can remap keys, configure combos, tap dance, encoders, and tune HRM settings — all in real time without reflashing.

## Repo Structure

```
keyboards/geigeigeist/klor/           # Full board definition (from QMK upstream)
  keymaps/zynex/
    keymap.c                           # Active keymap (5 layers, combos, macros, home row mods)
    config.h                           # Keymap config (tap-hold: Flow Tap + Chordal Hold + HOOKE)
    rules.mk                           # Build flags (KEY_OVERRIDE_ENABLE=no, OLED_ENABLE=no)
    zynex_logo.h                       # OLED logo (dead code, kept behind #ifdef)
  keymaps/vial/
    keymap.c                           # Vial-compatible keymap (MO() layers, encoder map, QK_KB_0)
    config.h                           # Vial UID, unlock combo, HRM config, dynamic feature slots
    rules.mk                           # VIA_ENABLE + VIAL_ENABLE + feature flags
    vial.json                          # Keyboard layout definition for Vial GUI

firmware/home-row-mods/
  geigeigeist_klor_2040_zynex.uf2     # Stock QMK firmware with HRM (84,992 bytes)

firmware/nav-layer/
  geigeigeist_klor_2040_zynex.uf2     # Previous firmware — rollback target (81,920 bytes)

firmware/vial/
  geigeigeist_klor_2040_vial.uf2      # Vial firmware (112,640 bytes)

artifacts/
  geigeigeist_klor_2040_zynex_hrm.uf2 # Artifact copy of stock QMK firmware
  geigeigeist_klor_2040_zynex_nav.uf2 # Artifact copy of previous firmware
  geigeigeist_klor_2040_vial.uf2      # Artifact copy of Vial firmware
```

## Documentation

| File | Purpose |
|------|---------|
| [KLOR_KEYMAP_OVERVIEW.md](KLOR_KEYMAP_OVERVIEW.md) | Human-readable layer diagrams and key maps |
| [OMARCHY_SHORTCUT_MAP.md](OMARCHY_SHORTCUT_MAP.md) | Comprehensive Omarchy keybinding reference |
| [OMARCHY_BINDING_MANIFEST.md](OMARCHY_BINDING_MANIFEST.md) | Source-annotated inventory of all Omarchy bindings |
| [OMARCHY_BINDING_CONFLICTS.md](OMARCHY_BINDING_CONFLICTS.md) | Known binding conflicts between keyboard and Omarchy |

## QMK Baseline

- **QMK repo:** `qmk_firmware`
- **Commit:** `1426eedfc1`
- **Branch:** `master`
- **Tracked subtree:** `keyboards/geigeigeist/klor/`

## Notable Design Decisions

1. **Home Row Mods (GACS order)** — The home row keys (A, S, D, F / J, K, L, ;) are dual-function: tap for the letter, hold for a modifier. Uses the "Modern Safe" approach with three layers of protection against misfires: Flow Tap (fast typing bypass), Chordal Hold (same-hand = tap), and Hold On Other Key Press (instant opposite-hand activation). See `KLOR_KEYMAP_OVERVIEW.md` for details.

2. **Right Shift replaced with `MO(_NAV)`** — The bottom-right key on QWERTY activates the NAV layer instead of acting as right Shift. Right Shift was rarely used since the left thumb handles Shift for most shortcuts.

3. **No key overrides** — `KEY_OVERRIDE_ENABLE = no`. An earlier `sve_key_override` that converted `SUPER+S` to `Ctrl+S` was removed because it blocked Omarchy's scratchpad toggle.

4. **Standard number keycodes in LOWER** — Uses `KC_0`-`KC_9` (not keypad `KC_P0`-`KC_P9`) to eliminate NumLock dependency.

5. **OLED disabled** — `OLED_ENABLE = no`. All OLED code is behind `#ifdef` guards and compiles away cleanly.

6. **SNAP2 macro (LOWER bottom-left)** — Sends `Shift+Win+S` (Windows screenshot). Does nothing on Omarchy. Left in place for potential Windows use.

7. **Vial keymap as separate build target** — The `vial` keymap lives alongside `zynex`. It's built from the vial-qmk fork (not stock QMK) and converts all custom keycodes to standard QMK equivalents so Vial can remap them. The `zynex` keymap remains the stock QMK reference. Choose based on your preference: `zynex` for maximum QMK feature access (Chordal Hold, Flow Tap guaranteed), `vial` for runtime configurability through a GUI.

## Changelog

### Vial support (2026-04-04)

Added a `vial` keymap for real-time keyboard configuration through the [Vial](https://get.vial.today/) GUI:

- **New keymap:** `keyboards/geigeigeist/klor/keymaps/vial/` — built from the [vial-qmk](https://github.com/vial-kb/vial-qmk) fork
- **Layer switching:** Converted custom `LOWER`/`RAISE` keycodes to `MO(_LOWER)`/`MO(_RAISE)` + `TRI_LAYER_ENABLE` (standard QMK, Vial-visible)
- **Custom keycode:** `SNAP2` uses `QK_KB_0` (visible in Vial as "Screenshot" under User tab)
- **Encoder map:** Replaced `encoder_update_user` callback with `encoder_map` (per-layer, Vial-remappable)
- **Dynamic features:** Combos (8 slots), Tap Dance (8 slots), Key Overrides (4 slots), QMK Settings — all configurable through Vial GUI
- **Unlock combo:** Q + P (matrix positions [0,1] + [4,1])
- **Firmware size:** 112,640 bytes (110 KB) — 5.4% of 2 MB flash
- **HRM preserved:** Full Chordal Hold + Flow Tap + HOOKE configuration carries over from `zynex`
- **Rollback:** Flash `firmware/home-row-mods/geigeigeist_klor_2040_zynex.uf2` to return to stock QMK

### Home Row Mods (2026-04-04)

Added home row mods to the QWERTY base layer using the "Modern Safe" approach:

- **Mod-tap keys:** `GUI/A`, `ALT/S`, `CTL/D`, `SFT/F` | `SFT/J`, `CTL/K`, `ALT/L`, `GUI/;` (GACS order)
- **Flow Tap** (`FLOW_TAP_TERM 150`): Fast typing automatically bypasses mod-tap — no lag or false triggers during normal typing
- **Chordal Hold**: Same-hand key after mod-tap = always tap; opposite-hand = modifier. Eliminates same-hand misfires entirely
- **Hold On Other Key Press**: Opposite-hand modifier activates instantly on key press (safe because Chordal Hold guards same-hand)
- **`QUICK_TAP_TERM 0`**: Disables auto-repeat on mod-taps (fixes accidental letter repeat in camelCase scenarios)
- **AltGr safety**: Right-hand Alt position (L) uses `LALT` instead of `RALT` to avoid conflicts with `RALT()` international characters on the RAISE layer
- Removed stale `TAPPING_FORCE_HOLD` define (silently ignored since QMK 0.20)
- **Rollback:** Flash `firmware/nav-layer/geigeigeist_klor_2040_zynex.uf2`

### Nav-layer redesign (2026-04-04)

Replaced the `_OMARCHY` layer with a new `_NAV` layer:

- **Removed:** `_OMARCHY` layer (had launcher/system/capture shortcuts that duplicated Omarchy's native `LGUI+key` behavior)
- **Added:** `_NAV` layer with LGUI-wrapped arrows (workspace focus/swap), numbers 0-9 (workspace switching), and TAB (workspace cycling)
- **Removed:** `sve_key_override` (`SUPER+S` -> `Ctrl+S`), disabled `KEY_OVERRIDE_ENABLE`
- **Result:** Cleaner 5-layer design. All common Omarchy shortcuts accessible via NAV hold + number/arrow, with Shift/Alt/Ctrl modifiers for variants.

### Full Omarchy implementation pass (2026-04-04)

- Replaced keypad keycodes (`KC_P0`-`KC_P9`) with standard (`KC_0`-`KC_9`) in LOWER layer
- Removed `keyboard_post_init_user()` NumLock-on-boot hack
- Disabled OLED support (`OLED_ENABLE = no`)

### Minimal rescue pass (2026-04-04)

- Fixed `layer_state_set_kb` -> `layer_state_set_user` (keymaps use `_user` callbacks)
- Confirmed `oled_task_user` rename was correct (`klor.c` already defines `oled_task_kb`)
- First successful compile of the Omarchy adaptation

### Initial snapshot

- Imported KLOR board definition and `zynex` keymap from QMK
- Added `_OMARCHY` layer (later replaced by `_NAV`)
