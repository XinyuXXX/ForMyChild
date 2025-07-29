#!/bin/bash

echo "=== 聪明儿童数学应用打包脚本 ==="
echo ""

# 检查Python环境
echo "检查Python环境..."
python3 --version

# 安装PyInstaller（如果未安装）
echo ""
echo "安装/更新 PyInstaller..."
pip3 install --upgrade pyinstaller

# 清理之前的构建
echo ""
echo "清理之前的构建..."
rm -rf build dist

# 打包应用
echo ""
echo "开始打包应用..."
pyinstaller smart_kids_math.spec

# 检查是否成功
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 打包成功！"
    echo ""
    echo "应用位置："
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  macOS: dist/聪明儿童数学.app"
        echo "  可以直接双击运行"
        # 创建DMG（可选）
        # echo ""
        # echo "创建DMG安装包..."
        # hdiutil create -volname "聪明儿童数学" -srcfolder dist/聪明儿童数学.app -ov -format UDZO dist/聪明儿童数学.dmg
    else
        echo "  可执行文件: dist/聪明儿童数学"
    fi
else
    echo ""
    echo "❌ 打包失败，请检查错误信息"
fi