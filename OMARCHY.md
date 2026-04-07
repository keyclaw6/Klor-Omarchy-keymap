# Omarchy Integration

How the KLOR AI Writing Workstation integrates with [Omarchy](https://omarchy.com), the Arch Linux desktop environment built on Hyprland.

This guide is only relevant if you run Omarchy. On other Linux desktops or Windows, skip this document.

## What Omarchy Provides

The bridge daemon depends on several Wayland tools that Omarchy ships by default:

- **wtype** — Simulates keypresses (Ctrl+C, Ctrl+V) and types text at the cursor
- **wl-clipboard** (`wl-copy`, `wl-paste`) — Reads and writes the Wayland clipboard
- **GNOME Keyring** — Stores API keys securely via Python's `keyring` library

These are already installed on Omarchy. The setup script (`setup.sh`) will install them on other Arch systems if missing.

## Hyprland Autostart

The bridge runs as a systemd user service and needs Wayland session variables to function. This line in `~/.config/hypr/autostart.conf` imports them:

```
exec-once = systemctl --user import-environment WAYLAND_DISPLAY XDG_RUNTIME_DIR
```

The setup script adds this automatically. Without it, `wtype` and `wl-clipboard` fail because they can't find the Wayland display socket.

## NAV Layer — Full Omarchy/Hyprland Window Manager

Layer 4 (`_NAV`), activated by holding the bottom-right key, provides comprehensive Hyprland window management. Every key on this layer sends `SUPER+<key>`, which Hyprland intercepts. The thumb keys provide CTRL, SHIFT, and ALT modifiers that compose naturally with the SUPER-embedded keycodes, giving access to the full Omarchy keybinding tree from a single layer.

### Layout

```
              ┌─────────┬─────────┬─────────┬─────────┬─────────┐                    ┌─────────┬─────────┬─────────┬─────────┬─────────┐
              │  GUI+Q  │ GUI+W ✕ │  GUI+↑  │  GUI+R  │ GUI+T ⇅ │                    │  GUI+Y  │  GUI+7  │  GUI+8  │  GUI+9  │ GUI+P ◫ │
    ┌─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤                    ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┐
    │ GUI+TAB │  GUI+A  │  GUI+←  │  GUI+↓  │  GUI+→  │ GUI+G ⊞ │                    │  GUI+H  │  GUI+4  │  GUI+5  │  GUI+6  │ GUI+K ⌨ │ GUI+L ⊟ │
    ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤╭────────╮╭────────╮├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
    │ GUI+ESC │  GUI+Z  │  GUI+X  │  GUI+C  │  GUI+V  │  GUI+B  ││  MUTE  ││PLY/PSE ││  GUI+N  │  GUI+1  │  GUI+2  │  GUI+3  │ GUI+/ ⊕ │ [held]  │
    └─────────┴─────────┴─────────┼─────────┼─────────┼─────────┼╰────────╯╰────────╯┼─────────┼─────────┼─────────┼─────────┴─────────┴─────────┘
                                  │  CTRL   │ GUI+SPC │ GUI+F ☐ │  SHIFT  ││   ALT   │ GUI+ENT │ GUI+, 🔕│  GUI+0  │
                                  └─────────┴─────────┴─────────┴─────────┘└─────────┴─────────┴─────────┴─────────┘
```

### Modifier Composition

The magic of this layer: thumb keys (CTRL, SHIFT, ALT) combine with the SUPER-embedded main keys to produce all Omarchy modifier combos:

| Thumb modifier | + Arrow keys (ESDF) | + Number keys (1-0) | + Letter keys |
|----------------|--------------------|--------------------|---------------|
| None | Focus window | Switch workspace | Window commands (W=close, T=float, G=group, etc.) |
| +SHIFT | Swap window position | Move window to workspace (follow) | App launchers (B=browser, N=editor, etc.) |
| +ALT | Move into group | Group window 1-5 | Special commands (S=scratchpad via base layer) |
| +CTRL | Group tab navigate | — | System panels (A=audio, B=bluetooth, etc.) |
| +SHIFT+ALT | Move workspace to monitor | Move window silently (stay) | — |

### Key Reference

**Left hand — Arrows & Window Commands:**

| Position | Key | Omarchy action |
|----------|-----|---------------|
| E (up) | `SUPER+↑` | Focus window up |
| S (left) | `SUPER+←` | Focus window left |
| D (down) | `SUPER+↓` | Focus window down |
| F (right) | `SUPER+→` | Focus window right |
| W | `SUPER+W` | Close window |
| T | `SUPER+T` | Toggle floating |
| G | `SUPER+G` | Toggle group |
| TAB | `SUPER+TAB` | Next workspace (+SHIFT = previous) |
| ESC | `SUPER+ESC` | System menu (logout/reboot/shutdown) |
| C | `SUPER+C` | Universal copy |
| V | `SUPER+V` | Universal paste (+CTRL = clipboard manager) |
| X | `SUPER+X` | Universal cut |

**Right hand — Workspaces & Navigation:**

| Position | Key | Omarchy action |
|----------|-----|---------------|
| 1-9, 0 | `SUPER+N` | Switch to workspace N (+SHIFT = move window, +SHIFT+ALT = move silently) |
| K | `SUPER+K` | Show all keybindings |
| L | `SUPER+L` | Toggle workspace layout |
| P | `SUPER+P` | Pseudo-tile window |
| / | `SUPER+/` | Cycle monitor scaling |

**Thumb keys:**

| Position | Key | Omarchy action |
|----------|-----|---------------|
| Left 1 | CTRL | Modifier for SUPER+CTRL combos (tiled fullscreen, system panels) |
| Left 2 | `SUPER+SPACE` | App launcher (walker) (+SHIFT = toggle waybar, +CTRL = backgrounds) |
| Left 3 | `SUPER+F` | Fullscreen (+CTRL = tiled fullscreen, +ALT = maximize) |
| Left 4 | SHIFT | Modifier for SUPER+SHIFT combos (move windows, swap, app launchers) |
| Right 1 | ALT | Modifier for SUPER+ALT combos (groups, special workspaces) |
| Right 2 | `SUPER+ENTER` | Terminal (+ALT = terminal with tmux) |
| Right 3 | `SUPER+,` | Dismiss notification (+SHIFT = dismiss all, +ALT = invoke, +CTRL = silence) |
| Right 4 | `SUPER+0` | Workspace 10 |

### Common Workflows

**Switch workspace:** NAV + number key (right hand numpad)
**Move window to workspace 3:** NAV + SHIFT + 3
**Move window silently to workspace 5:** NAV + SHIFT + ALT + 5
**Focus window left:** NAV + S
**Swap window left:** NAV + SHIFT + S
**Move into group left:** NAV + ALT + S
**Move workspace to left monitor:** NAV + SHIFT + ALT + S
**Fullscreen:** NAV + Space (thumb)
**Tiled fullscreen:** NAV + CTRL + Space (thumb)
**Close window:** NAV + W
**Open launcher:** NAV + Lower-thumb (SUPER+SPACE)
**Open terminal:** NAV + Enter-thumb (SUPER+ENTER)

## RAISE Layer — Omarchy Shortcuts

The RAISE layer's left-hand column sends `LALT+F13` through `LALT+F23`. These are high F-keys that no standard application uses, making them ideal for binding to Omarchy-specific actions in Hyprland config.

```
Row 0:  —          —          —          —          —
Row 1:  LALT+F13   LALT+F14   LALT+F15   LALT+F16   LALT+F17
Row 2:  LALT+F18   LALT+F19   LALT+F20   LALT+F21   LALT+F22   LALT+F23
```

To bind one in Hyprland:
```
# Example: LALT+F13 → open application launcher
bind = ALT, F13, exec, walker
```

These are intentionally left unbound in the default Hyprland config so you can assign them freely.

## DK_SC_AE Cross-Hand RGUI Chord

The semicolon key (`DK_SC_AE`) has special behavior relevant to Hyprland shortcuts:

- **Tap:** sends semicolon
- **Hold:** sends æ (Danish character)
- **Hold + left-hand key:** activates RGUI modifier instead of æ

This means you can chord the semicolon key with any left-hand key to trigger `GUI+<key>` shortcuts. The firmware detects which hand the interrupting key is on via the `chordal_hold_layout` matrix.

This replaces a traditional RGUI home row mod on the right pinky, which was removed to make room for the Danish æ character.

## Screenshot Shortcut (Print Screen)

The LOWER layer's bottom-left key sends a standard `Print Screen` keypress.

On Omarchy/Hyprland, `PRINT` is already bound by default:

```
bindd = , PRINT, Screenshot, exec, omarchy-cmd-screenshot
```

This makes the key platform-neutral while still using Omarchy's default screenshot flow.

## Unicode Input Method

Danish characters (æ, ø, å) on the RAISE layer use QMK's Unicode Map feature in `UNICODE_MODE_LINUX` mode. This sends characters via the `Ctrl+Shift+U` input method, which works in GTK and Qt applications under Wayland.

The `UNICODE_TYPE_DELAY 10` setting in `config.h` adds a small delay between key events to ensure Wayland compositors process them reliably.

If Unicode input doesn't work in a specific application, the hold-to-activate keys on the base layer (hold P=å, hold ;=æ, hold '=ø) use the same mechanism and serve as a fallback.

