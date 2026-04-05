# KLOR AI Writing Workstation

Custom QMK/Vial firmware and AI bridge daemon for the [KLOR split keyboard](https://github.com/GEIGEIGEIST/KLOR) (RP2040 Polydactyl). Transforms a mechanical keyboard into an AI-powered writing tool with LLM text transformations, speech-to-text, Danish character support, and autocorrect.

## What It Does

**Triple-tap Right Alt** to enter command mode, then press a letter key to trigger an action:

| Key | Action | Description |
|-----|--------|-------------|
| I | Improve | Improve writing quality of selected text |
| R | Rewrite | Rephrase selected text differently |
| E | Expand | Add more detail to selected text |
| G | Grammar | Fix grammar and spelling errors |
| S | Summarize | Condense selected text to key points |
| D | Translate DA>EN | Translate Danish to English |
| N | Translate EN>DA | Translate English to Danish |
| T | Speech-to-text | Tap 1-3 times for correction depth levels |

All 26 letter keys are mapped — unconfigured ones are placeholders you can assign to custom prompts without reflashing firmware.

**Danish characters** via hold-to-activate on the base layer:
- Hold P = å/Å
- Hold ; = æ/Æ
- Hold ' = ø/Ø

**Autocorrect** built into firmware: common English typos, company names, and text expansion shortcuts.

## Architecture

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
                        │ OpenRouter│  │ElevenLabs│  │ wtype /  │
                        │   LLM    │  │ Scribe v2│  │ clipboard│
                        └──────────┘  └──────────┘  └──────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full technical details.

## Requirements

**Hardware:**
- KLOR split keyboard (Polydactyl layout, RP2040 MCU)
- USB connection to host computer

**Software (Linux/Wayland):**
- Python 3.10+
- QMK build environment (for firmware compilation only)
- System packages: `wtype`, `wl-clipboard`
- Python packages: `hid` (or `hidapi` via pip), `openai`, `pyyaml`, `keyring`, `sounddevice`, `numpy`, `aiohttp`

**Software (Windows):**
- Python 3.10+
- Python packages: same as above plus `pyautogui`, `pyperclip`

**API Keys:**
- [OpenRouter](https://openrouter.ai/) — for LLM text transformations
- [ElevenLabs](https://elevenlabs.io/) — for speech-to-text (optional, only needed for STT)

## Quick Start

### 1. Flash Firmware

Put your KLOR into bootloader mode, then:

```bash
cp firmware/geigeigeist_klor_2040_vial.uf2 /run/media/$USER/RPI-RP2/
```

**Entering bootloader mode:** Press all 4 thumb keys on one half simultaneously, 5 times in a row (within 3 seconds). Each half can enter bootloader independently — no need to short pins or use the reset button. Alternatively, `QK_BOOT` is on the ADJUST layer (LOWER+RAISE, bottom-left key).

### 2. Run Setup

**Linux (Arch/Debian/Fedora):**
```bash
git clone https://github.com/YOUR_USERNAME/Klor-Omarchy-keymap.git
cd Klor-Omarchy-keymap
bash setup.sh
```

**Windows (PowerShell as Admin):**
```powershell
git clone https://github.com/YOUR_USERNAME/Klor-Omarchy-keymap.git
cd Klor-Omarchy-keymap
.\setup-windows.ps1
```

### 3. Set API Keys

Keys are stored in your OS keyring — never in config files or on the keyboard.

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

Or use environment variables:
```bash
export KLOR_OPENROUTER_KEY=sk-or-...
export KLOR_ELEVENLABS_KEY=...
```

### 4. Start the Bridge

**Linux (systemd):**
```bash
systemctl --user enable --now klor-bridge
journalctl --user -u klor-bridge -f  # view logs
```

**Manual / debugging:**
```bash
python3 ~/.config/klor-bridge/klor-bridge.py --verbose
```

**Windows:**
```powershell
python %USERPROFILE%\.config\klor-bridge\klor-bridge-windows.py --verbose
```

## Customization

### Adding a New Action

No firmware reflash needed — just edit config files and restart the bridge.

1. Open `~/.config/klor-bridge/actions.yml`
2. Find an unconfigured placeholder (e.g., `placeholder_b` for the B key)
3. Change `type: unconfigured` to `type: llm_text`
4. Set `prompt_key` to a template name
5. Add the template in `~/.config/klor-bridge/prompts.yml`
6. Restart the bridge: `systemctl --user restart klor-bridge`

### Changing the LLM Model

Edit `~/.config/klor-bridge/config.yml`:
```yaml
llm:
  default_model: anthropic/claude-3.5-sonnet  # or any OpenRouter model
```

### Adding Autocorrect Entries

Edit `bridge/autocorrect.txt`, then regenerate and reflash:
```bash
cd ~/vial-qmk
qmk generate-autocorrect-data ~/.config/klor-bridge/autocorrect.txt -kb geigeigeist/klor/2040 -km vial
qmk compile -kb geigeigeist/klor/2040 -km vial
```

### Speech-to-Text Depth Levels

After entering command mode (triple-tap RALT), tap T multiple times:
- **T x1** — Layer 1 only: raw ElevenLabs transcription
- **T x2** — L1 + Layer 2: domain-specific corrections (lexicon + regex)
- **T x3** — L1 + L2 + Layer 3: LLM post-processing for grammar cleanup

## Repository Structure

```
├── README.md                 # This file
├── ARCHITECTURE.md           # Technical design documentation
├── OMARCHY.md                # Omarchy desktop integration guide
├── setup.sh                  # Linux setup script
├── setup-windows.ps1         # Windows setup script
├── bridge/                   # Python bridge daemon + config templates
│   ├── klor-bridge.py        # Linux daemon (Wayland)
│   ├── klor-bridge-windows.py# Windows daemon (pyautogui)
│   ├── config.yml            # Bridge configuration
│   ├── actions.yml           # Action registry (26 keys)
│   ├── prompts.yml           # LLM prompt templates
│   ├── lexicon.yml           # Domain vocabulary for STT
│   ├── corrections.yml       # Regex corrections for STT
│   └── autocorrect.txt       # QMK autocorrect dictionary source
├── keyboards/                # QMK firmware source
│   └── geigeigeist/klor/keymaps/vial/
│       ├── keymap.c          # Main firmware (~650 lines)
│       ├── config.h          # QMK configuration
│       ├── rules.mk          # Build features
│       ├── autocorrect_data.h# Generated autocorrect trie
│       └── vial.json         # Vial GUI descriptor
├── firmware/                 # Pre-built firmware
│   └── geigeigeist_klor_2040_vial.uf2
└── systemd/                  # Linux service files
    ├── klor-bridge.service   # systemd user service
    └── 99-klor-hid.rules     # udev rule for HID access
```

## Building Firmware from Source

```bash
# Clone vial-qmk (one-time)
git clone https://github.com/vial-kb/vial-qmk.git ~/vial-qmk
cd ~/vial-qmk
make git-submodule

# Copy keymap source
cp -r Klor-Omarchy-keymap/keyboards/geigeigeist ~/vial-qmk/keyboards/

# Compile
qmk compile -kb geigeigeist/klor/2040 -km vial
```

The compiled `.uf2` file will be at `~/vial-qmk/geigeigeist_klor_2040_vial.uf2`.

## Layers

| # | Name | Activation |
|---|------|-----------|
| 0 | `_QWERTY` | Default base layer (HRM + Danish hold keys) |
| 1 | `_LOWER` | Hold left thumb `LOWER` key (numbers, nav, brackets) |
| 2 | `_RAISE` | Hold right thumb `RAISE` key (symbols, Unicode, Danish) |
| 3 | `_ADJUST` | Hold `LOWER` + `RAISE` together (F-keys) |
| 4 | `_NAV` | Hold bottom-right key (Hyprland workspace switching) |

## Vial Compatibility

This firmware is fully Vial-compatible. You can remap keys using the [Vial GUI](https://get.vial.today/) while keeping all custom features (Danish characters, command mode, autocorrect) active. The Raw HID bridge protocol coexists with Vial's protocol through the `raw_hid_receive_kb()` hook.

## License

This keymap and bridge daemon are provided as-is for the KLOR keyboard community. The KLOR keyboard design is by [GEIGEIGEIST](https://github.com/GEIGEIGEIST/KLOR).
