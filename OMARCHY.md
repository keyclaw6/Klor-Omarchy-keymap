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

> [!WARNING]
> NAV, LOWER screenshot behavior, verified STT/LLM notifications, and the current prompt picker behavior are now locked.
> Do not change these again unless the user explicitly asks for it.
> This is the agreed stable mapping and should be treated as frozen.

Layer 4 (`_NAV`), activated by holding the bottom-right key, is a navigation-only Omarchy layer. It keeps only window/workspace navigation, movement, grouping, and resize behavior. The thumb keys provide CTRL, SHIFT, and ALT modifiers that compose with the dedicated navigation keys.

Frozen NAV contract:

- Plain arrows = `Super+Arrow` window focus
- `Shift+Arrow` = `Super+Shift+Arrow` window swap / move
- `Alt+Arrow` = `Super+Alt+Arrow` move window into group
- `Shift+Alt+Arrow` = `Super+Shift+Alt+Arrow` move workspace to monitor
- `Ctrl+Arrow` = resize on the arrow cluster
- `Ctrl+Alt+Left/Right` = `Super+Ctrl+Left/Right` group focus fallback
- Number row = `Super+1..0` workspace switch
- `Shift+Number` = `Super+Shift+1..0` move window to workspace
- `Shift+Alt+Number` = `Super+Shift+Alt+1..0` move window silently to workspace
- `Alt+1..5` = `Super+Alt+1..5` activate grouped window 1..5
- `Super+Tab` on NAV with thumb modifiers for previous/former/group cycling
- `Super+G` on NAV with `Alt+G` for group-out behavior
- Dedicated `Super+Ctrl+Left/Right` keys remain on NAV and must stay there

### Layout

```
              ┌─────────┬─────────┬─────────┬─────────┬─────────┐                    ┌─────────┬─────────┬─────────┬─────────┬─────────┐
               │         │ GUI+CTL←│    ↑    │ GUI+CTL→│         │                    │         │  GUI+7  │  GUI+8  │  GUI+9  │         │
    ┌─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤                    ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┐
     │ GUI+TAB │         │    ←    │    ↓    │    →    │ GUI+G ⊞ │                    │         │  GUI+4  │  GUI+5  │  GUI+6  │         │         │
    ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤╭────────╮╭────────╮├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
    │         │         │         │         │         │         ││  MUTE  ││PLY/PSE ││         │  GUI+1  │  GUI+2  │  GUI+3  │         │ [held]  │
    └─────────┴─────────┴─────────┼─────────┼─────────┼─────────┼╰────────╯╰────────╯┼─────────┼─────────┼─────────┼─────────┴─────────┴─────────┘
                                   │  CTRL   │         │         │  SHIFT  ││   ALT   │         │         │  GUI+0  │
                                  └─────────┴─────────┴─────────┴─────────┘└─────────┴─────────┴─────────┴─────────┘
```

### Modifier Composition

The thumb keys (CTRL, SHIFT, ALT) combine with the dedicated navigation keys to produce the full navigation tree:

| Thumb modifier | + Arrow keys | + Number keys (1-0) | + WS-TAB / G |
|----------------|------------|--------------------|--------------|
| None | Focus window | Switch workspace | WS-TAB = next workspace, G = toggle group |
| +SHIFT | Swap window | Move window to workspace | WS-TAB = previous workspace |
| +ALT | Move into group | Group window 1-5 | WS-TAB = next in group, G = move out of group |
| +CTRL | Resize window | — | WS-TAB = former workspace |
| +SHIFT+ALT | Move workspace to monitor | Move window silently | WS-TAB = previous in group |

### Key Reference

**Left hand — Navigation cluster:**

| Position | Key | Omarchy action |
|----------|-----|---------------|
| E (up) | `SUPER+↑` | Focus window up |
| S (left) | `SUPER+←` | Focus window left |
| D (down) | `SUPER+↓` | Focus window down |
| F (right) | `SUPER+→` | Focus window right |
| G | `SUPER+G` | Toggle group |
| TAB | `SUPER+TAB` | Next workspace (+SHIFT = previous, +CTRL = former, +ALT = next in group, +SHIFT+ALT = previous in group) |
| Top inner left | `SUPER+CTRL+LEFT` | Group focus backward |
| Top inner right | `SUPER+CTRL+RIGHT` | Group focus forward |
| CTRL + Left/Right | `SUPER+-` / `SUPER+=` | Horizontal resize on the arrow cluster |
| CTRL + Up/Down | `SUPER+SHIFT+-` / `SUPER+SHIFT+=` | Vertical resize on the arrow cluster |
| CTRL + ALT + Left/Right | `SUPER+CTRL+LEFT/RIGHT` | Alternate path to group focus on the arrow cluster |

**Right hand — Workspaces & Navigation:**

| Position | Key | Omarchy action |
|----------|-----|---------------|
| 1-9, 0 | `SUPER+N` | Switch to workspace N (+SHIFT = move window, +SHIFT+ALT = move silently) |
| 1-9, 0 | `SUPER+N` | Switch to workspace N (+SHIFT = move window, +SHIFT+ALT = move silently, +ALT on 1-5 = activate grouped window) |

