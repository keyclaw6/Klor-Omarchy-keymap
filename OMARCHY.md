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

## NAV Layer — Hyprland Workspace Switching

Layer 4 (`_NAV`), activated by holding the bottom-right key, provides direct Hyprland workspace navigation:

```
              ┌─────────┬─────────┬─────────┬─────────┬─────────┐
              │         │         │  GUI+↑  │         │         │
    ┌─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
    │ GUI+TAB │         │  GUI+←  │  GUI+↓  │  GUI+→  │         │
    ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
    │         │         │         │         │         │         │
    └─────────┴─────────┼─────────┼─────────┼─────────┤
                        │         │         │         │
                        └─────────┴─────────┴─────────┘

              ┌─────────┬─────────┬─────────┬─────────┬─────────┐
              │         │  GUI+7  │  GUI+8  │  GUI+9  │         │
    ┌─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
    │         │  GUI+4  │  GUI+5  │  GUI+6  │         │         │
    ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
    │         │  GUI+1  │  GUI+2  │  GUI+3  │         │    ▼    │
    └─────────┴─────────┼─────────┼─────────┤─────────┤
                        │         │         │  GUI+0  │
                        └─────────┴─────────┴─────────┘
```

This mirrors Hyprland's default workspace bindings (`$mod+1` through `$mod+9`, `$mod+0`). The left hand provides arrow-key window navigation (`GUI+arrows`) and task switcher (`GUI+TAB`).

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

## Screenshot Shortcut (SNAP2)

The LOWER layer's bottom-left key sends `Shift+GUI+S` — the standard Windows/KDE screenshot shortcut. On Omarchy/Hyprland, this needs a matching bind:

```
bind = $mod SHIFT, S, exec, grimblast copy area
```

This is handled by Omarchy's default screenshot configuration.

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
