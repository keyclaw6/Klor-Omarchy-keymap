# 00 — State & Todo Log

<think>
Phase 1 reasoning: This document is the rigorous checklist that tracks every assumption
about the physical KLOR Polydactyl layout and every deliverable that must be produced.
It must capture the physical geometry, electrical matrix, key counts, and stagger data
so that subsequent phases can reference verified facts rather than guesswork.

Key facts to lock down:
- 42 usable keys from a 44-position matrix (2 encoder positions occupy matrix slots L35/R30)
- 8x6 matrix (rows 0-7, cols 0-5), split across two halves
- Column stagger derived from keyboard.json RGB y-coordinates
- Encoder positions are in the matrix but act as rotary encoders, not key switches
- 4 thumb keys per side in row 3 (left) / row 7 (right), cols 1-4
- Row 0 has no outer column (col 0 is KC_NO)
</think>

## Physical Layout Assumptions

### Hardware Identity
| Property         | Value                                              |
|------------------|----------------------------------------------------|
| Board            | KLOR Polydactyl (by Geigeigeist)                   |
| MCU              | RP2040 (Raspberry Pi Pico compatible)               |
| Split            | Wired, left half is USB master (`MASTER_LEFT`)      |
| USB VID/PID      | `0x3A3C` / `0x0001`                                |
| Key switches     | 42 (from 44-position matrix; 2 are encoder clicks)  |
| Encoders         | 2 rotary (1 per half)                               |
| OLED             | Not installed (`OLED_ENABLE = no`)                  |
| RGB              | Not installed (`RGB_MATRIX_ENABLE = no`)            |
| Pointing device  | Not installed                                       |

### Electrical Matrix (8 rows x 6 cols)

```
LEFT HALF                          RIGHT HALF
         Col0   Col1   Col2   Col3   Col4   Col5       Col0   Col1   Col2   Col3   Col4   Col5
Row 0:   ---    L01    L02    L03    L04    L05        ---    R04    R03    R02    R01    R00
Row 1:   L10    L11    L12    L13    L14    L15        R15    R14    R13    R12    R11    R10
Row 2:   L20    L21    L22    L23    L24    L25        R25    R24    R23    R22    R21    R20
Row 3:   ---    L31    L32    L33    L34    L35(enc)   ---    R34    R33    R32    R31    R30(enc)
```

Note: Right half columns are mirrored in the matrix definition (col5=inner, col0=outer).

### Physical Rows & Key Counts

| Physical Row | Left Keys | Right Keys | Total | Notes                                |
|--------------|-----------|------------|-------|--------------------------------------|
| Row 0 (top)  | 5         | 5          | 10    | No outer column (col 0 = KC_NO)     |
| Row 1 (home) | 6         | 6          | 12    | Has outer column                     |
| Row 2 (bot)  | 6 + enc   | 6 + enc    | 12+2  | Enc: L35=MUTE, R30=PLAY/PAUSE       |
| Thumb row    | 4         | 4          | 8     | L31-L34, R31-R34                     |
| **Total**    | **21+enc**| **21+enc** | **42+2** |                                   |

### Column Stagger (from keyboard.json RGB y-coordinates)

Using left-half RGB `y` values as proxy for vertical offset (lower y = higher physical position):

| Column Position | Label     | RGB y | Relative Stagger |
|-----------------|-----------|-------|-------------------|
| Middle finger   | Col 3 (E) | 0     | Highest           |
| Index finger    | Col 4 (R) | 6     | -6 from middle    |
| Inner column    | Col 5 (T) | 8     | -8 from middle    |
| Ring finger     | Col 2 (W) | 7     | -7 from middle    |
| Pinky finger    | Col 1 (Q) | 17    | -17 from middle   |
| Outer column    | Col 0 (TAB)| 28   | -28 from middle   |

### Encoder Physical Positions

| Encoder | Matrix Slot | Physical Location       | Default Function               |
|---------|-------------|-------------------------|--------------------------------|
| Left    | L35 (r3c5)  | Between row 2 & thumbs  | Vol-/Vol+ (NAV: Prev/Next WS)  |
| Right   | R30 (r7c5)  | Between row 2 & thumbs  | Bright-/Bright+ (NAV: Prev/Next WS) |

---

## Deliverable Checklist

| # | File                          | Status       | Description                                     |
|---|-------------------------------|--------------|-------------------------------------------------|
| 0 | `00_state_and_todo_log.md`    | COMPLETE     | This file. Physical layout assumptions.         |
| 1 | `01_klor_extraction_map.md`   | PENDING      | All layers, macros, combos, bridge headlines.   |
| 2 | `02_ascii_scale_strategy.md`  | PENDING      | 4K terminal math, cell dimensions, coordinates. |
| 3 | `03_validation_audit.md`      | PENDING      | Cross-reference extraction vs. scaling.         |
| 4 | `04_4k_klor_layout.txt`       | PENDING      | The massive 4K ASCII art cheat sheet.           |

---

## Verified Source Files

| File | Lines | Role |
|------|-------|------|
| `keymaps/vial/keymap.c` | 788 | Core: layers, command mode, NAV macros, HID, bootloader |
| `keymaps/vial/config.h` | 64 | HRM tuning, Unicode, Vial slots |
| `keymaps/vial/rules.mk` | 35 | Build feature flags |
| `2040/klor.h` | 105 | LAYOUT_polydactyl matrix mapping |
| `keyboard.json` | 167 | Physical positions, RGB coords, USB IDs |
| `bridge/actions.yml` | 195 | Action registry (9 active + 17 unconfigured) |
| `bridge/prompts.yml` | 130 | 7 LLM prompt templates + 1 STT postprocess |
| `bridge/snippets.yml` | 313 | 22 prompt snippets for picker |
| `bridge/config.yml` | 69 | Bridge/LLM/STT/platform config |
| `bridge/corrections.yml` | 45 | STT regex corrections (10 rules) |
| `bridge/lexicon.yml` | 58 | Domain vocabulary (4 categories) |
| `ARCHITECTURE.md` | 533 | System architecture reference |

---

## Constraints for Phase 5 (ASCII Art)

- Target: 42-inch 4K display (~3840x2160 pixels)
- Terminal assumption: monospaced font, ~350-400 columns x 100-120 rows
- Cell size: 11-char internal (13 total with box borders), 12 positions per cell in a row
- Layout width: ~172 chars (73 per half + 26 gap)
- Must use box-drawing characters: `+---+---+` pattern with `|` verticals
- All 5 layers must be represented
- Bridge prompt headlines (NOT full bodies) integrated around encoder/OLED sections
- Command mode overlay documented
