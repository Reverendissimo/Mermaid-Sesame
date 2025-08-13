# PN7150 MicroPython Library Reference - Complete Function Documentation

## Overview
This document provides comprehensive reference for the professional PN7150 MicroPython library, including all functions, HCE (Host Card Emulation) support, APDU communication, and critical implementation details.

## Library Initialization

### `Electroniccats_PN7150.__init__(IRQpin, VENpin, I2Caddress, wire=None)`
**Purpose:** Initialize PN7150 instance with pin configuration
**Parameters:**
- `IRQpin`: GPIO pin for interrupt (MUST be GPIO15 for working configuration)
- `VENpin`: GPIO pin for enable (MUST be GPIO14 for working configuration)  
- `I2Caddress`: I2C address (0x28)
- `wire`: I2C instance (optional)

**Critical Notes:**
- **Pin configuration is CRITICAL:** Must use GPIO15/14, not GPIO32/27
- IRQ pin is ACTIVE HIGH (PN7150 drives it HIGH when data available)
- No external pull-up resistors needed for IRQ pin

**Initialization Sequence:**
1. Create Pin objects for IRQ (INPUT) and VEN (OUTPUT)
2. Initialize message handling variables (rxBuffer, rxMessageLength, etc.)
3. Initialize controller info variables (gNfcController_generation, gNfcController_fw_version)

---

## Core Communication Functions

### `begin()`
**Purpose:** Initialize hardware and perform power-up sequence
**Returns:** SUCCESS (0) or ERROR (1)

**Operation Sequence:**
1. Initialize I2C if not provided (SCL=22, SDA=21, 100kHz)
2. Power-up sequence for VEN pin:
   - Set VEN HIGH
   - Wait 1ms
   - Set VEN LOW  
   - Wait 1ms
   - Set VEN HIGH
   - Wait 3ms

**Timing:** ~5ms total for power-up sequence

### `hasMessage()`
**Purpose:** Check if PN7150 has data to send
**Returns:** True if IRQ pin is HIGH, False otherwise

**Critical Implementation:**
```python
return self.irq.value() == 1  # ACTIVE HIGH - PN7150 drives IRQ HIGH
```

**Timing:** Immediate read of GPIO pin

### `writeData(txBuffer, txBufferLevel)`
**Purpose:** Send data to PN7150 via I2C
**Parameters:**
- `txBuffer`: Data to send
- `txBufferLevel`: Number of bytes to send

**Returns:** 0 (SUCCESS) or 4 (ERROR)

**Operation Sequence:**
1. Write data to I2C address 0x28
2. Handle any I2C communication errors

**Timing:** Depends on data length, typically 1-5ms

### `readData(rxBuffer)`
**Purpose:** Read data from PN7150 via I2C
**Parameters:**
- `rxBuffer`: Buffer to store received data

**Returns:** Number of bytes received

**Operation Sequence:**
1. Check if IRQ pin is HIGH (hasMessage())
2. If HIGH, read 3-byte header first
3. Extract payload length from header[2]
4. If payload > 0, read payload bytes
5. Combine header + payload into rxBuffer

**Critical Notes:**
- Only reads if IRQ pin is HIGH
- Reads header first, then payload based on length field
- Header format: [MessageType, GID/OID, PayloadLength]

**Timing:** 
- Header read: ~1ms
- Payload read: ~1-10ms depending on length

### `getMessage(timeout=5)`
**Purpose:** Wait for and read complete message from PN7150
**Parameters:**
- `timeout`: Timeout in milliseconds

**Returns:** Number of bytes received

**Operation Sequence:**
1. Set timeout timer
2. Loop until timeout or message received:
   - Call readData() to check for message
   - If message received, break
   - If timeout=1337, reset timer (special case)
3. Return message length

**Timing:** 
- Immediate if message available
- Up to timeout milliseconds if waiting

---

## NCI Protocol Functions

### `wakeupNCI()`
**Purpose:** Wake up PN7150 and establish NCI communication
**Returns:** SUCCESS (0) or ERROR (1)

