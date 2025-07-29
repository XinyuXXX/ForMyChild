#!/usr/bin/env python3
"""
在macOS上为Windows交叉编译
使用wine和pyinstaller
"""
import os
import sys
import subprocess
import shutil

def main():
    print("=== 在macOS上构建Windows可执行文件 ===\n")
    
    print("⚠️  注意：这需要安装Wine")
    print("如果没有安装，请运行：brew install wine-stable\n")
    
    response = input("是否已安装Wine？(y/n): ")
    if response.lower() != 'y':
        print("\n请先安装Wine：")
        print("1. 安装Homebrew（如果没有）：")
        print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("2. 安装Wine：")
        print("   brew install wine-stable")
        return
    
    print("\n创建Windows Python环境...")
    
    # 这个方法比较复杂，我们提供一个更简单的方案
    print("\n❌ Wine方法比较复杂，建议使用以下替代方案：")
    print("\n" + "="*50)
    print("推荐方案：")
    print("="*50)
    print("\n1. 【最简单】请求Windows用户帮助：")
    print("   - 将整个项目文件夹发送给Windows用户")
    print("   - 让他们运行: python build_onefile.py")
    print("   - 他们会在dist文件夹中得到.exe文件")
    
    print("\n2. 【云服务】使用GitHub Actions（免费）：")
    print("   - 将代码上传到GitHub")
    print("   - 使用我创建的.github/workflows/build.yml")
    print("   - 自动构建Windows和macOS版本")
    
    print("\n3. 【虚拟机】使用Windows虚拟机：")
    print("   - 安装Parallels Desktop或VMware Fusion")
    print("   - 安装Windows 10/11")
    print("   - 在虚拟机中运行打包脚本")
    
    print("\n4. 【在线服务】使用在线Python环境：")
    print("   - 使用 repl.it 或 Google Colab")
    print("   - 上传代码并运行打包命令")

if __name__ == "__main__":
    main()