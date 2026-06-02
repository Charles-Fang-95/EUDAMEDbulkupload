#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-run}"
APP_NAME="EUDAMED Local Beta"
EXECUTABLE_NAME="EUDAMEDLocalBeta"
BUNDLE_ID="com.xiongfeifang.eudamed-local-beta"
MIN_SYSTEM_VERSION="13.0"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_DIR="$ROOT_DIR/mac_app"
DIST_DIR="$ROOT_DIR/dist"
BUILD_CACHE="$ROOT_DIR/.build-cache"
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"
APP_CONTENTS="$APP_BUNDLE/Contents"
APP_MACOS="$APP_CONTENTS/MacOS"
APP_RESOURCES="$APP_CONTENTS/Resources"
APP_BINARY="$APP_MACOS/$EXECUTABLE_NAME"
INFO_PLIST="$APP_CONTENTS/Info.plist"
RESOURCE_ROOT="$APP_RESOURCES/EUDAMEDLocalBeta"

pkill -x "$EXECUTABLE_NAME" >/dev/null 2>&1 || true

mkdir -p "$BUILD_CACHE/home" "$BUILD_CACHE/swiftpm" "$BUILD_CACHE/clang-modules"
export HOME="$BUILD_CACHE/home"
export CLANG_MODULE_CACHE_PATH="$BUILD_CACHE/clang-modules"
if [[ -d "/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk" ]]; then
  export SDKROOT="/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk"
fi

swift build --package-path "$PACKAGE_DIR" --cache-path "$BUILD_CACHE/swiftpm" --disable-sandbox
BUILD_BINARY="$(swift build --package-path "$PACKAGE_DIR" --cache-path "$BUILD_CACHE/swiftpm" --disable-sandbox --show-bin-path)/$EXECUTABLE_NAME"

rm -rf "$APP_BUNDLE"
mkdir -p "$APP_MACOS" "$RESOURCE_ROOT"
cp "$BUILD_BINARY" "$APP_BINARY"
chmod +x "$APP_BINARY"

copy_item() {
  local source="$1"
  local target="$2"
  if [[ -d "$source" ]]; then
    mkdir -p "$target"
    /usr/bin/rsync -a \
      --exclude '.DS_Store' \
      --exclude '__pycache__' \
      --exclude '*.pyc' \
      "$source"/ "$target"/
  elif [[ -f "$source" ]]; then
    mkdir -p "$(dirname "$target")"
    cp "$source" "$target"
  fi
}

copy_item "$ROOT_DIR/local_beta" "$RESOURCE_ROOT/local_beta"
copy_item "$ROOT_DIR/EUDAMED_TOOL_v2" "$RESOURCE_ROOT/EUDAMED_TOOL_v2"
copy_item "$ROOT_DIR/official_docs" "$RESOURCE_ROOT/official_docs"
copy_item "$ROOT_DIR/EUDAMED_Template_v2.5.xlsx" "$RESOURCE_ROOT/EUDAMED_Template_v2.5.xlsx"
copy_item "$ROOT_DIR/run_local_beta.py" "$RESOURCE_ROOT/run_local_beta.py"
copy_item "$ROOT_DIR/README.md" "$RESOURCE_ROOT/README.md"
copy_item "$ROOT_DIR/LOCAL_BETA_README.md" "$RESOURCE_ROOT/LOCAL_BETA_README.md"

rm -rf \
  "$RESOURCE_ROOT/local_beta_data" \
  "$RESOURCE_ROOT/dist" \
  "$RESOURCE_ROOT/.git" \
  "$RESOURCE_ROOT/__pycache__" \
  "$RESOURCE_ROOT/local_beta/__pycache__"
find "$RESOURCE_ROOT" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "$RESOURCE_ROOT" -name '*.pyc' -delete
find "$RESOURCE_ROOT" -name '.DS_Store' -delete

cat >"$INFO_PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>$EXECUTABLE_NAME</string>
  <key>CFBundleIdentifier</key>
  <string>$BUNDLE_ID</string>
  <key>CFBundleName</key>
  <string>$APP_NAME</string>
  <key>CFBundleDisplayName</key>
  <string>$APP_NAME</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.4</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>$MIN_SYSTEM_VERSION</string>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSAppTransportSecurity</key>
  <dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
  </dict>
</dict>
</plist>
PLIST

open_app() {
  /usr/bin/open -n "$APP_BUNDLE"
}

case "$MODE" in
  --build-only|build)
    echo "Built $APP_BUNDLE"
    ;;
  run)
    open_app
    ;;
  --debug|debug)
    lldb -- "$APP_BINARY"
    ;;
  --logs|logs)
    open_app
    /usr/bin/log stream --info --style compact --predicate "process == \"$EXECUTABLE_NAME\""
    ;;
  --telemetry|telemetry)
    open_app
    /usr/bin/log stream --info --style compact --predicate "subsystem == \"$BUNDLE_ID\""
    ;;
  --verify|verify)
    open_app
    sleep 2
    pgrep -x "$EXECUTABLE_NAME" >/dev/null
    ;;
  *)
    echo "usage: $0 [run|--build-only|--debug|--logs|--telemetry|--verify]" >&2
    exit 2
    ;;
esac
