# ── Encoder maps ──
ENCODER_MAP_ENABLE = yes

# ── Tri-layer: LOWER(1) + RAISE(2) = ADJUST(3) ──
TRI_LAYER_ENABLE = yes

# ── BIOS/pre-OS compatibility: keep standard 6KRO boot protocol ──
NKRO_ENABLE = no

# ── Match zynex keymap hardware config ──
OLED_ENABLE = no
ENCODER_ENABLE = yes
EXTRAKEY_ENABLE = yes
DYNAMIC_MACRO_ENABLE = no
KEY_OVERRIDE_ENABLE = yes

# ── Disable features for hardware not present on this Polydactyl build ──
HAPTIC_ENABLE = no
RGB_MATRIX_ENABLE = no
AUDIO_ENABLE = no

# ── Danish characters (æ ø å) ──
UNICODEMAP_ENABLE = yes

# ── Autocorrect (typo correction + text expansion) ──
AUTOCORRECT_ENABLE = yes

# ── Raw HID for bridge protocol ──
RAW_ENABLE = yes

PIN_COMPATIBLE = promicro
