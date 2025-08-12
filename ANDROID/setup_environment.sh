#!/bin/bash

# Android Development Environment Setup Script
# This script sets up a self-contained Android 12 development environment

set -e

echo "Setting up Android Development Environment..."

# Set environment variables
export ANDROID_HOME="$(pwd)/android-sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator"

# Create directories
mkdir -p "$ANDROID_HOME/cmdline-tools"
mkdir -p "$ANDROID_HOME/platforms"
mkdir -p "$ANDROID_HOME/platform-tools"
mkdir -p "$ANDROID_HOME/build-tools"
mkdir -p "$ANDROID_HOME/system-images"
mkdir -p "$ANDROID_HOME/emulator"

# Download Android Command Line Tools
echo "Downloading Android Command Line Tools..."
if [ ! -f "tools/commandlinetools-linux.zip" ]; then
    wget -O tools/commandlinetools-linux.zip \
        "https://dl.google.com/android/repository/commandlinetools-linux-10406996_latest.zip"
fi

# Extract Command Line Tools
echo "Extracting Command Line Tools..."
unzip -q tools/commandlinetools-linux.zip -d "$ANDROID_HOME/cmdline-tools/"
mv "$ANDROID_HOME/cmdline-tools/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"

# Accept licenses
echo "Accepting Android licenses..."
yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses

# Install Android 12 (API 31) SDK
echo "Installing Android 12 (API 31) SDK..."
"$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" \
    "platforms;android-31" \
    "platform-tools" \
    "build-tools;33.0.0" \
    "system-images;android-31;google_apis;x86_64"

# Install additional tools
echo "Installing additional tools..."
"$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" \
    "emulator" \
    "extras;android;m2repository" \
    "extras;google;m2repository"

# Use system Gradle 8.5 (already installed)
echo "Using system Gradle 8.5..."
export GRADLE_HOME="/opt/gradle"
export PATH="$GRADLE_HOME/bin:$PATH"

# Create environment file
cat > .env << EOF
# Android Development Environment Variables
export ANDROID_HOME="$(pwd)/android-sdk"
export ANDROID_SDK_ROOT="\$ANDROID_HOME"
export GRADLE_HOME="/opt/gradle"
export PATH="\$GRADLE_HOME/bin:\$PATH:\$ANDROID_HOME/cmdline-tools/latest/bin:\$ANDROID_HOME/platform-tools:\$ANDROID_HOME/emulator"
EOF

# Create project template
mkdir -p projects/template
cat > projects/template/build.gradle << 'EOF'
plugins {
    id 'com.android.application'
}

android {
    namespace 'com.example.nfcapp'
    compileSdk 33

    defaultConfig {
        applicationId "com.example.nfcapp"
        minSdk 21
        targetSdk 31
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.9.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
}
EOF

cat > projects/template/app/build.gradle << 'EOF'
plugins {
    id 'com.android.application'
}

android {
    namespace 'com.example.nfcapp'
    compileSdk 33

    defaultConfig {
        applicationId "com.example.nfcapp"
        minSdk 21
        targetSdk 31
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.9.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
}
EOF

cat > projects/template/settings.gradle << 'EOF'
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "NFCApp"
include ':app'
EOF

cat > projects/template/gradle.properties << 'EOF'
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
EOF

# Create basic Android manifest
mkdir -p projects/template/app/src/main
cat > projects/template/app/src/main/AndroidManifest.xml << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.nfcapp">

    <uses-permission android:name="android.permission.NFC" />
    <uses-feature android:name="android.hardware.nfc" android:required="true" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.NFCApp">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
EOF

# Create basic MainActivity
mkdir -p projects/template/app/src/main/java/com/example/nfcapp
cat > projects/template/app/src/main/java/com/example/nfcapp/MainActivity.java << 'EOF'
package com.example.nfcapp;

import android.app.PendingIntent;
import android.content.Intent;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.os.Bundle;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    private NfcAdapter nfcAdapter;
    private PendingIntent pendingIntent;
    private TextView statusText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        statusText = findViewById(R.id.status_text);
        
        // Initialize NFC
        nfcAdapter = NfcAdapter.getDefaultAdapter(this);
        if (nfcAdapter == null) {
            statusText.setText("NFC not available on this device");
            return;
        }
        
        if (!nfcAdapter.isEnabled()) {
            statusText.setText("Please enable NFC");
            return;
        }
        
        // Create pending intent for NFC
        Intent intent = new Intent(this, getClass());
        intent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        pendingIntent = PendingIntent.getActivity(this, 0, intent, 
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_MUTABLE);
        
        statusText.setText("NFC Ready - Hold device near reader");
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        if (nfcAdapter != null) {
            nfcAdapter.enableForegroundDispatch(this, pendingIntent, null, null);
        }
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        if (nfcAdapter != null) {
            nfcAdapter.disableForegroundDispatch(this);
        }
    }
    
    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (NfcAdapter.ACTION_TAG_DISCOVERED.equals(intent.getAction()) ||
            NfcAdapter.ACTION_NDEF_DISCOVERED.equals(intent.getAction()) ||
            NfcAdapter.ACTION_TECH_DISCOVERED.equals(intent.getAction())) {
            
            Tag tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
            if (tag != null) {
                byte[] id = tag.getId();
                StringBuilder uid = new StringBuilder();
                for (byte b : id) {
                    uid.append(String.format("%02X:", b));
                }
                if (uid.length() > 0) {
                    uid.setLength(uid.length() - 1); // Remove last colon
                }
                statusText.setText("Card detected: " + uid.toString());
            }
        }
    }
}
EOF

