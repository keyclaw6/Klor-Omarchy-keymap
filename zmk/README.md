# KLOR Omarchy — ZMK port

This directory is the ZMK replacement for the existing QMK firmware in this
repository. The QMK firmware remains untouched as the rollback/reference
implementation.

## Scope

Carried over:

- exact 44-position Polydactyl physical map;
- LOWER, RAISE, ADJUST and NAV layers;
- GACS home-row modifiers and G/H NAV layer-taps;
- Shift+Backspace -> Delete;
- Danish ae/oe/aa Unicode entry on Linux;
- left encoder volume, right encoder display brightness;
- NAV encoder workspace switching;
- volatile Training Mode;
- double-tap right Alt command mode;
- 1/2/3-tap speech-to-text depth;
- the existing 32-byte KLOR Raw HID bridge protocol;
- the existing USB VID/PID and vendor HID usage page/usage so
  `bridge/klor-bridge.py` does not need a protocol rewrite;
- the new RP2040 one-wire ZMK split transport on KLOR D2/GP1.

Intentionally **not** carried over:

- QMK autocorrect;
- the autocorrect dictionary/trie;
- `AC_TOGG` on ADJUST.

The former autocorrect-toggle position is deliberately unassigned.

## Hardware

Target kit: BeeKeeb KLOR rev1.3 with Sea-Picro RP2040 controllers.

Sea-Picro uses the same legacy I/O pinout as SparkFun Pro Micro RP2040, so ZMK
builds use `sparkfun_pro_micro_rp2040//zmk` while all KLOR-critical GPIOs are
specified directly.

The three-wire split link is VCC + GND + DATA. KLOR's TRS plug bridges the PCB
RX/TX jack contacts. GP1 is the PIO one-wire driver; GP4 is forced input-only.

## ZMK source

`config/west.yml` currently points at the working single-wire ZMK mirror:

- repository: `keyclaw6/zz-scratch-probe-20260902`
- branch: `feature/single-wire-wired-split`

Once the native fork is created/renamed to
`keyclaw6/zmk-single-wire-wired-split`, only the manifest repository path
needs to change.

## Raw HID compatibility

The central exposes a second HID interface (`HID_1`) matching QMK Raw HID:

- VID/PID: `3A3C:0001`
- usage page: `0xFF60`
- top-level usage: `0x61`
- 32-byte input report
- 32-byte output report
- no report ID

Bridge packets remain:

- `0x20` action
- `0x21` status
- `0x22` heartbeat
- `0x23` config

Host status/heartbeat/config packets are acknowledged exactly like the QMK
firmware.

## Build

The CI validation builds the files explicitly with:

- central: `klor-left.conf` + `klor-left.overlay`
- peripheral: `klor-right.conf` + `klor-right.overlay`
- keymap: `klor.keymap`
- extra module: `../module`

Do not hot-plug the powered TRS/TRRS split cable.

## Known validation gate

Software builds/tests are not the final gate. Before retiring QMK, test both
halves standalone, then the 19.2 kbaud split pair, bridge heartbeat/actions,
command/STT mode, every layer, both encoders, resets, and a typing soak on the
actual BeeKeeb/Sea-Picro KLOR.
