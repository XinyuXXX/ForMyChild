#!/usr/bin/env python3
"""
创建便携式包，Windows用户可以用来生成exe
"""
import os
import shutil
import zipfile

def create_portable_package():
    print("创建便携式打包包...")
    
    # 创建临时目录
    package_dir = "smart_kids_math_portable"
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # 复制必要文件
    items_to_copy = [
        "main.py",
        "src",
        "assets", 
        "data",
        "requirements.txt",
        "build_onefile.py"
    ]
    
    for item in items_to_copy:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.copytree(item, os.path.join(package_dir, item))
            else:
                shutil.copy2(item, package_dir)
    
    # 创建Windows批处理文件
    batch_content = """@echo off
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
"""
    
    with open(os.path.join(package_dir, "打包为exe.bat"), "w", encoding="utf-8") as f:
        f.write(batch_content)
    
    # 创建说明文件
    readme_content = """# Windows打包说明

## 使用方法

1. 确保已安装Python 3.8或更高版本
   - 下载地址：https://www.python.org/downloads/
   - 安装时勾选"Add Python to PATH"

2. 双击运行 `打包为exe.bat`

3. 等待打包完成（约1-2分钟）

4. 在 `dist` 文件夹中找到 `聪明儿童数学.exe`

## 如果遇到问题

1. 确保有网络连接（需要下载依赖包）
2. 以管理员身份运行批处理文件
3. 暂时关闭杀毒软件

## 成功后

- `dist\聪明儿童数学.exe` 就是独立的可执行文件
- 可以分享给其他人，无需Python环境
- 双击即可运行游戏
"""
    
    with open(os.path.join(package_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # 创建ZIP文件
    zip_filename = "聪明儿童数学-Windows打包工具.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, os.path.dirname(package_dir))
                zf.write(file_path, arc_path)
    
    # 清理临时目录
    shutil.rmtree(package_dir)
    
    print(f"\n✅ 创建成功！")
    print(f"\n文件：{zip_filename}")
    print(f"大小：{os.path.getsize(zip_filename) / 1024 / 1024:.1f} MB")
    print(f"\n发送给Windows用户的步骤：")
    print(f"1. 将 {zip_filename} 发送给Windows用户")
    print(f"2. 让他们解压并运行 '打包为exe.bat'")
    print(f"3. 他们会在dist文件夹得到可执行文件")

if __name__ == "__main__":
    create_portable_package()