## AUR Package

The `python-sounddevice` dependency (needed for speech-to-text microphone capture) is only available in the AUR. The setup script uses Omarchy's `omarchy-pkg-aur-add` command if available, falling back to `yay` or `paru`.

## Troubleshooting

**Bridge can't simulate keypresses or access clipboard:**
Check that Wayland environment is imported:
```bash
systemctl --user show-environment | grep WAYLAND
```
If empty, run:
```bash
systemctl --user import-environment WAYLAND_DISPLAY XDG_RUNTIME_DIR
```
Or add the `exec-once` line to `~/.config/hypr/autostart.conf`.

**HID device not accessible:**
Check the udev rule is installed:
```bash
ls /etc/udev/rules.d/99-klor-hid.rules
```
Verify your user is in the `input` group:
```bash
groups | grep input
```
If not: `sudo usermod -aG input $USER` then log out and back in.

**Unicode characters not appearing:**
Verify the input method works: press `Ctrl+Shift+U`, type `00e5`, press Enter. If `å` doesn't appear, your application may not support the GTK Unicode input method. Try a different application (terminal, Firefox, etc.).

## Notifications (Mako)

The bridge sends desktop notifications via `notify-send` for operation feedback (LLM processing, STT recording, errors). On Omarchy, these are handled by **mako**.

