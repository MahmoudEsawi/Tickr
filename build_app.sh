#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="Tickr"
APP_BUNDLE="${APP_NAME}.app"
MACOS_DIR="${APP_BUNDLE}/Contents/MacOS"
RESOURCES_DIR="${APP_BUNDLE}/Contents/Resources"

echo "🔨 Compiling ${APP_NAME} for macOS..."
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

# Compile Swift sources into executable binary
SDK_PATH="$(xcrun --show-sdk-path)"
swiftc \
  -sdk "$SDK_PATH" \
  -target arm64-apple-macosx13.0 \
  -parse-as-library \
  $(find Sources/Tickr -name "*.swift") \
  -o "${MACOS_DIR}/${APP_NAME}"

# Create Info.plist with LSUIElement (Accessory / Menu Bar App)
cat <<EOF > "${APP_BUNDLE}/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.mahmoudesawi.${APP_NAME}</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "✅ Successfully built ${APP_BUNDLE}!"
echo "🚀 Launching ${APP_NAME} in macOS Menu Bar..."
open "${APP_BUNDLE}"
