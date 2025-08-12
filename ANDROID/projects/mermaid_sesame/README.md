# Mermaid Sesame - Android HCE App

## Overview
Mermaid Sesame is an Android Host-Based Card Emulation (HCE) application designed to work with the ESP32 PN7150 NFC reader. The app emulates an NFC card that responds to specific AID requests with configurable 6-byte responses.

## Features

### Core Functionality
- **AID:** `F1726576406873` (7-byte Application Identifier)
- **Category:** OTHER (non-payment to avoid Google Pay conflicts)
- **Response:** Configurable 6-byte hex data
- **Theme:** Dark UI with neon cyan, purple, and yellow accents

### User Interface
- **Dark Theme:** Professional dark background (#0A0A0A)
- **Neon Accents:** 
  - Cyan (#00FFFF) for titles and highlights
  - Purple (#FF00FF) for buttons and accents
  - Yellow (#FFFF00) for data and warnings
  - Green (#00FF00) for success messages
- **Monospace Font:** Technical appearance for all text elements

### Configuration
- **Response Data Field:** Text input for 6-byte hex response (12 characters)
- **Save Button:** Persists configuration to device storage
- **Validation:** Ensures proper hex format and exact 6-byte length
- **Default Response:** `010203040506` (configurable)

### Logging System
- **Real-time Logs:** Comprehensive activity logging with timestamps
- **Auto-scroll:** Automatically scrolls to show latest entries
- **Clear Function:** Button to clear all logs
- **Categories:** NFC status, permissions, HCE events, configuration changes

## Technical Details

### HCE Service
- **Service Class:** `MermaidSesameService` extends `HostApduService`
- **AID Selection:** Responds to SELECT APDU for `F1726576406873`
- **APDU Processing:** Handles standard ISO 7816-4 APDU commands
- **Response Format:** 6-byte data + SW (0x9000 for success)

### Permissions
- `android.permission.NFC` - Required for NFC functionality
- `android.hardware.nfc` - Device must have NFC hardware
- `android.hardware.nfc.hce` - Device must support HCE

### Data Persistence
- **SharedPreferences:** Stores response data configuration
- **Key:** `MermaidSesamePrefs.response_data`
- **Format:** 12-character hex string (6 bytes)

## ESP32 Integration

### Reader Requirements
- ESP32 with PN7150 NFC controller
- Must send SELECT APDU for AID `F1726576406873`
- Should handle 6-byte response + status words

### Expected Communication Flow
1. ESP32 sends: `00 A4 04 00 07 F1726576406873`
2. App responds: `[6-byte-data] 90 00`

### Testing
- Place phone near ESP32 reader
- App will automatically respond to AID selection
- Logs show all APDU exchanges in real-time

## Build Information

### Requirements
- Android SDK 33 (API 33)
- Minimum SDK: 21 (Android 5.0)
- Target SDK: 31 (Android 12)
- Gradle 8.5

### Dependencies
- AndroidX AppCompat 1.6.1
- Material Design 1.9.0
- ConstraintLayout 2.1.4

### Build Commands
```bash
# Build debug APK
gradle assembleDebug

# Build release APK
gradle assembleRelease

# Install on connected device
gradle installDebug
```

## File Structure
```
app/src/main/
├── java/com/example/mermaidsesame/
│   ├── MainActivity.java          # Main UI and configuration
│   └── MermaidSesameService.java  # HCE service implementation
├── res/
│   ├── layout/
│   │   └── activity_main.xml      # Dark theme UI layout
│   ├── values/
│   │   ├── colors.xml             # Neon color definitions
│   │   ├── strings.xml            # App strings
│   │   └── styles.xml             # Dark theme styles
│   └── xml/
│       └── aid_list.xml           # HCE AID configuration
└── AndroidManifest.xml            # App permissions and services
```

## Usage Instructions

1. **Install:** Build and install the APK on Android device
2. **Configure:** Enter desired 6-byte response in hex format
3. **Save:** Tap "SAVE RESPONSE DATA" to persist configuration
4. **Test:** Place phone near ESP32 reader
5. **Monitor:** Watch real-time logs for NFC activity

## Security Notes
- Uses OTHER category to avoid payment system conflicts
- No sensitive data stored or transmitted
- AID is custom and non-standard
- Response data is user-configurable

## Troubleshooting

### Common Issues
- **NFC Disabled:** Enable NFC in device settings
- **Invalid Hex:** Ensure exactly 12 hex characters (0-9, A-F)
- **No Response:** Check ESP32 is sending correct AID
- **Permission Denied:** Grant NFC permission when prompted

### Debug Information
- All APDU exchanges are logged with timestamps
- NFC status and permission states are displayed
- Configuration changes are tracked
- Service activation/deactivation events logged 