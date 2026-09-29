# Architecture

Technical reference for the KLOR AI Writing Workstation. Covers the firmware, bridge daemon, communication protocol, and integration points.

## System Overview

The active system has three responsibilities with a deliberately narrow boundary:

1. **Firmware (QMK or ZMK)** — typing/layers plus command-mode input. Non-dictation actions use the existing 32-byte Raw HID protocol. Dictation never sends audio or STT packets; T emits the OpenWhispr F8 hotkey directly.
2. **KLOR bridge (Python)** — handles non-dictation actions such as OpenRouter transformations, prompt picker and bridge-side helpers. Legacy custom STT code remains in source for rollback but `LEGACY_STT_ENABLED = False` prevents it from starting.
3. **OpenWhispr** — owns microphone capture, dictation state, cleanup, custom dictionary, history and text insertion. Its Self-Hosted transcription request goes to a localhost protocol adapter, which forwards the audio to ElevenLabs Scribe v2 using the existing keyring credential.

```text
KLOR keyboard
├─ normal command letter ── Raw HID ──> KLOR bridge ──> OpenRouter / helpers
└─ command T ────────────── F8 ───────> OpenWhispr
                                             │
                                             ├─ record / cleanup / insert
                                             └─ POST localhost:8765/audio/transcriptions
                                                    └─ ElevenLabs Scribe v2
```

See `OPENWHISPR.md` for host configuration, credential reuse, acceptance testing and rollback.

## Firmware Architecture

**Source:** `keyboards/geigeigeist/klor/keymaps/plain/keymap.c` (plain keymap)

### Layers

> [!WARNING]
> `_NAV`, the LOWER screenshot key, the verified STT/LLM notification flows, and the current prompt picker behavior are locked.
> Their current behavior is the accepted stable contract.
> Do not edit them again unless the user explicitly requests a change.

| # | Name | Purpose |
|---|------|---------|
| 0 | `_QWERTY` | Base layer. Home row mods (GACS), plain left shift (`KC_LSFT`) |
| 1 | `_LOWER` | Left thumb hold. Numbers, navigation, brackets |
| 2 | `_RAISE` | Right thumb hold. Symbols, Unicode Danish (æ/ø/å via Unicode Map), currency |
| 3 | `_ADJUST` | LOWER+RAISE (tri-layer). F-keys (F1-F24), QK_BOOT, AC_TOGG |
| 4 | `_NAV` | Bottom-right key hold. Full Omarchy/Hyprland window manager control — every key sends `LGUI(key)`, compose with thumb SHIFT/CTRL/ALT for all WM operations |

Locked behavior summary:

- `_LOWER` bottom-left is plain `KC_PSCR`
- `_NAV` numbers are `Super+1..0` with `Shift` for move-to-workspace and `Shift+Alt` for silent move
- `_NAV` arrows are custom navigation keycodes that map to focus, swap, move-into-group, move-workspace-to-monitor, and resize depending on held thumb mods
- `_NAV` keeps dedicated `Super+Ctrl+Left/Right` group focus keys

### Home Row Mods

Left hand (pinky to index): GUI / ALT / CTL / SFT on A / S / D / F.
Right hand (index to ring): SFT / CTL / ALT on J / K / L.

The right pinky (semicolon position) is restored as `RGUI_T(KC_SCLN)`. HRM_L uses `LALT_T` (not RALT) to avoid AltGr conflicts on the RAISE layer.

Tuning:
- `TAPPING_TERM 250` — hold duration before mod activates
- `PERMISSIVE_HOLD` — resolves intentional rolls into holds sooner
- `QUICK_TAP_TERM 0` — disables quick-tap repeat
- `CHORDAL_HOLD` — only activates mod when keys are on opposite hands
- `FLOW_TAP_TERM 150` — flow-tap threshold for rapid typing
- `SPECULATIVE_HOLD` — improves hold responsiveness while keeping native QMK mod-taps

### Danish Characters

Danish characters are available on the RAISE layer via QMK Unicode Map. The base layer uses plain `P`, `;`, and `'` again.

### Left Thumb Shift

Left thumb: plain `KC_LSFT`. Standard hold-to-shift behavior. `ONESHOT_TIMEOUT` and `ONESHOT_TAP_TOGGLE` are defined in `config.h` but no OSM key is active in the current keymap.

### Bootloader Combo

Press all 4 thumb keys on one half simultaneously, 5 times consecutively within 3 seconds, to enter UF2 bootloader (`reset_keyboard()`). Works per-half — each half can enter bootloader independently, even when disconnected from the other half for flashing.

Implementation: `boot_combo_tick()` in `matrix_scan_user()` reads the live key matrix via `matrix_is_on()`. Thumb key matrix positions:
- Left half: row 3, cols 1-4 (L31, L32, L33, L34)
- Right half: row 7, cols 1-4 (R31, R32, R33, R34)

