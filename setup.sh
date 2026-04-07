#!/usr/bin/env bash
set -euo pipefail

# KLOR Bridge — Setup Script
# Installs dependencies, configures udev, sets up systemd service.
# Run on any new Arch Linux / Omarchy machine.
#
# Usage:
#   bash setup.sh              # interactive (prompts for API keys)
#   bash setup.sh --no-keys    # skip API key setup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/klor-bridge"
SERVICE_DIR="$HOME/.config/systemd/user"
UDEV_RULE="99-klor-hid.rules"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[x]${NC} $*"; }

# ── Detect distro ─────────────────────────────────────────────────────────────

detect_distro() {
    if command -v pacman &>/dev/null; then
        echo "arch"
    elif command -v apt &>/dev/null; then
        echo "debian"
    elif command -v dnf &>/dev/null; then
        echo "fedora"
    else
        echo "unknown"
    fi
}

# ── Install system packages ───────────────────────────────────────────────────

install_packages() {
    local distro
    distro=$(detect_distro)
    info "Detected distro: $distro"

    case "$distro" in
        arch)
            info "Installing Arch packages..."
            # python-hid provides the 'hid' module (NOT python-hidapi, which
            # conflicts with python-hid required by qmk). The bridge supports both.
            sudo pacman -S --needed --noconfirm \
                python python-yaml python-openai python-keyring \
                python-numpy python-aiohttp python-hid \
                wtype wl-clipboard brightnessctl ddcutil

            # python-sounddevice is AUR-only
            if ! pacman -Qi python-sounddevice &>/dev/null; then
                if command -v omarchy-pkg-aur-add &>/dev/null; then
                    info "Installing python-sounddevice from AUR via omarchy..."
                    omarchy-pkg-aur-add python-sounddevice
                elif command -v yay &>/dev/null; then
                    yay -S --needed --noconfirm python-sounddevice
                elif command -v paru &>/dev/null; then
                    paru -S --needed --noconfirm python-sounddevice
                else
                    warn "python-sounddevice not found in repos. Install manually from AUR."
                    warn "  yay -S python-sounddevice  OR  paru -S python-sounddevice"
                fi
            fi
            ;;

        debian)
            info "Installing Debian/Ubuntu packages..."
            sudo apt update
            sudo apt install -y \
                python3 python3-pip python3-yaml python3-numpy python3-aiohttp \
                wtype wl-clipboard libhidapi-hidraw0 brightnessctl ddcutil
            pip3 install --user openai keyring sounddevice hidapi
            ;;

        fedora)
            info "Installing Fedora packages..."
            sudo dnf install -y \
                python3 python3-pip python3-pyyaml python3-numpy python3-aiohttp \
                wtype wl-clipboard hidapi brightnessctl ddcutil
            pip3 install --user openai keyring sounddevice hid
            ;;

        *)
            error "Unknown distro. Install these manually:"
            echo "  Python 3.10+, pip, pyyaml, openai, keyring, sounddevice, numpy, aiohttp, hid (or hidapi)"
            echo "  System: wtype, wl-clipboard, brightnessctl, ddcutil"
            return 1
            ;;
    esac
    info "System packages installed."
}

# ── Deploy config files ───────────────────────────────────────────────────────

deploy_configs() {
    info "Deploying config files to $CONFIG_DIR..."
    mkdir -p "$CONFIG_DIR"

    # Copy config files (don't overwrite existing)
    for f in config.yml actions.yml prompts.yml lexicon.yml corrections.yml snippets.yml; do
        src="$SCRIPT_DIR/bridge/$f"
        dst="$CONFIG_DIR/$f"
        if [[ -f "$src" ]]; then
            if [[ -f "$dst" ]]; then
                warn "  $f already exists, skipping (backup at ${dst}.setup-bak)"
                cp "$dst" "${dst}.setup-bak"
            else
                cp "$src" "$dst"
                info "  Installed $f"
            fi
        fi
    done

    # Always overwrite the bridge script (it's code, not config)
    if [[ -f "$SCRIPT_DIR/bridge/klor-bridge.py" ]]; then
        cp "$SCRIPT_DIR/bridge/klor-bridge.py" "$CONFIG_DIR/klor-bridge.py"
        chmod +x "$CONFIG_DIR/klor-bridge.py"
        info "  Installed klor-bridge.py"
    fi

    info "Config files deployed."
}

# ── Install udev rule ────────────────────────────────────────────────────────

