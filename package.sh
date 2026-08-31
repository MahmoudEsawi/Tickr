#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="Tickr"
DIST_DIR="${SCRIPT_DIR}/dist"
APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"
MACOS_DIR="${APP_BUNDLE}/Contents/MacOS"
RESOURCES_DIR="${APP_BUNDLE}/Contents/Resources"
DMG_ROOT="${DIST_DIR}/dmg_root"
DMG_FILE="${DIST_DIR}/${APP_NAME}-v1.0.0.dmg"
ZIP_FILE="${DIST_DIR}/${APP_NAME}-v1.0.0-macOS.zip"

echo "🧹 Cleaning previous build artifacts..."
rm -rf "$DIST_DIR"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

echo "📦 Packaging ${APP_NAME}.app bundle..."

# Copy Python script, UI assets, and resources into app bundle
cp tickr_app.py "${RESOURCES_DIR}/"
cp -R ui "${RESOURCES_DIR}/"
cp -R assets "${RESOURCES_DIR}/"

# Create launcher executable in Contents/MacOS
cat << 'EOF' > "${MACOS_DIR}/${APP_NAME}"
#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../Resources" && pwd)"
exec python3 "${DIR}/tickr_app.py"
EOF

chmod +x "${MACOS_DIR}/${APP_NAME}"

# Create Info.plist
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

echo "🗜️ Creating ZIP archive..."
ditto -c -k --sequesterRsrc --keepParent "$APP_BUNDLE" "$ZIP_FILE"

echo "💿 Creating DMG installer..."
mkdir -p "$DMG_ROOT"
cp -R "$APP_BUNDLE" "$DMG_ROOT/"
ln -s /Applications "$DMG_ROOT/Applications"

hdiutil create -volname "${APP_NAME}" -srcfolder "$DMG_ROOT" -ov -format UDZO "$DMG_FILE"
rm -rf "$DMG_ROOT"

echo "✅ Successfully created release assets:"
ls -lh "${DIST_DIR}"
