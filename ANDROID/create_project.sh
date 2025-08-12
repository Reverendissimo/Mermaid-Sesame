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