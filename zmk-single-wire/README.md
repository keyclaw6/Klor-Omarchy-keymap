# KLOR ZMK single-wire prototype

This is an experimental ZMK build for the existing wired KLOR PCB with SparkFun Pro Micro RP2040 controllers and the existing TRS/TRRS interconnect. It does not require a wiring change.

## Hardware mapping verified before implementation

The official KLOR QMK configuration uses `SOFT_SERIAL_PIN D2`. On the ATmega32U4-style Pro Micro naming used by QMK, that is AVR PD2 / the physical RX pin. QMK's SparkFun Pro Micro RP2040 converter maps that pin to RP2040 GP1. Zephyr's SparkFun Pro Micro RP2040 connector calls the same physical pin Arduino D0 / `pro_micro 0`, which is why this prototype deliberately uses **GP1**, not Zephyr `pro_micro 2`.

The KLOR build guide explicitly supports a TRS cable for half-duplex operation, so VCC + GND + this single data conductor matches the existing PCB.

## Transport design

Current ZMK main already contains an experimental `half-duplex` wired-split protocol, but RP2040's stock Zephyr PIO UART assumes separate TX and RX pins. This prototype therefore supplies a small PIO UART device which owns one GPIO, listens with the pin as an input, and changes it to an output only while transmitting.

The link is configured for 115200 baud and polling mode. The receive poll period is reduced from ZMK's 10-tick default to 2 ticks to stay comfortably ahead of the RP2040 PIO RX FIFO.

## Build

GitHub Actions builds two UF2 files with:

- board: `sparkfun_pro_micro_rp2040//zmk`
- shields: `klor_left` and `klor_right`

The left half is the fixed ZMK split central and is the half that should be connected to the host over USB during normal use.

## Test gate before any upstream PR

Do not treat a successful compile as validation. Before proposing this upstream, test on the actual KLOR hardware, including all keys on the peripheral half, simultaneous/cross-half chords, encoder traffic, repeated resets of either half, unplug/replug cycles with power removed first, and a multi-hour soak.

There is also an open upstream ZMK discussion around polling + partial receive fragments. A proposed one-line change in PR #3497 is not being copied blindly here because a maintainer review correctly points out that changing the wakeup predicate to `read > 0` can strand already-buffered work. If the KLOR reproduces that wedge, the fix should be made at the half-duplex RX-complete scheduling boundary rather than by removing the buffered-work retry.

## Safety

TRS/TRRS split cables must only be inserted or removed while the keyboard is unpowered. The connector can momentarily short adjacent contacts during insertion/removal.
