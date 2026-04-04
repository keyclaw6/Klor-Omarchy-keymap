# Omarchy Binding Manifest

This document is the source-annotated inventory. It is not a design summary.

Scope:
- Official Omarchy repo files on `basecamp/omarchy` `dev`
- Official Omarchy discussions/issues only when they document runtime bindings or native workflows not present in the repo files

Active default repo files:
- `default/hypr/bindings/clipboard.conf`
- `default/hypr/bindings/media.conf`
- `default/hypr/bindings/tiling-v2.conf`
- `default/hypr/bindings/utilities.conf`

Deprecated repo files:
- `default/hypr/bindings.conf`
- `default/hypr/bindings/tiling.conf`

Alternate repo file:
- `default/hypr/plain-bindings.conf`

Non-Hyprland runtime bindings documented in official issues/discussions:
- Fcitx5 defaults from issue `#2276`

## Active Defaults

### `default/hypr/bindings/clipboard.conf`

Source: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings/clipboard.conf>

| Keys | Directive | Action | Description |
| --- | --- | --- | --- |
| `SUPER + C` | `bindd` | `sendshortcut, CTRL, Insert` | Universal copy |
| `SUPER + V` | `bindd` | `sendshortcut, SHIFT, Insert` | Universal paste |
| `SUPER + X` | `bindd` | `sendshortcut, CTRL, X` | Universal cut |
| `SUPER + CTRL + V` | `bindd` | `exec, omarchy-launch-walker -m clipboard` | Clipboard manager |

### `default/hypr/bindings/media.conf`

Source: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings/media.conf>

| Keys | Directive | Action | Description |
| --- | --- | --- | --- |
| `XF86AudioRaiseVolume` | `bindeld` | `exec, $osdclient --output-volume raise` | Volume up |
| `XF86AudioLowerVolume` | `bindeld` | `exec, $osdclient --output-volume lower` | Volume down |
| `XF86AudioMute` | `bindeld` | `exec, $osdclient --output-volume mute-toggle` | Mute |
| `XF86AudioMicMute` | `bindeld` | `exec, $osdclient --input-volume mute-toggle` | Mute microphone |
| `XF86MonBrightnessUp` | `bindeld` | `exec, omarchy-brightness-display +5%` | Brightness up |
| `XF86MonBrightnessDown` | `bindeld` | `exec, omarchy-brightness-display 5%-` | Brightness down |
| `XF86KbdBrightnessUp` | `bindeld` | `exec, omarchy-brightness-keyboard up` | Keyboard brightness up |
| `XF86KbdBrightnessDown` | `bindeld` | `exec, omarchy-brightness-keyboard down` | Keyboard brightness down |
| `XF86KbdLightOnOff` | `bindld` | `exec, omarchy-brightness-keyboard cycle` | Keyboard backlight cycle |
| `ALT + XF86AudioRaiseVolume` | `bindeld` | `exec, $osdclient --output-volume +1` | Volume up precise |
| `ALT + XF86AudioLowerVolume` | `bindeld` | `exec, $osdclient --output-volume -1` | Volume down precise |
| `ALT + XF86MonBrightnessUp` | `bindeld` | `exec, omarchy-brightness-display +1%` | Brightness up precise |
| `ALT + XF86MonBrightnessDown` | `bindeld` | `exec, omarchy-brightness-display 1%-` | Brightness down precise |
| `XF86AudioNext` | `bindld` | `exec, $osdclient --playerctl next` | Next track |
| `XF86AudioPause` | `bindld` | `exec, $osdclient --playerctl play-pause` | Pause |
| `XF86AudioPlay` | `bindld` | `exec, $osdclient --playerctl play-pause` | Play |
| `XF86AudioPrev` | `bindld` | `exec, $osdclient --playerctl previous` | Previous track |
| `SUPER + XF86AudioMute` | `bindld` | `exec, omarchy-cmd-audio-switch` | Switch audio output |

