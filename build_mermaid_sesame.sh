#!/bin/bash

# Build and Install Mermaid Sesame App Script

echo "Building and installing Mermaid Sesame app..."

# Source the Android environment
source setup_android_env.sh

# Navigate to the project
cd ANDROID/projects/mermaid_sesame

# Build the app
echo "Building app..."
gradle assembleDebug

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    
    # Check if device is connected
    if adb devices | grep -q "device$"; then
        echo "Installing app..."
        adb install -r app/build/outputs/apk/debug/app-debug.apk
        
        if [ $? -eq 0 ]; then
            echo "✅ App installed successfully!"
            echo ""
            echo "The Mermaid Sesame app should now:"
            echo "1. Auto-start the HCE service when launched"
            echo "2. Request all required permissions"
            echo "3. Be ready to respond to ESP32 SELECT AID commands"
            echo ""
            echo "Test it by placing the phone near your ESP32 reader!"
        else
            echo "❌ Failed to install app"
            exit 1
        fi
    else
        echo "❌ No Android device connected"
        echo "Please connect a device and run: adb devices"
        exit 1
    fi
else
    echo "❌ Build failed"
    exit 1
fi 