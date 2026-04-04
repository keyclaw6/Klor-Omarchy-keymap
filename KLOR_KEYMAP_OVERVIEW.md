# KLOR Keyboard — Human Readable Keymap

## Physical Layout (42 keys, Polydactyl)

```
         ┌─────┬─────┬─────┬─────┬─────┐                    ┌─────┬─────┬─────┬─────┬─────┐
         │  Q  │  W  │  E  │  R  │  T  │                    │  Y  │  U  │  I  │  O  │  P  │
 ┌───────┼─────┼─────┼─────┼─────┼─────┼────────────────────┼─────┼─────┼─────┼─────┼─────┼───────┐
 │  TAB  │  A  │  S  │  D  │  F  │  G  │                    │  H  │  J  │  K  │  L  │  ;  │  '    │
 ├───────┼─────┼─────┼─────┼─────┼─────┤╭──────────╮╭───────┤├─────┼─────┼─────┼─────┼─────┼───────┤
 │LGUI   │  Z  │  X  │  C  │  V  │  B  ││  MUTE  ││ PLY/PSE││  N  │  M  │  ,  │  .  │  /  │ NAV   │
  └───────┴─────┴─────┴─────┴─────┴─────┤│        ││        │├─────┴─────┴─────┴─────┴─────┴───────┘
                          ┌─────┬─────┬┤│        ││        ├┤┌─────┬─────┬─────┐
                          │CTRL │LOWER│││  SPACE ││  ALT   │││ ENTER│RAISE│BSPC │
                          └─────┴─────┴┘└────────┘└────────┘└┴─────┴─────┴─────┘
```

