#!/usr/bin/env python3
"""Install only host brightness controls, preserving other user bindings."""
from datetime import datetime
from pathlib import Path
import shutil

source = Path(__file__).resolve().parent
target = Path.home() / ".config/hypr"
target.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def write(path, content):
    if path.exists():
        if path.read_text() == content:
            return
        shutil.copy2(path, path.with_name(path.name + ".bak-klor-brightness-" + stamp))
    path.write_text(content)


def replace_block(path, begin, end, block):
    lines = path.read_text().splitlines() if path.exists() else []
    result = []
    in_block = False
    for line in lines:
        if line.strip() == begin:
            in_block = True
        elif in_block:
            if line.strip() == end:
                in_block = False
        elif "brightness-display-ddc.sh" not in line:
            result.append(line)
    if in_block:
        raise RuntimeError(f"Unclosed brightness block in {path}")
    if block:
        if result and result[-1].strip():
            result.append("")
        result.extend([begin, *block, end])
    write(path, "\n".join(result) + "\n")


helper = target / "brightness-display-ddc.sh"
write(helper, (source / helper.name).read_text())
helper.chmod(0o755)
legacy_begin = "# KLOR external monitor brightness begin"
legacy_end = "# KLOR external monitor brightness end"
if (target / "hyprland.lua").exists():
    module = target / "brightness-bindings.lua"
    write(module, (source / module.name).read_text())
    replace_block(
        target / "bindings.lua",
        "-- KLOR external monitor brightness begin",
        "-- KLOR external monitor brightness end",
        ['dofile(os.getenv("HOME") .. "/.config/hypr/brightness-bindings.lua")'],
    )
    legacy = target / "bindings.conf"
    if legacy.exists():
        replace_block(legacy, legacy_begin, legacy_end, [])
else:
    block = ["# Route standard brightness media keys to both DDC monitors."]
    for modifiers, amount in [("", 5), ("ALT", 1)]:
        for direction, key in [("up", "Up"), ("down", "Down")]:
            block.extend([
                f"unbind = {modifiers}, XF86MonBrightness{key}",
                f'bindeld = {modifiers}, XF86MonBrightness{key}, Both monitors brightness {direction}, exec, "{helper}" {direction} {amount}',
            ])
    replace_block(target / "bindings.conf", legacy_begin, legacy_end, block)
print(f"Installed both-monitor brightness controls in {target}")