### `default/hypr/bindings/tiling-v2.conf`

Source: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings/tiling-v2.conf>

| Keys | Directive | Action | Description |
| --- | --- | --- | --- |
| `SUPER + W` | `bindd` | `killactive` | Close window |
| `CTRL + ALT + DELETE` | `bindd` | `exec, omarchy-hyprland-window-close-all` | Close all windows |
| `SUPER + J` | `bindd` | `layoutmsg, togglesplit` | Toggle window split |
| `SUPER + P` | `bindd` | `pseudo` | Pseudo window |
| `SUPER + T` | `bindd` | `togglefloating` | Toggle tiling/floating |
| `SUPER + F` | `bindd` | `fullscreen, 0` | Full screen |
| `SUPER + CTRL + F` | `bindd` | `fullscreenstate, 0 2` | Tiled full screen |
| `SUPER + ALT + F` | `bindd` | `fullscreen, 1` | Full width |
| `SUPER + O` | `bindd` | `exec, omarchy-hyprland-window-pop` | Pop window out |
| `SUPER + L` | `bindd` | `exec, omarchy-hyprland-workspace-layout-toggle` | Toggle workspace layout |
| `SUPER + LEFT` | `bindd` | `movefocus, l` | Focus left |
| `SUPER + RIGHT` | `bindd` | `movefocus, r` | Focus right |
| `SUPER + UP` | `bindd` | `movefocus, u` | Focus up |
| `SUPER + DOWN` | `bindd` | `movefocus, d` | Focus down |
| `SUPER + code:10` | `bindd` | `workspace, 1` | Switch to workspace 1 |
| `SUPER + code:11` | `bindd` | `workspace, 2` | Switch to workspace 2 |
| `SUPER + code:12` | `bindd` | `workspace, 3` | Switch to workspace 3 |
| `SUPER + code:13` | `bindd` | `workspace, 4` | Switch to workspace 4 |
| `SUPER + code:14` | `bindd` | `workspace, 5` | Switch to workspace 5 |
| `SUPER + code:15` | `bindd` | `workspace, 6` | Switch to workspace 6 |
| `SUPER + code:16` | `bindd` | `workspace, 7` | Switch to workspace 7 |
| `SUPER + code:17` | `bindd` | `workspace, 8` | Switch to workspace 8 |
| `SUPER + code:18` | `bindd` | `workspace, 9` | Switch to workspace 9 |
| `SUPER + code:19` | `bindd` | `workspace, 10` | Switch to workspace 10 |
| `SUPER + SHIFT + code:10` | `bindd` | `movetoworkspace, 1` | Move window to workspace 1 |
| `SUPER + SHIFT + code:11` | `bindd` | `movetoworkspace, 2` | Move window to workspace 2 |
| `SUPER + SHIFT + code:12` | `bindd` | `movetoworkspace, 3` | Move window to workspace 3 |
| `SUPER + SHIFT + code:13` | `bindd` | `movetoworkspace, 4` | Move window to workspace 4 |
| `SUPER + SHIFT + code:14` | `bindd` | `movetoworkspace, 5` | Move window to workspace 5 |
| `SUPER + SHIFT + code:15` | `bindd` | `movetoworkspace, 6` | Move window to workspace 6 |
| `SUPER + SHIFT + code:16` | `bindd` | `movetoworkspace, 7` | Move window to workspace 7 |
| `SUPER + SHIFT + code:17` | `bindd` | `movetoworkspace, 8` | Move window to workspace 8 |
| `SUPER + SHIFT + code:18` | `bindd` | `movetoworkspace, 9` | Move window to workspace 9 |
| `SUPER + SHIFT + code:19` | `bindd` | `movetoworkspace, 10` | Move window to workspace 10 |
| `SUPER + SHIFT + ALT + code:10` | `bindd` | `movetoworkspacesilent, 1` | Move window silently to workspace 1 |
| `SUPER + SHIFT + ALT + code:11` | `bindd` | `movetoworkspacesilent, 2` | Move window silently to workspace 2 |
| `SUPER + SHIFT + ALT + code:12` | `bindd` | `movetoworkspacesilent, 3` | Move window silently to workspace 3 |
| `SUPER + SHIFT + ALT + code:13` | `bindd` | `movetoworkspacesilent, 4` | Move window silently to workspace 4 |
| `SUPER + SHIFT + ALT + code:14` | `bindd` | `movetoworkspacesilent, 5` | Move window silently to workspace 5 |
| `SUPER + SHIFT + ALT + code:15` | `bindd` | `movetoworkspacesilent, 6` | Move window silently to workspace 6 |
| `SUPER + SHIFT + ALT + code:16` | `bindd` | `movetoworkspacesilent, 7` | Move window silently to workspace 7 |
| `SUPER + SHIFT + ALT + code:17` | `bindd` | `movetoworkspacesilent, 8` | Move window silently to workspace 8 |
| `SUPER + SHIFT + ALT + code:18` | `bindd` | `movetoworkspacesilent, 9` | Move window silently to workspace 9 |
| `SUPER + SHIFT + ALT + code:19` | `bindd` | `movetoworkspacesilent, 10` | Move window silently to workspace 10 |
| `SUPER + S` | `bindd` | `togglespecialworkspace, scratchpad` | Toggle scratchpad |
| `SUPER + ALT + S` | `bindd` | `movetoworkspacesilent, special:scratchpad` | Move window to scratchpad |
| `SUPER + TAB` | `bindd` | `workspace, e+1` | Next workspace |
| `SUPER + SHIFT + TAB` | `bindd` | `workspace, e-1` | Previous workspace |
| `SUPER + CTRL + TAB` | `bindd` | `workspace, previous` | Former workspace |
| `SUPER + SHIFT + ALT + LEFT` | `bindd` | `movecurrentworkspacetomonitor, l` | Move workspace to left monitor |
| `SUPER + SHIFT + ALT + RIGHT` | `bindd` | `movecurrentworkspacetomonitor, r` | Move workspace to right monitor |
| `SUPER + SHIFT + ALT + UP` | `bindd` | `movecurrentworkspacetomonitor, u` | Move workspace to upper monitor |
| `SUPER + SHIFT + ALT + DOWN` | `bindd` | `movecurrentworkspacetomonitor, d` | Move workspace to lower monitor |
| `SUPER + SHIFT + LEFT` | `bindd` | `swapwindow, l` | Swap window left |
| `SUPER + SHIFT + RIGHT` | `bindd` | `swapwindow, r` | Swap window right |
| `SUPER + SHIFT + UP` | `bindd` | `swapwindow, u` | Swap window up |
| `SUPER + SHIFT + DOWN` | `bindd` | `swapwindow, d` | Swap window down |
| `ALT + TAB` | `bindd` | `cyclenext` | Cycle next window |
| `ALT + SHIFT + TAB` | `bindd` | `cyclenext, prev` | Cycle previous window |
| `ALT + TAB` | `bindd` | `bringactivetotop` | Bring active window to top |
| `ALT + SHIFT + TAB` | `bindd` | `bringactivetotop` | Bring active window to top |
| `SUPER + code:20` | `bindd` | `resizeactive, -100 0` | Expand window left |
| `SUPER + code:21` | `bindd` | `resizeactive, 100 0` | Shrink window left |
| `SUPER + SHIFT + code:20` | `bindd` | `resizeactive, 0 -100` | Shrink window up |
| `SUPER + SHIFT + code:21` | `bindd` | `resizeactive, 0 100` | Expand window down |
| `SUPER + mouse_down` | `bindd` | `workspace, e+1` | Scroll active workspace forward |
| `SUPER + mouse_up` | `bindd` | `workspace, e-1` | Scroll active workspace backward |
| `SUPER + mouse:272` | `bindmd` | `movewindow` | Move window drag |
| `SUPER + mouse:273` | `bindmd` | `resizewindow` | Resize window drag |
| `SUPER + G` | `bindd` | `togglegroup` | Toggle window grouping |
| `SUPER + ALT + G` | `bindd` | `moveoutofgroup` | Move active window out of group |
| `SUPER + ALT + LEFT` | `bindd` | `moveintogroup, l` | Move into group on left |
| `SUPER + ALT + RIGHT` | `bindd` | `moveintogroup, r` | Move into group on right |
| `SUPER + ALT + UP` | `bindd` | `moveintogroup, u` | Move into group on top |
| `SUPER + ALT + DOWN` | `bindd` | `moveintogroup, d` | Move into group on bottom |
| `SUPER + ALT + TAB` | `bindd` | `changegroupactive, f` | Next window in group |
| `SUPER + ALT + SHIFT + TAB` | `bindd` | `changegroupactive, b` | Previous window in group |
| `SUPER + CTRL + LEFT` | `bindd` | `changegroupactive, b` | Move grouped focus left |
| `SUPER + CTRL + RIGHT` | `bindd` | `changegroupactive, f` | Move grouped focus right |
| `SUPER + ALT + mouse_down` | `bindd` | `changegroupactive, f` | Next window in group via scroll |
| `SUPER + ALT + mouse_up` | `bindd` | `changegroupactive, b` | Previous window in group via scroll |
| `SUPER + ALT + code:10` | `bindd` | `changegroupactive, 1` | Activate group window 1 |
| `SUPER + ALT + code:11` | `bindd` | `changegroupactive, 2` | Activate group window 2 |
| `SUPER + ALT + code:12` | `bindd` | `changegroupactive, 3` | Activate group window 3 |
| `SUPER + ALT + code:13` | `bindd` | `changegroupactive, 4` | Activate group window 4 |
| `SUPER + ALT + code:14` | `bindd` | `changegroupactive, 5` | Activate group window 5 |
| `SUPER + Slash` | `bindd` | `exec, omarchy-hyprland-monitor-scaling-cycle` | Cycle monitor scaling |

