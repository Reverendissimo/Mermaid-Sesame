# keypad howto

1) flash MiniCore for atmega168pa
2) make sure you have the Keypad arduino library
3) if re-making the hw from scratch, you need to make some HW mods to the keypad:
	- green led moved to a different pin (due to UART conflict)
4) verify the pin IDs

Clock external 4 mhz
Board: ATmega168
Variant: 168/168A
avrdude -p atmega168 -c usbasp -v -B 4 -U lfuse:w:0xed:m -U hfuse:w:0xdd:m -U efuse:w:0xf9:m
