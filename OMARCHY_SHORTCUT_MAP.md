# Omarchy Shortcut Map

Derived design map. Use [OMARCHY_BINDING_MANIFEST.md](/home/kboc/Klor-Omarchy-keymap/OMARCHY_BINDING_MANIFEST.md) as the source-annotated inventory.

Current active source chain, as quoted in the official repo discussion:
- `~/.config/hypr/monitors.conf`
- `~/.config/hypr/input.conf`
- `~/.config/hypr/bindings.conf`
- `~/.config/hypr/envs.conf`
- `~/.config/hypr/looknfeel.conf`
- `~/.config/hypr/autostart.conf`
- `~/.local/share/omarchy/default/hypr/autostart.conf`
- `~/.local/share/omarchy/default/hypr/bindings/media.conf`
- `~/.local/share/omarchy/default/hypr/bindings/clipboard.conf`
- `~/.local/share/omarchy/default/hypr/bindings/tiling-v2.conf`
- `~/.local/share/omarchy/default/hypr/bindings/utilities.conf`
- `~/.local/share/omarchy/default/hypr/envs.conf`
- `~/.local/share/omarchy/default/hypr/looknfeel.conf`
- `~/.local/share/omarchy/default/hypr/input.conf`
- `~/.local/share/omarchy/default/hypr/windows.conf`
- `~/.config/omarchy/current/theme/hyprland.conf`

Notes:
- `default/hypr/bindings.conf` and `default/hypr/bindings/tiling.conf` are deprecated in-file.
- `default/hypr/plain-bindings.conf` is an official alternate launcher set in the repo, not the active default.
- This file intentionally merges and normalizes; the manifest does not.

## 1. Core Modifier System

- `SUPER` is the primary modifier for almost everything.
- `SUPER + SHIFT` usually means an alternate, stronger, or move/transfer variant.
- `SUPER + CTRL` usually means system, utility, or admin-oriented actions.
- `SUPER + ALT` usually means contextual or secondary variants, especially groups, private launches, and alternate navigation.
- `ALT` alone is used for app cycling.
- Arrow keys are the main directional vocabulary for focus, swap, group motion, and workspace movement.
- `TAB` is used for temporal cycling: workspaces, windows, and grouped windows.
- The number row is used for direct workspace and group-index access.
- Mouse buttons and scroll are first-class: moving, resizing, and workspace/group cycling all have mouse bindings.
- Media keys are also first-class; Omarchy treats laptop function keys as part of the control surface.

## 2. Application Launching

### Current active default launcher/menu bindings

| Keys | Action | Description |
| --- | --- | --- |
| `SUPER + SPACE` | `exec, omarchy-launch-walker` | Open the main application launcher. |
| `SUPER + CTRL + E` | `exec, omarchy-launch-walker -m symbols` | Open the emoji/symbol picker. |
| `SUPER + CTRL + C` | `exec, omarchy-menu capture` | Open the capture menu. |
| `SUPER + CTRL + O` | `exec, omarchy-menu toggle` | Open the toggle menu. |
| `SUPER + ALT + SPACE` | `exec, omarchy-menu` | Open the Omarchy menu. |
| `SUPER + ESCAPE` | `exec, omarchy-menu system` | Open the system menu. |
| `XF86PowerOff` | `exec, omarchy-menu system` | Open the system menu from the power key. |
| `SUPER + K` | `exec, omarchy-menu-keybindings` | Show the keybinding reference menu. |
| `XF86Calculator` | `exec, gnome-calculator` | Open the calculator. |

### Official alternate launcher set: `plain-bindings.conf`

