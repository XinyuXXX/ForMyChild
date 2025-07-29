#!/bin/bash

# 聪明小宝贝启动脚本

echo "欢迎使用聪明小宝贝数学启蒙软件！"

# 检查Python是否安装
if ! command -v python3 &> /dev/null
then
    echo "错误：未找到Python3，请先安装Python3.8或更高版本"
    exit 1
fi

# 创建数据目录
mkdir -p data

# 直接启动游戏
echo "启动游戏..."
python3 main.py