**Operation Sequence:**
1. Send CORE_RESET_CMD: `[0x20, 0x00, 0x01, 0x01]`
2. Wait for response (15ms timeout)
3. Check response: `[0x40, 0x00, ...]` (CORE_RESET_RSP)
4. Read any additional messages (CORE_GENERIC_ERROR_NTF)
5. Return SUCCESS if reset successful

**Critical Response Checks:**
- First response must be `0x40, 0x00` (CORE_RESET_RSP)
- Additional messages may indicate anti-tearing recovery

**Timing:** ~20-50ms total

### `connectNCI()`
**Purpose:** Establish full NCI connection and get controller info
**Returns:** SUCCESS (0) or ERROR (1)

**Operation Sequence:**
1. Call `begin()` for hardware initialization
2. Loop up to 2 times calling `wakeupNCI()`
3. Send CORE_INIT_CMD: `[0x20, 0x01, 0x00]`
4. Wait for CORE_INIT_RSP: `[0x40, 0x01, ...]`
5. Extract controller generation and firmware version
6. Store controller info in instance variables

**Critical Response Checks:**
- CORE_INIT_RSP must be `0x40, 0x01`
- Check response[3] for status (0x00 = success)

**Timing:** ~100-200ms total (including retries)

---

## Configuration Functions

### `ConfigureSettings(uidcf=None, uidlen=0)`
**Purpose:** Apply all NXP-specific configuration settings
**Returns:** False (SUCCESS) or True (ERROR)

**Operation Sequence:**
1. **CORE Configuration:**
   - Send: `[0x20, 0x02, 0x05, 0x01, 0x00, 0x02, 0x00, 0x01]`
   - Expect: `[0x40, 0x02, 0x02, 0x00, 0x00]`

2. **CORE Extension Configuration:**
   - Send: `[0x20, 0x02, 0x0D, 0x03, 0xA0, 0x40, 0x01, 0x00, 0xA0, 0x41, 0x01, 0x04, 0xA0, 0x43, 0x01, 0x00]`
   - Expect: `[0x40, 0x02, 0x02, 0x00, 0x00]`

3. **CORE Standby Configuration:**
   - Send: `[0x2F, 0x00, 0x01, 0x01]`
   - Expect: `[0x4F, 0x00, 0x01, 0x00]`

4. **Clock Configuration:**
   - Send: `[0x20, 0x02, 0x05, 0x01, 0xA0, 0x03, 0x01, 0x08]`
   - Expect: `[0x40, 0x02, 0x02, 0x00, 0x00]`

5. **TVDD Configuration (2nd Gen):**
   - Send: `[0x20, 0x02, 0x07, 0x01, 0xA0, 0x0E, 0x03, 0x06, 0x64, 0x00]`
   - Expect: `[0x40, 0x02, 0x02, 0x00, 0x00]`

6. **RF Configuration (2nd Gen):**
   - Send: Large RF configuration array (148 bytes)
   - Expect: `[0x40, 0x02, 0x02, 0x00, 0x00]`

**Critical Notes:**
- Each step must succeed before proceeding
- Response format: `[0x40, 0x02, 0x02, 0x00, 0x00]` indicates success
- CORE_STANDBY response is different: `[0x4F, 0x00, 0x01, 0x00]`

**Timing:** ~500-1000ms total (RF config is slowest)

### `ConfigMode(modeSE)`
**Purpose:** Configure discovery map for specific mode
**Parameters:**
- `modeSE`: 1=Reader/Writer, 2=Card Emulation, 3=P2P

**Returns:** SUCCESS (0) or ERROR (1)

**Operation Sequence:**
1. Map modeSE to internal mode flags
2. If Reader/Writer mode, enable proprietary interface
3. Build discovery map command based on mode
4. Send RF_DISCOVER_MAP_CMD
5. Wait for RF_DISCOVER_MAP_RSP: `[0x41, 0x00, 0x01, 0x05, 0xFF]`

**Discovery Map for Reader/Writer Mode:**
```
[0x21, 0x00, 0x10, 0x05, 
 0x01, 0x01, 0x01, 0x02, 0x01, 0x01, 0x03, 0x01, 0x01, 0x04, 0x01, 0x02, 0x80, 0x01, 0x80]
```

