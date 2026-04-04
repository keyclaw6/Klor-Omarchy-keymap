# Klor-Omarchy-keymap

Snapshot of the KLOR RP2040 keymap work, mirrored from QMK for rollback and diffing.

Source baseline:
- QMK repo: `qmk_firmware`
- Commit: `1426eedfc1`
- Branch: `master`

Tracked subtree:
- `keyboards/geigeigeist/klor/`

Current custom keymap:
- `keyboards/geigeigeist/klor/keymaps/zynex/`

Reference docs:
- [OMARCHY_BINDING_MANIFEST.md](/home/kboc/Klor-Omarchy-keymap/OMARCHY_BINDING_MANIFEST.md)
- [OMARCHY_BINDING_CONFLICTS.md](/home/kboc/Klor-Omarchy-keymap/OMARCHY_BINDING_CONFLICTS.md)
- [OMARCHY_SHORTCUT_MAP.md](/home/kboc/Klor-Omarchy-keymap/OMARCHY_SHORTCUT_MAP.md)

Known-good fallback:
- [known-good-klor/README.md](/home/kboc/Klor-Omarchy-keymap/known-good-klor/README.md)
- [known-good-klor/zynex/keymap.c](/home/kboc/Klor-Omarchy-keymap/known-good-klor/zynex/keymap.c)
- [artifacts/geigeigeist_klor_2040_zynex_known_good.uf2](/home/kboc/Klor-Omarchy-keymap/artifacts/geigeigeist_klor_2040_zynex_known_good.uf2)

## Changelog

- Replaced the base-layer right Shift position with `MO(_OMARCHY)`.
- Added a dedicated `_OMARCHY` layer for launcher, menus, scratchpad controls, and other secondary Omarchy actions.
- Kept native Omarchy workspace and focus behavior on the main desktop modifier path instead of moving it behind a layer.
- Added [KLOR_OMARCHY_REVISION.md](/home/kboc/Klor-Omarchy-keymap/KLOR_OMARCHY_REVISION.md) with a readable layer view.
- Archived the synced keymap snapshot and UF2 builds under [`artifacts/`](/home/kboc/Klor-Omarchy-keymap/artifacts).
- Added a separate known-good KLOR snapshot from `Downloads` for recovery and rollback.
