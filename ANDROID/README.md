# Android Development Environment

A self-contained Android 12 development environment for building NFC applications.

## Directory Structure

```
ANDROID/
├── android-sdk/          # Android SDK installation
├── android-studio/       # Android Studio (if needed)
├── gradle/              # Gradle installation
├── projects/            # Android projects
│   └── template/        # Project template with NFC support
├── tools/               # Downloaded tools
├── setup_environment.sh # Environment setup script
├── build.sh            # Project build script
├── create_project.sh   # New project creation script
└── .env                # Environment variables
```

## Quick Start

### 1. Setup Environment
```bash
# Make setup script executable and run it
chmod +x setup_environment.sh
./setup_environment.sh
```

### 2. Activate Environment
```bash
source .env
```

### 3. Create New Project
```bash
./create_project.sh my_nfc_app
```

### 4. Build Project
```bash
./build.sh my_nfc_app
```

## Features

### Self-Contained Environment
- **Android SDK:** API 31 (Android 12)
- **Build Tools:** Version 33.0.0
- **Gradle:** Version 8.0
- **Command Line Tools:** Latest version

### NFC-Ready Template
- **NFC Permissions:** Already configured
- **NFC Detection:** Basic card reading functionality
- **Host-Based Card Emulation:** Ready for HCE development
- **AndroidX Support:** Modern Android libraries

### Project Management
- **Template System:** Quick project creation
- **Build Automation:** One-command builds
- **Package Management:** Automatic package name updates

## Supported Android Features

### NFC Capabilities
- **Card Reading:** Detect NFC tags and cards
- **Host-Based Card Emulation:** Emulate NFC cards
- **NDEF Reading/Writing:** NFC Data Exchange Format
- **ISO-DEP Support:** ISO14443-4 protocol

### Android 12 Features
- **Target SDK:** 31 (Android 12)
- **Minimum SDK:** 21 (Android 5.0)
- **Modern APIs:** AndroidX, Material Design
- **Security:** Runtime permissions

## Development Workflow

### 1. Environment Setup
```bash
# First time only
./setup_environment.sh
source .env
```

### 2. Project Creation
```bash
# Create new NFC project
./create_project.sh my_nfc_project
```

### 3. Development
```bash
# Edit source files in projects/my_nfc_project/
# Main activity: app/src/main/java/com/example/my_nfc_project/MainActivity.java
# Layout: app/src/main/res/layout/activity_main.xml
# Manifest: app/src/main/AndroidManifest.xml
```

### 4. Building
```bash
# Build debug APK
./build.sh my_nfc_project

# APK location: projects/my_nfc_project/app/build/outputs/apk/debug/app-debug.apk
```

### 5. Testing
```bash
# Install on device
adb install projects/my_nfc_project/app/build/outputs/apk/debug/app-debug.apk

# Or use Android Studio for debugging
```

## NFC Development

### Card Reading
The template includes basic NFC card reading functionality:
- Detects NFC tags when app is in foreground
- Displays card UID in hex format
- Supports multiple NFC technologies

### Host-Based Card Emulation
Ready for HCE development:
- NFC permissions configured
- Basic HCE structure provided
- Compatible with payment apps (Google Pay, etc.)

### Testing with ESP32
- Use the ESP32 PN7150 reader to test Android HCE
- Android phone should appear as Protocol 0x04 card
- 4-byte UID format (like MIFARE cards)

## Environment Variables

After running setup, these variables are available:
- `ANDROID_HOME`: Path to Android SDK
- `ANDROID_SDK_ROOT`: SDK root directory
- `GRADLE_HOME`: Path to Gradle installation
- `PATH`: Updated with Android tools

## Troubleshooting

### Common Issues

1. **License Acceptance**
   ```bash
   # If licenses not accepted during setup
   yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --licenses
   ```

2. **Gradle Wrapper**
   ```bash
   # If gradle wrapper missing in project
   cd projects/my_project
   gradle wrapper
   ```

3. **Build Tools**
   ```bash
   # If build tools not found
   $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager "build-tools;33.0.0"
   ```

### System Requirements
- **OS:** Linux (Ubuntu/Debian recommended)
- **Java:** OpenJDK 11 or 17
- **Memory:** 4GB RAM minimum, 8GB recommended
- **Storage:** 10GB free space for SDK and tools

## Integration with ESP32 Project

This Android environment is designed to work with the ESP32 PN7150 NFC reader:

1. **Test HCE Apps:** Build Android apps that emulate NFC cards
2. **Cross-Platform Testing:** Test ESP32 reader with Android HCE
3. **Payment Simulation:** Test Google Pay compatibility
4. **Custom Protocols:** Develop custom NFC communication

## Next Steps

1. **Run Setup:** Execute `./setup_environment.sh`
2. **Create Project:** Use `./create_project.sh` to start development
3. **Test HCE:** Build and test Host-Based Card Emulation
4. **Integrate:** Connect with ESP32 PN7150 reader for testing 