| Keys | Action | Description |
| --- | --- | --- |
| `SUPER + RETURN` | `exec, uwsm-app -- xdg-terminal-exec --dir="$(omarchy-cmd-terminal-cwd)"` | Launch the terminal in the current terminal directory. |
| `SUPER + SHIFT + RETURN` | `exec, omarchy-launch-browser` | Launch the browser. |
| `SUPER + SHIFT + F` | `exec, uwsm-app -- nautilus --new-window` | Launch the file manager in a new window. |
| `SUPER + ALT + SHIFT + F` | `exec, uwsm-app -- nautilus --new-window "$(omarchy-cmd-terminal-cwd)"` | Launch the file manager in the current terminal directory. |
| `SUPER + SHIFT + B` | `exec, omarchy-launch-browser` | Launch the browser. |
| `SUPER + SHIFT + ALT + B` | `exec, omarchy-launch-browser --private` | Launch the browser in private mode. |
| `SUPER + SHIFT + N` | `exec, omarchy-launch-editor` | Launch the editor. |

### Deprecated legacy launcher set: `default/hypr/bindings.conf`

| Keys | Action | Description |
| --- | --- | --- |
| `SUPER + RETURN` | `exec, $terminal` | Launch the terminal. |
| `SUPER + F` | `exec, $fileManager` | Launch the file manager. |
| `SUPER + B` | `exec, $browser` | Launch the browser. |
| `SUPER + M` | `exec, $music` | Launch the music player. |
| `SUPER + N` | `exec, $terminal -e nvim` | Launch Neovim in a terminal. |
| `SUPER + T` | `exec, $terminal -e btop` | Launch `btop` in a terminal. |
| `SUPER + D` | `exec, $terminal -e lazydocker` | Launch Lazy Docker in a terminal. |
| `SUPER + G` | `exec, $messenger` | Launch the messenger app. |
| `SUPER + O` | `exec, obsidian -disable-gpu` | Launch Obsidian. |
| `SUPER + SLASH` | `exec, $passwordManager` | Launch the password manager. |

## 3. Window Management

### Current active default tiling set: `default/hypr/bindings/tiling-v2.conf`

| Keys | Action | Description |
| --- | --- | --- |
| `SUPER + W` | `killactive` | Close the active window. |
| `CTRL + ALT + DELETE` | `exec, omarchy-hyprland-window-close-all` | Close all windows. |
| `SUPER + J` | `layoutmsg, togglesplit` | Toggle the split orientation in dwindle. |
| `SUPER + P` | `pseudo` | Toggle pseudo floating behavior in dwindle. |
| `SUPER + T` | `togglefloating` | Toggle the active window between floating and tiled. |
| `SUPER + F` | `fullscreen, 0` | Toggle fullscreen. |
| `SUPER + CTRL + F` | `fullscreenstate, 0 2` | Toggle tiled fullscreen. |
| `SUPER + ALT + F` | `fullscreen, 1` | Toggle full-width fullscreen. |
| `SUPER + O` | `exec, omarchy-hyprland-window-pop` | Pop the window out as a floating/pinned window. |
| `SUPER + L` | `exec, omarchy-hyprland-workspace-layout-toggle` | Toggle the workspace layout. |
| `SUPER + LEFT` | `movefocus, l` | Focus the window to the left. |
| `SUPER + RIGHT` | `movefocus, r` | Focus the window to the right. |
| `SUPER + UP` | `movefocus, u` | Focus the window above. |
| `SUPER + DOWN` | `movefocus, d` | Focus the window below. |
| `SUPER + SHIFT + LEFT` | `swapwindow, l` | Swap the active window left. |
| `SUPER + SHIFT + RIGHT` | `swapwindow, r` | Swap the active window right. |
| `SUPER + SHIFT + UP` | `swapwindow, u` | Swap the active window up. |
| `SUPER + SHIFT + DOWN` | `swapwindow, d` | Swap the active window down. |
| `ALT + TAB` | `cyclenext` | Cycle to the next window on the current workspace. |
| `ALT + SHIFT + TAB` | `cyclenext, prev` | Cycle to the previous window on the current workspace. |
| `ALT + TAB` | `bringactivetotop` | Bring the active window to the top of the stack. |
| `ALT + SHIFT + TAB` | `bringactivetotop` | Bring the active window to the top of the stack. |
| `SUPER + G` | `togglegroup` | Toggle grouping for the focused window. |
| `SUPER + ALT + G` | `moveoutofgroup` | Remove the active window from its group. |
| `SUPER + ALT + LEFT` | `moveintogroup, l` | Move the window into the group on the left. |
| `SUPER + ALT + RIGHT` | `moveintogroup, r` | Move the window into the group on the right. |
| `SUPER + ALT + UP` | `moveintogroup, u` | Move the window into the group above. |
| `SUPER + ALT + DOWN` | `moveintogroup, d` | Move the window into the group below. |
| `SUPER + ALT + TAB` | `changegroupactive, f` | Select the next window in the current group. |
| `SUPER + ALT + SHIFT + TAB` | `changegroupactive, b` | Select the previous window in the current group. |
| `SUPER + CTRL + LEFT` | `changegroupactive, b` | Move grouped focus left. |
| `SUPER + CTRL + RIGHT` | `changegroupactive, f` | Move grouped focus right. |
| `SUPER + ALT + MOUSE_DOWN` | `changegroupactive, f` | Cycle to the next grouped window with the mouse wheel. |
| `SUPER + ALT + MOUSE_UP` | `changegroupactive, b` | Cycle to the previous grouped window with the mouse wheel. |
| `SUPER + ALT + 1` | `changegroupactive, 1` | Select grouped window 1. |
| `SUPER + ALT + 2` | `changegroupactive, 2` | Select grouped window 2. |
| `SUPER + ALT + 3` | `changegroupactive, 3` | Select grouped window 3. |
| `SUPER + ALT + 4` | `changegroupactive, 4` | Select grouped window 4. |
| `SUPER + ALT + 5` | `changegroupactive, 5` | Select grouped window 5. |
| `SUPER + MOUSE_DOWN` | `workspace, e+1` | Scroll to the next workspace. |
| `SUPER + MOUSE_UP` | `workspace, e-1` | Scroll to the previous workspace. |
| `SUPER + MOUSE_272` | `movewindow` | Move the active window by dragging with the primary mouse button. |
| `SUPER + MOUSE_273` | `resizewindow` | Resize the active window by dragging with the secondary mouse button. |

