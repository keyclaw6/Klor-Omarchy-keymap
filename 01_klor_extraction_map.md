# 01 — KLOR Extraction Map

<think>
Phase 2 reasoning: This document must exhaustively extract every data point from the
firmware and bridge files that will feed into the ASCII cheat sheet. The key requirement
is to map every physical key position to its function on every layer, extract all macros,
document the command mode state machine, list encoder mappings per layer, catalog bridge
action headlines (NOT prompt bodies), and list all 22 snippet headlines.

I need to be systematic: go position by position through the LAYOUT_polydactyl arguments
for each of the 5 layers, then document everything else.
</think>

## 1. Layer-by-Layer Key Extraction

### Position Reference (LAYOUT_polydactyl argument order)

```
Row 0:       L01  L02  L03  L04  L05                R00  R01  R02  R03  R04
Row 1:  L10  L11  L12  L13  L14  L15                R10  R11  R12  R13  R14  R15
Row 2:  L20  L21  L22  L23  L24  L25  L35(enc) R30(enc)  R20  R21  R22  R23  R24  R25
Thumb:            L31  L32  L33  L34                R31  R32  R33  R34
```

---

### Layer 0: _QWERTY (Base)

| Pos  | Keycode           | Tap        | Hold       | Notes                        |
|------|--------------------|-----------|------------|------------------------------|
| L01  | KC_Q               | Q         |            |                              |
| L02  | KC_W               | W         |            |                              |
| L03  | KC_E               | E         |            |                              |
| L04  | KC_R               | R         |            |                              |
| L05  | KC_T               | T         |            |                              |
| L10  | KC_TAB             | Tab       |            |                              |
| L11  | LGUI_T(KC_A)       | A         | L-GUI      | Home row mod                 |
| L12  | LALT_T(KC_S)       | S         | L-ALT      | Home row mod                 |
| L13  | LCTL_T(KC_D)       | D         | L-CTL      | Home row mod                 |
| L14  | LSFT_T(KC_F)       | F         | L-SFT      | Home row mod                 |
| L15  | KC_G               | G         |            |                              |
| L20  | KC_LGUI            | L-GUI     |            | Left Windows/Super           |
| L21  | KC_Z               | Z         |            |                              |
| L22  | KC_X               | X         |            |                              |
| L23  | KC_C               | C         |            |                              |
| L24  | KC_V               | V         |            |                              |
| L25  | KC_B               | B         |            |                              |
| L35  | KC_MUTE            | Mute      |            | Encoder click                |
| L31  | KC_LCTL            | L-Ctrl    |            | Thumb                        |
| L32  | MO(_LOWER)         | (hold)    | LOWER      | Thumb, layer 1 momentary     |
| L33  | KC_SPC             | Space     |            | Thumb                        |
| L34  | KC_LSFT            | L-Shift   |            | Thumb                        |
| R00  | KC_Y               | Y         |            |                              |
| R01  | KC_U               | U         |            |                              |
| R02  | KC_I               | I         |            |                              |
| R03  | KC_O               | O         |            |                              |
| R04  | KC_P               | P         |            |                              |
| R10  | KC_H               | H         |            |                              |
| R11  | RSFT_T(KC_J)       | J         | R-SFT      | Home row mod                 |
| R12  | RCTL_T(KC_K)       | K         | R-CTL      | Home row mod                 |
| R13  | LALT_T(KC_L)       | L         | L-ALT      | HRM uses LALT not RALT      |
| R14  | RGUI_T(KC_SCLN)    | ;         | R-GUI      | Home row mod                 |
| R15  | KC_QUOT            | '         |            |                              |
| R20  | KC_N               | N         |            |                              |
| R21  | KC_M               | M         |            |                              |
| R22  | KC_COMM            | ,         |            |                              |
| R23  | KC_DOT             | .         |            |                              |
| R24  | KC_SLSH            | /         |            |                              |
| R25  | MO(_NAV)           | (hold)    | NAV        | Bottom-right, layer 4        |
| R30  | KC_MPLY            | Play/Pause|            | Encoder click                |
| R31  | KC_RALT            | R-Alt     |            | Thumb; double-tap = Cmd Mode |
| R32  | KC_ENT             | Enter     |            | Thumb                        |
| R33  | MO(_RAISE)         | (hold)    | RAISE      | Thumb, layer 2 momentary     |
| R34  | KC_BSPC            | Backspace |            | Thumb; +Shift = Delete       |

