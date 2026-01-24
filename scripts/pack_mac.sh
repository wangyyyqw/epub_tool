#!/bin/bash
set -e

echo "📦 Packaging Mac application..."

# Configuration
APP_NAME="epub_tool"
APP_PATH="build/bin/${APP_NAME}.app"
DMG_NAME="${APP_NAME}_macos.dmg"
DMG_PATH="dist/${DMG_NAME}"
VOLUME_NAME="EPUB Tool"
TEMP_DIR="tmp_dmg_package"

# Clean up
if [ -d "${TEMP_DIR}" ]; then
    rm -rf "${TEMP_DIR}"
fi

if [ -f "${DMG_PATH}" ]; then
    echo "Removing existing DMG: ${DMG_PATH}"
    rm -f "${DMG_PATH}"
fi

# Check if app exists
if [ ! -d "${APP_PATH}" ]; then
    echo "❌ Error: App not found at ${APP_PATH}"
    echo "Please run './build.sh' first or 'wails build'"
    exit 1
fi

echo "📁 Preparing package contents..."

# Create temporary directory
mkdir -p "${TEMP_DIR}"

# Copy app
cp -R "${APP_PATH}" "${TEMP_DIR}/"

# Create Applications symlink
ln -s /Applications "${TEMP_DIR}/Applications"

# Create simple README
cat > "${TEMP_DIR}/README.txt" << 'EOF'
EPUB Tool - 多功能EPUB处理工具

安装方法：
1. 将 "epub_tool.app" 拖拽到 "应用程序" 文件夹
2. 从启动台或应用程序文件夹中打开应用

功能特性：
- EPUB加密/解密
- EPUB格式重整
- 字体加密与子集化
- 图片格式转换（WebP/JPEG/PNG）
- 简繁体中文转换
- 生僻字注音功能

系统要求：
- macOS 11.0 或更高版本
- 支持 Apple Silicon 和 Intel 芯片

注意事项：
- 首次启动可能需要几秒钟时间
- 应用程序包含Python后端用于EPUB处理
- 如果无法打开，请右键点击应用并选择"打开"

祝使用愉快！
EOF

echo "📀 Creating DMG image..."

# Calculate app size and add buffer
APP_SIZE_MB=$(du -sm "${APP_PATH}" | cut -f1)
DMG_SIZE_MB=$((APP_SIZE_MB + 25))  # Add 25MB buffer

echo "App size: ${APP_SIZE_MB}MB, DMG size: ${DMG_SIZE_MB}MB"

# Create DMG
hdiutil create \
    -srcfolder "${TEMP_DIR}" \
    -volname "${VOLUME_NAME}" \
    -fs HFS+ \
    -format UDZO \
    -imagekey zlib-level=9 \
    -size "${DMG_SIZE_MB}m" \
    "${DMG_PATH}"

echo "🧹 Cleaning up..."
rm -rf "${TEMP_DIR}"

# Verify DMG
if [ -f "${DMG_PATH}" ]; then
    DMG_ACTUAL_SIZE=$(du -h "${DMG_PATH}" | cut -f1)
    echo ""
    echo "✅ 打包完成！"
    echo "📊 DMG文件: ${DMG_PATH}"
    echo "📏 文件大小: ${DMG_ACTUAL_SIZE}"
    echo ""
    echo "📋 分发说明："
    echo "   1. 分享DMG文件: ${DMG_NAME}"
    echo "   2. 用户可以将应用拖拽到'应用程序'文件夹"
    echo "   3. 首次启动可能需要右键点击选择'打开'（Gatekeeper安全限制）"
    echo ""
    echo "🔧 应用程序包含："
    echo "   - 图形界面 (Go + Vue.js)"
    echo "   - Python后端 (包含生僻字字典修复)"
    echo "   - 所有依赖库"
else
    echo "❌ DMG创建失败"
    exit 1
fi