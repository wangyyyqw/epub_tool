#!/bin/bash
set -e

echo "🚧 Starting Build Process..."

# 1. Build Python Backend
echo "🐍 Building Python Backend..."
python3 -m PyInstaller --clean --onefile --name epub_tool_backend --paths python_core --log-level ERROR python_core/cli.py

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

$WAILS_CMD build

# 3. Bundle Python Backend into App
echo "📦 Bundling Python Backend into App..."
APP_PATH="build/bin/epub_tool.app"
DEST_DIR="$APP_PATH/Contents/MacOS"

if [ ! -d "$DEST_DIR" ]; then
    echo "❌ Error: App bundle not found at $APP_PATH"
    exit 1
fi

cp dist/epub_tool_backend "$DEST_DIR/"
chmod +x "$DEST_DIR/epub_tool_backend"

echo "✅ Build Complete!"
echo "🚀 Application is ready at: $APP_PATH"
