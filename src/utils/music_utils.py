#!/usr/bin/env python3
"""
音乐相关工具函数
"""
import pygame
import numpy as np
import math


def generate_tone(frequency: float, duration: float = 0.5, sample_rate: int = 22050) -> pygame.mixer.Sound:
    """
    生成指定频率的音调
    Args:
        frequency: 频率（Hz）
        duration: 持续时间（秒）
        sample_rate: 采样率
    Returns:
        pygame.mixer.Sound对象
    """
    frames = int(duration * sample_rate)
    arr = np.zeros(frames)
    
    for i in range(frames):
        # 生成正弦波
        arr[i] = 4096 * np.sin(2 * np.pi * frequency * i / sample_rate)
        
        # 添加包络线，使声音更自然
        if i < frames * 0.1:  # 淡入
            arr[i] *= i / (frames * 0.1)
        elif i > frames * 0.9:  # 淡出
            arr[i] *= (frames - i) / (frames * 0.1)
    
    # 转换为16位整数
    arr = arr.astype(np.int16)
    
    # 创建立体声数组
    stereo_arr = np.empty((frames, 2), dtype=np.int16)
    stereo_arr[:, 0] = arr  # 左声道
    stereo_arr[:, 1] = arr  # 右声道
    
    # 创建Sound对象
    sound = pygame.sndarray.make_sound(stereo_arr)
    return sound


# 预定义的音符频率（Hz）
NOTE_FREQUENCIES = {
    'C3': 130.81,
    'D3': 146.83,
    'E3': 164.81,
    'F3': 174.61,
    'G3': 196.00,
    'A3': 220.00,
    'B3': 246.94,
    'C4': 261.63,
    'D4': 293.66,
    'E4': 329.63,
    'F4': 349.23,
    'G4': 392.00,
    'A4': 440.00,
    'B4': 493.88,
    'C5': 523.25,
    'D5': 587.33,
    'E5': 659.25,
    'F5': 698.46,
    'G5': 783.99,
    'A5': 880.00,
    'B5': 987.77,
    'C6': 1046.50,
}


def play_note(note_name: str, octave: int, duration: float = 0.5):
    """
    播放指定音符
    Args:
        note_name: 音符名称（C, D, E, F, G, A, B）
        octave: 八度（3, 4, 5, 6）
        duration: 持续时间（秒）
    """
    try:
        # 确保 pygame mixer 已初始化
        init_pygame_mixer()
        
        note_key = f"{note_name}{octave}"
        if note_key in NOTE_FREQUENCIES:
            frequency = NOTE_FREQUENCIES[note_key]
            sound = generate_tone(frequency, duration)
            sound.play()
        else:
            print(f"未知的音符: {note_key}")
    except Exception as e:
        print(f"播放音符时出错: {e}")


def init_pygame_mixer():
    """初始化pygame mixer"""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    except Exception as e:
        print(f"Pygame mixer 初始化失败: {e}")