**Timing:** ~10-20ms

### `StartDiscovery(modeSE)`
**Purpose:** Start RF discovery process
**Parameters:**
- `modeSE`: 1=Reader/Writer, 2=Card Emulation, 3=P2P

**Returns:** SUCCESS (0) or ERROR (1)

**Operation Sequence:**
1. Select discovery technologies based on mode
2. Build RF_DISCOVER_CMD with technology list
3. Send command to PN7150
4. Wait for RF_DISCOVER_RSP: `[0x41, 0x03, 0x01, 0x06, 0xFF]`

**Discovery Technologies for Reader/Writer:**
- `[0x00, 0x02, 0x05, 0x06]` (NFC-A, NFC-B, NFC-F, ISO15693)

**Timing:** ~10-20ms

---

## Card Detection Functions

### `WaitForDiscoveryNotification(pRfIntf, tout=0)`
**Purpose:** Wait for card detection notification
**Parameters:**
- `pRfIntf`: RfIntf_t structure to fill with card info
- `tout`: Timeout in milliseconds (0 = infinite)

**Returns:** True if card detected, False if timeout

**Operation Sequence:**
1. Wait for RF notification (0x61 group)
2. Check for RF_DISCOVER_NTF (0x61, 0x03) or RF_INTF_ACTIVATED_NTF (0x61, 0x05)
3. Fill RfIntf_t structure with card information
4. If RF_DISCOVER_NTF, handle card selection process
5. Return True if card successfully detected and activated

**Critical Response Types:**
- `RF_DISCOVER_NTF`: `[0x61, 0x03, ...]` - Card discovered, needs selection
- `RF_INTF_ACTIVATED_NTF`: `[0x61, 0x05, ...]` - Card already activated

**Supported Card Types:**
- **MIFARE Classic:** Protocol 0x80, 4-byte UID
- **NTAG:** Protocol 0x02 (ISO-DEP), 7-byte UID
- **Android HCE:** Protocol 0x04 (ISO-DEP), dynamic UID
- **Other NFC-A:** Any card using TECH_PASSIVE_NFCA

**Card Selection Process (if needed):**
1. Send RF_DISCOVER_SELECT_CMD
2. Wait for RF_DISCOVER_SELECT_RSP
3. Handle multiple cards if present

**Timing:** 
- Immediate if card present
- Up to timeout if waiting for card

---

## HCE and APDU Communication Functions

### `SendApduCommand(apdu_cmd)`
**Purpose:** Send APDU command to activated tag using DATA_PACKET format
**Parameters:**
- `apdu_cmd`: APDU command bytearray (e.g., SELECT AID command)

**Returns:** Response bytearray or None if failed

**Operation Sequence:**
1. **Format DATA_PACKET:** `[0x00, 0x00, CommandSize, CommandData]`
2. **Send DATA_PACKET** via `writeData()`
3. **Get immediate response** via `getMessage()` (acknowledgment)
4. **Get data response** via `getMessage(1000)` (actual APDU response)
5. **Parse response** and extract payload

**Critical Implementation Details:**
- Uses **DATA_PACKET format** for ISO-DEP communication
- **Dual getMessage() calls** - exact like official ElectronicCats library
- **Immediate response** (acknowledgment) followed by **data response**
- **Response format:** `[0x00, 0x00, PayloadLength, PayloadData]`

**Example SELECT AID Command:**
```python
# SELECT AID: CLA=00, INS=A4, P1=04, P2=00, Lc=07, AID=F1726576406873
select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, 0x07, 0xF1, 0x72, 0x65, 0x76, 0x40, 0x68, 0x73])
response = nfc.SendApduCommand(select_cmd)
```

**Expected Response Format:**
- **Success:** `[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x90, 0x00]`
- **Status:** Last 2 bytes are status words (0x90 0x00 = success)
- **Data:** All bytes except last 2 are response data

**Timing:** ~50-100ms total (including both message reads)

