#!/usr/bin/env python3
"""Validate built KLOR halves, including actual linked event listener order.

Usage: python3 zmk/tests/validate_build.py LEFT_BUILD RIGHT_BUILD
Requires arm-none-eabi-nm on PATH; only Python's standard library is used.
"""

import argparse
from pathlib import Path
import re
import struct
import subprocess


def node(dts, name):
    match = re.search(r"\b" + re.escape(name) + r"\s*\{", dts)
    assert match, f"missing DTS node {name}"
    depth = 1
    end = match.end()
    while depth:
        depth += (dts[end] == "{") - (dts[end] == "}")
        end += 1
    return dts[match.end():end - 1]


def cells(text, prop):
    match = re.search(r"\b" + re.escape(prop) + r"\s*=\s*<([^>]+)>", text)
    assert match, f"missing DTS property {prop}"
    return [int(value, 0) for value in match[1].split()]


def elf_bytes(elf, address, count):
    """Resolve a linked ELF32 virtual address to its on-disk load segment."""
    assert elf[:6] == b"\x7fELF\x01\x01", "expected little-endian ELF32"
    phoff = struct.unpack_from("<I", elf, 28)[0]
    phentsize, phnum = struct.unpack_from("<HH", elf, 42)
    for index in range(phnum):
        kind, offset, vaddr, _, size, _, _, _ = struct.unpack_from(
            "<IIIIIIII", elf, phoff + index * phentsize)
        if kind == 1 and vaddr <= address and address + count <= vaddr + size:
            start = offset + address - vaddr
            return elf[start:start + count]
    raise AssertionError("descriptor not in a file-backed load segment")


def validate(directory, central):
    directory = directory / "zephyr"
    config = dict(re.findall(r"^(CONFIG_\w+)=(.*)$",
                             (directory / ".config").read_text(), re.MULTILINE))

    def enabled(key, expected=True):
        assert (config.get("CONFIG_" + key) == "y") == expected, key

    def number(key, expected):
        assert int(config["CONFIG_" + key], 0) == expected, key

    for key in ["ZMK_SPLIT", "ZMK_SPLIT_WIRED", "ZMK_SPLIT_WIRED_UART_MODE_INTERRUPT",
                "UART_RP2040_PIO_HALF_DUPLEX", "GPIO_HOGS", "RETENTION_BOOT_MODE",
                "KLOR_OMARCHY", "EC11"]:
        enabled(key)
    enabled("ZMK_SPLIT_ROLE_CENTRAL", central)
    enabled("ZMK_SPLIT_BLE", False)
    enabled("ZMK_USB", central)
    enabled("KLOR_OMARCHY_RAW_HID", central)
    number("ZMK_SPLIT_WIRED_HALF_DUPLEX_RX_TIMEOUT", 20)
    if central:
        enabled("ZMK_HID_REPORT_TYPE_HKRO")
        enabled("ZMK_USB_BOOT")
        enabled("ZMK_HID_INDICATORS")
        enabled("ENABLE_HID_INT_OUT_EP")
        number("ZMK_HID_KEYBOARD_REPORT_SIZE", 6)
        number("USB_DEVICE_VID", 0x3A3C)
        number("USB_DEVICE_PID", 1)
        number("USB_HID_DEVICE_COUNT", 2)
        number("HID_INTERRUPT_EP_MPS", 32)

    dts = (directory / "zephyr.dts").read_text()
    uart = node(dts, "klor_split_uart: uart")
    assert 'compatible = "zmk,uart-rp2040-pio-half-duplex";' in uart
    assert 'status = "okay";' in uart
    assert cells(uart, "current-speed") == [19200]
    assert "&klor_split_uart_default" in uart
    pin = node(dts, "klor_split_uart_default")
    assert cells(pin, "pinmux") == [0x27]  # RP2040 PIO1 function 7, GP1 << 5.
    assert "input-enable;" in pin and "bias-pull-up;" in pin
    guard = node(dts, "klor_trrs_rx_guard")
    assert cells(guard, "gpios") == [4, 0]
    assert "input;" in guard and "output-" not in guard
    # GP4 is reserved to its input-only hog; no matrix/encoder GPIO consumer.
    assert not re.search(r"<\s*&gpio0\s+(?:0x0*4|4)\s", dts)
    wired = node(dts, "wired_split")
    assert "&klor_split_uart" in wired and "half-duplex;" in wired
    assert 'status = "disabled";' in node(dts, "uart@40034000")
    transform = node(dts, "keymap_transform_0")
    positions = cells(transform, "map")
    assert len(positions) == 44 and len(set(positions)) == 44
    assert positions[36:40] == [0x301, 0x302, 0x303, 0x304]
    assert positions[40:44] == [0x704, 0x703, 0x702, 0x701]
    if central:
        assert "row-offset" not in transform or cells(transform, "row-offset") == [0]
    else:
        assert cells(transform, "row-offset") == [4]
    for side, active in [("left", central), ("right", not central)]:
        encoder = node(dts, "encoder_" + side)
        assert cells(encoder, "steps") == [40]
        assert f'status = "{"okay" if active else "disabled"}";' in encoder
    assert cells(node(dts, "sensors"), "triggers-per-rotation") == [20]

    elf = directory / "zmk.elf"
    output = subprocess.check_output(["arm-none-eabi-nm", "-n", str(elf)], text=True)
    symbols = {name: int(addr, 16) for addr, _, name in
               re.findall(r"^([0-9a-fA-F]+)\s+(\w)\s+(\S+)$", output, re.MULTILINE)}
    assert not subprocess.check_output(["arm-none-eabi-nm", "-u", str(elf)], text=True).strip()
    boot = symbols["zmk_event_sub_klor_boot_combo_listenerzmk_position_state_changed"]
    if central:
        command = symbols["zmk_event_sub_klor_command_listenerzmk_position_state_changed"]
        holdtap = symbols["zmk_event_sub_behavior_hold_tapzmk_position_state_changed"]
        keymap = symbols["zmk_event_sub_keymapzmk_position_state_changed"]
        assert boot < command < holdtap < keymap, "capturing listeners precede KLOR observers"
        descriptor = bytes.fromhex("06 60 ff 09 61 a1 01 15 00 26 ff 00 75 08 95 20 "
                                   "09 62 81 02 95 20 09 63 91 02 c0")
        assert elf_bytes(elf.read_bytes(), symbols["raw_hid_report_desc"], len(descriptor)) == descriptor
    else:
        assert boot < symbols["zmk_event_sub_split_peripheralzmk_position_state_changed"]
        assert not any(name.startswith(("zmk_hid_", "zmk_keymap_", "raw_hid_"))
                       for name in symbols), "central-only code linked on peripheral"
    assert (directory / "zmk.uf2").stat().st_size > 0
    print(f"{'central' if central else 'peripheral'}: config, GPIO/PIO, transform, encoders, ELF, UF2 passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    args = parser.parse_args()
    validate(args.left, True)
    validate(args.right, False)
