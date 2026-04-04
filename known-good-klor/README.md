
# QMK CONFIG FOR THE KLOR SPLIT KEYBOARD

[Here](https://github.com/GEIGEIGEIST/klor) you can find the hardware files and build guide.

KLOR is a 36-42 key column-staggered split keyboard. It supports a per key RGB matrix, encoders, OLED displays, haptic feedback, audio, a Pixart Paw3204 trackball and four different layouts, through brake off parts.

![KLOR layouts](/docs/images/klor-layouts.svg)

Polydactyl is the default layout. If you choose one of the other layouts you can use the matching template in the default keymap.\
If you choose Konrad or Saegewerk and plan on using LEDs you need to uncomment the appropiate lines in the `klor.c` file.



## RP2040 MCU
**Adafruit KB2040 / Sparkfun Pro Micro RP2040 / BastardKB Splinky / Boardsource Blok / Elite-Pi / Sea-Picro / key micro RP**

Place the klor folder from this repository in the keyboards folder of your qmk installation.\
Most of the RP2040 MCUs use the same pinout, the Adafruit KB2040 is an exclusion. If you plan on using it you need to uncomment the appropiate lines in the `/2040/rules.mk` file.\
Than you can use this command to compile the RP2040 firmware for the KLOR.

`qmk compile -kb klor/2040 -km default`