**Thumb keys:** `CTRL` `LOWER` `SPACE` `NAV` | `ALT` `ENTER` `RAISE` `BSPC`
**Center keys:** `MUTE` and `PLY/PSE` (always active, don't change with layers)
**Encoders:** Both left and right encoders control volume (clockwise = up, counter = down)

---

## Layer 0: QWERTY (Base Layer)

```
         ┌─────┬─────┬─────┬─────┬─────┐                    ┌─────┬─────┬─────┬─────┬─────┐
         │  Q  │  W  │  E  │  R  │  T  │                    │  Y  │  U  │  I  │  O  │  P  │
 ┌───────┼─────┼─────┼─────┼─────┼─────┼────────────────────┼─────┼─────┼─────┼─────┼─────┼───────┐
 │  TAB  │  A  │  S  │  D  │  F  │  G  │                    │  H  │  J  │  K  │  L  │  ;  │  '    │
 ├───────┼─────┼─────┼─────┼─────┼─────┤╭──────────╮╭───────┤├─────┼─────┼─────┼─────┼─────┼───────┤
 │LGUI   │  Z  │  X  │  C  │  V  │  B  ││  MUTE  ││ PLY/PSE││  N  │  M  │  ,  │  .  │  /  │ NAV   │
 └───────┴─────┴─────┴─────┴─────┴─────┤│        ││        │├─────┴─────┴─────┴─────┴─────┴───────┘
                          ┌─────┬─────┬┤│        ││        ├┤┌─────┬─────┬─────┐
                          │CTRL │LOWER│││  SPACE ││  ALT   │││ ENTER│RAISE│BSPC │
                          └─────┴─────┴┘└────────┘└────────┘└┴─────┴─────┴─────┘
```

**How it works:** Standard QWERTY typing. Hold `LGUI` (bottom-left) to access Omarchy/SUPER shortcuts.
Hold `LOWER` or `RAISE` thumb keys to access layers below.

**Special:**
- `TAB + Q` (combo) = `ESC`

---

## Layer 1: LOWER (Hold LOWER thumb key)

```
         ┌──────┬──────┬──────┬──────┬──────┐                    ┌──────┬──────┬──────┬──────┬──────┐
         │ CAPS │ HOME │  UP  │  =   │  {   │                    │  }   │  7   │  8   │  9   │  +   │
 ┌───────┼──────┼──────┼──────┼──────┼──────┼────────────────────┼──────┼──────┼──────┼──────┼──────┼───────┐
 │  ESC  │ DEL  │ LEFT │ DOWN │ RIGHT│  [   │                    │  ]   │  4   │  5   │  6   │  -   │  _    │
 ├───────┼──────┼──────┼──────┼──────┼──────┤╭──────────╮╭───────┤├──────┼──────┼──────┼──────┼──────┼───────┤
 │WIN+S  │ END  │ PGUP │SAVE  │ PGDN │  (   ││  MUTE  ││ PLY/PSE││  )   │  1   │  2   │  3   │  *   │  —    │
 └───────┴──────┴──────┴──────┴──────┴──────┤│        ││        │├──────┴──────┴──────┴──────┴──────┴───────┘
                          ┌─────┬─────┬────┤│        ││        ├┤┌─────┬──────┬─────┐
                          │  —  │  —  │ —  ││  —     ││  —     │││  —  │ADJUST│  0  │
                          └─────┴─────┴────┘└────────┘└────────┘└┴─────┴──────┴─────┘
```

**Purpose:** Navigation + numpad + symbols
- **Left hand:** Navigation (arrows, home/end, page up/down), escape, delete
- **Right hand:** Numpad (7-9 top, 4-6 mid, 1-3 bottom, 0 on thumb)
- **Bottom-left:** `WIN+S` screenshot macro (Windows-style, may not work on Linux)
- **Bottom-right:** `ADJUST` layer access (hold RAISE + LOWER together also works)
- **SAVE** = `Ctrl+S` (save shortcut)

---

## Layer 2: RAISE (Hold RAISE thumb key)

```
         ┌─────┬─────┬─────┬─────┬─────┐                    ┌─────┬─────┬─────┬─────┬─────┐
         │  !  │  @  │  #  │  $  │  %  │                    │  ^  │  &  │  \  │  °  │  á  │
 ┌───────┼─────┼─────┼─────┼─────┼─────┼────────────────────┼─────┼─────┼─────┼─────┼─────┼───────┐
 │ AF13  │AF14 │AF15 │AF16 │AF17 │ AltGr│                    │  ¥  │  €  │  £  │  ≈  │  ú  │  ó    │
 ├───────┼─────┼─────┼─────┼─────┼─────┤╭──────────╮╭───────┤├─────┼─────┼─────┼─────┼─────┼───────┤
 │ AF18  │AF19 │AF20 │AF21 │AF22 │AF23 ││  MUTE  ││ PLY/PSE││  ≤  │  ≥  │ CUE │  ~  │  `  │  —    │
 └───────┴─────┴─────┴─────┴─────┴─────┤│        ││        │├─────┴─────┴─────┴─────┴─────┴───────┘
                          ┌─────┬─────┬┤│        ││        ├┤┌─────┬─────┬─────┐
                          │  —  │ADJ  │ —  ││  —     ││  —     │││  —  │  —  │  —  │
                          └─────┴─────┴┘└────────┘└────────┘└┴─────┴─────┴─────┘
```

**Purpose:** Symbols, special characters, media function keys
- **Top row:** Shifted numbers (`!@#$%^&`) + special chars (`\°á`)
- **Middle row:** `Alt+F13` through `Alt+F17` + AltGr symbols (`SZ ¥€£≈úó`)
- **Bottom row:** `Alt+F18` through `Alt+F23` + symbols (`≤≥CUE~\``)
- **AF = Alt+F-keys** — these are custom function keys, likely for macros or app-specific bindings
- **CUE** = `AltGr+C` — special character
- **SZ** = `AltGr+S` — German ß or similar

---

## Layer 3: ADJUST (Hold LOWER + RAISE together, or ADJUST key)

```
         ┌─────┬─────┬─────┬─────┬─────┐                    ┌─────┬─────┬─────┬─────┬─────┐
         │ F15 │ F16 │ F17 │ F18 │ F19 │                    │  —  │  F7 │  F8 │  F9 │ F14 │
 ┌───────┼─────┼─────┼─────┼─────┼─────┼────────────────────┼─────┼─────┼─────┼─────┼─────┼───────┐
 │  F20  │ F21 │ F22 │ F23 │ F24 │ APP │                    │  —  │  F4 │  F5 │  F6 │ F12 │ F13   │
 ├───────┼─────┼─────┼─────┼─────┼─────┤╭──────────╮╭───────┤├─────┼─────┼─────┼─────┼─────┼───────┤
 │RESET  │  —  │  —  │  —  │  —  │  —  ││  MUTE  ││ PLY/PSE││  —  │  F1 │  F2 │  F3 │ F10 │ F11   │
 └───────┴─────┴─────┴─────┴─────┴─────┤│        ││        │├─────┴─────┴─────┴─────┴─────┴───────┘
                          ┌─────┬─────┬┤│        ││        ├┤┌─────┬─────┬─────┐
                          │  —  │  —  │ —  ││  —     ││  —     │││  —  │  —  │BSPC │
                          └─────┴─────┴┘└────────┘└────────┘└┴─────┴─────┴─────┘
```

**Purpose:** Function keys + system controls
- **Left hand:** Extended F-keys (F15-F24)
- **Right hand:** Standard F-keys (F1-F14)
- **Bottom-left:** `RESET` — boots keyboard into bootloader (flash firmware)
- **Bottom-right:** `BSPC` — backspace
- **APP** — application/context menu key
- **`—`** = no action (transparent/disabled)

---

## Layer 4: NAV (Hold bottom-right key on QWERTY layer)

```
         ┌─────┬─────┬─────┬─────┬─────┐                    ┌─────┬─────┬─────┬─────┬─────┐
         │  —  │  —  │  ↑  │  —  │  —  │                    │  —  │  7  │  8  │  9  │  —  │
 ┌───────┼─────┼─────┼─────┼─────┼─────┼────────────────────┼─────┼─────┼─────┼─────┼─────┼───────┐
 │  —    │  —  │  ←  │  ↓  │  →  │  —  │                    │  —  │  4  │  5  │  6  │  —  │  —    │
 ├───────┼─────┼─────┼─────┼─────┼─────┤╭──────────╮╭───────┤├─────┼─────┼─────┼─────┼─────┼───────┤
 │  —    │  —  │  —  │  —  │  —  │  —  ││  MUTE  ││ PLY/PSE││  —  │  1  │  2  │  3  │  —  │  —    │
 └───────┴─────┴─────┴─────┴─────┴─────┤│        ││        │├─────┴─────┴─────┴─────┴─────┴───────┘
                          ┌─────┬─────┬┤│        ││        ├┤┌─────┬─────┬─────┬─────┐
                          │  —  │  —  │││  —     ││  —     │││  —  │  —  │  —  │  0  │
                          └─────┴─────┴┘└────────┘└────────┘└┴─────┴─────┴─────┴─────┘
```

**Purpose:** Navigation — exposes numbers and arrows so Omarchy's `SUPER+number/arrow` shortcuts work with minimal modifiers.

This layer acts as a SUPER-prefix for navigation. Every mapped key sends `SUPER + keycode`. Add Shift/Alt/Ctrl to access Omarchy's variant shortcuts.

### Number keys (right hand):
| Key | Sends | Omarchy action | With Shift | With Alt |
|-----|-------|---------------|------------|----------|
| **m** | `SUPER+1` | Workspace 1 | Move window to ws 1 | Grouped window 1 |
| **,** | `SUPER+2` | Workspace 2 | Move window to ws 2 | Grouped window 2 |
| **.** | `SUPER+3` | Workspace 3 | Move window to ws 3 | Grouped window 3 |
| **j** | `SUPER+4` | Workspace 4 | Move window to ws 4 | Grouped window 4 |
| **k** | `SUPER+5` | Workspace 5 | Move window to ws 5 | Grouped window 5 |
| **l** | `SUPER+6` | Workspace 6 | Move window to ws 6 | — |
| **u** | `SUPER+7` | Workspace 7 | Move window to ws 7 | — |
| **i** | `SUPER+8` | Workspace 8 | Move window to ws 8 | — |
| **o** | `SUPER+9` | Workspace 9 | Move window to ws 9 | — |
| **Right thumb** | `SUPER+0` | Workspace 10 | Move window to ws 10 | — |

### Arrow keys (left hand):
| Key | Sends | Omarchy action | With Shift | With Alt | With Ctrl |
|-----|-------|---------------|------------|----------|-----------|
| **e** | `SUPER+UP` | Focus up | Swap up | Move into group up | — |
| **s** | `SUPER+LEFT` | Focus left | Swap left | Move into group left | Group focus left |
| **d** | `SUPER+DOWN` | Focus down | Swap down | Move into group down | — |
| **f** | `SUPER+RIGHT` | Focus right | Swap right | Move into group right | Group focus right |

### Other keys:
| Key | Sends | Omarchy action |
|-----|-------|---------------|
| **TAB** | `SUPER+TAB` | Next workspace |

All other keys = transparent (pass through to base layer for typing).

**Access:** Hold the bottom-right key (was SHIFT position) on the QWERTY layer. Release to return to typing.

---

## How to Enter Each Layer

| Layer | How to Enter | How to Exit |
|-------|-------------|-------------|
| **QWERTY** | Default (always on) | — |
| **LOWER** | Hold left thumb `LOWER` key | Release key |
| **RAISE** | Hold right thumb `RAISE` key | Release key |
| **ADJUST** | Hold LOWER + RAISE together, or ADJUST key on LOWER/RAISE | Release both |
| **NAV** | Hold bottom-right key (was SHIFT position) on QWERTY | Release key |

---

## Conflicts & Gotchas

1. **`WIN+S` on LOWER layer (SNAP2 macro)** — Sends `Shift+Win+S` (Windows screenshot shortcut). Does nothing on Omarchy/Linux. Pre-existing; left in place for Windows compatibility.

2. **`LGUI` on QWERTY** — The bottom-left key is `LGUI` (Super). Holding it + any letter sends `SUPER+letter` to Hyprland. This is intentional and how Omarchy works, but be aware you're triggering desktop shortcuts while typing.

3. **`voxtype` not installed** — `SUPER + CTRL + X` (dictation toggle) is in Omarchy config but the binary isn't installed on this system.

4. **Fcitx5 runtime bindings** — `SUPER + ;` and `CTRL + ;` are Fcitx5 input method shortcuts, separate from Hyprland. Fcitx5 IS installed (v5.1.19).

---

## Missing from Nav Layer

These Omarchy shortcuts exist in Hyprland but are NOT on the Nav layer (they use base-layer letters, so they work with `LGUI + key` on QWERTY):

- `SUPER + ALT + SPACE` — Omarchy menu
- `SUPER + CTRL + E` — Emoji picker
- `SUPER + CTRL + L` — Lock screen
- `SUPER + CTRL + S` — Share menu
- `PRINT` / `ALT + PRINT` / `SUPER + PRINT` — Screenshot / recording / color picker
- `SUPER + BACKSPACE` / `SHIFT+BACKSPACE` / `CTRL+BACKSPACE` — Window appearance toggles
- `SUPER + CTRL + Z` / `CTRL+ALT+Z` — Zoom
- `SUPER + CTRL + ALT + T` / `CTRL+ALT+B` — Time / battery status