---

### Layer 1: _LOWER (Left thumb hold)

| Pos  | Keycode    | Function    | Notes                                |
|------|------------|-------------|--------------------------------------|
| L01  | KC_CAPS    | Caps Lock   |                                      |
| L02  | KC_HOME    | Home        |                                      |
| L03  | KC_UP      | Arrow Up    |                                      |
| L04  | KC_EQL     | =           |                                      |
| L05  | KC_LCBR    | {           |                                      |
| L10  | KC_ESC     | Escape      |                                      |
| L11  | KC_DEL     | Delete      |                                      |
| L12  | KC_LEFT    | Arrow Left  |                                      |
| L13  | KC_DOWN    | Arrow Down  |                                      |
| L14  | KC_RGHT    | Arrow Right |                                      |
| L15  | KC_LBRC    | [           |                                      |
| L20  | KC_PSCR    | Print Screen| Screenshot key                       |
| L21  | KC_END     | End         |                                      |
| L22  | KC_PGUP    | Page Up     |                                      |
| L23  | C(KC_S)    | Ctrl+S      | Save                                 |
| L24  | KC_PGDN    | Page Down   |                                      |
| L25  | KC_LPRN    | (           |                                      |
| L35  | KC_MUTE    | Mute        | Encoder click (same as base)         |
| L31  | _______    | (trans)     | Ctrl from base                       |
| L32  | _______    | (trans)     | LOWER held (this layer active)       |
| L33  | _______    | (trans)     | Space from base                      |
| L34  | _______    | (trans)     | Shift from base                      |
| R00  | KC_RCBR    | }           |                                      |
| R01  | KC_7       | 7           |                                      |
| R02  | KC_8       | 8           |                                      |
| R03  | KC_9       | 9           |                                      |
| R04  | KC_PPLS    | + (numpad)  |                                      |
| R10  | KC_RBRC    | ]           |                                      |
| R11  | KC_4       | 4           |                                      |
| R12  | KC_5       | 5           |                                      |
| R13  | KC_6       | 6           |                                      |
| R14  | KC_MINS    | -           |                                      |
| R15  | KC_UNDS    | _           |                                      |
| R20  | KC_RPRN    | )           |                                      |
| R21  | KC_1       | 1           |                                      |
| R22  | KC_2       | 2           |                                      |
| R23  | KC_3       | 3           |                                      |
| R24  | KC_PAST    | * (numpad)  |                                      |
| R25  | _______    | (trans)     | NAV from base                        |
| R30  | KC_MPLY    | Play/Pause  | Encoder click (same as base)         |
| R31  | _______    | (trans)     | RALT from base                       |
| R32  | _______    | (trans)     | Enter from base                      |
| R33  | _______    | (trans)     | RAISE from base                      |
| R34  | KC_0       | 0           |                                      |

---

### Layer 2: _RAISE (Right thumb hold)