Key implementation details:
- Notifications use both `string:x-dunst-stack-tag` and `string:x-canonical-private-synchronous` hints for cross-compositor compatibility
- Never uses `-t 0` (infinite timeout) — maximum timeout is 30 seconds, with tag replacement handling state transitions
- Before replacing a notification with different urgency, the bridge attempts `makoctl dismiss` (best-effort, silent on failure)
- App name `klor-bridge` is set via `-a` flag for mako filtering/styling

To customize notification appearance, create `~/.config/mako/config` with criteria:
```ini
[app-name=klor-bridge]
border-color=#89b4fa
default-timeout=5000
```

## Brightness Control

The right rotary encoder controls monitor brightness via the bridge daemon, using:
- **`brightnessctl`** — for laptop/internal backlight (available by default on Omarchy)
- **`ddcutil`** — for external monitors via DDC/CI (install: `sudo pacman -S ddcutil`)

If `ddcutil` is needed, your user must have access to the I2C bus:
```bash
sudo usermod -aG i2c $USER
# Log out and back in
```

Configure step size in `~/.config/klor-bridge/config.yml`:
```yaml
brightness:
  step_percent: 5          # % per encoder tick
  ddcutil_fallback: true   # try ddcutil if brightnessctl fails
```

## Prompt Picker (Walker)

The Prompt Picker (double-tap RALT → P) uses **walker** in `--dmenu` mode to present a searchable list of text snippets. Walker is Omarchy's default launcher and supports dmenu-compatible input.

If walker is not available, the bridge falls back to `fuzzel`, `wofi`, `rofi`, or `bemenu` (in that order).
