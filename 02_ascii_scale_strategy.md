# 02 — ASCII Scale Strategy (4K Terminal Math)

<think>
Phase 3 reasoning: This document must define the exact coordinate system and cell
dimensions for the 4K ASCII art. The target is a 42-inch 4K display with a terminal
running a monospaced font.

Key decisions needed:
1. How many columns/rows does a 4K terminal give us?
2. What cell width fits all key labels (some are long like "GUI+CTL+R")?
3. How to arrange 5 layers + command mode + metadata on the canvas?
4. What box-drawing style to use?

4K resolution: 3840x2160 pixels.
Typical monospaced font at comfortable reading size on 42":
- At 14pt (~18.7px cell width, ~37px cell height in a typical terminal):
  Cols = 3840 / 9.4 ≈ 408 columns (at roughly 9.4px per char width)
  Rows = 2160 / 18.8 ≈ 115 rows (at roughly 18.8px per char height)
- Conservative estimate: 380 cols x 100 rows
- Generous estimate: 420 cols x 120 rows
- Design target: 380 cols x 110 rows (safe for most configs)

Cell dimensions for key boxes:
- Each key needs to show: primary label + optional secondary (tap/hold)
- Minimum useful width: 9 chars internal (like the existing keymap.c ASCII)
- Better for 4K: 11 chars internal = 13 total with borders
- Height per cell: 3 lines (top border, content, bottom border) or 5 lines (2 content rows)
- For multi-layer display: use 3-line cells with stacked info

Layout structure for the full sheet:
- Title/header: 3-5 lines
- Each layer block: ~15-18 lines (row headers + 4 physical rows + thumb row + spacing)
- 5 layers × 18 = 90 lines just for layers
- That's too many for a single screen. Better approach: show all layers SIDE BY SIDE
  or use a COMPACT format where each key shows multiple layers vertically.

Alternative: The keymap.c already shows each layer in ~15 lines. If we stack 5 layers
vertically with 2-line gaps, that's 5×15 + 4×2 = 83 lines. Leaves 27 lines for
header, command mode, encoder info, and snippets. That fits!

But the instructions say "massive" and "4K" -- the intent is to USE the space, not cram it.
Let me use the full canvas with generous spacing.

Best approach for the ASCII file:
- Width: ~172 chars per layer row (73 per half + 26 gap) -- from the discovery notes
- Height per layer: ~12 lines (with generous key boxes)
- 5 layers stacked: 5 × 14 (with spacing) = 70 lines
- Header: 5 lines
- Command mode section: 12 lines
- Encoder/metadata section: 8 lines
- Snippet catalog: 12 lines
- Total: ~107 lines -- perfect for 110-row display

For the key cells, I'll use the 11-char internal width:
┌─────────────┐
│  label/tap  │
│  hold/note  │
└─────────────┘
= 15 chars wide (13 + borders), but that's too wide for 6 keys per half.
6 keys × 15 = 90 per half, 90+90+gap = too much.

Let me recalculate. With 11-char internal (13 total box width):
6 keys × 13 = 78 per half. Two halves + 20 char gap = 78+78+20 = 176 chars.
That's within 380-column budget. Good.

But some keys need only 1 content line if the label is short. For a READABLE cheat sheet,
2 content lines per cell is ideal: line 1 = tap, line 2 = hold/layer info.

Cell height = 4 lines: top border, tap line, hold line, bottom border.
Row height = 4 lines per physical row.
But adjacent rows share borders: actual = 4 + 3*(rows-1) = 4 + 3*3 = 13 for 4 rows.
Plus thumb row = 13 + 3 = 16 lines per layer.

5 layers × 16 = 80 lines. Plus headers/gaps = ~95. Fits.

Actually, let me simplify. For the actual ASCII art, I'll:
1. Use single-line content cells (3 lines per row: top, content, bottom)
2. Show the primary function prominently
3. Use separate sections for hold/tap details where needed
4. Keep it clean and scannable
</think>