### `FillInterfaceInfo(pRfIntf, pBuf)`
**Purpose:** Fill RfIntf_t structure with detailed card information
**Parameters:**
- `pRfIntf`: RfIntf_t structure to fill
- `pBuf`: Raw card information buffer

**Operation Sequence:**
1. Check card protocol (T1T, T2T, etc.)
2. Extract SENS_RES, NFCID, SEL_RES based on protocol
3. Store information in appropriate structure fields

**Supported Protocols:**
- **T1T (Topaz):** SENS_RES, NFCID
- **T2T (MIFARE):** SENS_RES, NFCID, SEL_RES

---

## Utility Functions

### `print_hex_array(data, length)`
**Purpose:** Convert byte array to formatted hex string
**Parameters:**
- `data`: Byte array to format
- `length`: Number of bytes to format

**Returns:** Formatted hex string (e.g., "0x01 0x02 0x03")

**Example:**
```python
result = nfc.print_hex_array([0x01, 0x02, 0x03], 3)
# Returns: "0x01 0x02 0x03"
```

### `StopDiscovery()`
**Purpose:** Stop current discovery process
**Returns:** True

**Operation Sequence:**
1. Send RF_DEACTIVATE_CMD: `[0x21, 0x06, 0x01, 0x00]`
2. Read immediate response via `getMessage()`
3. Read completion response via `getMessage(1000)`

**Timing:** ~10-20ms

---

## UID Extraction Functions

### `extract_correct_uid(response, length)` (Helper function)
**Purpose:** Extract UID from NCI response for different card types
**Parameters:**
- `response`: Raw NCI response buffer
- `length`: Length of response buffer

**Returns:** UID bytearray or None if extraction fails

**Operation Sequence:**
1. Check response length (minimum 17 bytes)
2. Analyze response structure to identify card type
3. Extract UID based on card type pattern

**Card Type Patterns:**
- **MIFARE Pattern:** `[0x04, 0x00, 0x04]` at positions 11-13, UID at position 14 (4 bytes)
- **NTAG Pattern:** `[0x07, 0x04]` at positions 12-13, UID at position 13 (7 bytes)
- **Android HCE:** Dynamic UID generation, varies per read

**Example Responses:**
- **MIFARE:** `[0x61, 0x05, 0x14, ..., 0x04, 0x00, 0x04, 0x93, 0x5C, 0xE2, 0x26, ...]`
- **NTAG:** `[0x61, 0x05, 0x17, ..., 0x07, 0x04, 0x04, 0x89, 0xB7, 0xAA, 0x28, 0x63, 0x80, ...]`
- **Android HCE:** `[0x61, 0x05, 0x19, ..., 0x08, 0x9A, 0xF7, 0xCB, ...]`

**Timing:** Immediate

---

## Data Structures

### `RfIntf_t`
**Purpose:** Store card interface information
**Structure:**
```python
class RfIntf_t:
    Interface: int      # Interface type (0x80 for TAGCMD, 0x02 for ISODEP)
    Protocol: int       # Protocol (0x80 for MIFARE, 0x04 for HCE)
    ModeTech: int       # Mode and technology (0x00 for NFC-A)
    MoreTags: bool      # Multiple cards present
    Info: RfIntf_Info_t # Detailed card information
```

### `RfIntf_Info_t`
**Purpose:** Store detailed card information
**Structure:**
```python
class RfIntf_Info_t:
    NFC_APP: RfIntf_info_APP_t  # NFC-A card info
    NFC_BPP: RfIntf_info_BPP_t  # NFC-B card info  
    NFC_FPP: RfIntf_info_FPP_t  # NFC-F card info
    NFC_VPP: RfIntf_info_VPP_t  # ISO15693 card info
```

---

## Critical Timing Summary

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| Power-up sequence | 5ms | VEN pin cycling |
| NCI connection | 100-200ms | Including retries |
| Configuration | 500-1000ms | RF config is slowest |
| Discovery start | 10-20ms | Quick operation |
| Card detection | Immediate-5s | Depends on card presence |
| APDU communication | 50-100ms | Dual getMessage() calls |
| Card reset | 20-40ms | Stop + restart discovery |

## Error Handling

