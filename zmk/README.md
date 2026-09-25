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

## Build and software validation

Validated with the existing checkout at
`/home/kab/code/zmk-single-wire-final`, on `feature/single-wire-wired-split`.
Validation on 2026-09-25 used ZMK
`c7172fd6eabbca9f3e05564e91d353d0211d4675` and Zephyr
`10ba6d0cb38bc3d258775d27982f707599320085`. Neither feature source was changed.
Dependencies live inside that checkout; the old `zmk-single-wire-work/zmk`
checkout is not modified. Its existing Python environment can be reused.

```bash
cd /home/kab/code/zmk-single-wire-final
export PATH=/home/kab/code/zmk-single-wire-work/.venv/bin:$PATH
export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb
export GNUARMEMB_TOOLCHAIN_PATH=/usr

for side in left right; do
  west build -p always -s app -d build/klor-$side \
    -b sparkfun_pro_micro_rp2040//zmk -- \
    -DZMK_CONFIG=/home/kab/Klor-Omarchy-keymap/zmk/config \
    -DZMK_EXTRA_MODULES=/home/kab/Klor-Omarchy-keymap/zmk/module \
    -DEXTRA_CONF_FILE=/home/kab/Klor-Omarchy-keymap/zmk/config/klor-$side.conf \
    -DDTC_OVERLAY_FILE=/home/kab/Klor-Omarchy-keymap/zmk/config/klor-$side.overlay \
    -DKEYMAP_FILE=/home/kab/Klor-Omarchy-keymap/zmk/config/klor.keymap
done
```

Use `EXTRA_CONF_FILE`, preserving ZMK's application defaults. `CONFIG_FILE`
is not the Zephyr configuration argument. The UF2 outputs are
`build/klor-left/zephyr/zmk.uf2` and `build/klor-right/zephyr/zmk.uf2`.

From this repository:

```bash
python3 -m unittest discover -s zmk/tests -p 'test_*.py'
python3 zmk/tests/validate_build.py \
  /home/kab/code/zmk-single-wire-final/build/klor-left \
  /home/kab/code/zmk-single-wire-final/build/klor-right
clang-format --dry-run --Werror \
  -style=file:/home/kab/code/zmk-single-wire-final/.clang-format \
  zmk/module/src/*.c
git diff --check
```

The host tests compile the actual custom C sources with small Zephyr/ZMK test
stubs; they do not emulate USB hardware or the ZMK hold-tap engine. The build
validator checks the generated configuration, devicetree and linked symbols.
Both are required: a previous invalid Kconfig dependency silently disabled the
custom module even though it was requested in the `.conf` file.

Validation result: both firmware builds, all 10 host test groups, generated
configuration/devicetree/ELF checks, ZMK C formatting, and `git diff --check`
passed. The 220-position comparison reads the actual QMK `main` reference.
Remaining upstream build warnings concern deprecated KSCAN, the retained-memory
unit address, and an ELF RWX load segment.

| Artifact | UF2 bytes | FLASH / RAM used | SHA-256 |
| --- | ---: | --- | --- |
| left central | 108032 | 53684 / 18687 bytes | `bac490a0d6fe03284bec1569dc72ad3f52c87630fd7c84c86dc36c413ef613cf` |
| right peripheral | 64000 | 31688 / 9548 bytes | `59a1fdbd4b745ca07a04424fd665cc56c5d0dc29e5e8bfa376725a122c8d643a` |

## QMK parity audit

The reference is `main:keyboards/geigeigeist/klor/keymaps/plain/` and its
`keymap.c`, `config.h`, and `rules.mk`. All 44 positions on each of the five
layers were compared, including the two encoder pushes and transparent thumbs.