### Deprecated legacy tiling set: `default/hypr/bindings/tiling.conf`

| Keys | Action | Description |
| --- | --- | --- |
| `SUPER + W` | `killactive` | Close the active window. |
| `CTRL + ALT + DELETE` | `exec, omarchy-hyprland-window-close-all` | Close all windows. |
| `SUPER + J` | `togglesplit` | Toggle the split orientation. |
| `SUPER + P` | `pseudo` | Toggle pseudo floating behavior. |
| `SUPER + SHIFT + V` | `togglefloating` | Toggle the active window between floating and tiled. |
| `SHIFT + F11` | `fullscreen, 0` | Force fullscreen. |
| `ALT + F11` | `fullscreen, 1` | Force full width. |
| `SUPER + LEFT` | `movefocus, l` | Focus the window to the left. |
| `SUPER + RIGHT` | `movefocus, r` | Focus the window to the right. |
| `SUPER + UP` | `movefocus, u` | Focus the window above. |
| `SUPER + DOWN` | `movefocus, d` | Focus the window below. |
| `SUPER + 1` to `SUPER + 0` | `workspace, 1..10` | Switch to workspaces 1 through 10. |
| `SUPER + SHIFT + 1` to `SUPER + SHIFT + 0` | `movetoworkspace, 1..10` | Move the active window to workspaces 1 through 10. |
| `SUPER + TAB` | `workspace, e+1` | Next workspace. |
| `SUPER + SHIFT + TAB` | `workspace, e-1` | Previous workspace. |
| `SUPER + CTRL + TAB` | `workspace, previous` | Former workspace. |
| `SUPER + SHIFT + LEFT` | `swapwindow, l` | Swap the active window left. |
| `SUPER + SHIFT + RIGHT` | `swapwindow, r` | Swap the active window right. |
| `SUPER + SHIFT + UP` | `swapwindow, u` | Swap the active window up. |
| `SUPER + SHIFT + DOWN` | `swapwindow, d` | Swap the active window down. |
| `ALT + TAB` | `cyclenext` | Cycle to the next window. |
| `ALT + SHIFT + TAB` | `cyclenext, prev` | Cycle to the previous window. |
| `ALT + TAB` | `bringactivetotop` | Bring the active window to the top. |
| `ALT + SHIFT + TAB` | `bringactivetotop` | Bring the active window to the top. |
| `SUPER + CODE:20` | `resizeactive, -100 0` | Expand the window left. |
| `SUPER + CODE:21` | `resizeactive, 100 0` | Shrink the window left. |
| `SUPER + SHIFT + CODE:20` | `resizeactive, 0 -100` | Shrink the window up. |
| `SUPER + SHIFT + CODE:21` | `resizeactive, 0 100` | Expand the window down. |
| `SUPER + MOUSE_DOWN` | `workspace, e+1` | Scroll to the next workspace. |
| `SUPER + MOUSE_UP` | `workspace, e-1` | Scroll to the previous workspace. |
| `SUPER + MOUSE_272` | `movewindow` | Move the window by dragging. |
| `SUPER + MOUSE_273` | `resizewindow` | Resize the window by dragging. |

