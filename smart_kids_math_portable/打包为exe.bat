@echo off
echo === 聪明儿童数学 Windows打包工具 ===
echo.
echo 这个工具会创建Windows可执行文件
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ 检测到Python
echo.

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo 开始打包...
python build_onefile.py

echo.
echo ✅ 如果打包成功，可执行文件在 dist 文件夹中
echo.
pause