| Feature | Port behavior |
| --- | --- |
| BASE / LOWER / RAISE / ADJUST / NAV | Same 220 positions; ADJUST's former correction toggle is unassigned. All eleven AF13–AF23 bindings include left Alt. LOWER+RAISE activates ADJUST. |
| Home-row modifiers | GACS / SCAG, right-side L uses left Alt, semicolon uses right GUI. 180 ms balanced hold-tap, 0 ms quick-tap, 120 ms prior-idle. Both encoder pushes and all thumbs are exempt from the opposite-hand rule. Ctrl/Shift alone use speculative holds. |
| G / H | Tap letters, hold NAV, opposite-hand rule with thumb/push exemptions; training does not suppress these. |
| Training | Volatile flag, no hidden layer. Bare GUI/Ctrl/Shift on BASE and Ctrl/Shift/Alt on NAV are suppressed. Transparent LOWER/RAISE/ADJUST thumb modifiers continue working. Direct NAV is suppressed on every layer; RAlt still double-taps but sends no held modifier. Release matching prevents stuck keys when toggled while a key is down. |
| Command mode | No hidden layer. Uses the currently resolved key binding, unwraps home-row/layer taps, times out after 3 s except during STT. Unmapped keys exit and retain their normal behavior; consumed presses have consumed releases. |
| STT | T tap depth 1/2/3, 300 ms window, third tap finalizes immediately. Active-session T uses the same depth/toggle protocol. RAlt or an unmapped key stops with parameter 0. A different key during counting finalizes first and passes its original behavior through, as QMK does. |
| Escape | Consumed while command mode is active; cancels a pending STT count or stops recording. This also applies during counting, following the explicit port requirement rather than QMK's counting-first edge case. |
| NAV arrows | Same modifier-dependent actions, including Ctrl resize and Ctrl+Alt horizontal workspace actions. Existing held modifiers remain in the report, as in QMK. |
| Danish Unicode | Linux Ctrl+Shift+U, unmodified hexadecimal, Space; Shift XOR Caps Lock selects case. Caps temporarily disabled/restored; existing modifiers and keys restored. 10 ms report spacing. |
| Encoders | Left volume, right brightness, both workspace navigation on NAV; two quadrature edges per event, matching QMK resolution 2. |
| Shift+Backspace | Delete with Shift suppressed; available on BASE, transparent RAISE, and ADJUST. LOWER retains 0; NAV retains Super+0. |
| Bridge | Central only, VID/PID `3A3C:0001`, vendor usage `FF60:61`, 32 bytes without report ID, commands `20`–`23`. Status/heartbeat/config ACKs preserve the payload. A transmit FIFO avoids blocking in a USB callback. |
| Boot | ADJUST boot key plus five all-four-thumb presses within 3 s on either local half. The boot observer runs before capturing key behaviors and peripheral forwarding. Both controllers also retain the board's double-reset boot access. |

### Deliberate boundaries of equivalence

ZMK's native hold-tap engine is not QMK's tapping engine. Its prior-idle filter
observes nonmodifier key-down events, whereas QMK Flow Tap also tracks releases,
filters the preceding/current key classes, and disables flow on Ctrl/GUI/left-Alt
hotkeys. Balanced positional holds and speculative Ctrl/Shift holds preserve the
intended chords but do not promise identical timing for every roll or nested
chord. Validate typing feel on hardware before replacing QMK.

ZMK mod-morph selects Backspace/Delete at key-down. QMK's key override can also
switch an already-held Backspace when Shift changes afterward. That dynamic
held-key transition is not reproduced by this native ZMK behavior.

Unicode entry needs one free slot in the 6KRO report. With all six slots occupied
it safely declines entry; holding a key used by the Unicode sequence can prevent
its second key-down edge, as in QMK.

The peripheral remains a split peripheral when isolated: its local boot gesture
works without the central, but it does not become an independent USB keyboard.

## Remaining hardware gate

Before retiring QMK, test each half's isolated boot gesture, then the 19.2 kbaud
split pair: all keys/layers, encoder direction and detents, cross-hand NAV chords,
training with LOWER/RAISE/ADJUST, rapid typing/rolls, Danish characters with held
modifiers/Caps, USB BIOS boot protocol, bridge reconnect/heartbeat/actions, and
STT depth/start/stop. Test resets and a typing soak. Software tests cannot verify
matrix wiring, diode polarity, USB host behavior, encoder direction or electrical
signal integrity. Do not hot-plug the powered TRS/TRRS split cable.