## 4. Workspace Management

### Current active default bindings

| Keys | Action | Description |
| --- | --- | --- |
| `SUPER + 1` through `SUPER + 0` | `workspace, 1..10` | Switch directly to workspaces 1 through 10. |
| `SUPER + SHIFT + 1` through `SUPER + SHIFT + 0` | `movetoworkspace, 1..10` | Move the active window to workspaces 1 through 10. |
| `SUPER + SHIFT + ALT + 1` through `SUPER + SHIFT + ALT + 0` | `movetoworkspacesilent, 1..10` | Move the active window silently to workspaces 1 through 10. |
| `SUPER + S` | `togglespecialworkspace, scratchpad` | Toggle the scratchpad special workspace. |
| `SUPER + ALT + S` | `movetoworkspacesilent, special:scratchpad` | Send the active window to the scratchpad without switching focus. |
| `SUPER + TAB` | `workspace, e+1` | Switch to the next workspace. |
| `SUPER + SHIFT + TAB` | `workspace, e-1` | Switch to the previous workspace. |
| `SUPER + CTRL + TAB` | `workspace, previous` | Return to the former workspace. |
| `SUPER + SHIFT + ALT + LEFT` | `movecurrentworkspacetomonitor, l` | Move the current workspace to the monitor on the left. |
| `SUPER + SHIFT + ALT + RIGHT` | `movecurrentworkspacetomonitor, r` | Move the current workspace to the monitor on the right. |
| `SUPER + SHIFT + ALT + UP` | `movecurrentworkspacetomonitor, u` | Move the current workspace to the monitor above. |
| `SUPER + SHIFT + ALT + DOWN` | `movecurrentworkspacetomonitor, d` | Move the current workspace to the monitor below. |
| `SUPER + MOUSE_DOWN` | `workspace, e+1` | Scroll forward through workspaces. |
| `SUPER + MOUSE_UP` | `workspace, e-1` | Scroll backward through workspaces. |

### Legacy tiling set notes

- The deprecated `tiling.conf` file uses the same workspace numbering and `Tab` cycling model.
- The legacy set does not include the current scratchpad or move-workspace-to-monitor bindings.

## 5. System Controls

### Current active default media bindings