### `default/hypr/bindings/utilities.conf`

Source: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings/utilities.conf>

| Keys | Directive | Action | Description |
| --- | --- | --- | --- |
| `SUPER + SPACE` | `bindd` | `exec, omarchy-launch-walker` | Launch apps |
| `SUPER + CTRL + E` | `bindd` | `exec, omarchy-launch-walker -m symbols` | Emoji picker |
| `SUPER + CTRL + C` | `bindd` | `exec, omarchy-menu capture` | Capture menu |
| `SUPER + CTRL + O` | `bindd` | `exec, omarchy-menu toggle` | Toggle menu |
| `SUPER + ALT + SPACE` | `bindd` | `exec, omarchy-menu` | Omarchy menu |
| `SUPER + ESCAPE` | `bindd` | `exec, omarchy-menu system` | System menu |
| `XF86PowerOff` | `bindld` | `exec, omarchy-menu system` | Power menu |
| `SUPER + K` | `bindd` | `exec, omarchy-menu-keybindings` | Show key bindings |
| `XF86Calculator` | `bindd` | `exec, gnome-calculator` | Calculator |
| `SUPER + SHIFT + SPACE` | `bindd` | `exec, omarchy-toggle-waybar` | Toggle top bar |
| `SUPER + CTRL + SPACE` | `bindd` | `exec, omarchy-menu background` | Theme background menu |
| `SUPER + SHIFT + CTRL + SPACE` | `bindd` | `exec, omarchy-menu theme` | Theme menu |
| `SUPER + BACKSPACE` | `bindd` | `exec, omarchy-hyprland-active-window-transparency-toggle` | Toggle window transparency |
| `SUPER + SHIFT + BACKSPACE` | `bindd` | `exec, omarchy-hyprland-window-gaps-toggle` | Toggle window gaps |
| `SUPER + CTRL + BACKSPACE` | `bindd` | `exec, omarchy-hyprland-window-single-square-aspect-toggle` | Toggle single-window square aspect |
| `SUPER + COMMA` | `bindd` | `exec, makoctl dismiss` | Dismiss last notification |
| `SUPER + SHIFT + COMMA` | `bindd` | `exec, makoctl dismiss --all` | Dismiss all notifications |
| `SUPER + CTRL + COMMA` | `bindd` | `exec, omarchy-toggle-notification-silencing` | Toggle notification silencing |
| `SUPER + ALT + COMMA` | `bindd` | `exec, makoctl invoke` | Invoke last notification |
| `SUPER + SHIFT + ALT + COMMA` | `bindd` | `exec, makoctl restore` | Restore last notification |
| `SUPER + CTRL + I` | `bindd` | `exec, omarchy-toggle-idle` | Toggle locking on idle |
| `SUPER + CTRL + N` | `bindd` | `exec, omarchy-toggle-nightlight` | Toggle nightlight |
| `CTRL + F1` | `bindd` | `exec, omarchy-brightness-display-apple -5000` | Apple display brightness down |
| `CTRL + F2` | `bindd` | `exec, omarchy-brightness-display-apple +5000` | Apple display brightness up |
| `SHIFT + CTRL + F2` | `bindd` | `exec, omarchy-brightness-display-apple +60000` | Apple display full brightness |
| `PRINT` | `bindd` | `exec, omarchy-cmd-screenshot` | Screenshot |
| `ALT + PRINT` | `bindd` | `exec, omarchy-menu screenrecord` | Screenrecording |
| `SUPER + PRINT` | `bindd` | `exec, pkill hyprpicker || hyprpicker -a` | Color picker |
| `SUPER + CTRL + S` | `bindd` | `exec, omarchy-menu share` | Share |
| `SUPER + CTRL + ALT + T` | `bindd` | `exec, notify-send -u low "..."` | Show time |
| `SUPER + CTRL + ALT + B` | `bindd` | `exec, notify-send -u low "$(omarchy-battery-status)"` | Show battery remaining |
| `SUPER + CTRL + A` | `bindd` | `exec, omarchy-launch-audio` | Audio controls |
| `SUPER + CTRL + B` | `bindd` | `exec, omarchy-launch-bluetooth` | Bluetooth controls |
| `SUPER + CTRL + W` | `bindd` | `exec, omarchy-launch-wifi` | Wifi controls |
| `SUPER + CTRL + T` | `bindd` | `exec, omarchy-launch-tui btop` | Activity |
| `SUPER + CTRL + X` | `bindd` | `exec, voxtype record toggle` | Toggle dictation |
| `SUPER + CTRL + Z` | `bindd` | `exec, hyprctl keyword cursor:zoom_factor $(hyprctl getoption cursor:zoom_factor -j | jq '.float + 1')` | Zoom in |
| `SUPER + CTRL + ALT + Z` | `bindd` | `exec, hyprctl keyword cursor:zoom_factor 1` | Reset zoom |
| `SUPER + CTRL + L` | `bindd` | `exec, omarchy-lock-screen` | Lock system |