install_udev() {
    local rule_src="$SCRIPT_DIR/systemd/$UDEV_RULE"
    local rule_dst="/etc/udev/rules.d/$UDEV_RULE"

    if [[ ! -f "$rule_src" ]]; then
        rule_src="$CONFIG_DIR/$UDEV_RULE"
    fi

    if [[ -f "$rule_src" ]]; then
        info "Installing udev rule for KLOR HID access..."
        sudo cp "$rule_src" "$rule_dst"
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        info "udev rule installed. Unplug and replug keyboard for it to take effect."
    else
        warn "udev rule not found. Create $CONFIG_DIR/$UDEV_RULE manually."
    fi
}

# ── Install systemd service ──────────────────────────────────────────────────

install_service() {
    info "Installing systemd user service..."
    mkdir -p "$SERVICE_DIR"

    local svc_src="$SCRIPT_DIR/systemd/klor-bridge.service"
    local svc_dst="$SERVICE_DIR/klor-bridge.service"

    if [[ -f "$svc_src" ]]; then
        cp "$svc_src" "$svc_dst"
    elif [[ -f "$CONFIG_DIR/../systemd/user/klor-bridge.service" ]]; then
        : # already in place
    else
        warn "Service file not found. Skipping."
        return
    fi

    systemctl --user daemon-reload
    info "Service installed. Enable with: systemctl --user enable --now klor-bridge"
}

# ── Configure API keys ───────────────────────────────────────────────────────

setup_keys() {
    if [[ "${1:-}" == "--no-keys" ]]; then
        info "Skipping API key setup (--no-keys)"
        return
    fi

    echo ""
    info "API Key Setup"
    echo "  Keys are stored in your OS keyring (GNOME Keyring / KWallet)."
    echo "  They are NOT stored in any config file or on the keyboard."
    echo ""

    read -rp "  OpenRouter API key (sk-or-...): " openrouter_key
    if [[ -n "$openrouter_key" ]]; then
        python3 - "$openrouter_key" <<'PYEOF'
import sys, keyring
keyring.set_password("klor-bridge", "openrouter_key", sys.argv[1])
PYEOF
        info "  OpenRouter key saved to keyring."
    else
        warn "  Skipped OpenRouter key."
    fi

    read -rp "  ElevenLabs API key: " elevenlabs_key
    if [[ -n "$elevenlabs_key" ]]; then
        python3 - "$elevenlabs_key" <<'PYEOF'
import sys, keyring
keyring.set_password("klor-bridge", "elevenlabs_key", sys.argv[1])
PYEOF
        info "  ElevenLabs key saved to keyring."
    else
        warn "  Skipped ElevenLabs key."
    fi
}

# ── Wayland env for systemd ──────────────────────────────────────────────────

setup_wayland_env() {
    # Import current Wayland session env into systemd
    if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
        systemctl --user import-environment WAYLAND_DISPLAY XDG_RUNTIME_DIR
        info "Wayland environment imported into systemd."
    else
        warn "WAYLAND_DISPLAY not set. Run this from a Wayland session, or"
        warn "add to ~/.config/hypr/autostart.conf:"
        warn "  exec-once = systemctl --user import-environment WAYLAND_DISPLAY XDG_RUNTIME_DIR"
    fi
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║   KLOR Bridge — Setup Script             ║"
    echo "╚══════════════════════════════════════════╝"
    echo ""

    # Package installation requires sudo. If it fails (no TTY, missing sudo, etc.)
    # we warn and continue — the remaining steps (config deploy, service install)
    # don't need root and should always run.
    local packages_ok=true
    install_packages || {
        packages_ok=false
        warn "Package installation failed (sudo unavailable or distro unknown)."
        warn "Install manually before starting the bridge, then re-run setup.sh."
    }
    echo ""
    deploy_configs
    echo ""
    install_udev || warn "udev rule installation failed — run with sudo or install manually."
    echo ""
    install_service
    echo ""
    setup_wayland_env
    echo ""
    setup_keys "${1:-}"

    echo ""
    if $packages_ok; then
        info "Setup complete!"
    else
        warn "Setup complete (with warnings — see above)."
    fi
    echo ""
    echo "  Next steps:"
    echo "    1. Flash firmware: cp geigeigeist_klor_2040_vial.uf2 /run/media/$USER/RPI-RP2/"
    echo "    2. Start bridge:  systemctl --user enable --now klor-bridge"
    echo "    3. Check logs:    journalctl --user -u klor-bridge -f"
    echo "    4. Manual test:   python3 ~/.config/klor-bridge/klor-bridge.py --verbose"
    echo ""
}

main "$@"
