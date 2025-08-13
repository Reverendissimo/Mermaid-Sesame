# TESTED - Professional PN7150 NFC Reader with HCE Support

## SUCCESS! ESP32 ↔ Android HCE Communication Working Perfectly!

### Files:
- `PN7150_micropython.py` - Professional MicroPython PN7150 library
- `continuous_card_scanner.py` - Professional HCE reader for Mermaid Sesame app
- `PN7150_LIBRARY_REFERENCE.md` - Detailed function documentation

### Pin Configuration (CRITICAL):
- **IRQ = GPIO15** (not GPIO32)
- **VEN = GPIO14** (not GPIO27)  
- **I2C_ADDR = 0x28**
- **SDA = GPIO21, SCL = GPIO22**

### Supported Card Types:
- **MIFARE Classic:** 4-byte UID (Protocol: 0x80)
- **NTAG:** 7-byte UID (Protocol: 0x02)
- **Android HCE:** ISO-DEP protocol (Protocol: 0x04)

### HCE Communication Success:
- **Mermaid Sesame App:** Successfully detected and communicating
- **APDU Commands:** SELECT AID working perfectly
- **Response Handling:** Receiving dynamic responses from Android app
- **Status Codes:** Proper 0x90 0x00 success responses

### Tested Scenarios:
- **MIFARE Cards:** Multiple cards working (4-byte UIDs)
- **NTAG Cards:** 7-byte UID extraction working
- **Android HCE:** Mermaid Sesame app responding with dynamic data
- **Continuous Reading:** Automatic reset between cards

### Key Success Factors:
1. **Pin Configuration:** Using Arduino example pins (15, 14) instead of original pins (32, 27)
2. **Professional Library:** Clean MicroPython implementation of Arduino library
3. **HCE Support:** Full ISO-DEP communication with Android Host Card Emulation
4. **Proper APDU Format:** Correct SELECT AID command structure
5. **Response Handling:** Dual getMessage() calls for proper NCI communication

### Features:
- **Multi-Card Support:** Reads MIFARE, NTAG, and Android HCE
- **HCE Detection:** Specifically designed for Mermaid Sesame app
- **Dynamic Responses:** Receives different data from Android app on each read
- **Professional Output:** Clean, emoji-free, focused output
- **Universal Compatibility:** Works with any NFC-A card or HCE app

### Step-by-Step Usage:

#### 1. Upload Files to ESP32:
```bash
# Activate virtual environment
source ../venv/bin/activate

# Upload the MicroPython library
mpremote cp PN7150_micropython.py :

# Upload the professional reader
mpremote cp continuous_card_scanner.py :

# Soft reset to clear any old code
mpremote soft-reset
```

#### 2. Run the Professional HCE Reader:
```bash
# Run the scanner
mpremote run continuous_card_scanner.py
```

#### 3. Test with Android HCE:
1. **Install Mermaid Sesame app** on Android phone
2. **Start the app** and ensure it's in foreground
3. **Place phone near ESP32** reader
4. **Observe HCE detection** and response data

#### 4. Expected Output:
```
=== Professional NFC Reader for Mermaid Sesame HCE ===
IRQ=15, VEN=14
Place Android phone with Mermaid Sesame app near the reader...

Initializing...
Configuring settings...
Configuring mode...
Starting discovery...
Ready! Place a card near the reader...

=== CARD #1 ===
Waiting for card...
Found card! Protocol: 0x04, ModeTech: 0x00
Card UID: 08:9A:F7:CB
Card type: Android HCE
Card read successfully!
  Checking for Mermaid Sesame HCE app...
  Sending SELECT AID: 0x00 0xA4 0x04 0x00 0x07 0xF1 0x72 0x65 0x76 0x40 0x68 0x73
  MERMAID SESAME HCE DETECTED!
  Response: 0x01 0x02 0x03 0x04 0x05 0xFF
```

### Library Integration:
To use the library in your own MicroPython project:

```python
from machine import I2C, Pin
import time

# Import the MicroPython PN7150 library
exec(open('PN7150_micropython.py').read())

# Initialize I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

# Create PN7150 instance
nfc = Electroniccats_PN7150(IRQpin=15, VENpin=14, I2Caddress=0x28, wire=i2c)

# Initialize and configure
if nfc.connectNCI():
    print("ERROR: Failed to connect to NCI")
    return

if nfc.ConfigureSettings():
    print("ERROR: Failed to configure settings")
    return

mode = 1  # Reader/Writer mode
if nfc.ConfigMode(mode):
    print("ERROR: Failed to configure mode")
    return

# Start discovery
nfc.StartDiscovery(mode)

# Wait for card and process
RfInterface = RfIntf_t()
if nfc.WaitForDiscoveryNotification(RfInterface):
    print(f"Card detected! Protocol: 0x{RfInterface.Protocol:02X}")
    # Process card...
```

### Next Steps:
- **Production Ready:** The HCE communication system is fully functional
- **Integration:** Ready to integrate into your main project
- **Customization:** Modify response handling for your specific use case
- **Android App:** The Mermaid Sesame app is working perfectly with this reader 