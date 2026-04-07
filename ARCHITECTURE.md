# Architecture

Technical reference for the KLOR AI Writing Workstation. Covers the firmware, bridge daemon, communication protocol, and integration points.

## System Overview

The system has two halves that communicate over USB Raw HID:

1. **Firmware** (RP2040, QMK/Vial) — Handles typing, layers, home row mods, Danish characters, autocorrect, and command mode detection. When a command action is triggered, it sends a 32-byte HID packet to the host.

2. **Bridge daemon** (Python, asyncio) — Listens for HID packets, dispatches to OpenRouter LLM or ElevenLabs STT, and writes results to the clipboard via platform tools (wl-clipboard on Linux, pyperclip on Windows). Results are never auto-pasted — the user pastes manually with Ctrl+V.

```
┌─────────────────────────────────────────┐
│            KLOR Keyboard (RP2040)        │
│                                          │
│  ┌──────────┐  ┌───────────┐  ┌───────┐ │
│  │ Layers   │  │ Danish    │  │ Auto- │ │
│  │ HRM/OSM  │  │ Hold Keys │  │ corr. │ │
│  └──────────┘  └───────────┘  └───────┘ │
│  ┌──────────────────────────────────────┐│
│  │ Command Mode State Machine           ││
│  │ (double-tap RALT → action dispatch)  ││
│  └──────────────────────────────────────┘│
│         │ host_raw_hid_send()            │
└─────────┼────────────────────────────────┘
          │ USB Raw HID (32-byte packets)
          │ VID=0x3A3C  PID=0x0001
          │ usage_page=0xFF60  usage=0x61
          ▼
┌─────────┼────────────────────────────────┐
│         │ HIDConnection.read()           │
│  ┌──────────────────────────────────────┐│
│  │ Bridge Daemon (Python asyncio)       ││
│  │                                      ││
│  │  ┌──────────┐  ┌──────────┐         ││
│  │  │ LLMClient│  │STTPipeline│        ││
│  │  │(OpenRouter)  │(ElevenLabs)│       ││
│  │  └──────────┘  └──────────┘         ││
│  │  ┌──────────────────────────┐       ││
│  │  │ Platform (clipboard)     │       ││
│  │  └──────────────────────────┘       ││
│  └──────────────────────────────────────┘│
│            Host Computer                 │
└──────────────────────────────────────────┘
```

## Firmware Architecture

**Source:** `keyboards/geigeigeist/klor/keymaps/vial/keymap.c` (~800 lines)

### Layers

| # | Name | Purpose |
|---|------|---------|
| 0 | `_QWERTY` | Base layer. Home row mods (GACS), one-shot shift |
| 1 | `_LOWER` | Left thumb hold. Numbers, navigation, brackets |
| 2 | `_RAISE` | Right thumb hold. Symbols, Unicode Danish (æ/ø/å via Unicode Map), currency |
| 3 | `_ADJUST` | LOWER+RAISE (tri-layer). F-keys (F1-F24), QK_BOOT, AC_TOGG |
| 4 | `_NAV` | Bottom-right key hold. Full Omarchy/Hyprland window manager control — every key sends `LGUI(key)`, compose with thumb SHIFT/CTRL/ALT for all WM operations |

### Home Row Mods

Left hand (pinky to index): GUI / ALT / CTL / SFT on A / S / D / F.
Right hand (index to ring): SFT / CTL / ALT on J / K / L.

The right pinky (semicolon position) is restored as `RGUI_T(KC_SCLN)`. HRM_L uses `LALT_T` (not RALT) to avoid AltGr conflicts on the RAISE layer.

Tuning:
- `TAPPING_TERM 200` — hold duration before mod activates
- `QUICK_TAP_TERM 0` — disables quick-tap repeat
- `CHORDAL_HOLD` — only activates mod when keys are on opposite hands
- `HOLD_ON_OTHER_KEY_PRESS` — resolves hold immediately when another key is pressed
- `FLOW_TAP_TERM 150` — flow-tap threshold for rapid typing

### Danish Characters

Danish characters are available on the RAISE layer via QMK Unicode Map. The base layer uses plain `P`, `;`, and `'` again.

### One-Shot Shift

Left thumb: `OSM(MOD_LSFT)`. Tap once → next keypress is shifted, then shift auto-releases. Double-tap → toggle (acts as caps lock). Times out after 3 seconds (`ONESHOT_TIMEOUT 3000`).

### Bootloader Combo

Press all 4 thumb keys on one half simultaneously, 5 times consecutively within 3 seconds, to enter UF2 bootloader (`reset_keyboard()`). Works per-half — each half can enter bootloader independently, even when disconnected from the other half for flashing.

