@echo off
echo === 聪明儿童数学应用打包脚本 ===
echo.

REM 检查Python环境
echo 检查Python环境...
python --version

REM 安装PyInstaller（如果未安装）
echo.
echo 安装/更新 PyInstaller...
pip install --upgrade pyinstaller

REM 清理之前的构建
echo.
echo 清理之前的构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 打包应用
echo.
echo 开始打包应用...
pyinstaller smart_kids_math.spec

REM 检查是否成功
if %errorlevel% equ 0 (
    echo.
    echo ✅ 打包成功！
    echo.
    echo 应用位置：dist\聪明儿童数学.exe
    echo 可以直接双击运行
) else (
    echo.
    echo ❌ 打包失败，请检查错误信息
)

pause