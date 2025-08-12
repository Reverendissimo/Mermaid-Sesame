#!/bin/bash

# Android Development Environment Setup Script
# This script sets up the environment for building Android apps in this project

echo "Setting up Android Development Environment..."

# Set Android SDK paths
export ANDROID_HOME="/home/rev/ESP-32-AGAIN/ANDROID/android-sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export GRADLE_HOME="/opt/gradle"

# Add Android tools to PATH
export PATH="$GRADLE_HOME/bin:$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator"

# Verify environment
echo "Environment variables set:"
echo "  ANDROID_HOME: $ANDROID_HOME"
echo "  ANDROID_SDK_ROOT: $ANDROID_SDK_ROOT"
echo "  GRADLE_HOME: $GRADLE_HOME"
echo "  Android tools in PATH: $(echo $PATH | grep android-sdk | wc -l) entries found"

# Check if Android SDK exists
if [ ! -d "$ANDROID_HOME" ]; then
    echo "ERROR: Android SDK not found at $ANDROID_HOME"
    echo "Please run: cd ANDROID && source setup_environment.sh"
    exit 1
fi

# Check if Gradle is available
if ! command -v gradle &> /dev/null; then
    echo "ERROR: Gradle not found in PATH"
    exit 1
fi

# Check if adb is available
if ! command -v adb &> /dev/null; then
    echo "ERROR: adb not found in PATH"
    exit 1
fi

echo "✅ Android development environment is ready!"
echo ""
echo "Available commands:"
echo "  gradle assembleDebug    - Build debug APK"
echo "  adb devices            - List connected devices"
echo "  adb install app/build/outputs/apk/debug/app-debug.apk  - Install APK"
echo ""
echo "To build the Mermaid Sesame app:"
echo "  cd ANDROID/projects/mermaid_sesame && gradle assembleDebug"
echo ""
echo "To install the updated app:"
echo "  adb install ANDROID/projects/mermaid_sesame/app/build/outputs/apk/debug/app-debug.apk" 