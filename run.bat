@echo off
echo 欢迎使用聪明小宝贝数学启蒙软件！
echo 正在检查环境...

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python3.8或更高版本
    pause
    exit /b 1
)

:: 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 安装依赖
echo 检查并安装依赖...
pip install -r requirements.txt -q

:: 创建数据目录
if not exist "data" mkdir data

:: 启动游戏
echo 启动游戏...
python main.py

:: 暂停以查看可能的错误信息
pause