# doorman2: electric boogaloo

- `esp32/` contains the micropython source which talks w/ NFC module and keypad over UART (two channels)
- `keypad/` has some magical Arduino code (sorry)

## scanning new cards

connect USB cable, use `mpremote` or any serial termnal to listen to logs, read card hash from logs

example:

```
$ mpremote 
Connected to MicroPython at /dev/ttyUSB1
Use Ctrl-] or Ctrl-x to exit this shell
PN532: No response from PN532!
PN532: No response from PN532!
PN532: No response from PN532!
Card UUID: 403dcb1e
Card hash: dfe9bedbf230cf67dfa65249a7517af81175496642724a18ac728ecac7c90862
Unknown hash, ignoring
PN532: No response from PN532!
PN532: No response from PN532!
$
```

## scanning new cards with a phone app

get a phone with nfc and the "nfc tools" app installed, scan card, look for "serial number", get first four bytes of that, use following code:

```
# assumes card serial number 0x13121337 and pin 2137
import hashlib
def generate_hash(card_uid, pin):
    card_uid = bytes(reversed(card_uid[:4])).hex()
    s = "{:08x}:{}".format(int(pin), card_uid)
    hash=hashlib.sha256(s.encode('ascii')).digest().hex()
    return hash

generate_hash([0x13,0x12,0x13,0x37],bytearray(source=[ord('2'),ord('1'),ord('3'),ord('7')]))
```

## syncing data from LDAP

big TODO; currently, you need to:
1. use the `tools/get_hashes` python script to pull card hashes from LDAP (requires python-ldap)
2. put the output in a `hashes` file
3. `mpremote fs cp hashes :hashes`

plans: web UI like vuko's design

## esp <-> keypad protocol definition

- one byte per command, no delimeters, keypad is supposed to be as stateless as possible
- the keypad can only send numbers and the hash symbol
- ESP can send the following commands:
	- `H` ("happy" noise, success; turns on the green LED for a second and turns it back off)
	- `S` ("sad" failure noise; likewise with the red LED)
	- `F` ("flush"; turns off LEDs and tries to bring the env to a sane level)
	- `G`, `R` ("green", "red"; turns on the specific LEDs)
	- `Q` ("quiet"; turns on audible keypresses)


---

i am so sorry
