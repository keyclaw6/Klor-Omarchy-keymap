# KLOR AI Writing Workstation

Custom QMK/Vial firmware and AI bridge daemon for the [KLOR split keyboard](https://github.com/GEIGEIGEIST/KLOR) (RP2040, Polydactyl layout). Transforms a mechanical keyboard into an AI-powered writing tool with on-device command dispatch, LLM text transformations, speech-to-text, Danish character support on the RAISE layer, and 4,200+ autocorrect entries.

Built for daily use on Arch Linux / [Omarchy](https://omarchy.com) (Hyprland/Wayland). Windows support included.

## How It Works

The system has two parts:

1. **Firmware** (runs on the keyboard) — Handles typing, layers, home row mods, Danish characters, autocorrect, and detects command mode activation. When you trigger a command, the keyboard sends a 32-byte USB HID packet to the host.

2. **Bridge daemon** (runs on your computer) — A Python asyncio service that listens for those HID packets, routes them to OpenRouter (LLM) or ElevenLabs (speech-to-text), and writes results to your clipboard. You paste when ready.

```
┌─────────────┐    Raw HID (USB)     ┌──────────────┐
│  KLOR Kbd   │ ──────────────────> │ Bridge Daemon │
│  (RP2040)   │   32-byte packets    │  (Python)     │
│  QMK/Vial   │ <────────────────── │  asyncio      │
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
| **T** | Speech-to-text | Starts recording; tap 1-3 times for correction depth |
| **ESC** | Cancel | Exits command mode (stops STT if recording) |

All 26 letter keys are mapped in firmware. 18 are unconfigured placeholders — assign them to custom prompts by editing `actions.yml` and `prompts.yml`. No firmware reflash needed.

**Output behavior:** Results are written to clipboard only. Paste manually with Ctrl+V. This is intentional — it avoids focus-stealing and gives you control over placement.

## Speech-to-Text

After entering command mode (double-tap RALT), tap **T** 1-3 times to select correction depth:

| Taps | Pipeline | Description |
|------|----------|-------------|
| T x1 | Layer 1 | Raw ElevenLabs Scribe v2 transcription |
| T x2 | L1 + L2 | + domain-specific corrections (regex + fuzzy lexicon matching) |
| T x3 | L1+L2+L3 | + LLM post-processing for grammar cleanup |

Recording starts automatically. Press **RALT** or **T** again to stop. Result is copied to clipboard.

Notification behavior is hardened for Omarchy/mako:

- `Recording...` and `Processing transcription...` are finite notifications and should clear correctly after STT state changes
- `Processing with LLM...` is also treated as a finite flow notification
- STT notifications are intentionally not sent as critical urgency
- STT, LLM, and prompt-picker notifications now use the same explicit notification-flow lifecycle in the bridge
- These STT and LLM notification behaviors are now verified working and locked; do not change them unless the user explicitly asks

## Prompt Picker

Enter command mode (double-tap RALT), then press **P** to open a searchable popup with reusable text snippets. Select one and its text is copied to your clipboard for pasting.

Snippets are organized by category (Writing, Email, Code, Translation, Analysis, Creative, Prompting) and stored in `~/.config/klor-bridge/snippets.yml`. Ships with 28 default snippets — add your own and restart the bridge.

**Linux:** Uses the custom GTK prompt picker window. It is compact, keyboard-first, and opens once, centered on the monitor under the cursor.
**Windows:** Uses PowerShell `Out-GridView`.

Prompt picker lock:

- The current Linux prompt picker behavior is verified working and locked
- Keep the compact GTK UI, keyboard-first filtering, single-launch centered placement on the cursor's monitor, and clipboard result flow unchanged unless the user explicitly asks for a change

## Brightness Control

The **right rotary encoder** controls monitor brightness:
- **Clockwise** — brightness up (5% per tick, configurable)
- **Counter-clockwise** — brightness down

Works on both Linux and Windows:
- **Linux:** `brightnessctl` for laptop backlight, with `ddcutil` fallback for external monitors
- **Windows:** WMI/PowerShell brightness control

Configure step size and tool preference in `~/.config/klor-bridge/config.yml` under the `brightness:` section. The left encoder remains volume control.

## Danish Characters

Use the **RAISE layer** (hold right thumb): dedicated Unicode Map keys for å/Å, æ/Æ, ø/Ø with shift awareness.

On the base layer, **P**, **;**, and **'** are plain keys again, and semicolon is restored as a normal **RGUI home-row mod**.

## Layers

> [!WARNING]
> The NAV layer, the LOWER screenshot key, the verified notification flows, and the current prompt picker behavior are now locked.
> Treat their current behavior as frozen and do not change them again unless the user explicitly asks.

| # | Layer | Activation | Purpose |
|---|-------|-----------|---------|
| 0 | QWERTY | Default | Home row mods (GACS), one-shot shift |
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
- STT notifications, LLM notifications, and prompt-picker notifications are verified working and must not be changed unless explicitly requested

## Home Row Mods

| Position | Left hand | Right hand |
|----------|-----------|------------|
| Pinky | GUI / A | GUI / ; |
| Ring | ALT / S | ALT / L (LALT, not RALT) |
| Middle | CTL / D | CTL / K |
| Index | SFT / F | SFT / J |

Tuned for reliable typing with minimal misfires:
- `TAPPING_TERM 200` — hold threshold
- `CHORDAL_HOLD` — mod only activates on cross-hand chords
- `HOLD_ON_OTHER_KEY_PRESS` — immediate hold resolution on interrupt
- `FLOW_TAP_TERM 150` — fast typing pass-through
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
- [ElevenLabs](https://elevenlabs.io/) — speech-to-text (optional, only for STT)

## Quick Start

### 1. Flash Firmware

Enter bootloader mode (thumb combo or QK_BOOT), then copy the UF2:

```bash
cp firmware/geigeigeist_klor_2040_vial.uf2 /run/media/$USER/RPI-RP2/
```

### 2. Run Setup

```bash
git clone https://github.com/keyclaw6/Klor-Omarchy-keymap.git
cd Klor-Omarchy-keymap
bash setup.sh
```

Windows:
```powershell
git clone https://github.com/keyclaw6/Klor-Omarchy-keymap.git
cd Klor-Omarchy-keymap
.\setup-windows.ps1
```

### 3. Set API Keys

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

### 4. Start the Bridge

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
5. Restart: `systemctl --user restart klor-bridge`

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
vim keyboards/geigeigeist/klor/keymaps/vial/autocorrect.txt

# Copy to vial-qmk build tree
cp -r keyboards/geigeigeist ~/vial-qmk/keyboards/

# Regenerate trie + compile
cd ~/vial-qmk
qmk generate-autocorrect-data \
    keyboards/geigeigeist/klor/keymaps/vial/autocorrect.txt \
    -kb geigeigeist/klor/2040 -km vial
make -C ~/vial-qmk geigeigeist/klor/2040:vial

# Flash
cp ~/vial-qmk/.build/geigeigeist_klor_2040_vial.uf2 /run/media/$USER/RPI-RP2/
```

## Building Firmware from Source

```bash
# Clone vial-qmk (one-time)
git clone https://github.com/vial-kb/vial-qmk.git ~/vial-qmk
cd ~/vial-qmk && make git-submodule

# Copy keymap source into build tree
cp -r Klor-Omarchy-keymap/keyboards/geigeigeist ~/vial-qmk/keyboards/

# Compile (use make, not qmk compile)
make -C ~/vial-qmk geigeigeist/klor/2040:vial

# Output: ~/vial-qmk/.build/geigeigeist_klor_2040_vial.uf2
```

**Important:** Use `make -C ~/vial-qmk`, not `qmk compile`. The `qmk` CLI resolves to `~/qmk_firmware` which lacks Vial declarations and will fail.

## Vial Compatibility

This firmware is fully [Vial](https://get.vial.today/)-compatible. You can remap keys, combos, tap dances, and key overrides through the Vial GUI while all custom features (Danish characters, command mode, autocorrect, bootloader combo) remain active.

The bridge daemon coexists with Vial's protocol through the `raw_hid_receive_kb()` hook — our commands use IDs 0x20-0x3F while VIA/Vial uses 0x01-0x0F.

## Repository Structure

```
Klor-Omarchy-keymap/
├── bridge/                          # Python bridge daemon + config templates
│   ├── klor-bridge.py               # Linux daemon (Wayland)
│   ├── klor-bridge-windows.py       # Windows daemon
│   ├── config.yml                   # Bridge settings (USB IDs, LLM, STT, brightness)
│   ├── actions.yml                  # Action registry (26 letter keys + STT + brightness)
│   ├── prompts.yml                  # LLM prompt templates
│   ├── snippets.yml                 # Prompt snippet library for Prompt Picker (P key)
│   ├── lexicon.yml                  # Domain vocabulary for STT
│   └── corrections.yml             # Regex corrections for STT
├── keyboards/                       # QMK firmware source
│   └── geigeigeist/klor/keymaps/vial/
│       ├── keymap.c                 # Main firmware (~800 lines)
│       ├── config.h                 # QMK/Vial configuration
│       ├── rules.mk                # Build feature flags
│       ├── vial.json                # Vial GUI descriptor
│       ├── autocorrect.txt          # Autocorrect dictionary (4,200+ entries)
│       └── autocorrect_data.h       # Generated trie (65 KB)
├── firmware/                        # Pre-built firmware
│   └── geigeigeist_klor_2040_vial.uf2
├── systemd/                         # Linux service files
│   ├── klor-bridge.service          # systemd user service
│   └── 99-klor-hid.rules           # udev rule for HID access
├── keymap-reference.html            # Visual keymap (open in browser)
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