## Deprecated Repo Files

### `default/hypr/bindings.conf`

Source: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings.conf>

Status: deprecated legacy file

| Keys | Directive | Action | Description |
| --- | --- | --- | --- |
| `SUPER + RETURN` | `bindd` | `exec, $terminal` | Terminal |
| `SUPER + F` | `bindd` | `exec, $fileManager` | File manager |
| `SUPER + B` | `bindd` | `exec, $browser` | Browser |
| `SUPER + M` | `bindd` | `exec, $music` | Music |
| `SUPER + N` | `bindd` | `exec, $terminal -e nvim` | Neovim |
| `SUPER + T` | `bindd` | `exec, $terminal -e btop` | btop |
| `SUPER + D` | `bindd` | `exec, $terminal -e lazydocker` | LazyDocker |
| `SUPER + G` | `bindd` | `exec, $messenger` | Messenger |
| `SUPER + O` | `bindd` | `exec, obsidian -disable-gpu` | Obsidian |
| `SUPER + SLASH` | `bindd` | `exec, $passwordManager` | Password manager |

### `default/hypr/bindings/tiling.conf`

Source: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/bindings/tiling.conf>

Status: deprecated legacy file

| Keys | Directive | Action | Description |
| --- | --- | --- | --- |
| `SUPER + W` | `bindd` | `killactive` | Close window |
| `CTRL + ALT + DELETE` | `bindd` | `exec, omarchy-hyprland-window-close-all` | Close all windows |
| `SUPER + J` | `bindd` | `togglesplit` | Toggle window split |
| `SUPER + P` | `bindd` | `pseudo` | Pseudo window |
| `SUPER + SHIFT + V` | `bindd` | `togglefloating` | Toggle window floating/tiling |
| `SHIFT + F11` | `bindd` | `fullscreen, 0` | Force full screen |
| `ALT + F11` | `bindd` | `fullscreen, 1` | Full width |
| `SUPER + LEFT` | `bindd` | `movefocus, l` | Move focus left |
| `SUPER + RIGHT` | `bindd` | `movefocus, r` | Move focus right |
| `SUPER + UP` | `bindd` | `movefocus, u` | Move focus up |
| `SUPER + DOWN` | `bindd` | `movefocus, d` | Move focus down |
| `SUPER + code:10` | `bindd` | `workspace, 1` | Switch to workspace 1 |
| `SUPER + code:11` | `bindd` | `workspace, 2` | Switch to workspace 2 |
| `SUPER + code:12` | `bindd` | `workspace, 3` | Switch to workspace 3 |
| `SUPER + code:13` | `bindd` | `workspace, 4` | Switch to workspace 4 |
| `SUPER + code:14` | `bindd` | `workspace, 5` | Switch to workspace 5 |
| `SUPER + code:15` | `bindd` | `workspace, 6` | Switch to workspace 6 |
| `SUPER + code:16` | `bindd` | `workspace, 7` | Switch to workspace 7 |
| `SUPER + code:17` | `bindd` | `workspace, 8` | Switch to workspace 8 |
| `SUPER + code:18` | `bindd` | `workspace, 9` | Switch to workspace 9 |
| `SUPER + code:19` | `bindd` | `workspace, 10` | Switch to workspace 10 |
| `SUPER + SHIFT + code:10` | `bindd` | `movetoworkspace, 1` | Move to workspace 1 |
| `SUPER + SHIFT + code:11` | `bindd` | `movetoworkspace, 2` | Move to workspace 2 |
| `SUPER + SHIFT + code:12` | `bindd` | `movetoworkspace, 3` | Move to workspace 3 |
| `SUPER + SHIFT + code:13` | `bindd` | `movetoworkspace, 4` | Move to workspace 4 |
| `SUPER + SHIFT + code:14` | `bindd` | `movetoworkspace, 5` | Move to workspace 5 |
| `SUPER + SHIFT + code:15` | `bindd` | `movetoworkspace, 6` | Move to workspace 6 |
| `SUPER + SHIFT + code:16` | `bindd` | `movetoworkspace, 7` | Move to workspace 7 |
| `SUPER + SHIFT + code:17` | `bindd` | `movetoworkspace, 8` | Move to workspace 8 |
| `SUPER + SHIFT + code:18` | `bindd` | `movetoworkspace, 9` | Move to workspace 9 |
| `SUPER + SHIFT + code:19` | `bindd` | `movetoworkspace, 10` | Move to workspace 10 |
| `SUPER + TAB` | `bindd` | `workspace, e+1` | Next workspace |
| `SUPER + SHIFT + TAB` | `bindd` | `workspace, e-1` | Previous workspace |
| `SUPER + CTRL + TAB` | `bindd` | `workspace, previous` | Former workspace |
| `SUPER + SHIFT + LEFT` | `bindd` | `swapwindow, l` | Swap left |
| `SUPER + SHIFT + RIGHT` | `bindd` | `swapwindow, r` | Swap right |
| `SUPER + SHIFT + UP` | `bindd` | `swapwindow, u` | Swap up |
| `SUPER + SHIFT + DOWN` | `bindd` | `swapwindow, d` | Swap down |
| `ALT + TAB` | `bindd` | `cyclenext` | Cycle next window |
| `ALT + SHIFT + TAB` | `bindd` | `cyclenext, prev` | Cycle previous window |
| `ALT + TAB` | `bindd` | `bringactivetotop` | Bring active window to top |
| `ALT + SHIFT + TAB` | `bindd` | `bringactivetotop` | Bring active window to top |
| `SUPER + code:20` | `bindd` | `resizeactive, -100 0` | Expand left |
| `SUPER + code:21` | `bindd` | `resizeactive, 100 0` | Shrink left |
| `SUPER + SHIFT + code:20` | `bindd` | `resizeactive, 0 -100` | Shrink up |
| `SUPER + SHIFT + code:21` | `bindd` | `resizeactive, 0 100` | Expand down |
| `SUPER + mouse_down` | `bindd` | `workspace, e+1` | Scroll workspace forward |
| `SUPER + mouse_up` | `bindd` | `workspace, e-1` | Scroll workspace backward |
| `SUPER + mouse:272` | `bindmd` | `movewindow` | Move window drag |
| `SUPER + mouse:273` | `bindmd` | `resizewindow` | Resize window drag |

