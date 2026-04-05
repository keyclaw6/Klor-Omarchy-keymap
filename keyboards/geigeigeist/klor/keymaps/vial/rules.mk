# ── Vial support ──
VIA_ENABLE = yes
VIAL_ENABLE = yes
ENCODER_MAP_ENABLE = yes

# ── Tri-layer: LOWER(1) + RAISE(2) = ADJUST(3) ──
TRI_LAYER_ENABLE = yes

# ── Match zynex keymap hardware config ──
OLED_ENABLE = no
ENCODER_ENABLE = yes
EXTRAKEY_ENABLE = yes
DYNAMIC_MACRO_ENABLE = no
COMBO_ENABLE = yes
KEY_OVERRIDE_ENABLE = yes
TAP_DANCE_ENABLE = yes

# ── Disable features for hardware not present on this Polydactyl build ──
HAPTIC_ENABLE = no
RGB_MATRIX_ENABLE = no
AUDIO_ENABLE = no

# ── Danish characters (æ ø å) ──
UNICODEMAP_ENABLE = yes

# ── Autocorrect (typo correction + text expansion) ──
AUTOCORRECT_ENABLE = yes

# ── Raw HID for bridge protocol (VIA already implies this, explicit for clarity) ──
RAW_ENABLE = yes

PIN_COMPATIBLE = promicro
