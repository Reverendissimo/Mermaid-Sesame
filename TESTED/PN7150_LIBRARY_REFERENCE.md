# PN7150 Library Reference - Detailed Function Documentation

## Overview
This document provides detailed reference for each function in the working PN7150 library, including operation sequences, timing, and critical implementation details.

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
3. Initialize controller info variables

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
- **Other NFC-A:** Any card using TECH_PASSIVE_NFCA

**Card Selection Process (if needed):**
1. Send RF_DISCOVER_SELECT_CMD
2. Wait for RF_DISCOVER_SELECT_RSP
3. Handle multiple cards if present

**Timing:** 
- Immediate if card present
- Up to timeout if waiting for card

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

**Example Responses:**
- **MIFARE:** `[0x61, 0x05, 0x14, ..., 0x04, 0x00, 0x04, 0x93, 0x5C, 0xE2, 0x26, ...]`
- **NTAG:** `[0x61, 0x05, 0x17, ..., 0x07, 0x04, 0x04, 0x89, 0xB7, 0xAA, 0x28, 0x63, 0x80, ...]`

**Timing:** Immediate

## Reset Functions

### `stop_discovery(nfc)` (Helper function)
**Purpose:** Stop current discovery process
**Operation Sequence:**
1. Send RF_DEACTIVATE_CMD: `[0x21, 0x06, 0x01, 0x00]`
2. Read response messages
3. Wait for completion

**Timing:** ~10-20ms

### `reset_mode(nfc, mode)` (Helper function)
**Purpose:** Reset mode configuration
**Operation Sequence:**
1. Call `ConfigMode(mode)`
2. Call `StartDiscovery(mode)`

**Timing:** ~20-40ms

---

## Data Structures

### `RfIntf_t`
**Purpose:** Store card interface information
**Structure:**
```python
class RfIntf_t:
    Interface: int      # Interface type (0x80 for TAGCMD)
    Protocol: int       # Protocol (0x80 for MIFARE)
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
| Card reset | 20-40ms | Stop + restart discovery |

## Error Handling

**Common Error Responses:**
- `[0x40, 0x02, 0x02, 0x05, 0x00]` - Configuration rejected
- `[0x60, 0x07, ...]` - CORE_GENERIC_ERROR_NTF
- `[0x41, 0x03, 0x01, 0x06, 0x00]` - Discovery failed

**Timeout Values:**
- NCI operations: 15-1000ms
- Card detection: 0-5000ms (0 = infinite)
- I2C operations: 1-5ms

## Usage Pattern

**Typical Usage Sequence:**
1. Initialize: `nfc = Electroniccats_PN7150(15, 14, 0x28)`
2. Connect: `nfc.connectNCI()`
3. Configure: `nfc.ConfigureSettings()`
4. Set mode: `nfc.ConfigMode(1)`
5. Start discovery: `nfc.StartDiscovery(1)`
6. Wait for cards: `nfc.WaitForDiscoveryNotification(RfInterface)`
7. Extract UID: `extract_correct_uid(nfc.rxBuffer, nfc.rxMessageLength)`
8. Process card data based on protocol (0x80=MIFARE, 0x02=NTAG)
9. Reset for next card: `stop_discovery()` → `StartDiscovery()` → `reset_mode()`

**Multi-Card Support:**
- **MIFARE Classic:** 4-byte UID, Protocol 0x80
- **NTAG:** 7-byte UID, Protocol 0x02 (ISO-DEP)
- **Universal:** Works with any NFC-A card type

**Continuous Reading Pattern:**
```python
while True:
    if nfc.WaitForDiscoveryNotification(RfInterface):
        uid = extract_correct_uid(nfc.rxBuffer, nfc.rxMessageLength)
        if uid:
            uid_str = ":".join([f"{b:02X}" for b in uid])
            print(f"CARD UID: {uid_str}")
        
        # Reset for next card
        stop_discovery(nfc)
        nfc.StartDiscovery(mode)
        reset_mode(nfc, mode)
```

This reference should provide complete documentation for working with the PN7150 library. 