Implementation: `boot_combo_tick()` in `matrix_scan_user()` reads the live key matrix via `matrix_is_on()`. Thumb key matrix positions:
- Left half: row 3, cols 1-4 (L31, L32, L33, L34)
- Right half: row 7, cols 1-4 (R31, R32, R33, R34)

State machine detects rising edges (all 4 pressed where they weren't before), counts consecutive presses, and resets the count if the 3-second window expires.

### Autocorrect

QMK's built-in autocorrect feature with a trie-based dictionary (~4,200 entries, 65 KB).

- Source dictionary: `keyboards/geigeigeist/klor/keymaps/vial/autocorrect.txt`
- Generated trie: `keyboards/geigeigeist/klor/keymaps/vial/autocorrect_data.h`
- Triggers are alpha-only (a-z) and apostrophe, minimum 5 characters to avoid false positives
- Corrections can contain any character (uses `send_string`)
- `:` prefix in the source file marks word-boundary-only matches

Sources merged into the dictionary:
- Custom email shortcuts (`:'kb`, `:'kab`, `:'key`)
- Zynex brand corrections
- Common contractions
- Getreuer's curated QMK dictionary (~400 entries)
- AutoHotkey AutoCorrect classic script (~2,500 entries)
- AutoCorrect2 HotstringLib by kunkel321 (~4,000 entries)
- Wikipedia common misspellings list (~3,000 entries)
- After deduplication and conflict removal: ~4,200 unique entries

**Constraints:**
- Trie uses 16-bit byte offsets → max 65,535 bytes (~4,200 entries at ~15 bytes/entry average)
- Triggers must not be substrings of each other (shorter match prevents longer from firing)
- If the typo is a prefix of the correction, the backspace formula goes negative — these entries are filtered out during generation
- The `@` character is not trackable by the autocorrect engine

Regenerate after editing:
```bash
cd ~/vial-qmk
qmk generate-autocorrect-data \
    keyboards/geigeigeist/klor/keymaps/vial/autocorrect.txt \
    -kb geigeigeist/klor/2040 -km vial
make -C ~/vial-qmk geigeigeist/klor/2040:vial
```

## Command Mode & HID Protocol

### Entering Command Mode

Double-tap right ALT within 250ms (`RALT_TAP_WINDOW`). Manual state machine in `process_ralt_tap()` — QMK's `tap_dance_actions[]` cannot be used because Vial owns that array.

- 1 tap: normal RALT (registered on press, unregistered on release)
- 2 taps: enter command mode (second tap is consumed, RALT not registered)
- Window expiry: tap count resets
- Any non-RALT keypress: tap count resets

While STT is recording, a single RALT press stops recording immediately (bypasses the double-tap detection).

### Command Mode Dispatch

Once active, the next letter keypress is intercepted by `process_command_mode()`:

1. `cmd_action_for_key(keycode)` maps the keycode to an action ID
2. Mod-tap wrappers (`LGUI_T(KC_A)` etc.) are stripped to extract the base keycode
3. All 26 letters return their ASCII uppercase code (0x41-0x5A)
4. T (KC_T) returns 0xFF sentinel → enters STT tap-counting path
5. ESC cancels command mode (also stops STT if recording)
6. Any unmapped key exits command mode and passes through

Command mode times out after 3 seconds (`COMMAND_MODE_TIMEOUT`).

### Action ID Scheme

```
Letter  Hex   Action
A       0x41  unconfigured
B       0x42  unconfigured
C       0x43  unconfigured
D       0x44  translate_da_en
E       0x45  prompt_expand
F       0x46  unconfigured
G       0x47  fix_grammar
H       0x48  unconfigured
I       0x49  improve_writing
J       0x4A  unconfigured
K       0x4B  unconfigured
L       0x4C  unconfigured
M       0x4D  unconfigured
N       0x4E  translate_en_da
O       0x4F  unconfigured
P       0x50  prompt_picker
Q       0x51  unconfigured
R       0x52  write_email
S       0x53  summarize
T       0xFF  → ACTION_STT (0x10) with depth param
U       0x55  unconfigured
V       0x56  unconfigured
W       0x57  unconfigured
X       0x58  unconfigured
Y       0x59  unconfigured
Z       0x5A  unconfigured

Special (non-command-mode, sent directly by firmware):
0x10    ACTION_STT             — Speech-to-text toggle (T key via command mode)
0x11    ACTION_BRIGHTNESS_UP   — Right encoder clockwise
0x12    ACTION_BRIGHTNESS_DOWN — Right encoder counter-clockwise
```

Unconfigured IDs are valid in firmware — the bridge logs a notice and does nothing. To assign an action, edit `actions.yml` and `prompts.yml` only (no firmware reflash).

### STT Tap Counting

The T key uses a separate path for selecting STT correction depth:

1. First T press: start counting, `stt_tap_count = 1`, start 300ms window
2. Additional T presses within window: increment count (max 3)
3. Window expires OR different key pressed: finalize → `bridge_send_action(ACTION_STT, count)`
4. Count 3 reached: finalize immediately

Depth meanings:
- 1 = Layer 1 only (raw transcription)
- 2 = L1 + Layer 2 (domain corrections)
- 3 = L1 + L2 + Layer 3 (LLM post-processing)

### HID Packet Format

All packets are 32 bytes, zero-padded. Protocol uses command IDs 0x20-0x3F; VIA/Vial uses 0x01-0x0F, so they coexist without conflict.

**Firmware → Host (action dispatch):**
```
byte[0] = 0x20 (CMD_BRIDGE_ACTION)
byte[1] = action_id (0x41-0x5A for letters, 0x10 for STT, 0x11/0x12 for brightness)
byte[2] = param (0 for letters/brightness, 1-3 for STT depth)
byte[3..31] = 0x00
```

**Host → Firmware (status/heartbeat):**
```
byte[0] = 0x21 (CMD_BRIDGE_STATUS) or 0x22 (CMD_BRIDGE_HEARTBEAT)
byte[1..31] = payload
```

**Firmware response (via via.c auto-send):**
```
byte[0] = original command ID
byte[1] = 0x01 (ACK) or 0x00 (NACK)
byte[2..31] = 0x00
```

### Vial Coexistence

The bridge protocol hooks into `raw_hid_receive_kb()`, which vial-qmk's `via.c` calls for unrecognized command IDs. Key rules:

- Do NOT call `raw_hid_send()` inside `raw_hid_receive_kb()` — `via.c` calls it automatically after the hook returns
- Modify `data[]` in-place to set the response
- Use `host_raw_hid_send()` (from `host.h`) for firmware-initiated packets — `raw_hid_send()` is not visible when `keymap_introspection.c` includes `keymap.c`
- Command IDs 0x20-0x3F are ours; VIA uses 0x01-0x0F
- Unrecognized IDs set `data[0] = id_unhandled`

## Bridge Daemon Architecture

**Source:** `bridge/klor-bridge.py` (Linux/Wayland, ~865 lines), `bridge/klor-bridge-windows.py` (Windows, ~850 lines)

### Components

```
KlorBridge (main daemon)
├── HIDConnection     — USB Raw HID read/write via hid module (python-hid or hidapi)
├── LLMClient         — OpenRouter API via openai SDK (AsyncOpenAI)
├── STTPipeline       — ElevenLabs Scribe v2 + 3-layer correction
└── Platform          — Clipboard (wl-clipboard / pyperclip), key simulation (wtype / pyautogui)
```

### Event Loop

```
while True:
    if not connected:
        connect() or sleep(reconnect_interval)
        continue

    while connected:
        packet = hid.read()          # non-blocking
        if packet:
            handle_packet(packet)
        if heartbeat_due:
            hid.send_heartbeat()
        sleep(5ms)                   # 200 polls/sec
```

A test socket on `127.0.0.1:19378` accepts TCP connections for injecting simulated HID packets without a physical keyboard. Useful for development and testing.

### Action Dispatch Flow

**LLM text transformation (`llm_text` type):**

```
1. Simulate Ctrl+C → copy selected text to clipboard
2. Wait copy_delay_ms (150ms)
3. Read clipboard → selected text
4. Look up prompt template from prompts.yml
5. Send to OpenRouter: prompt.replace("${text}", selected_text)
6. Write LLM result to clipboard (replaces copied text)
7. Show desktop notification with result length
8. User pastes manually with Ctrl+V when ready
```

Note: The bridge does NOT auto-paste results. This is intentional — it gives the user control over when and where to paste, and avoids focus-stealing issues.

**STT toggle (`stt_toggle` type):**

```
First trigger (start recording):
1. Store depth parameter (1-3)
2. Open sounddevice InputStream (16kHz, mono, float32)
3. Buffer audio chunks in callback
4. Show "Recording..." notification

Second trigger (stop + process):
1. Stop and close audio stream
2. Concatenate audio buffer → numpy array
3. Layer 1: Convert to raw PCM int16 → POST to ElevenLabs Scribe v2
4. Layer 2 (if depth >= 2): regex corrections + fuzzy lexicon matching
5. Layer 3 (if depth >= 3): LLM post-processing via stt_postprocess prompt
6. Write result to clipboard
7. Show "Transcription complete" notification
```

### STT Correction Pipeline

**Layer 1 — Transcription:**
POST audio as raw PCM (int16, 16kHz, mono, no WAV header) to `https://api.elevenlabs.io/v1/speech-to-text`. Parameters: `model_id=scribe_v2`, auto language detection (no hardcoded language), `no_verbatim=true`, `diarize=false`, `timestamps_granularity=none`, `file_format=pcm_s16le_16`, plus lexicon terms as individual `keyterms[]` form fields for vocabulary biasing. Raw PCM avoids WAV container overhead for faster turnaround on short dictation clips.

**Layer 2 — Domain Corrector:**
Two-pass correction on the transcript:
1. Regex substitutions from `corrections.yml` (exact pattern matches, applied in order)
2. Fuzzy matching against `lexicon.yml` terms using Levenshtein distance (threshold=2, min word length=4)

**Layer 3 — LLM Post-processing:**
Sends the corrected transcript through the `stt_postprocess` prompt template via OpenRouter.

### Prompt Picker (`prompt_picker` type)

Activated by double-tap RALT → P. Flow:

```
1. Load snippets from ~/.config/klor-bridge/snippets.yml
2. Format as "category: name" lines
3. Pipe to walker --dmenu (Linux) or Out-GridView (Windows)
4. User selects a snippet from the searchable popup
5. Copy snippet's full text to clipboard
6. Show notification: "Prompt copied — X chars"
```

Snippets are YAML entries with `name`, `category`, and `text` fields. Ships with 28 defaults across 7 categories (Writing, Email, Code, Translation, Analysis, Creative, Prompting).

**Linux launcher fallback chain:** `walker --dmenu` → `fuzzel --dmenu` → `wofi --dmenu` → `rofi -dmenu` → `bemenu`.

### Brightness Control (encoder)

The right rotary encoder sends `ACTION_BRIGHTNESS_UP` (0x11) / `ACTION_BRIGHTNESS_DOWN` (0x12) via Raw HID on every encoder tick. These are custom keycodes handled in `process_record_user` — they are NOT standard keycodes and are consumed before reaching the host OS.

**Linux brightness chain:**
1. `brightnessctl set {step}%+` / `{step}%-` — controls laptop backlight
2. If `brightnessctl` fails and `ddcutil_fallback: true`: `ddcutil setvcp 10 + {step}` / `- {step}` — controls external monitors via DDC/CI

**Windows:** PowerShell WMI call to `WmiMonitorBrightnessMethods.WmiSetBrightness()`.

**Configuration** (`config.yml`):
```yaml
brightness:
  step_percent: 5        # % per encoder tick
  tool: brightnessctl    # or "ddcutil"
  ddcutil_fallback: true # try ddcutil if brightnessctl fails
  notify: false          # show notification on change
```

### Encoder Map

```
Encoder 0 (left):  Volume Down / Volume Up (all layers)
Encoder 1 (right): Brightness Down / Brightness Up (all layers, via bridge)
```

### Configuration Files

All config is in `~/.config/klor-bridge/`:

| File | Purpose |
|------|---------|
| `config.yml` | Bridge settings: USB IDs, LLM params, STT params, platform tools, brightness |
| `actions.yml` | Action registry: maps action IDs (0x41-0x5A, 0x10-0x12) to behaviors |
| `prompts.yml` | LLM prompt templates referenced by `prompt_key` in actions |
| `snippets.yml` | Prompt snippet library for the Prompt Picker (P key) |
| `lexicon.yml` | Domain vocabulary for STT Layer 2 fuzzy matching + ElevenLabs keyterms |
| `corrections.yml` | Regex substitution rules for STT Layer 2 |

### Secrets

API keys are stored in the OS keyring (`gnome-keyring` on Linux, Windows Credential Manager) via Python's `keyring` library. Keys are never in config files or the repository.

| Keyring entry | Env var fallback | Service |
|---------------|-----------------|---------|
| `klor-bridge/openrouter_key` | `KLOR_OPENROUTER_KEY` | OpenRouter LLM |
| `klor-bridge/elevenlabs_key` | `KLOR_ELEVENLABS_KEY` | ElevenLabs STT |

### HID Library Compatibility

Arch Linux ships `python-hid` (required by QMK) which provides `hid.Device`. Most other platforms use `hidapi` (pip) which provides `hid.device`. The bridge detects which API is available at runtime and adapts:

| Library | Class | Open method |
|---------|-------|-------------|
| `hidapi` (pip) | `hid.device()` | `open_path()` / `set_nonblocking(True)` |
| `python-hid` (Arch) | `hid.Device()` | `Device(path=...)` / `.nonblocking = True` |

### Windows Variant

`klor-bridge-windows.py` replaces platform-specific tools:
- `wl-clipboard` → `pyperclip` (clipboard access)
- `wtype` → `pyautogui` (keyboard simulation for Ctrl+C copy)
- `notify-send` → PowerShell toast notifications
- All other logic (HID, LLM, STT pipeline) is identical

## Build System

### Prerequisites

- `vial-qmk` fork cloned to `~/vial-qmk` (NOT `~/qmk_firmware` — the vanilla QMK tree lacks Vial declarations)
- QMK CLI tools installed
- Build target: `geigeigeist/klor/2040` with keymap `vial`

### Build Commands

```bash
# Sync keymap source to vial-qmk
cp -r keyboards/geigeigeist ~/vial-qmk/keyboards/

# Regenerate autocorrect trie (if dictionary changed)
qmk generate-autocorrect-data \
    keyboards/geigeigeist/klor/keymaps/vial/autocorrect.txt \
    -kb geigeigeist/klor/2040 -km vial

# Compile (use make, not qmk compile — avoids ~/qmk_firmware resolution)
make -C ~/vial-qmk geigeigeist/klor/2040:vial

# Copy UF2 to firmware/
cp ~/vial-qmk/.build/geigeigeist_klor_2040_vial.uf2 firmware/
```

### Build Rules

- `COMBO_ENABLE = yes` and `KEY_OVERRIDE_ENABLE = yes` are **required** in `rules.mk`. Setting them to `no` causes `unknown type name 'vial_combo_entry_t'` build errors because Vial's `keymap_introspection.c` depends on these being enabled.
- `RAW_ENABLE = yes` is explicitly set for clarity, though VIA already implies it.
- `PIN_COMPATIBLE = promicro` is a board-level directive inherited from the KLOR PCB config.

### Known Build Warnings

- `CONVERT_TO=promicro_rp2040` deprecation — harmless, comes from KLOR board config
- `LAYOUT` redefinition — harmless, Polydactyl layout macro

### Firmware Size

The compiled UF2 is ~252 KB. The RP2040 has 2 MB flash, so there is ample room. The autocorrect trie accounts for ~65 KB of this.

## System Integration

### Linux (systemd)

`systemd/klor-bridge.service` runs the bridge as a user service, bound to `graphical-session.target`. Security hardening: `NoNewPrivileges`, `ProtectHome=read-only`, `ProtectSystem=strict`, `PrivateTmp`, CPU/memory limits (512 MB, 50% CPU).

`systemd/99-klor-hid.rules` grants the user read/write access to the KLOR's HID device via uaccess:
```
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="3a3c", ATTRS{idProduct}=="0001", MODE="0660", TAG+="uaccess"
```

### Wayland Environment

The bridge needs `WAYLAND_DISPLAY` and `XDG_RUNTIME_DIR` in the systemd user environment for wtype/wl-clipboard to work. The Hyprland autostart imports these:
```
exec-once = systemctl --user import-environment WAYLAND_DISPLAY XDG_RUNTIME_DIR
```

## Extending the System

### Adding a New LLM Action

No firmware change required:

1. In `actions.yml`: change an unconfigured placeholder's `type` to `llm_text`, set `prompt_key`
2. In `prompts.yml`: add the corresponding template with `${text}` placeholder
3. Restart: `systemctl --user restart klor-bridge`

### Adding a New Action Type

If you need behavior beyond `llm_text`, `stt_toggle`, and `prompt_picker`:

1. Add a handler method in `KlorBridge` (e.g., `_handle_my_type()`)
2. Add the dispatch case in `_dispatch_action()`
3. Register in `actions.yml` with `type: my_type`

### Adding Autocorrect Entries

Edit `keyboards/geigeigeist/klor/keymaps/vial/autocorrect.txt`, regenerate the trie, and reflash. Rules:
- Triggers: alpha only (a-z) and apostrophe, 5+ characters recommended
- `:` prefix for word-boundary-only matches
- No substring conflicts between triggers
- Corrections can contain any character
- Max trie size: 65,535 bytes (~4,200 entries)

### Changing STT Language

By default, language is auto-detected (ElevenLabs detects Danish, English, and other languages automatically). To force a specific language, edit `config.yml`:
```yaml
stt:
  language: eng  # ISO 639-3 code (dan, eng, deu, fra, etc.)
```
