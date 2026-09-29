# KLOR AI Writing Workstation

Custom QMK/ZMK firmware and host tooling for the [KLOR split keyboard](https://github.com/GEIGEIGEIST/KLOR) (RP2040, Polydactyl layout). LLM text actions still use the KLOR bridge; dictation is delegated to OpenWhispr so recording, cleanup, text insertion, history, dictionary and UI live in one maintained application.

Built for daily use on Arch Linux / [Omarchy](https://omarchy.com) (Hyprland/Wayland). Windows support included.

## How It Works

The system has two parts:

1. **Firmware** (runs on the keyboard) — Handles typing, layers, home row mods, Danish characters, autocorrect, and detects command mode activation. When you trigger a command, the keyboard sends a 32-byte USB HID packet to the host.

2. **Host** — The KLOR Python bridge handles non-OpenWhispr Raw HID actions (OpenRouter, prompt picker, brightness). **OpenWhispr** owns both voice modes: T emits F8 for normal dictation; C emits F9 for the Voice Assistant with native screen context. A tiny localhost adapter lets OpenWhispr keep using the existing ElevenLabs Scribe v2 API key.

```
┌─────────────┐    Raw HID (USB)     ┌──────────────┐
│  KLOR Kbd   │ ──────────────────> │ Bridge Daemon │
│  (RP2040)   │   32-byte packets    │  (Python)     │
│  QMK/plain  │ <────────────────── │  asyncio      │
└─────────────┘    status/heartbeat  └──────┬───────┘
                                            │
                              ┌──────────────┼──────────────┐
                              ▼              ▼              ▼
                        ┌──────────┐  ┌──────────┐  ┌──────────┐
                        │ OpenRouter│  │ElevenLabs│  │ Clipboard│
                        │   LLM    │  │ Scribe v2│  │ (result) │
                        └──────────┘  └──────────┘  └──────────┘
```

## Command Mode

**Double-tap Right Alt** to enter command mode, then press a letter key:

| Key | Action | What it does |
|-----|--------|-------------|
| **E** | Prompt Expand | Amplifies highlighted text into a stronger LLM instruction |
| **G** | Grammar | Fixes spelling, grammar, and punctuation (minimal changes) |
| **I** | Improve | Improves writing quality — clearer, more concise |
| **P** | Prompt Picker | Opens searchable popup to insert a text snippet from your library |
| **R** | Email | Rewrites selected text as a Danish/Nordic professional email |
| **S** | Summarize | Condenses selected text to key points |
| **D** | DA → EN | Translates Danish to English |
| **N** | EN → DA | Translates English to Danish |
| **T** | OpenWhispr dictation | Emit F8 and exit command mode |
| **C** | OpenWhispr + screen | Emit F9 Voice Assistant hotkey; OpenWhispr captures screen context |
| **ESC** | Cancel | Exits command mode |

All 26 letter keys are mapped in firmware. T and C are direct OpenWhispr hotkeys; 16 letters remain unconfigured placeholders that can be assigned in `actions.yml`/`prompts.yml` without reflashing firmware.

**Output behavior:** Results are written to clipboard only. Paste manually with Ctrl+V. This is intentional — it avoids focus-stealing and gives you control over placement.

## Voice — OpenWhispr

The old KLOR recorder/depth/correction pipeline is not part of the active path.

- **RALT×2 → T**: firmware emits **F8** for normal OpenWhispr dictation and exits command mode.
- **RALT×2 → C**: firmware emits **F9** for OpenWhispr Voice Assistant and exits command mode. With OpenWhispr's **Share screen context** enabled, OpenWhispr captures the active screen itself and sends it with the spoken assistant command.

Both are stateless in firmware. OpenWhispr is the single source of truth; there is no depth counter, recording flag, screenshot helper, or bridge hop for either key.

Configure OpenWhispr once:

- **Dictation hotkey:** `F8`
- **Voice Assistant hotkey:** `F9`
- **Share screen context:** enabled for Voice Assistant
- **Dictation activation:** Toggle
- **Speech to Text:** Self-Hosted
- **Server URL:** `http://127.0.0.1:8765`
- **Model:** `scribe_v2`

The C action is an assistant command with screenshot context, not ordinary transcript cleanup.

## Prompt Picker

Enter command mode (double-tap RALT), then press **P** to open a searchable popup with reusable text snippets. Select one and its text is copied to your clipboard for pasting.

Snippets are stored in the live file at `~/.config/klor-bridge/snippets.yml`. The bridge reloads that file the next time you open the picker, so snippet edits are live after save.

**Linux:** Uses the custom GTK prompt picker window. It is keyboard-first, opens once, centered on the monitor under the cursor, and uses a taller denser layout so more prompts remain visible at once.
**Windows:** Uses PowerShell `Out-GridView`.

Prompt picker lock:

- The current Linux prompt picker behavior is verified working and locked
- Keep the keyboard-first filtering, single-launch centered placement on the cursor's monitor, visible-selection scrolling, denser taller layout, and clipboard result flow unchanged unless the user explicitly asks for a change

## Brightness Control

The **right rotary encoder** controls monitor brightness:
- **Clockwise** — brightness up
- **Counter-clockwise** — brightness down

The firmware sends standard media keycodes (`KC_BRIU` / `KC_BRID`) directly. On Omarchy external-monitor setups, `setup.sh` installs a Hyprland override that routes those media keys through `~/.config/hypr/brightness-display-ddc.sh`, using DDC/CI instead of Omarchy's default laptop-backlight helper.

The bridge daemon also handles Raw HID brightness action IDs (`0x11`/`0x12`) by calling the same DDC helper when present, then falls back to Omarchy media-key shortcuts.

The left encoder remains volume control.

## Danish Characters

Use the **RAISE layer** (hold right thumb): dedicated Unicode Map keys for å/Å, æ/Æ, ø/Ø with shift awareness.

On the base layer, **P**, **;**, and **'** are plain keys again, and semicolon is restored as a normal **RGUI home-row mod**.

## Layers

> [!WARNING]
> The NAV layer, the LOWER screenshot key, the verified notification flows, and the current prompt picker behavior are now locked.
> Treat their current behavior as frozen and do not change them again unless the user explicitly asks.

| # | Layer | Activation | Purpose |
|---|-------|-----------|---------|
| 0 | QWERTY | Default | Home row mods (GACS), plain left shift (`KC_LSFT`) |
| 1 | LOWER | Hold left thumb | Numbers (numpad layout), arrow keys, brackets, navigation |
| 2 | RAISE | Hold right thumb | Symbols, Unicode Danish, currency (€£¥), Omarchy F-keys |
| 3 | ADJUST | LOWER+RAISE | F1-F24, QK_BOOT (bootloader), AC_TOGG (autocorrect toggle) |
| 4 | NAV | Hold bottom-right | Full Omarchy/Hyprland WM control — workspaces, focus, window management |

See `keymap-reference.html` for a complete visual layout of every key on every layer.

Locked layer contract:

- LOWER bottom-left is plain `KC_PSCR` and must remain the standard host `Print Screen` key
- NAV is navigation-only and must keep workspace switching, move-to-workspace, silent move-to-workspace, group navigation, and resize on the arrow cluster
- NAV arrows use thumb modifiers for focus, swap, group move, monitor move, and resize
- Dedicated group-focus keys `Super+Ctrl+Left/Right` remain on NAV
- LLM and prompt-picker notifications remain verified behavior. The old custom STT notification/overlay path is rollback-only on this branch.

## Home Row Mods

| Position | Left hand | Right hand |
|----------|-----------|------------|
| Pinky | GUI / A | GUI / ; |
| Ring | ALT / S | ALT / L (LALT, not RALT) |
| Middle | CTL / D | CTL / K |
| Index | SFT / F | SFT / J |

Tuned for reliable typing with minimal misfires:
- `TAPPING_TERM 250` — hold threshold
- `PERMISSIVE_HOLD` — resolves intentional rolls into holds sooner
- `CHORDAL_HOLD` — mod only activates on cross-hand chords
- `FLOW_TAP_TERM 150` — fast typing pass-through
- `SPECULATIVE_HOLD` — improves hold responsiveness without replacing native mod-taps
- `QUICK_TAP_TERM 0` — no quick-tap repeat

## Autocorrect

4,200+ entries compiled into a QMK trie (65 KB), active by default on boot. Sources:
- Custom email shortcuts (`:'kb`, `:'kab`, `:'key`)
- Zynex brand corrections
- Common contractions (won't, don't, etc.)
- Getreuer's curated QMK dictionary
- AutoHotkey AutoCorrect classic + HotstringLib
- Wikipedia common misspellings

Toggle on/off: ADJUST layer (LOWER+RAISE), second key from bottom-left (`AC_TOGG`).

## Bootloader Access

**Thumb combo:** Press all 4 thumb keys on one half simultaneously, 5 times within 3 seconds. Each half enters bootloader independently — works even when disconnected from the other half.

**QK_BOOT:** ADJUST layer (LOWER+RAISE), bottom-left key.

## Requirements

**Hardware:**
- KLOR split keyboard (Polydactyl layout, RP2040 MCU)
- USB-C connection to host

**Software (Linux/Wayland):**
- Python 3.10+
- `wtype`, `wl-clipboard` (Wayland clipboard/key simulation)
- Python: `hid` or `hidapi`, `openai`, `pyyaml`, `keyring`, `sounddevice`, `numpy`, `aiohttp`

**Software (Windows):**
- Python 3.10+
- Python: same as above plus `pyautogui`, `pyperclip`

**API Keys:**
- [OpenRouter](https://openrouter.ai/) — LLM text transformations
- [ElevenLabs](https://elevenlabs.io/) — Scribe v2 transcription used by the OpenWhispr localhost adapter

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/keyclaw6/Klor-Omarchy-keymap.git
cd Klor-Omarchy-keymap
```

### 2. Build and Flash Firmware

Build the plain keymap in a stock QMK checkout (default `~/qmk_firmware`; see [Building Firmware from Source](#building-firmware-from-source)), enter bootloader mode (thumb combo or QK_BOOT), then copy the UF2:

```bash
cp ~/qmk_firmware/.build/geigeigeist_klor_2040_plain.uf2 /run/media/$USER/RPI-RP2/
```

### 3. Run Setup

```bash
bash setup.sh
```

Windows:
```powershell
.\setup-windows.ps1
```

### 4. Set API Keys

Stored in your OS keyring — never in config files.

```bash
python3 <<'EOF'
import keyring
keyring.set_password("klor-bridge", "openrouter_key", "sk-or-YOUR-KEY")
EOF

python3 <<'EOF'
import keyring
keyring.set_password("klor-bridge", "elevenlabs_key", "YOUR-KEY")
EOF
```

Or via environment variables: `KLOR_OPENROUTER_KEY`, `KLOR_ELEVENLABS_KEY`.

### 5. Start the Bridge

```bash
systemctl --user enable --now klor-bridge
journalctl --user -u klor-bridge -f   # view logs
```

Supported runtime strategy:

- Normal start/restart path is `systemctl --user enable --now klor-bridge` and `systemctl --user restart klor-bridge`
- Treat the systemd user service as the only supported long-running runtime on Linux
- Do not use ad-hoc manual bridge launches as a normal restart method; they can desync the live session environment and create duplicate bridge processes

Manual/debug mode:
```bash
python3 ~/.config/klor-bridge/klor-bridge.py --verbose
```

Debug mode is for temporary foreground troubleshooting only. Exit it before returning to the supported systemd-managed runtime.

## Customization

### Adding a New Action

No firmware reflash needed:

1. Open `~/.config/klor-bridge/actions.yml`
2. Find an unconfigured placeholder (e.g., `placeholder_b` for the B key)
3. Change `type: unconfigured` to `type: llm_text` and set `prompt_key`
4. Add the prompt template in `~/.config/klor-bridge/prompts.yml`
5. Restart: `systemctl --user restart klor-bridge` (needed for `actions.yml` changes)

Prompt/snippet edit behavior:

- `prompts.yml` text changes are picked up on the next KLOR LLM use; dictation cleanup is configured in OpenWhispr
- `snippets.yml` changes are picked up the next time the prompt picker opens
- `actions.yml`, `config.yml`, bridge code, and setup changes still require a restart or redeploy

## Change Log

### 2026-04-13

- Added prompt/snippet hot reload in the bridge runtime: prompt text changes are now live on next use and snippet library changes are live on next picker open
- Reduced the default prompt snippet library to the current nine prompt-engineering snippets only
- Updated the Linux GTK prompt picker UI: taller window, denser row layout, smaller text and margins, and explicit keep-selection-visible scrolling during keyboard navigation
- Removed the stale `deepinfra` provider preference from the repo config template; the documented provider chain is now `cerebras`, `groq`, then `together`
- Tightened setup/deploy guidance so the documented Linux runtime matches the systemd-managed `~/.config/klor-bridge/` deployment model

Minimal-change maintenance rule:

- Keep future changes minimal and congruent across code, config templates, setup scripts, and docs
- When behavior changes, update both the repo source and the deployed/runtime guidance in the same pass
- Do not let the live bridge gain features that the tracked repo source and setup scripts do not also describe

### Changing the LLM Model

Edit `~/.config/klor-bridge/config.yml`:
```yaml
llm:
  default_model: anthropic/claude-3.5-sonnet  # any OpenRouter model
```

### Adding Autocorrect Entries

Edit the source dictionary, regenerate the trie, compile, and flash:
```bash
# Edit the dictionary
vim keyboards/geigeigeist/klor/keymaps/plain/autocorrect.txt

# Regenerate trie + compile in stock QMK
qmk generate-autocorrect-data \
    keyboards/geigeigeist/klor/keymaps/plain/autocorrect.txt \
    -kb geigeigeist/klor/2040 -km plain
qmk compile -kb geigeigeist/klor/2040 -km plain

# Flash
cp ~/qmk_firmware/.build/geigeigeist_klor_2040_plain.uf2 /run/media/$USER/RPI-RP2/
```

## Building Firmware from Source

Run these commands from the repository root with a normal stock QMK checkout. The examples below assume QMK lives at `~/qmk_firmware`; substitute your own QMK path if needed.

```bash
# Copy keymap source into your stock QMK tree
cp -r keyboards/geigeigeist ~/qmk_firmware/keyboards/
cd ~/qmk_firmware

# Generate autocorrect data if the dictionary changed
qmk generate-autocorrect-data \
    keyboards/geigeigeist/klor/keymaps/plain/autocorrect.txt \
    -kb geigeigeist/klor/2040 -km plain

# Compile the plain keymap
qmk compile -kb geigeigeist/klor/2040 -km plain

# Output: ~/qmk_firmware/.build/geigeigeist_klor_2040_plain.uf2
```

**Important:** Use the stock QMK tree and `qmk compile`; `keymaps/plain` is the only supported firmware path.

## Plain QMK Only

This firmware uses the canonical `keymaps/plain` path and stock QMK build commands only. There is no supported dynamic GUI keymap path.

The bridge daemon talks over the plain keymap's standard `raw_hid_receive()` hook. Firmware-initiated action packets use `host_raw_hid_send()`, and bridge command IDs stay reserved in the 0x20-0x3F range.

## Repository Structure

```
Klor-Omarchy-keymap/
├── bridge/                          # Python bridge daemon + config templates
│   ├── klor-bridge.py               # Linux daemon (Wayland)
│   ├── klor-bridge-windows.py       # Windows daemon
│   ├── openwhispr_elevenlabs_shim.py # Active OpenWhispr → ElevenLabs adapter
│   ├── stt_listening_window.py      # Legacy rollback-only waveform helper
│   ├── config.yml                   # Bridge settings (legacy STT block retained for rollback)
│   ├── actions.yml                  # Action registry (legacy 0x10 STT entry retained)
│   ├── prompts.yml                  # LLM prompt templates
│   ├── snippets.yml                 # Prompt snippet library for Prompt Picker (P key)
│   ├── lexicon.yml                  # Legacy custom STT vocabulary (rollback only)
│   └── corrections.yml             # Legacy custom STT corrections (rollback only)
├── keyboards/                       # QMK firmware source
│   └── geigeigeist/klor/keymaps/plain/
│       ├── keymap.c                 # Main firmware
│       ├── config.h                 # QMK configuration
│       ├── rules.mk                 # Build feature flags
│       ├── autocorrect.txt          # Autocorrect dictionary (4,200+ entries)
│       └── autocorrect_data.h       # Generated trie (65 KB)
├── systemd/                         # Linux service files
│   ├── klor-bridge.service          # systemd user service
│   └── 99-klor-hid.rules           # udev rule for HID access
├── keymap-reference.html            # Visual keymap (open in browser, 4K)
├── 04_4k_klor_layout.txt            # ASCII art keymap reference (plain text, printable)
├── 10_klor_wallpaper_FINAL.html     # 4K HTML desktop wallpaper (3840×2160)
├── setup.sh                         # Linux setup script
├── setup-windows.ps1                # Windows setup script
├── ARCHITECTURE.md                  # Technical design documentation
├── OMARCHY.md                       # Omarchy/Hyprland integration guide
└── README.md                        # This file
```

## Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) — Protocol details, firmware internals, bridge architecture
- [OMARCHY.md](OMARCHY.md) — Hyprland/Omarchy integration (NAV layer, F-key bindings, Unicode)
- [KLOR keyboard](https://github.com/GEIGEIGEIST/KLOR) — Original hardware design by GEIGEIGEIST

## License

This keymap and bridge daemon are provided as-is for the KLOR keyboard community. The KLOR keyboard design is by [GEIGEIGEIST](https://github.com/GEIGEIGEIST/KLOR).