## Display Target

| Parameter           | Value                    | Notes                        |
|---------------------|--------------------------|------------------------------|
| Display             | 42-inch 4K (3840×2160)   |                              |
| Font                | Monospaced, ~14pt        | Standard terminal font       |
| Estimated columns   | 380-420                  | Depends on font metrics      |
| Estimated rows      | 100-120                  | Depends on font metrics      |
| **Design target**   | **380 cols × 110 rows**  | Safe lower bound             |

---

## Cell Dimensions

### Key Box Design

```
┌───────────┐    Width: 13 chars total (11 internal + 2 border)
│   LABEL   │    Height: 3 lines (top border, content, bottom border)
└───────────┘
```

For keys with tap/hold info (home row mods, layer keys):
```
┌───────────┐    Width: 13 chars total
│ tap: A    │    Line 1: tap function
│hold: GUI  │    Line 2: hold function
└───────────┘    Height: 4 lines
```

### Row Width Calculation

```
Per half:
  Row 0 (5 keys):  gap(13) + 5 × 13 = 13 + 65 = 78 chars
  Row 1 (6 keys):  6 × 13 = 78 chars
  Row 2 (6 keys + encoder): 6 × 13 + 1 + 10 = 89 chars
  Thumb  (4 keys): offset + 4 × 13 = offset + 52 chars

Full width:
  Left half (78) + Center gap (20) + Right half (78) = 176 chars
  With encoder boxes: ~196 chars max

Budget check: 196 < 380 columns ✓ (54% utilization, generous margins)
```

### Vertical Budget

```
Per layer section:
  Title line                     =  1 line
  Blank separator                =  1 line
  Row 0 (3-line cells, 5 keys)  =  3 lines
  Row 1 (4-line cells, HRM)     =  4 lines (shared top border with row 0)
  Row 2 (3-line cells + enc)    =  3 lines (shared top border with row 1)
  Thumb row (3-line cells)       =  3 lines (shared top border with row 2)
  Subtotal per layer             = ~12 lines (with shared borders)
  Gap between layers             =  2 lines

5 layers: 5 × 12 + 4 × 2 = 68 lines

Additional sections:
  Title/header block             =  5 lines
  Command mode section           = 10 lines
  Encoder map table              =  8 lines
  Bridge actions summary         =  6 lines
  Snippet catalog (compact)      = 14 lines
  Footer                         =  2 lines
  Subtotal                       = 45 lines

Total: 68 + 45 = 113 lines

Budget check: 113 ≈ 110 rows ✓ (tight but workable, can compress gaps)
```

---

## Canvas Layout Plan

```
Line Range    Section
──────────    ──────────────────────────────────────────────────
  1 -   5    Title block (keyboard name, firmware version, date)
  6 -   7    Blank separator
  8 -  19    Layer 0: QWERTY (base + home row mods annotated)
 20 -  21    Blank separator
 22 -  33    Layer 1: LOWER (numbers, nav, brackets)
 34 -  35    Blank separator
 36 -  47    Layer 2: RAISE (symbols, Danish, currency)
 48 -  49    Blank separator
 50 -  61    Layer 3: ADJUST (F-keys, system)
 62 -  63    Blank separator
 64 -  75    Layer 4: NAV (Hyprland WM)
 76 -  77    Blank separator
 78 -  87    Command Mode overlay + action table
 88 -  89    Blank separator
 90 -  97    Encoder maps + key overrides + bootloader info
 98 -  99    Blank separator
100 - 113    Prompt snippet catalog (2-column layout)
```

---

## Coordinate System

### X-axis (columns)

