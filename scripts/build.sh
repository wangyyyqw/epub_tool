#!/bin/bash
set -e

echo "🚧 Starting Build Process..."

# Detect OS
OS_TYPE=$(uname -s)
echo "🖥️  Detected OS: $OS_TYPE"

# Set platform-specific variables
if [[ "$OS_TYPE" == "Darwin" ]]; then
    BACKEND_BIN="epub_tool_backend"
    APP_BUNDLE="build/bin/epub_tool.app"
    DEST_DIR="$APP_BUNDLE/Contents/MacOS"
    WAILS_BIN="epub_tool"
elif [[ "$OS_TYPE" == MINGW* ]] || [[ "$OS_TYPE" == CYGWIN* ]] || [[ "$OS_TYPE" == MSYS* ]]; then
    BACKEND_BIN="epub_tool_backend.exe"
    DEST_DIR="build/bin"
    WAILS_BIN="epub_tool.exe"
else
    # Linux or other
    BACKEND_BIN="epub_tool_backend"
    DEST_DIR="build/bin"
    WAILS_BIN="epub_tool"
fi

# 1. Build Python Backend
echo "🐍 Building Python Backend..."
# Check for python command (python3 or python)
if command -v python3 &> /dev/null; then
    PY_CMD="python3"
elif command -v python &> /dev/null; then
    PY_CMD="python"
else
    echo "❌ Error: Python not found."
    exit 1
fi

echo "Using Python command: $PY_CMD"
$PY_CMD -m PyInstaller --clean --onefile --name epub_tool_backend --paths backend --log-level ERROR backend/cli.py

# 2. Build Wails Application
echo "🕸️  Building Wails Application..."
# Check for wails in common locations
if [ -f "$HOME/go/bin/wails" ]; then
    WAILS_CMD="$HOME/go/bin/wails"
elif command -v wails &> /dev/null; then
    WAILS_CMD="wails"
else
    echo "❌ Error: 'wails' command not found. Please ensure it is installed and in your PATH."
    exit 1
fi

echo "Using Wails command: $WAILS_CMD"
$WAILS_CMD build

# 3. Bundle Python Backend into App
echo "📦 Bundling Python Backend into App..."

if [ ! -d "$DEST_DIR" ]; then
    echo "⚠️  Destination directory $DEST_DIR not found. Creating it..."
    mkdir -p "$DEST_DIR"
fi

if [ -f "dist/$BACKEND_BIN" ]; then
    echo "📋 Copying dist/$BACKEND_BIN to $DEST_DIR/"
    cp "dist/$BACKEND_BIN" "$DEST_DIR/"
    chmod +x "$DEST_DIR/$BACKEND_BIN"
    echo "✅ Python backend copied successfully"
else
    echo "❌ Error: Python backend binary not found at dist/$BACKEND_BIN"
    exit 1
fi

echo "✅ Build Complete!"
if [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "🚀 Application is ready at: $APP_BUNDLE"
else
    echo "🚀 Application is ready at: $DEST_DIR/$WAILS_BIN"
fi