State machine detects rising edges (all 4 pressed where they weren't before), counts consecutive presses, and resets the count if the 3-second window expires.

### Autocorrect

QMK's built-in autocorrect feature with a trie-based dictionary (~4,200 entries, 65 KB).

- Source dictionary: `keyboards/geigeigeist/klor/keymaps/plain/autocorrect.txt`
- Generated trie: `keyboards/geigeigeist/klor/keymaps/plain/autocorrect_data.h`
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
qmk generate-autocorrect-data \
    keyboards/geigeigeist/klor/keymaps/plain/autocorrect.txt \
    -kb geigeigeist/klor/2040 -km plain
qmk compile -kb geigeigeist/klor/2040 -km plain
```

## Command Mode & HID Protocol

### Entering Command Mode

Double-tap right ALT within 350ms (`RALT_TAP_WINDOW`). Manual state machine in `process_ralt_tap()` — QMK's `tap_dance_actions[]` cannot be used, so the keymap handles the taps explicitly.

- 1 tap: normal RALT (registered on press, unregistered on release)
- 2 taps: enter command mode (second tap is consumed, RALT not registered)
- Window expiry: tap count resets
- Any non-RALT keypress: tap count resets

### Command Mode Dispatch

Once active, the next letter keypress is intercepted by `process_command_mode()`:

1. `cmd_action_for_key(keycode)` maps the keycode to an action ID
2. Mod-tap wrappers (`LGUI_T(KC_A)` etc.) are stripped to extract the base keycode
3. All 26 letters return their ASCII uppercase code (0x41-0x5A)
4. T (KC_T) returns 0xFF sentinel → emit one F8 OpenWhispr toggle and exit command mode
5. ESC cancels command mode
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
T       0xFF  → OpenWhispr F8 toggle (no Raw HID packet)
U       0x55  unconfigured
V       0x56  unconfigured
W       0x57  unconfigured
X       0x58  unconfigured
Y       0x59  unconfigured
Z       0x5A  unconfigured

Special / reserved:
0x10    ACTION_STT             — legacy custom-STT rollback ID; current firmware does not send it
0x11    ACTION_BRIGHTNESS_UP   — Right encoder clockwise
0x12    ACTION_BRIGHTNESS_DOWN — Right encoder counter-clockwise
```

Unconfigured IDs are valid in firmware — the bridge logs a notice and does nothing. To assign an action, edit `actions.yml` and `prompts.yml` only (no firmware reflash).

### OpenWhispr Dictation State

There is deliberately **no firmware-side OpenWhispr state**.

Each command-mode T press emits exactly one F8 key tap and exits command mode. Starting and stopping are therefore the same stateless operation from the keyboard's perspective. To toggle again, enter command mode again and press T.

This keeps OpenWhispr as the single source of truth and prevents drift if recording ends from OpenWhispr's UI, an error, timeout, or any other app-side path. There is no 300 ms T-tap window, no 1/2/3 depth parameter, and no firmware STT packet in the active path.

### HID Packet Format

All packets are 32 bytes, zero-padded. The bridge uses command IDs 0x20-0x3F and stays outside normal QMK control traffic.

**Firmware → Host (action dispatch):**
```
byte[0] = 0x20 (CMD_BRIDGE_ACTION)
byte[1] = action_id (0x41-0x5A for bridge-routed letters, 0x11/0x12 for brightness)
byte[2] = param (0 for current actions)

0x10 remains reserved only for the disabled legacy STT rollback path; current firmware does not emit it.
byte[3..31] = 0x00
```

**Host → Firmware (status/heartbeat):**
```
byte[0] = 0x21 (CMD_BRIDGE_STATUS) or 0x22 (CMD_BRIDGE_HEARTBEAT)
byte[1..31] = payload
```

**Firmware response from the plain Raw HID hook:**
```
byte[0] = original command ID
byte[1] = 0x01 (ACK) or 0x00 (NACK)
byte[2..31] = 0x00
```

### Raw HID Bridge Contract

The bridge protocol hooks into `raw_hid_receive()`, which the plain keymap uses for bridge packets. Key rules:

- `raw_hid_receive()` handles host-initiated bridge packets and returns immediate ACK/NACK responses with `raw_hid_send()`
- Modify `data[]` in place before the immediate response
- Use `host_raw_hid_send()` (from `host.h`) only for firmware-initiated action packets
- Command IDs 0x20-0x3F are ours
- Unrecognized IDs are ignored

## Bridge Daemon Architecture

**Source:** `bridge/klor-bridge.py` (Linux/Wayland, 1,607 lines), `bridge/klor-bridge-windows.py` (Windows, 1,139 lines)

### Components

```
KlorBridge (main daemon)
├── HIDConnection     — USB Raw HID read/write via hid module (python-hid or hidapi)
├── LLMClient         — OpenRouter API via openai SDK (AsyncOpenAI)
├── STTPipeline       — legacy rollback-only custom STT code; not instantiated
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

### OpenWhispr Dictation Integration

Dictation is intentionally outside `KlorBridge._dispatch_action()`. Current firmware does not send `ACTION_STT (0x10)`. If a legacy 0x10 packet nevertheless arrives, `stt_toggle` is ignored while `LEGACY_STT_ENABLED = False`.

`bridge/openwhispr_elevenlabs_shim.py` is the only KLOR-owned component on the active dictation data path. It:

1. listens only on `127.0.0.1:8765`;
2. accepts OpenWhispr's Self-Hosted `POST /audio/transcriptions` (or `/v1/audio/transcriptions`) multipart contract;
3. reads the ElevenLabs key from env or the existing `klor-bridge/elevenlabs_key` keyring slot;
4. maps OpenWhispr's optional language/model/dictionary prompt to Scribe v2 fields;
5. forwards the original encoded audio bytes to ElevenLabs; and
6. returns the OpenAI-style JSON shape `{ "text": "..." }` that OpenWhispr expects.

OpenWhispr, not the adapter, performs dictation cleanup and text insertion. Its custom dictionary prompt is translated into repeated ElevenLabs `keyterms[]` fields.

The old `STTPipeline`, waveform UI, correction pipeline, lexicon/corrections and flow verifier are retained as rollback material only.

### Prompt Picker (`prompt_picker` type)

Activated by double-tap RALT → P. Flow:

```
1. Reload snippets from ~/.config/klor-bridge/snippets.yml if the file changed since the last picker open
2. Format title-only picker rows with collision-safe labels
3. Launch the GTK picker helper on Linux once, centered on the monitor under the cursor
4. User selects a snippet from the searchable popup
5. Copy snippet's full text to clipboard
6. Show notification: "Prompt copied — X chars"
```

Snippets are YAML entries with `name`, `category`, and `text` fields.

The current Linux prompt picker behavior is verified working and locked. Do not change its GTK helper path, single-launch centered placement on the cursor's monitor, visible-selection scrolling, denser taller layout, or clipboard result flow unless the user explicitly requests it.

### Brightness Control (encoder)

The right rotary encoder uses custom keycodes `BRIGHT_UP` / `BRIGHT_DOWN` (defined as `QK_KB_0` / `QK_KB_1`), handled in `process_record_user`. Each tick taps `KC_BRIU` / `KC_BRID` — standard media brightness keycodes.

On Omarchy external-monitor setups, `setup.sh` installs `~/.config/hypr/brightness-display-ddc.sh` plus Hyprland media-key overrides so those standard brightness keys adjust DDC/CI brightness instead of Omarchy's default laptop-backlight helper.

The bridge daemon also handles brightness action IDs `0x11` (`ACTION_BRIGHTNESS_UP`) / `0x12` (`ACTION_BRIGHTNESS_DOWN`) by calling the same DDC helper when present, then falling back to Omarchy media-key shortcuts.

**Configuration** (`config.yml`):
```yaml
brightness:
  step_percent: 5        # % per encoder tick (used only if bridge brightness path is active)
  tool: brightnessctl    # or "ddcutil"
  ddcutil_fallback: true # try ddcutil if brightnessctl fails
  notify: false          # show notification on change
```

### Encoder Map

```
Encoder 0 (left):  Volume Down / Volume Up (all layers)
Encoder 1 (right): Brightness Down / Brightness Up (all layers, via KC_BRID / KC_BRIU media keys)
```

### Configuration Files

All config is in `~/.config/klor-bridge/`:

| File | Purpose |
|------|---------|
| `config.yml` | Bridge settings: USB IDs, LLM params, platform tools, brightness; legacy STT block retained for rollback |
| `actions.yml` | Action registry for bridge actions; legacy 0x10 STT entry retained but inactive |
| `prompts.yml` | LLM prompt templates referenced by `prompt_key` in actions; reloaded live on next use |
| `snippets.yml` | Prompt snippet library for the Prompt Picker (P key); reloaded live on next picker open |
| `lexicon.yml` | Legacy custom STT vocabulary; use OpenWhispr Custom Dictionary for the active path |
| `corrections.yml` | Legacy custom STT correction rules; active cleanup belongs to OpenWhispr |

### Secrets

API keys are stored in the OS keyring (`gnome-keyring` on Linux, Windows Credential Manager) via Python's `keyring` library. Keys are never in config files or the repository.

| Keyring entry | Env var fallback | Service |
|---------------|-----------------|---------|
| `klor-bridge/openrouter_key` | `KLOR_OPENROUTER_KEY` | OpenRouter LLM |
| `klor-bridge/elevenlabs_key` | `KLOR_ELEVENLABS_KEY` (or adapter-only `ELEVENLABS_API_KEY`) | ElevenLabs Scribe via OpenWhispr adapter |

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
- Non-dictation HID/LLM behavior remains parallel; legacy STT stays disabled on both variants

## Build System

### Prerequisites

- Stock QMK tree cloned to `~/qmk_firmware` or another maintained local QMK checkout
- QMK CLI tools installed
- Build target: `geigeigeist/klor/2040` with keymap `plain`

### Build Commands

```bash
# Sync keymap source to the stock QMK tree
cp -r keyboards/geigeigeist ~/qmk_firmware/keyboards/
cd ~/qmk_firmware

# Regenerate autocorrect trie (if dictionary changed)
qmk generate-autocorrect-data \
    keyboards/geigeigeist/klor/keymaps/plain/autocorrect.txt \
    -kb geigeigeist/klor/2040 -km plain

# Compile the plain keymap
qmk compile -kb geigeigeist/klor/2040 -km plain

# Copy UF2 to your flash volume
cp ~/qmk_firmware/.build/geigeigeist_klor_2040_plain.uf2 /run/media/$USER/RPI-RP2/
```

### Build Rules

- `TRI_LAYER_ENABLE = yes` keeps LOWER+RAISE = ADJUST.
- `KEY_OVERRIDE_ENABLE = yes` remains enabled for the keymap's overrides.
- `RAW_ENABLE = yes` is explicitly set for the bridge protocol.
- `PIN_COMPATIBLE = promicro` is a board-level directive inherited from the KLOR PCB config.

### Known Build Warnings

- `LTO_ENABLE in rules.mk is overwriting build.lto in info.json` - harmless board configuration overlap.
- `Feature audio is specified in both info.json ... and rules.mk (True). The rules.mk value wins.` - harmless board configuration overlap.
- `Invalid keyboard.json location detected: keyboards/geigeigeist/klor/keyboard.json.` - inherited KLOR tree layout warning from current QMK metadata validation.
- `LAYOUT` redefinition - harmless Polydactyl layout macro alias.

### Firmware Size

The current plain UF2 is 228,352 bytes (223 KiB). The RP2040 has 2 MB flash, so there is ample room. The autocorrect trie accounts for ~65 KB of this.

## System Integration

### Linux (systemd)

`systemd/klor-bridge.service` runs the non-dictation bridge as a user service. `systemd/openwhispr-elevenlabs.service` runs the loopback transcription adapter. OpenWhispr itself is the desktop application that owns microphone capture and insertion.

Supported runtime contract:

- The supported normal runtime is the user service only
- Supported restart command: `systemctl --user restart klor-bridge`
- Foreground manual runs are debug-only and should not be left running in parallel with the user service
- Do not use root-owned manual bridge launches; they can break cache ownership, duplicate bridge processes, and desynchronize the Wayland session environment

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
3. Restart: `systemctl --user restart klor-bridge` only if you changed `actions.yml`; prompt text edits in `prompts.yml` are picked up on the next use

## Repository Hygiene

### 2026-04-13 Cleanup

- Synced the repository documentation with the current runtime model: the supported Linux runtime is the user systemd service reading `~/.config/klor-bridge/`
- Documented live reload for `prompts.yml` and `snippets.yml`
- Documented the current prompt-picker UI contract after the scrolling and density fix
- Removed the stale `deepinfra` provider preference from the repo config template
- Reduced the default snippet library to the nine prompt-engineering snippets currently in use

### Maintenance Rule

- Keep behavior, config templates, setup scripts, and docs aligned in the same change set
- Prefer the smallest correct repo change that restores congruence
- If the live deployed bridge behavior changes, the tracked repo source and docs must be updated in the same pass

### Adding a New Action Type

If you need a new bridge action type beyond `llm_text` and `prompt_picker`:

1. Add a handler method in `KlorBridge` (e.g., `_handle_my_type()`)
2. Add the dispatch case in `_dispatch_action()`
3. Register in `actions.yml` with `type: my_type`

### Adding Autocorrect Entries

Edit `keyboards/geigeigeist/klor/keymaps/plain/autocorrect.txt`, regenerate the trie, and reflash. Rules:
- Triggers: alpha only (a-z) and apostrophe, 5+ characters recommended
- `:` prefix for word-boundary-only matches
- No substring conflicts between triggers
- Corrections can contain any character
- Max trie size: 65,535 bytes (~4,200 entries)

### Changing Dictation Language

Set the preferred/forced transcription language in OpenWhispr. Its Self-Hosted request forwards the selected language to the localhost adapter, which maps it to ElevenLabs `language_code`. Leave OpenWhispr on automatic language selection to let Scribe detect Danish/English dynamically.

Legacy `config.yml -> stt.language` is not consulted by the active OpenWhispr path.