| Keys | Action | Description |
| --- | --- | --- |
| `XF86AudioRaiseVolume` | `exec, $osdclient --output-volume raise` | Raise output volume. |
| `XF86AudioLowerVolume` | `exec, $osdclient --output-volume lower` | Lower output volume. |
| `XF86AudioMute` | `exec, $osdclient --output-volume mute-toggle` | Toggle output mute. |
| `XF86AudioMicMute` | `exec, $osdclient --input-volume mute-toggle` | Toggle microphone mute. |
| `XF86MonBrightnessUp` | `exec, omarchy-brightness-display +5%` | Increase display brightness. |
| `XF86MonBrightnessDown` | `exec, omarchy-brightness-display 5%-` | Decrease display brightness. |
| `XF86KbdBrightnessUp` | `exec, omarchy-brightness-keyboard up` | Increase keyboard backlight brightness. |
| `XF86KbdBrightnessDown` | `exec, omarchy-brightness-keyboard down` | Decrease keyboard backlight brightness. |
| `XF86KbdLightOnOff` | `exec, omarchy-brightness-keyboard cycle` | Cycle keyboard backlight state. |
| `ALT + XF86AudioRaiseVolume` | `exec, $osdclient --output-volume +1` | Raise output volume by 1 percent. |
| `ALT + XF86AudioLowerVolume` | `exec, $osdclient --output-volume -1` | Lower output volume by 1 percent. |
| `ALT + XF86MonBrightnessUp` | `exec, omarchy-brightness-display +1%` | Increase display brightness by 1 percent. |
| `ALT + XF86MonBrightnessDown` | `exec, omarchy-brightness-display 1%-` | Decrease display brightness by 1 percent. |
| `XF86AudioNext` | `exec, $osdclient --playerctl next` | Skip to the next track. |
| `XF86AudioPause` | `exec, $osdclient --playerctl play-pause` | Toggle pause/play. |
| `XF86AudioPlay` | `exec, $osdclient --playerctl play-pause` | Toggle play/pause. |
| `XF86AudioPrev` | `exec, $osdclient --playerctl previous` | Go to the previous track. |
| `SUPER + XF86AudioMute` | `exec, omarchy-cmd-audio-switch` | Switch the active audio output. |

### Current active utility/system bindings

| Keys | Action | Description |
| --- | --- | --- |
| `SUPER + CTRL + I` | `exec, omarchy-toggle-idle` | Toggle locking on idle. |
| `SUPER + CTRL + N` | `exec, omarchy-toggle-nightlight` | Toggle nightlight. |
| `SUPER + CTRL + L` | `exec, omarchy-lock-screen` | Lock the session. |
| `CTRL + F1` | `exec, omarchy-brightness-display-apple -5000` | Lower Apple display brightness. |
| `CTRL + F2` | `exec, omarchy-brightness-display-apple +5000` | Raise Apple display brightness. |
| `SHIFT + CTRL + F2` | `exec, omarchy-brightness-display-apple +60000` | Set Apple display brightness to full. |

### System-menu driven power controls

| Keys | Action | Description |
| --- | --- | --- |
| `SUPER + ESCAPE` | `exec, omarchy-menu system` | Open the system menu, where power and session actions live. |
| `XF86PowerOff` | `exec, omarchy-menu system` | Open the same system menu from the power key. |

## 6. UI / Session

### Current active menu and panel bindings

