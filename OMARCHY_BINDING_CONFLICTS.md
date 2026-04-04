# Omarchy Binding Conflicts

This file lists collisions, overrides, and scope mismatches. It is intentionally pessimistic.

## Conflicts Inside Active Defaults

| Keys | File | Problem | Notes |
| --- | --- | --- | --- |
| `ALT + TAB` | `default/hypr/bindings/tiling-v2.conf` | Defined twice | First as `cyclenext`, then again as `bringactivetotop` |
| `ALT + SHIFT + TAB` | `default/hypr/bindings/tiling-v2.conf` | Defined twice | First as `cyclenext, prev`, then again as `bringactivetotop` |

## Scope Collisions

| Keys | Scope | Problem | Notes |
| --- | --- | --- | --- |
| `SUPER + RETURN` | Legacy vs alternate launch layout | Same key used by both deprecated `bindings.conf` and alternate `plain-bindings.conf` | Not a conflict inside one file, but a design collision across Omarchy layouts |
| `SUPER + F` / `SUPER + B` / `SUPER + N` | Legacy vs alternate launch layout | Same launcher idea exists in multiple source files with different modifier schemes | This is why the manifest keeps file provenance separate |
| `SUPER + SPACE` | Active defaults vs alternate launcher example | Default launcher in active utilities config, but also shown as a comment override in `plain-bindings.conf` | User-specific override pattern, not a repo default |

## Non-Hyprland Ambiguities

| Keys | Scope | Problem | Notes |
| --- | --- | --- | --- |
| `SUPER + ;` / `SUPER + ~` | Fcitx5 input method | Runtime shortcut not in Hyprland config | Must be treated separately from Hyprland binds |
| `CTRL + ;` / `CTRL + ALT + H` | Fcitx5 input method | Runtime shortcut not in Hyprland config | Must not be merged into the Hyprland map |

## Reliability Notes

- The active defaults are more trustworthy than the deprecated and alternate files, but they still need runtime verification on a real Omarchy session.
- Any final keyboard-layer design should consume the manifest, not this conflicts file.