| Pos  | Keycode               | Function    | Notes                            |
|------|-----------------------|-------------|----------------------------------|
| L01  | KC_EXLM               | !           |                                  |
| L02  | KC_AT                  | @           |                                  |
| L03  | KC_HASH                | #           |                                  |
| L04  | KC_DLR                 | $           |                                  |
| L05  | KC_PERC                | %           |                                  |
| L10  | LALT(KC_F13)           | Alt+F13     | AF13                             |
| L11  | LALT(KC_F14)           | Alt+F14     | AF14                             |
| L12  | LALT(KC_F15)           | Alt+F15     | AF15                             |
| L13  | LALT(KC_F16)           | Alt+F16     | AF16                             |
| L14  | LALT(KC_F17)           | Alt+F17     | AF17                             |
| L15  | RALT(KC_S)             | AltGr+S     | SZ (sharp S / Eszett)            |
| L20  | LALT(KC_F18)           | Alt+F18     | AF18                             |
| L21  | LALT(KC_F19)           | Alt+F19     | AF19                             |
| L22  | LALT(KC_F20)           | Alt+F20     | AF20                             |
| L23  | LALT(KC_F21)           | Alt+F21     | AF21                             |
| L24  | LALT(KC_F22)           | Alt+F22     | AF22                             |
| L25  | LALT(KC_F23)           | Alt+F23     | AF23                             |
| L35  | KC_MUTE                | Mute        | Encoder click                    |
| L31  | _______                | (trans)     | Ctrl from base                   |
| L32  | _______                | (trans)     | LOWER from base                  |
| L33  | _______                | (trans)     | Space from base                  |
| L34  | _______                | (trans)     | Shift from base                  |
| R00  | KC_CIRC                | ^           |                                  |
| R01  | KC_AMPR                | &           |                                  |
| R02  | KC_BSLS                | \           |                                  |
| R03  | RALT(KC_3)             | AltGr+3     | degree (°)                       |
| R04  | UP(U_AA_L, U_AA_U)    | å / Å       | Unicode Map                      |
| R10  | RALT(KC_Y)             | AltGr+Y     | ¥ (Yen)                          |
| R11  | RALT(KC_5)             | AltGr+5     | € (Euro)                         |
| R12  | RALT(KC_4)             | AltGr+4     | £ (Pound)                        |
| R13  | RALT(KC_EQL)           | AltGr+=     | ≈ (approximately)                |
| R14  | UP(U_AE_L, U_AE_U)    | æ / Æ       | Unicode Map                      |
| R15  | UP(U_OE_L, U_OE_U)    | ø / Ø       | Unicode Map                      |
| R20  | RALT(KC_COMM)          | AltGr+,     | ≤ (less-equal)                   |
| R21  | RALT(KC_DOT)           | AltGr+.     | ≥ (greater-equal)                |
| R22  | RALT(KC_C)             | AltGr+C     | CUE (cedilla? ©?)               |
| R23  | LSFT(KC_GRV)          | ~           | Tilde                            |
| R24  | KC_GRV                 | `           | Grave                            |
| R25  | _______                | (trans)     | NAV from base                    |
| R30  | KC_MPLY                | Play/Pause  | Encoder click                    |
| R31  | _______                | (trans)     | RALT from base                   |
| R32  | _______                | (trans)     | Enter from base                  |
| R33  | _______                | (trans)     | RAISE held (this layer active)   |
| R34  | _______                | (trans)     | Backspace from base              |

---

### Layer 3: _ADJUST (Tri-layer: LOWER + RAISE)

| Pos  | Keycode    | Function    | Notes                                |
|------|------------|-------------|--------------------------------------|
| L01  | KC_F15     | F15         |                                      |
| L02  | KC_F16     | F16         |                                      |
| L03  | KC_F17     | F17         |                                      |
| L04  | KC_F18     | F18         |                                      |
| L05  | KC_F19     | F19         |                                      |
| L10  | KC_F20     | F20         |                                      |
| L11  | KC_F21     | F21         |                                      |
| L12  | KC_F22     | F22         |                                      |
| L13  | KC_F23     | F23         |                                      |
| L14  | KC_F24     | F24         |                                      |
| L15  | KC_APP     | App/Menu    |                                      |
| L20  | QK_BOOT    | Bootloader  | Reset to UF2 bootloader              |
| L21  | AC_TOGG    | AC Toggle   | Toggle autocorrect                   |
| L22  | XXXXXXX    | (none)      |                                      |
| L23  | XXXXXXX    | (none)      |                                      |
| L24  | XXXXXXX    | (none)      |                                      |
| L25  | XXXXXXX    | (none)      |                                      |
| L35  | KC_MUTE    | Mute        | Encoder click                        |
| L31  | _______    | (trans)     | Ctrl from base                       |
| L32  | _______    | (trans)     | LOWER held                           |
| L33  | _______    | (trans)     | Space from base                      |
| L34  | _______    | (trans)     | Shift from base                      |
| R00  | XXXXXXX    | (none)      |                                      |
| R01  | KC_F7      | F7          |                                      |
| R02  | KC_F8      | F8          |                                      |
| R03  | KC_F9      | F9          |                                      |
| R04  | KC_F14     | F14         |                                      |
| R10  | XXXXXXX    | (none)      |                                      |
| R11  | KC_F4      | F4          |                                      |
| R12  | KC_F5      | F5          |                                      |
| R13  | KC_F6      | F6          |                                      |
| R14  | KC_F12     | F12         |                                      |
| R15  | KC_F13     | F13         |                                      |
| R20  | XXXXXXX    | (none)      |                                      |
| R21  | KC_F1      | F1          |                                      |
| R22  | KC_F2      | F2          |                                      |
| R23  | KC_F3      | F3          |                                      |
| R24  | KC_F10     | F10         |                                      |
| R25  | KC_F11     | F11         |                                      |
| R30  | KC_MPLY    | Play/Pause  | Encoder click                        |
| R31  | _______    | (trans)     | RALT from base                       |
| R32  | _______    | (trans)     | Enter from base                      |
| R33  | _______    | (trans)     | RAISE held                           |
| R34  | KC_BSPC    | Backspace   | Overrides transparent                |

---

### Layer 4: _NAV (Omarchy/Hyprland WM)

| Pos  | Keycode                    | Function          | Notes                          |
|------|----------------------------|-------------------|--------------------------------|
| L01  | XXXXXXX                    | (none)            |                                |
| L02  | LCTL(LGUI(KC_LEFT))        | GUI+CTL+Left      | Focus prev group               |
| L03  | NAV_UP                     | GUI+Up (custom)   | Focus up; composable           |
| L04  | LCTL(LGUI(KC_RGHT))        | GUI+CTL+Right     | Focus next group               |
| L05  | XXXXXXX                    | (none)            |                                |
| L10  | LGUI(KC_TAB)               | GUI+Tab           | WS-Tab / next workspace        |
| L11  | XXXXXXX                    | (none)            |                                |
| L12  | NAV_LEFT                   | GUI+Left (custom) | Focus left; composable         |
| L13  | NAV_DOWN                   | GUI+Down (custom) | Focus down; composable         |
| L14  | NAV_RIGHT                  | GUI+Right (custom)| Focus right; composable        |
| L15  | LGUI(KC_G)                 | GUI+G             | Toggle group                   |
| L20  | XXXXXXX                    | (none)            |                                |
| L21  | XXXXXXX                    | (none)            |                                |
| L22  | XXXXXXX                    | (none)            |                                |
| L23  | XXXXXXX                    | (none)            |                                |
| L24  | XXXXXXX                    | (none)            |                                |
| L25  | XXXXXXX                    | (none)            |                                |
| L35  | KC_MUTE                    | Mute              | Encoder click                  |
| L31  | KC_LCTL                    | L-Ctrl            | Thumb compose: resize          |
| L32  | XXXXXXX                    | (none)            |                                |
| L33  | XXXXXXX                    | (none)            |                                |
| L34  | KC_LSFT                    | L-Shift           | Thumb compose: swap/move       |
| R00  | XXXXXXX                    | (none)            |                                |
| R01  | LGUI(KC_7)                 | GUI+7             | Workspace 7                    |
| R02  | LGUI(KC_8)                 | GUI+8             | Workspace 8                    |
| R03  | LGUI(KC_9)                 | GUI+9             | Workspace 9                    |
| R04  | XXXXXXX                    | (none)            |                                |
| R10  | XXXXXXX                    | (none)            |                                |
| R11  | LGUI(KC_4)                 | GUI+4             | Workspace 4                    |
| R12  | LGUI(KC_5)                 | GUI+5             | Workspace 5                    |
| R13  | LGUI(KC_6)                 | GUI+6             | Workspace 6                    |
| R14  | XXXXXXX                    | (none)            |                                |
| R15  | XXXXXXX                    | (none)            |                                |
| R20  | XXXXXXX                    | (none)            |                                |
| R21  | LGUI(KC_1)                 | GUI+1             | Workspace 1                    |
| R22  | LGUI(KC_2)                 | GUI+2             | Workspace 2                    |
| R23  | LGUI(KC_3)                 | GUI+3             | Workspace 3                    |
| R24  | XXXXXXX                    | (none)            |                                |
| R25  | _______                    | (trans)           | NAV held (this layer active)   |
| R30  | KC_MPLY                    | Play/Pause        | Encoder click                  |
| R31  | KC_LALT                    | L-Alt             | Thumb compose: group ops       |
| R32  | XXXXXXX                    | (none)            |                                |
| R33  | XXXXXXX                    | (none)            |                                |
| R34  | LGUI(KC_0)                 | GUI+0             | Workspace 10                   |

### NAV Compose Table (arrows + thumb modifiers)

| Arrow  | Plain (GUI+) | +Shift         | +Ctrl           | +Alt            | +Shift+Alt         |
|--------|-------------|----------------|-----------------|-----------------|---------------------|
| Left   | Focus left  | Swap left      | Resize (GUI+-)  | Move into group | Move WS to monitor  |
| Right  | Focus right | Swap right     | Resize (GUI+=)  | Move into group | Move WS to monitor  |
| Up     | Focus up    | Swap up        | Resize (SGU+-)  | Move into group | Move WS to monitor  |
| Down   | Focus down  | Swap down      | Resize (SGU+=)  | Move into group | Move WS to monitor  |

| WS Key | Plain       | +Shift           | +Alt             | +Shift+Alt            |
|--------|-------------|------------------|------------------|-----------------------|
| 1-9, 0 | Go to WS   | Move win to WS   | Group window 1-5 | Move win silently     |
| G      | Toggle group| —                | Move out of group| —                     |
| WS-Tab | Next WS     | Previous WS      | Next in group    | Previous in group     |
| +Ctrl  | —           | —                | —                | Former WS (on WS-Tab) |

---

## 2. Encoder Maps (per layer)

| Layer    | Left Encoder CCW/CW         | Right Encoder CCW/CW           |
|----------|-----------------------------|---------------------------------|
| QWERTY   | Vol Down / Vol Up            | Bright Down / Bright Up         |
| LOWER    | Vol Down / Vol Up            | Bright Down / Bright Up         |
| RAISE    | Vol Down / Vol Up            | Bright Down / Bright Up         |
| ADJUST   | Vol Down / Vol Up            | Bright Down / Bright Up         |
| NAV      | Prev WS (SGU+Tab) / Next WS (GUI+Tab) | Prev WS / Next WS   |

---

## 3. Key Overrides

| Trigger          | Override       | Notes                  |
|------------------|----------------|------------------------|
| Shift + Backspace | Delete        | `ko_make_basic`        |

---

## 4. Command Mode (Double-tap RALT)

### State Machine
1. Double-tap RALT within 350ms window
2. Command mode active for 3000ms timeout
3. Next letter keypress dispatches action via Raw HID
4. ESC cancels; unmapped key exits + passes through
5. While STT recording: single RALT stops recording

### Active Actions

| Key | Action ID | Type          | Description                              |
|-----|-----------|---------------|------------------------------------------|
| E   | 0x45      | llm_text      | Prompt Expand                            |
| G   | 0x47      | llm_text      | Fix Grammar                              |
| I   | 0x49      | llm_text      | Improve Writing                          |
| R   | 0x52      | llm_text      | Write Email (Danish/Nordic style)        |
| S   | 0x53      | llm_text      | Summarize                                |
| D   | 0x44      | llm_text      | Translate Danish → English               |
| N   | 0x4E      | llm_text      | Translate English → Danish               |
| T   | 0x10      | stt_toggle    | Speech-to-Text (1-3 taps = depth)        |
| P   | 0x50      | prompt_picker | Open snippet picker popup                |

### Unconfigured Placeholders (17 keys)
A, B, C, F, H, J, K, L, M, O, Q, U, V, W, X, Y, Z

---

## 5. Bridge Prompt Headlines (bodies omitted)

| prompt_key       | Headline / Role                                |
|------------------|------------------------------------------------|
| improve_writing  | Expert copyeditor — improve clarity and flow   |
| write_email      | Executive assistant — Danish/Nordic pro email   |
| prompt_expand    | Expert prompt engineer — strengthen instruction |
| fix_grammar      | Precision proofreader — minimal corrections     |
| summarize        | Executive analyst — decision-useful summary     |
| translate_da_en  | Bilingual translator — Danish to English        |
| translate_en_da  | Bilingual translator — English to Danish        |
| stt_postprocess  | Transcript editor — clean up STT output         |

---

## 6. Prompt Snippet Catalog (22 snippets for Picker)

| #  | Name                          | Category      |
|----|-------------------------------|---------------|
| 1  | Expand this properly          | Prompting     |
| 2  | Improve this prompt           | Prompting     |
| 3  | Write this email              | Email         |
| 4  | Reply to this email           | Email         |
| 5  | Follow up on this             | Email         |
| 6  | Explain this like I'm 10      | Explanation   |
| 7  | Make this concise             | Writing       |
| 8  | Improve the writing           | Writing       |
| 9  | Make this more formal         | Writing       |
| 10 | Make this more natural        | Writing       |
| 11 | Summarize the key points      | Analysis      |
| 12 | Extract action items          | Analysis      |
| 13 | Turn this into meeting notes  | Analysis      |
| 14 | Write a decision memo         | Analysis      |
| 15 | Review this code              | Code          |
| 16 | Explain this code             | Code          |
| 17 | Turn this into a bug report   | Code          |
| 18 | Refactor this code            | Code          |
| 19 | Write tests for this          | Code          |
| 20 | Translate Danish to English   | Translation   |
| 21 | Translate English to Danish   | Translation   |
| 22 | Brainstorm strong options     | Creative      |

---

## 7. Bootloader Combo

- **Trigger:** Press all 4 thumb keys on one half simultaneously, 5 times within 3 seconds
- **Left thumbs:** L31, L32, L33, L34 (matrix row 3, cols 1-4)
- **Right thumbs:** R31, R32, R33, R34 (matrix row 7, cols 1-4)
- **Result:** `reset_keyboard()` → enters UF2 bootloader
- **Per-half:** Each half can enter bootloader independently

---

## 8. Autocorrect

- **Engine:** QMK built-in trie-based, ~4,200 entries, ~65 KB
- **Toggle:** AC_TOGG on ADJUST layer (L21 position)
- **Enabled by default:** `autocorrect_enable()` in `keyboard_post_init_user()`
- **Triggers:** alpha (a-z) + apostrophe, 5+ chars recommended

---

## 9. STT Correction Pipeline

| Layer | Trigger     | Function                                           |
|-------|-------------|----------------------------------------------------|
| 1     | T (1 tap)   | Raw transcription via ElevenLabs Scribe v2         |
| 2     | T (2 taps)  | L1 + regex corrections + fuzzy lexicon matching    |
| 3     | T (3 taps)  | L1 + L2 + LLM post-processing (stt_postprocess)   |

### STT Corrections (10 regex rules)

| Pattern           | Replacement       |
|-------------------|-------------------|
| clore             | KLOR              |
| queue mk          | QMK               |
| Q.M.K.            | QMK               |
| vial              | Vial              |
| hyperland         | Hyprland          |
| way bar           | Waybar            |
| open router       | OpenRouter        |
| eleven labs       | ElevenLabs        |
| raspberry pi pico | Raspberry Pi Pico |
| rp2040            | RP2040            |

### STT Lexicon Categories

| Category   | Terms Count | Examples                              |
|------------|-------------|---------------------------------------|
| technical  | 28          | KLOR, QMK, Vial, Hyprland, Waybar... |
| energy     | 2           | BESS, aFRR                            |
| business   | 2           | ZynexGroup, Zynex                     |
| danish     | 5           | Kobenhavn, Aarhus, Odense...          |
| personal   | 0           | (empty, user-extensible)              |

---

## 10. HID Protocol Summary

| Command ID | Name               | Direction    | Purpose                  |
|------------|--------------------|--------------|--------------------------|
| 0x20       | CMD_BRIDGE_ACTION  | FW → Host    | Dispatch action          |
| 0x21       | CMD_BRIDGE_STATUS  | Host → FW    | Status update            |
| 0x22       | CMD_BRIDGE_HEARTBEAT | Bidirectional | Connection health      |
| 0x23       | CMD_BRIDGE_CONFIG  | Host → FW    | Config update            |

### Special Action IDs (non-letter)

| ID   | Name                  | Trigger            |
|------|-----------------------|--------------------|
| 0x10 | ACTION_STT            | T key (depth 1-3)  |
| 0x11 | ACTION_BRIGHTNESS_UP  | Right encoder CW   |
| 0x12 | ACTION_BRIGHTNESS_DOWN| Right encoder CCW  |
