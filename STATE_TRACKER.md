# KLOR Bridge — Master Task Tracker
## Created: 2026-04-07
## Status: ALL 6 OBJECTIVES COMPLETE

---

## HIGH-LEVEL OBJECTIVES
1. **Fix notifications** — DONE. Rewrote `Platform.notify()` to be mako-aware (no `-t 0`, dual hint tags, `makoctl dismiss`, app name). All STT/LLM paths have proper notification lifecycle.
2. **Fix Expand (E) command** — DONE. `_handle_llm_text()` rewritten with clipboard retry, 120s timeout, full notification lifecycle (copying → processing → result/error).
3. **Add Prompt Picker (P)** — DONE. `_handle_prompt_picker()` with walker --dmenu (Linux) / Out-GridView (Windows). 28 default snippets in snippets.yml.
4. **Right encoder → brightness** — DONE. Firmware encoder_map + process_record_user sends HID packets → bridge handles via brightnessctl/ddcutil (Linux) or WMI (Windows).
5. **Full audit** — DONE. All YAML files validated, Python syntax checked, firmware changes verified.
6. **Redesign NAV layer with full Omarchy/Hyprland keybindings** — DONE. Researched all Omarchy keybindings from Hyprland config files. Redesigned NAV layer: every key sends LGUI(key), thumb keys provide CTRL/SHIFT/ALT for modifier composition. Covers all WM operations: workspace switching, window focus/swap/move, fullscreen, floating, groups, launcher, terminal, notifications. Compiled to UF2 (252 KB).

---

## COMPLETED CHANGES

### Firmware (keymap.c)
- [x] Added `BRIGHT_UP`, `BRIGHT_DOWN` custom keycodes
- [x] Added `ACTION_BRIGHTNESS_UP` (0x11), `ACTION_BRIGHTNESS_DOWN` (0x12) defines
- [x] Updated encoder_map: right encoder → BRIGHT_DOWN/BRIGHT_UP on all 5 layers
- [x] Added BRIGHT_UP/BRIGHT_DOWN handling in process_record_user → bridge_send_action()
- [x] **Redesigned NAV layer** — all 42 keys now have LGUI-embedded keycodes for full Omarchy WM control
  - Left ESDF = LGUI(arrows) for window focus
  - Right numpad = LGUI(1-9, 0) for workspaces
  - Left letters = LGUI(W/T/G/etc.) for window commands (close, float, group, etc.)
  - Right outer = LGUI(K/L/P) for keybindings menu, layout toggle, pseudo-tile
  - Thumb CTRL/SHIFT/ALT = compose modifiers for SUPER+SHIFT (move/swap), SUPER+ALT (groups), etc.
  - Thumb SPACE = LGUI(F) for fullscreen, thumb LOWER = LGUI(SPC) for launcher, thumb ENTER = LGUI(ENT) for terminal
  - Thumb RAISE = LGUI(COMM) for dismiss notification
  - Left outer: LGUI(TAB) = next workspace, LGUI(ESC) = system menu
- [x] Compiled firmware to UF2 (252 KB) — `firmware/geigeigeist_klor_2040_vial.uf2`

### Linux Bridge (klor-bridge.py)
- [x] Rewrote `Platform.notify()` — mako-aware, dual hints, no `-t 0`, app name
- [x] Added `Platform._dismiss_notification()` method
- [x] Rewrote `_handle_llm_text()` — clipboard retry, 120s timeout, full notifications
- [x] Rewrote `_handle_stt_toggle()` — proper notification at every stage
- [x] Rewrote `_dispatch_action()` — handles brightness IDs, prompt_picker type
- [x] Added `_handle_prompt_picker()` — walker/fuzzel/wofi/rofi/bemenu fallback chain
- [x] Added `_handle_brightness()`, `_brightness_brightnessctl()`, `_brightness_ddcutil()`
- [x] Added `load_snippets()`, brightness config, new action ID constants

### Windows Bridge (klor-bridge-windows.py)
- [x] All Linux bridge changes mirrored
- [x] `_handle_prompt_picker()` using PowerShell Out-GridView
- [x] `_handle_brightness()` using WMI PowerShell

### Config Files
- [x] actions.yml — placeholder_p changed to `type: prompt_picker`
- [x] actions.yml — Added brightness + prompt_picker action type docs in header
- [x] config.yml — Added `brightness:` section (step_percent, tool, ddcutil_fallback, notify)
- [x] snippets.yml — Created with 28 default snippets across 7 categories

### Infrastructure
- [x] setup.sh — Updated to deploy snippets.yml

### Documentation
- [x] README.md — Updated NAV layer description, added Prompt Picker, Brightness Control sections
- [x] ARCHITECTURE.md — Updated NAV layer description, added prompt_picker, brightness, encoder map docs
- [x] OMARCHY.md — Complete rewrite of NAV layer section with full layout diagram, modifier composition table, key reference, and common workflows. Added Notifications, Brightness, Prompt Picker sections.

### Validation
- [x] config.yml — YAML valid
- [x] actions.yml — YAML valid
- [x] snippets.yml — YAML valid (28 snippets)
- [x] klor-bridge.py — Python syntax OK (py_compile)
- [x] klor-bridge-windows.py — Python syntax OK (py_compile)
- [x] keymap.c — Full NAV layer redesign, compiled successfully to UF2 (252 KB, 0 errors)