**Thumb keys:**

| Position | Key | Omarchy action |
|----------|-----|---------------|
| Left 1 | CTRL | Resize on arrows, former workspace on WS-TAB |
| Left 4 | SHIFT | Swap on arrows, move-to-workspace on numbers, previous workspace on WS-TAB |
| Right 1 | ALT | Group navigation on arrows/numbers, move-out-of-group on G |
| Right 4 | `SUPER+0` | Workspace 10 |

### Common Workflows

**Switch workspace:** NAV + number key (right hand numpad)
**Move window to workspace 3:** NAV + SHIFT + 3
**Move window silently to workspace 5:** NAV + SHIFT + ALT + 5
**Focus window left:** NAV + S
**Swap window left:** NAV + SHIFT + S
**Move into group left:** NAV + ALT + S
**Move workspace to left monitor:** NAV + SHIFT + ALT + S
**Resize left/right/up/down:** NAV + CTRL + arrow cluster
**Group focus backward/forward from arrows:** NAV + CTRL + ALT + Left/Right
**Group focus backward/forward:** NAV + top-row group keys

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

## Semicolon Home-Row Mod

The semicolon key is restored as a normal `RGUI_T(KC_SCLN)` home-row mod.

- **Tap:** sends semicolon
- **Hold:** acts as right GUI / Super

## Screenshot Shortcut (Print Screen)

> [!WARNING]
> The LOWER screenshot key is locked.
> Do not convert it back to a custom Vial keycode or custom macro unless the user explicitly asks.

The LOWER layer's bottom-left key sends a standard `Print Screen` keypress.

On Omarchy/Hyprland, `PRINT` is already bound by default:

```
bindd = , PRINT, Screenshot, exec, omarchy-cmd-screenshot
```

This makes the key platform-neutral while still using Omarchy's default screenshot flow.

## Unicode Input Method

Danish characters (æ, ø, å) on the RAISE layer use QMK's Unicode Map feature in `UNICODE_MODE_LINUX` mode. This sends characters via the `Ctrl+Shift+U` input method, which works in GTK and Qt applications under Wayland.

The `UNICODE_TYPE_DELAY 10` setting in `config.h` adds a small delay between key events to ensure Wayland compositors process them reliably.

If Unicode input doesn't work in a specific application, use an app that supports the Linux `Ctrl+Shift+U` Unicode input method (terminal, Firefox, etc.).

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
- STT notifications never use critical urgency anymore; they are intentionally sent as normal urgency with explicit timeouts
- Never uses `-t 0` (infinite timeout) — maximum timeout is 30 seconds
- Before posting a new tagged notification, the bridge now explicitly clears the old one with `makoctl dismiss -n <id>` and also falls back to dismissing the current group
- STT, LLM, and prompt-picker notifications now all use the same explicit begin/step/end flow lifecycle instead of ad-hoc raw replacements
- App name `KLOR Bridge` is set via `-a` flag for mako filtering/styling
- Local mako overrides in `~/.config/mako/config` force `Recording...` and `Processing transcription...` to expire and skip history

Important anti-regression rule:

- Do not switch STT notifications back to `critical` urgency. Omarchy's default mako config treats critical notifications as persistent (`default-timeout=0`), which is the exact failure mode that caused `Recording...` to stick on the 4K monitor.
- The current STT and LLM notification behavior is verified working on the user's monitors and is locked. Do not change it unless the user explicitly asks.

Verification notes:

- Session-level smoke tests live in `bridge/notification_smoke_test.py`
- Latest smoke test log is written to `~/.cache/klor-bridge-notification-smoke.log`
- The smoke test covers:
  - STT start -> processing -> complete -> clear
  - LLM copy -> processing -> ready -> clear
  - prompt-picker result -> clear
  - repeated STT lifecycle transitions

To customize notification appearance, create `~/.config/mako/config` with criteria:
```ini
[app-name=klor-bridge]
border-color=#89b4fa
default-timeout=5000
```

## Brightness Control

The right rotary encoder sends standard media brightness keycodes (`KC_BRID` / `KC_BRIU`). On Omarchy external-monitor setups, `setup.sh` installs a Hyprland override that routes those media keys through `~/.config/hypr/brightness-display-ddc.sh`, using DDC/CI instead of Omarchy's default laptop-backlight helper.

The bridge also handles Raw HID brightness action IDs (`0x11`/`0x12`) by calling the same DDC helper when present. DDC/CI access still requires I2C permissions:

```bash
sudo usermod -aG i2c $USER
# Log out and back in
```

## Prompt Picker

The Prompt Picker (double-tap RALT → P) uses a custom GTK window to present a searchable list of text snippets in the center of the monitor under the cursor.

This picker behavior is verified working and locked. Do not change its single-launch centered placement model, visible-selection scrolling, taller denser keyboard-first UI, or clipboard result flow unless the user explicitly asks.
