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