**Common Error Responses:**
- `[0x40, 0x02, 0x02, 0x05, 0x00]` - Configuration rejected
- `[0x60, 0x07, ...]` - CORE_GENERIC_ERROR_NTF
- `[0x41, 0x03, 0x01, 0x06, 0x00]` - Discovery failed
- `[0x60, 0x06, 0x03, 0x01, 0x00, 0x01]` - Interface not activated
- `[0x60, 0x08, 0x02, 0x05, 0x00]` - AID not found

**APDU Status Words:**
- `0x90 0x00` - Success
- `0x6A 0x82` - File not found
- `0x6A 0x86` - Incorrect P1P2
- `0x6A 0x87` - Lc inconsistent with P1P2

**Timeout Values:**
- NCI operations: 15-1000ms
- Card detection: 0-5000ms (0 = infinite)
- APDU operations: 1000ms
- I2C operations: 1-5ms

## Usage Patterns

### Basic Card Reading:
```python
# Initialize
nfc = Electroniccats_PN7150(IRQpin=15, VENpin=14, I2Caddress=0x28, wire=i2c)

# Connect and configure
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

# Wait for card
RfInterface = RfIntf_t()
if nfc.WaitForDiscoveryNotification(RfInterface):
    uid = extract_correct_uid(nfc.rxBuffer, nfc.rxMessageLength)
    if uid:
        uid_str = ":".join([f"{b:02X}" for b in uid])
        print(f"CARD UID: {uid_str}")
```

### HCE Communication:
```python
# After card detection, send APDU commands
if RfInterface.Protocol == 0x04:  # Android HCE
    # SELECT AID command
    select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, 0x07, 0xF1, 0x72, 0x65, 0x76, 0x40, 0x68, 0x73])
    response = nfc.SendApduCommand(select_cmd)
    
    if response:
        # Check status words (last 2 bytes)
        status = response[-2:]
        if status == bytearray([0x90, 0x00]):
            data = response[:-2]  # Remove status words
            print(f"HCE Response: {nfc.print_hex_array(data, len(data))}")
```

### Continuous Reading Pattern:
```python
while True:
    if nfc.WaitForDiscoveryNotification(RfInterface):
        uid = extract_correct_uid(nfc.rxBuffer, nfc.rxMessageLength)
        if uid:
            uid_str = ":".join([f"{b:02X}" for b in uid])
            print(f"CARD UID: {uid_str}")
            
            # Handle different card types
            if RfInterface.Protocol == 0x04:  # Android HCE
                # Send APDU commands for HCE communication
                pass
            elif RfInterface.Protocol == 0x80:  # MIFARE
                # Handle MIFARE cards
                pass
        
        # Reset for next card
        nfc.StopDiscovery()
        nfc.StartDiscovery(mode)
```

## Supported Card Types

| Card Type | Protocol | UID Length | Interface | Notes |
|-----------|----------|------------|-----------|-------|
| MIFARE Classic | 0x80 | 4 bytes | TAGCMD | Standard MIFARE cards |
| NTAG | 0x02 | 7 bytes | ISODEP | NTAG213/215/216 |
| Android HCE | 0x04 | Dynamic | ISODEP | Host Card Emulation |
| Other NFC-A | 0x02 | Variable | ISODEP | Any NFC-A card |

## HCE Communication Details

### APDU Command Format:
- **SELECT AID:** `[0x00, 0xA4, 0x04, 0x00, Lc, AID...]`
- **READ BINARY:** `[0x00, 0xB0, 0x00, 0x00, Le]`
- **UPDATE BINARY:** `[0x00, 0xD6, 0x00, 0x00, Lc, Data...]`

### Response Format:
- **Success:** `[Data..., 0x90, 0x00]`
- **Error:** `[0x6A, 0x82]` (File not found)

### Common AIDs:
- **Mermaid Sesame:** `F1726576406873`
- **Google Pay:** `325041592E5359532E4444463031`
- **Android Digital Car Key:** `A000000809434343444B467631`

This reference provides complete documentation for working with the professional PN7150 MicroPython library, including all HCE and APDU communication features. 