## Alternate Repo File

### `default/hypr/plain-bindings.conf`

Source: <https://raw.githubusercontent.com/basecamp/omarchy/dev/default/hypr/plain-bindings.conf>

Status: alternate launcher layout, not the default repo binding set

| Keys | Directive | Action | Description |
| --- | --- | --- | --- |
| `SUPER + RETURN` | `bindd` | `exec, uwsm-app -- xdg-terminal-exec --dir="$(omarchy-cmd-terminal-cwd)"` | Terminal |
| `SUPER + SHIFT + RETURN` | `bindd` | `exec, omarchy-launch-browser` | Browser |
| `SUPER + SHIFT + F` | `bindd` | `exec, uwsm-app -- nautilus --new-window` | File manager |
| `SUPER + ALT + SHIFT + F` | `bindd` | `exec, uwsm-app -- nautilus --new-window "$(omarchy-cmd-terminal-cwd)"` | File manager in cwd |
| `SUPER + SHIFT + B` | `bindd` | `exec, omarchy-launch-browser` | Browser |
| `SUPER + SHIFT + ALT + B` | `bindd` | `exec, omarchy-launch-browser --private` | Browser private |
| `SUPER + SHIFT + N` | `bindd` | `exec, omarchy-launch-editor` | Editor |

Commented examples in the file are not active bindings:
- `SUPER + SHIFT + A` -> ChatGPT webapp
- `SUPER + SHIFT + R` -> SSH example
- `SUPER + SPACE` can be rebound to `omarchy-menu`

