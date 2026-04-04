OLED_ENABLE = no
ENCODER_ENABLE = yes
EXTRAKEY_ENABLE = yes
DYNAMIC_MACRO_ENABLE = no
COMBO_ENABLE = yes
KEY_OVERRIDE_ENABLE = yes

# Disable features for hardware not present on this Polydactyl build.
# HAPTIC (DRV2605L) is enabled in keyboard.json but the chip is not on this PCB.
# Each I2C transaction to the missing DRV2605L blocks for its timeout duration,
# stalling the scan loop and causing ~3-4 second input latency.
HAPTIC_ENABLE = no

# RGB LEDs and audio buzzer are also not installed on this board.
RGB_MATRIX_ENABLE = no
AUDIO_ENABLE = no

PIN_COMPATIBLE = promicro

