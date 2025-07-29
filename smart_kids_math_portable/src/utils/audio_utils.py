#!/usr/bin/env python3
"""
音频和语音合成工具
"""
import os
import platform
import subprocess
import threading
from typing import Optional


class AudioPlayer:
    """音频播放器，使用系统自带的TTS功能"""
    
    def __init__(self):
        self.system = platform.system()
        self.is_speaking = False
        self.current_process = None
        
    def speak(self, text: str, wait: bool = False):
        """
        朗读文本
        Args:
            text: 要朗读的文本
            wait: 是否等待朗读完成
        """
        # print(f"[AudioPlayer] 准备朗读: {text}")  # 调试信息（已注释）
        
        # 如果正在播放，先停止
        if self.is_speaking:
            self.stop()
            # 等待一小段时间确保停止完成
            import time
            time.sleep(0.2)  # 增加等待时间
        
        # 在新线程中朗读，避免阻塞游戏
        if wait:
            self._speak_text(text)
        else:
            thread = threading.Thread(target=self._speak_text, args=(text,))
            thread.daemon = True
            thread.start()
            # 给线程一点时间启动
            import time
            time.sleep(0.05)
    
    def _speak_text(self, text: str):
        """执行朗读"""
        self.is_speaking = True
        
        try:
            if self.system == "Darwin":  # macOS
                # 使用 macOS 的 say 命令
                # 优先尝试中文语音
                # print(f"[AudioPlayer] 朗读内容: {text}")  # 调试内容（已注释）
                
                # 直接使用 Tingting 语音
                try:
                    self.current_process = subprocess.Popen(
                        ["say", "-v", "Tingting", text]
                    )
                    # print(f"[AudioPlayer] 使用 Tingting 语音")  # 调试信息（已注释）
                except:
                    # 如果失败，使用默认语音
                    try:
                        self.current_process = subprocess.Popen(["say", text])
                        # print(f"[AudioPlayer] 使用默认语音")  # 调试信息（已注释）
                    except Exception as e:
                        print(f"[AudioPlayer] 语音播放失败: {e}")
            elif self.system == "Windows":
                # 使用 Windows 的 PowerShell 语音合成
                # 转义引号
                escaped_text = text.replace('"', '""')
                command = f'''
                Add-Type -AssemblyName System.Speech
                $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $speak.Speak("{escaped_text}")
                '''
                self.current_process = subprocess.Popen(
                    ["powershell", "-Command", command],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True
                )
            elif self.system == "Linux":
                # 使用 espeak
                try:
                    self.current_process = subprocess.Popen(
                        ["espeak", "-v", "zh", "-s", "150", text],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                except:
                    print("请安装 espeak: sudo apt-get install espeak")
            
            if self.current_process:
                self.current_process.wait()
                
        except Exception as e:
            print(f"语音朗读失败: {e}")
        finally:
            self.is_speaking = False
            self.current_process = None
    
    def stop(self):
        """停止当前朗读"""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=0.5)  # 等待进程结束，最多0.5秒
                self.current_process = None
            except:
                # 如果进程没有正常结束，强制杀死
                try:
                    self.current_process.kill()
                except:
                    pass
                self.current_process = None
        self.is_speaking = False
    
    def is_playing(self) -> bool:
        """检查是否正在播放语音"""
        if self.current_process and self.is_speaking:
            # 检查进程是否还在运行
            poll = self.current_process.poll()
            if poll is None:
                return True
            else:
                # 进程已结束
                self.is_speaking = False
                self.current_process = None
                return False
        return False


# 全局音频播放器实例
audio_player = AudioPlayer()


def speak(text: str, wait: bool = False):
    """
    便捷函数：朗读文本
    Args:
        text: 要朗读的文本
        wait: 是否等待朗读完成
    """
    audio_player.speak(text, wait)


def stop_speaking():
    """停止当前朗读"""
    audio_player.stop()


def is_speaking() -> bool:
    """检查是否正在朗读"""
    return audio_player.is_playing()