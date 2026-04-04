# Omarchy Binding Conflicts

This file lists collisions, overrides, and scope mismatches. It is intentionally pessimistic.

## Conflicts Inside Active Defaults

| Keys | File | Problem | Notes |
| --- | --- | --- | --- |
| `ALT + TAB` | `default/hypr/bindings/tiling-v2.conf` | Defined twice | First as `cyclenext`, then again as `bringactivetotop` |
| `ALT + SHIFT + TAB` | `default/hypr/bindings/tiling-v2.conf` | Defined twice | First as `cyclenext, prev`, then again as `bringactivetotop` |

Verified live: both pairs of duplicate binds exist in the active Hyprland config on this machine. Hyprland applies both directives.

## Scope Collisions

| Keys | Scope | Problem | Notes |
| --- | --- | --- | --- |
| `SUPER + RETURN` | User overrides vs deprecated | `~/.config/hypr/bindings.conf` overrides the deprecated `default/hypr/bindings.conf` | On this machine, the user file wins with `uwsm-app -- xdg-terminal-exec` instead of `$terminal` |
| `SUPER + F` / `SUPER + B` / `SUPER + N` | Legacy vs user overrides | Same launcher idea exists in multiple source files with different modifier schemes | On this machine, `SUPER + SHIFT + F` (not `SUPER + F`) is the active file manager binding |
| `SUPER + SPACE` | Active defaults vs user comment | Default launcher in `utilities.conf`, but user file has commented-out override to `omarchy-menu` | Currently inactive; the comment is just a note |
| `SUPER + SHIFT + B` | User overrides | Bound twice to the same action (`omarchy-launch-browser`) in `~/.config/hypr/bindings.conf` | Harmless duplicate; no conflict at runtime |

## Non-Hyprland Ambiguities

| Keys | Scope | Problem | Notes |
| --- | --- | --- | --- |
| `SUPER + ;` / `SUPER + ~` | Fcitx5 input method | Runtime shortcut not in Hyprland config | Must be treated separately from Hyprland binds |
| `CTRL + ;` / `CTRL + ALT + H` | Fcitx5 input method | Runtime shortcut not in Hyprland config | Must not be merged into the Hyprland map |

## Reliability Notes

- All active defaults have been verified against the live Hyprland binding table (`hyprctl binds -j`) on this machine (2026-04-04).
- `voxtype` is NOT installed on this system — the `SUPER + CTRL + X` binding exists in config but will fail at runtime.
- Fcitx5 IS installed (v5.1.19) — its runtime bindings (`SUPER + ;`, `CTRL + ;`, etc.) are active but live outside Hyprland.
- Any final keyboard-layer design should consume the manifest, not this conflicts file.