| Keys | Action | Description |
| --- | --- | --- |
| `SUPER + SPACE` | `exec, omarchy-launch-walker` | Open the main launcher. |
| `SUPER + CTRL + E` | `exec, omarchy-launch-walker -m symbols` | Open the emoji/symbol picker. |
| `SUPER + CTRL + C` | `exec, omarchy-menu capture` | Open the capture menu. |
| `SUPER + CTRL + O` | `exec, omarchy-menu toggle` | Open the toggle menu. |
| `SUPER + ALT + SPACE` | `exec, omarchy-menu` | Open the Omarchy menu. |
| `SUPER + K` | `exec, omarchy-menu-keybindings` | Show the keybinding viewer. |
| `SUPER + SHIFT + SPACE` | `exec, omarchy-toggle-waybar` | Toggle the top bar. |
| `SUPER + CTRL + SPACE` | `exec, omarchy-menu background` | Open the wallpaper/background menu. |
| `SUPER + SHIFT + CTRL + SPACE` | `exec, omarchy-menu theme` | Open the theme menu. |
| `SUPER + BACKSPACE` | `exec, omarchy-hyprland-active-window-transparency-toggle` | Toggle transparency on the focused window. |
| `SUPER + SHIFT + BACKSPACE` | `exec, omarchy-hyprland-window-gaps-toggle` | Toggle window gaps. |
| `SUPER + CTRL + BACKSPACE` | `exec, omarchy-hyprland-window-single-square-aspect-toggle` | Toggle the single-window square-aspect behavior. |
| `SUPER + COMMA` | `exec, makoctl dismiss` | Dismiss the latest notification. |
| `SUPER + SHIFT + COMMA` | `exec, makoctl dismiss --all` | Dismiss all notifications. |
| `SUPER + CTRL + COMMA` | `exec, omarchy-toggle-notification-silencing` | Toggle notification silencing. |
| `SUPER + ALT + COMMA` | `exec, makoctl invoke` | Re-open the last dismissed notification. |
| `SUPER + SHIFT + ALT + COMMA` | `exec, makoctl restore` | Restore the last dismissed notification. |
| `SUPER + CTRL + S` | `exec, omarchy-menu share` | Open the share menu. |
| `SUPER + CTRL + X` | `exec, voxtype record toggle` | Toggle dictation. |
| `SUPER + CTRL + ALT + T` | `exec, notify-send -u low " $(date +"%A %H:%M · %d %B %Y · Week %V")"` | Show the current time without using the bar. |
| `SUPER + CTRL + ALT + B` | `exec, notify-send -u low "$(omarchy-battery-status)"` | Show battery status without using the bar. |
| `SUPER + CTRL + Z` | `exec, hyprctl keyword cursor:zoom_factor $(hyprctl getoption cursor:zoom_factor -j | jq '.float + 1')` | Zoom in. |
| `SUPER + CTRL + ALT + Z` | `exec, hyprctl keyword cursor:zoom_factor 1` | Reset zoom. |

### Current active capture and color tools

| Keys | Action | Description |
| --- | --- | --- |
| `PRINT` | `exec, omarchy-cmd-screenshot` | Take a screenshot. |
| `ALT + PRINT` | `exec, omarchy-menu screenrecord` | Start screen recording from the capture menu. |
| `SUPER + PRINT` | `exec, pkill hyprpicker || hyprpicker -a` | Toggle the color picker. |

### Current active control panels

| Keys | Action | Description |
| --- | --- | --- |
| `SUPER + CTRL + A` | `exec, omarchy-launch-audio` | Open audio controls. |
| `SUPER + CTRL + B` | `exec, omarchy-launch-bluetooth` | Open Bluetooth controls. |
| `SUPER + CTRL + W` | `exec, omarchy-launch-wifi` | Open Wi-Fi controls. |
| `SUPER + CTRL + T` | `exec, omarchy-launch-tui btop` | Open the activity monitor. |

## 7. Screenshots / Media

### Screenshot and recording entry points

| Keys | Action | Description |
| --- | --- | --- |
| `PRINT` | `exec, omarchy-cmd-screenshot` | Screenshot entry point. |
| `ALT + PRINT` | `exec, omarchy-menu screenrecord` | Screen-recording entry point. |
| `SUPER + PRINT` | `exec, pkill hyprpicker || hyprpicker -a` | Color picker entry point. |
| `SUPER + CTRL + C` | `exec, omarchy-menu capture` | Open the capture menu. |

### Media transport keys

| Keys | Action | Description |
| --- | --- | --- |
| `XF86AudioNext` | `exec, $osdclient --playerctl next` | Next track. |
| `XF86AudioPause` | `exec, $osdclient --playerctl play-pause` | Pause or resume playback. |
| `XF86AudioPlay` | `exec, $osdclient --playerctl play-pause` | Pause or resume playback. |
| `XF86AudioPrev` | `exec, $osdclient --playerctl previous` | Previous track. |
| `XF86AudioRaiseVolume` | `exec, $osdclient --output-volume raise` | Raise volume. |
| `XF86AudioLowerVolume` | `exec, $osdclient --output-volume lower` | Lower volume. |
| `XF86AudioMute` | `exec, $osdclient --output-volume mute-toggle` | Toggle mute. |
| `XF86AudioMicMute` | `exec, $osdclient --input-volume mute-toggle` | Toggle microphone mute. |

