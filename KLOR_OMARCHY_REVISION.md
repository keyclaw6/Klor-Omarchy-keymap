# KLOR Omarchy Revision

This revision makes the former right Shift position on the KLOR base layer a dedicated Omarchy layer key.

## Key change

- Base layer right Shift position now sends `MO(_OMARCHY)`.
- The Omarchy layer is momentary and secondary.
- It is intended for launcher, menus, scratchpad helpers, and other infrequent Omarchy actions.
- The base keyboard still uses native Omarchy modifiers directly for common navigation and workspace use.

## Human-readable view

```text
Base layer, right side bottom key:

...  N   M   ,   .   /   [MO(_OMARCHY)]

Omarchy layer, top row:

Q  W  E  R  T   -> launcher / system / capture / toggle / keys
Y  U  I  O  P   -> waybar / notify / clear all / invoke / restore

Omarchy layer, second row:

A  S  D  F  G  H   -> audio / bluetooth / wifi / activity / nightlight / idle
```

## Notes

- This does not change Omarchy's native host keybindings.
- This does not change screenshot behavior.
- This is a small layer-access correction only.

## Artifacts

- Synced keymap snapshot: `keyboards/geigeigeist/klor/keymaps/zynex/keymap.c`
- UF2 builds:
  - `artifacts/geigeigeist_klor_2040_zynex.uf2`
  - `artifacts/geigeigeist_klor_2040_zynex.build.uf2`