## Non-Hyprland Native Bindings

### Fcitx5 defaults documented in issue `#2276`

Source: <https://github.com/basecamp/omarchy/issues/2276>

These are not Hyprland binds, but they are native to the bundled input-method stack and matter for keyboard-layer design.

| Keys | Action | Notes |
| --- | --- | --- |
| `SUPER + ;` | `Quick Phrase` | Open quick phrase insertion |
| `SUPER + ~` | `Quick Phrase` | Same function as `SUPER + ;` |
| `CTRL + ;` | `Clipboard history` | Open clipboard history |
| `CTRL + ALT + H` | `Autocomplete toggle` | Toggle autocomplete |

## Live User Overrides (this machine)

These bindings are ACTIVE on this machine via `~/.config/hypr/bindings.conf`.
They are NOT part of the upstream Omarchy repo but override/extend the defaults.

Source: `~/.config/hypr/bindings.conf`

| Keys | Directive | Action | Description |
| --- | --- | --- | --- |
| `SUPER + ALT + RETURN` | `bindd` | `exec, uwsm-app -- xdg-terminal-exec --dir="$(omarchy-cmd-terminal-cwd)" tmux new` | Terminal with tmux |
| `SUPER + RETURN` | `bindd` | `exec, uwsm-app -- xdg-terminal-exec --dir="$(omarchy-cmd-terminal-cwd)"` | Terminal |
| `SUPER + SHIFT + RETURN` | `bindd` | `exec, omarchy-launch-browser` | Browser |
| `SUPER + SHIFT + F` | `bindd` | `exec, uwsm-app -- nautilus --new-window` | File manager |
| `SUPER + ALT + SHIFT + F` | `bindd` | `exec, uwsm-app -- nautilus --new-window "$(omarchy-cmd-terminal-cwd)"` | File manager in cwd |
| `SUPER + SHIFT + B` | `bindd` | `exec, omarchy-launch-browser` | Browser (duplicate) |
| `SUPER + SHIFT + ALT + B` | `bindd` | `exec, omarchy-launch-browser --private` | Browser private |
| `SUPER + SHIFT + M` | `bindd` | `exec, omarchy-launch-or-focus spotify` | Spotify |
| `SUPER + SHIFT + N` | `bindd` | `exec, omarchy-launch-editor` | Editor |
| `SUPER + SHIFT + D` | `bindd` | `exec, omarchy-launch-tui lazydocker` | LazyDocker |
| `SUPER + SHIFT + G` | `bindd` | `exec, omarchy-launch-or-focus ^signal$ "uwsm-app -- signal-desktop"` | Signal |
| `SUPER + SHIFT + O` | `bindd` | `exec, omarchy-launch-or-focus ^obsidian$ "uwsm-app -- obsidian -disable-gpu --enable-wayland-ime"` | Obsidian |
| `SUPER + SHIFT + W` | `bindd` | `exec, uwsm-app -- typora --enable-wayland-ime` | Typora |
| `SUPER + SHIFT + SLASH` | `bindd` | `exec, uwsm-app -- 1password` | 1Password |
| `SUPER + SHIFT + A` | `bindd` | `exec, omarchy-launch-webapp "https://chatgpt.com"` | ChatGPT |
| `SUPER + SHIFT + ALT + A` | `bindd` | `exec, omarchy-launch-webapp "https://grok.com"` | Grok |
| `SUPER + SHIFT + C` | `bindd` | `exec, omarchy-launch-webapp "https://app.hey.com/calendar/weeks/"` | Calendar |
| `SUPER + SHIFT + E` | `bindd` | `exec, omarchy-launch-webapp "https://app.hey.com"` | Email |
| `SUPER + SHIFT + Y` | `bindd` | `exec, omarchy-launch-webapp "https://youtube.com/"` | YouTube |
| `SUPER + SHIFT + ALT + G` | `bindd` | `exec, omarchy-launch-or-focus-webapp WhatsApp "https://web.whatsapp.com/"` | WhatsApp |
| `SUPER + SHIFT + CTRL + G` | `bindd` | `exec, omarchy-launch-or-focus-webapp "Google Messages" "https://messages.google.com/web/conversations"` | Google Messages |
| `SUPER + SHIFT + P` | `bindd` | `exec, omarchy-launch-or-focus-webapp "Google Photos" "https://photos.google.com/"` | Google Photos |
| `SUPER + SHIFT + X` | `bindd` | `exec, omarchy-launch-webapp "https://x.com/"` | X |
| `SUPER + SHIFT + ALT + X` | `bindd` | `exec, omarchy-launch-webapp "https://x.com/compose/post"` | X compose post |