## 8. Derived Patterns & Design Logic

- `SUPER` is the unifying layer. Omarchy expects the user to do most desktop navigation from a single modifier family rather than a modal launcher scheme.
- The launcher model is menu-first, not app-first. The active default set prioritizes Walker and Omarchy menus over direct app shortcuts.
- The app launch model exists in an alternate file set. `plain-bindings.conf` and the deprecated `bindings.conf` show a more traditional direct-launch style, but the current default source chain favors menu-driven workflows.
- `SUPER + C`, `SUPER + V`, and `SUPER + X` deliberately mirror cut/copy/paste conventions. Omarchy expects these to be muscle-memory shortcuts, even on Wayland.
- Directional actions are consistently encoded with arrow keys. The same spatial directions are reused for focus, swapping, moving between monitors, and group navigation.
- `TAB` is the cycle key. It is used for workspace traversal, window traversal, and group traversal, which keeps "next/previous" behavior consistent.
- The number row is for index-based addressing. Omarchy uses `code:10` through `code:19` so the visible number row maps cleanly to workspaces and grouped windows.
- `SHIFT` usually transforms an action rather than switching context. Examples include moving instead of switching, or a stronger version of the same action.
- `CTRL` usually exposes admin or system behavior. Examples include menus, idle locking, nightlight, zoom, share, and control panels.
- `ALT` usually adds a secondary layer. Examples include private browser launch, group membership, and alternate cycle paths.
- Mouse wheel bindings are treated as real navigation primitives, not just a fallback.
- The configuration evolved from older flat bindings to a newer `tiling-v2` system with grouping, scratchpad, and workspace-to-monitor movement.
- The repo itself documents that some older files are deprecated, which means Omarchy’s shortcut system is versioned through config files rather than a single frozen keymap.
- There are a few collisions in the source files. The clearest ones are `ALT + TAB` and `ALT + SHIFT + TAB`, which appear twice in `tiling-v2.conf` with different actions. I kept both entries instead of guessing which one Hyprland should prefer.

## 9. Observations for Keyboard Layer Design

- Most frequent keys are `SPACE`, `TAB`, `RETURN`, `1-0`, `ARROWS`, `C`, `V`, `X`, `F`, `G`, `L`, `O`, `S`, `T`, `W`, `B`, `N`, `K`, `COMMA`, `BACKSPACE`, `PRINT`, and `SLASH`.
- The highest-value single-chord actions are the launcher, clipboard, workspace switching, focus movement, and screenshot entry points.
- The best candidates for a dedicated keyboard layer are:
- `SUPER + SPACE` for the launcher.
- `SUPER + C / V / X` for clipboard behavior.
- `SUPER + 1-0` and `SUPER + SHIFT + 1-0` for workspace control.
- `SUPER + ARROWS` and `SUPER + SHIFT + ARROWS` for focus and swap.
- `PRINT` and `ALT + PRINT` for capture.
- The actions that should probably remain chords are the system and utility menus, the theme/background controls, and the more destructive window operations.
- A dedicated Omarchy layer should probably preserve the spatial clusters:
- Top row for workspace switching.
- Arrows for directional movement.
- Thumb-accessible placement for launcher and clipboard actions.
- Group operations should remain easy to access but clearly distinct from plain window movement.
- If the keyboard lacks `PRINT`, `XF86*`, or `RETURN` keys, the layer should provide alternate access paths for capture, media, and launcher workflows rather than remapping away the underlying mental model.

## 10. Sources

- `basecamp/omarchy` repository root: <https://github.com/basecamp/omarchy>
- Current active source chain quoted in the official discussion: <https://github.com/basecamp/omarchy/discussions/2766>
- Active bindings file: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings.conf>
- Active clipboard bindings: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings/clipboard.conf>
- Active media bindings: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings/media.conf>
- Active tiling bindings: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings/tiling-v2.conf>
- Deprecated tiling bindings: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings/tiling.conf>
- Active utilities bindings: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings/utilities.conf>
- Alternate direct-launch bindings: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/plain-bindings.conf>
