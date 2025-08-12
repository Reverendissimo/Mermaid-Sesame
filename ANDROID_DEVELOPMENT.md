# Android Development Environment

This project includes a self-contained Android development environment for building NFC/HCE apps.

## Quick Start

### 1. Set up the environment
```bash
source setup_android_env.sh
```

### 2. Build and install the Mermaid Sesame app
```bash
./build_mermaid_sesame.sh
```

## Scripts

### `setup_android_env.sh`
Sets up the Android development environment:
- Sets `ANDROID_HOME` and `ANDROID_SDK_ROOT` to the local Android SDK
- Adds Android tools to `PATH`
- Verifies that all required tools are available
- Provides helpful commands and instructions

### `build_mermaid_sesame.sh`
Builds and installs the Mermaid Sesame HCE app:
- Sources the Android environment
- Builds the debug APK
- Installs it on the connected device
- Provides feedback on success/failure

## Manual Commands

If you prefer to run commands manually:

```bash
# Set up environment
source setup_android_env.sh

# Build the app
cd ANDROID/projects/mermaid_sesame
gradle assembleDebug

# Install on device
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## What the Mermaid Sesame App Does

The updated Mermaid Sesame app now:

1. **Auto-starts HCE service** when the app launches
2. **Requests all required permissions** (NFC, Internet, Network State, etc.)
3. **Registers AID `F1726576406873`** for HCE routing
4. **Responds to SELECT AID commands** from the ESP32 reader
5. **Provides configurable response data** (default: `010203040506`)

## Troubleshooting

### "Android SDK not found"
Run the full Android environment setup:
```bash
cd ANDROID && source setup_environment.sh
```

### "No Android device connected"
Connect your device via USB and enable USB debugging, then run:
```bash
adb devices
```

### "Permission denied"
The app will request permissions on first launch. Grant all requested permissions.

## Environment Variables

The scripts set these environment variables:
- `ANDROID_HOME=/home/rev/ESP-32-AGAIN/ANDROID/android-sdk`
- `ANDROID_SDK_ROOT=$ANDROID_HOME`
- `GRADLE_HOME=/opt/gradle`
- `PATH` includes Android tools and Gradle

## Remember!

Always run `source setup_android_env.sh` before building Android apps in this project! 