| Element       | Start Col | End Col | Width  | Notes                     |
|---------------|-----------|---------|--------|---------------------------|
| Left margin   | 1         | 4       | 4      | Indent                    |
| Left outer    | 5         | 17      | 13     | Row 1-2 only (L10, L20)  |
| Left pinky    | 18        | 30      | 13     | L01, L11, L21             |
| Left ring     | 31        | 43      | 13     | L02, L12, L22             |
| Left middle   | 44        | 56      | 13     | L03, L13, L23             |
| Left index    | 57        | 69      | 13     | L04, L14, L24             |
| Left inner    | 70        | 82      | 13     | L05, L15, L25             |
| Left encoder  | 83        | 92      | 10     | L35 (row 2 only)         |
| Center gap    | 93        | 112     | 20     | Visual split separator    |
| Right encoder | 113       | 122     | 10     | R30 (row 2 only)         |
| Right inner   | 123       | 135     | 13     | R00, R10, R20             |
| Right index   | 136       | 148     | 13     | R01, R11, R21             |
| Right middle  | 149       | 161     | 13     | R02, R12, R22             |
| Right ring    | 162       | 174     | 13     | R03, R13, R23             |
| Right pinky   | 175       | 187     | 13     | R04, R14, R24             |
| Right outer   | 188       | 200     | 13     | R15, R25 (row 1-2 only)  |
| Right margin  | 201       | 204     | 4      | Padding                   |

**Total width: 204 chars** (well within 380 budget)

### Thumb Row X-offsets

Thumb keys are inset (start at left index column position):

| Element       | Start Col | End Col | Width  |
|---------------|-----------|---------|--------|
| Left thumb 1  | 44        | 56      | 13     | L31 (CTRL)    |
| Left thumb 2  | 57        | 69      | 13     | L32 (LOWER)   |
| Left thumb 3  | 70        | 82      | 13     | L33 (SPACE)   |
| Left thumb 4  | 83        | 95      | 13     | L34 (SHIFT)   |
| (gap)         | 96        | 108     | 13     |               |
| Right thumb 1 | 109       | 121     | 13     | R31 (RALT)    |
| Right thumb 2 | 122       | 134     | 13     | R32 (ENTER)   |
| Right thumb 3 | 135       | 147     | 13     | R33 (RAISE)   |
| Right thumb 4 | 148       | 160     | 13     | R34 (BKSP)    |

---

## Box Drawing Character Set

| Char | Unicode | Purpose            |
|------|---------|--------------------|
| `┌`  | U+250C  | Top-left corner    |
| `┐`  | U+2510  | Top-right corner   |
| `└`  | U+2514  | Bottom-left corner |
| `┘`  | U+2518  | Bottom-right corner|
| `─`  | U+2500  | Horizontal line    |
| `│`  | U+2502  | Vertical line      |
| `├`  | U+251C  | Left tee           |
| `┤`  | U+2524  | Right tee          |
| `┬`  | U+252C  | Top tee            |
| `┴`  | U+2534  | Bottom tee         |
| `┼`  | U+253C  | Cross              |

### Alternative: ASCII-safe fallback

If Unicode box drawing causes issues, fall back to:
```
+-----+   | for borders
|     |   + for corners
+-----+   - for horizontal
```

---

## Design Decisions

1. **Single-line cells for most keys** (3 lines: top, content, bottom). Keys with tap/hold get 4-line cells (top, tap, hold, bottom).

2. **Shared borders** between adjacent rows — bottom border of one row = top border of next.

3. **Row 0 offset** — starts at pinky column (no outer column), visually indented vs rows 1-2.

4. **Encoder boxes** — smaller (10 chars wide) and placed between row 2 and thumbs, connected with a small bracket or standalone.

5. **Layer titles** — centered above each layout block, in a highlighted box.

6. **Command mode** — shown as a partial overlay on the QWERTY layout, highlighting only active action keys.

7. **Snippet catalog** — 2-column table with numbering, placed at bottom for reference.

8. **Column stagger** — NOT represented in the ASCII art (too complex for monospaced grid). Instead, a note explains the physical stagger.