# Create layout file
mkdir -p projects/template/app/src/main/res/layout
cat > projects/template/app/src/main/res/layout/activity_main.xml << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <TextView
        android:id="@+id/status_text"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="NFC Ready"
        android:textSize="18sp"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent" />

</androidx.constraintlayout.widget.ConstraintLayout>
EOF

# Create strings resource
mkdir -p projects/template/app/src/main/res/values
cat > projects/template/app/src/main/res/values/strings.xml << 'EOF'
<resources>
    <string name="app_name">NFC App</string>
</resources>
EOF

# Create gradle wrapper
mkdir -p projects/template/gradle/wrapper
cat > projects/template/gradle/wrapper/gradle-wrapper.properties << 'EOF'
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.5-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
EOF

# Create build script
cat > build.sh << 'EOF'
#!/bin/bash

# Build script for Android projects
set -e

# Load environment
source .env

# Check if project name is provided
if [ -z "$1" ]; then
    echo "Usage: ./build.sh <project_name>"
    echo "Available projects:"
    ls -1 projects/
    exit 1
fi

PROJECT_NAME=$1
PROJECT_DIR="projects/$PROJECT_NAME"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Project $PROJECT_NAME not found in projects/"
    exit 1
fi

echo "Building project: $PROJECT_NAME"
cd "$PROJECT_DIR"

# Build the project
./gradlew assembleDebug

echo "Build completed successfully!"
echo "APK location: $PROJECT_DIR/app/build/outputs/apk/debug/app-debug.apk"
EOF

chmod +x build.sh

# Create new project script
cat > create_project.sh << 'EOF'
#!/bin/bash

# Create new Android project
set -e

if [ -z "$1" ]; then
    echo "Usage: ./create_project.sh <project_name>"
    exit 1
fi

PROJECT_NAME=$1
PROJECT_DIR="projects/$PROJECT_NAME"

if [ -d "$PROJECT_DIR" ]; then
    echo "Project $PROJECT_NAME already exists!"
    exit 1
fi

echo "Creating new project: $PROJECT_NAME"

# Copy template
cp -r projects/template "$PROJECT_DIR"

# Update project name in settings.gradle
sed -i "s/NFCApp/$PROJECT_NAME/g" "$PROJECT_DIR/settings.gradle"

# Update package name in build.gradle files
sed -i "s/com.example.nfcapp/com.example.$PROJECT_NAME/g" "$PROJECT_DIR/app/build.gradle"

# Update AndroidManifest.xml
sed -i "s/com.example.nfcapp/com.example.$PROJECT_NAME/g" "$PROJECT_DIR/app/src/main/AndroidManifest.xml"

# Update MainActivity package
mkdir -p "$PROJECT_DIR/app/src/main/java/com/example/$PROJECT_NAME"
mv "$PROJECT_DIR/app/src/main/java/com/example/nfcapp/MainActivity.java" \
   "$PROJECT_DIR/app/src/main/java/com/example/$PROJECT_NAME/"
sed -i "s/package com.example.nfcapp;/package com.example.$PROJECT_NAME;/g" \
   "$PROJECT_DIR/app/src/main/java/com/example/$PROJECT_NAME/MainActivity.java"

# Update AndroidManifest.xml activity reference
sed -i "s/.MainActivity/.$PROJECT_NAME.MainActivity/g" "$PROJECT_DIR/app/src/main/AndroidManifest.xml"

echo "Project $PROJECT_NAME created successfully!"
echo "To build: ./build.sh $PROJECT_NAME"
EOF

chmod +x create_project.sh

echo "Android Development Environment setup complete!"
echo ""
echo "To activate the environment:"
echo "  source .env"
echo ""
echo "To create a new project:"
echo "  ./create_project.sh <project_name>"
echo ""
echo "To build a project:"
echo "  ./build.sh <project_name>"
echo ""
echo "Environment variables:"
echo "  ANDROID_HOME: $ANDROID_HOME"
echo "  GRADLE_HOME: $(pwd)/gradle/gradle-8.0" 