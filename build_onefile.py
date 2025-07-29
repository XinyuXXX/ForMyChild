#!/usr/bin/env python3
"""
单文件打包脚本 - 创建不需要安装的独立可执行文件
"""
import os
import sys
import subprocess
import platform

def main():
    print("=== 聪明儿童数学 - 单文件打包工具 ===\n")
    
    # 确定操作系统
    system = platform.system()
    print(f"检测到操作系统: {system}")
    
    # 安装PyInstaller
    print("\n安装/更新 PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"])
    
    # 清理旧文件
    print("\n清理旧的构建文件...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            import shutil
            shutil.rmtree(folder)
    
    # 准备打包命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "聪明儿童数学",
        "--onefile",  # 打包成单个文件
        "--windowed",  # 不显示控制台
        "--add-data", f"assets{os.pathsep}assets",
        "--add-data", f"data{os.pathsep}data",
        "--add-data", f"src{os.pathsep}src",
        "--hidden-import", "pygame",
        "--hidden-import", "numpy",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "PIL",
        "--exclude-module", "cv2",
        "--exclude-module", "skimage",
        "--clean",  # 清理临时文件
    ]
    
    # macOS特定选项
    if system == "Darwin":
        cmd.extend([
            "--osx-bundle-identifier", "com.smartkids.math",
        ])
    
    # 添加主文件
    cmd.append("main.py")
    
    # 执行打包
    print("\n开始打包...")
    print(f"命令: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ 打包成功!")
        print(f"\n可执行文件位置:")
        if system == "Windows":
            print(f"  dist\\聪明儿童数学.exe")
        elif system == "Darwin":
            print(f"  dist/聪明儿童数学")
            print(f"\n提示: 可以使用以下命令创建macOS应用:")
            print(f"  1. 创建应用包: mkdir -p '聪明儿童数学.app/Contents/MacOS'")
            print(f"  2. 复制可执行文件: cp dist/聪明儿童数学 '聪明儿童数学.app/Contents/MacOS/'")
            print(f"  3. 双击 聪明儿童数学.app 运行")
        else:
            print(f"  dist/聪明儿童数学")
        
        print(f"\n特点:")
        print(f"  - 单个可执行文件，无需安装Python")
        print(f"  - 包含所有依赖和资源")
        print(f"  - 可以复制到任何地方运行")
    else:
        print("\n❌ 打包失败!")
        print("请检查错误信息并确保所有依赖已正确安装")

if __name__ == "__main__":
    main()