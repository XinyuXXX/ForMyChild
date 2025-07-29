import os
import pygame
import platform

# 资源路径 - 放在最前面，因为后面的函数需要用到
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
IMAGES_PATH = os.path.join(ASSETS_PATH, 'images')
SOUNDS_PATH = os.path.join(ASSETS_PATH, 'sounds')
FONTS_PATH = os.path.join(ASSETS_PATH, 'fonts')

# 窗口设置
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60
TITLE = "Smart Kids Math - Math & Logic Training"  # 使用英文避免标题乱码

# 颜色定义（使用柔和的儿童友好色彩）
COLORS = {
    'background': (255, 248, 240),  # 温暖的米色背景
    'primary': (255, 183, 77),      # 橙色
    'secondary': (129, 199, 132),   # 绿色
    'accent': (121, 134, 203),      # 紫色
    'danger': (239, 83, 80),        # 红色
    'success': (102, 187, 106),     # 成功绿
    'warning': (255, 193, 7),       # 警告黄
    'text': (66, 66, 66),           # 深灰文字
    'white': (255, 255, 255),
    'light_gray': (245, 245, 245),
    'disabled': (189, 189, 189),    # 禁用状态灰色
}

# 字体设置
def get_font_path():
    """获取中文字体路径"""
    font_dir = os.path.join(ASSETS_PATH, 'fonts')
    
    # 尝试查找可用的中文字体
    font_files = [
        'SourceHanSansCN-Regular.ttf',
        'NotoSansCJK-Regular.ttc',
        'wqy-microhei.ttc',
        'msyh.ttf',
        'SimHei.ttf'
    ]
    
    for font_file in font_files:
        font_path = os.path.join(font_dir, font_file)
        if os.path.exists(font_path):
            return font_path
    
    # 如果没有找到中文字体，根据系统尝试使用系统字体
    system = platform.system()
    if system == 'Darwin':  # macOS
        return '/System/Library/Fonts/PingFang.ttc'
    elif system == 'Windows':
        return 'C:/Windows/Fonts/msyh.ttc'
    else:  # Linux
        return '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'

FONTS = {
    'default': get_font_path(),
    'size': {
        'small': 24,
        'medium': 32,
        'large': 48,
        'xlarge': 64
    }
}

# 游戏设置
GAME_SETTINGS = {
    'find_difference': {
        'time_limit': 60,  # 秒
        'min_differences': 3,
        'max_differences': 8,
        'initial_difficulty': 1
    },
    'counting': {
        'max_number': 10,
        'show_time': 3,  # 显示物品的时间（秒）
        'initial_difficulty': 1
    },
    'simple_math': {
        'max_number': 10,
        'operations': ['+', '-'],
        'time_limit': 30,
        'initial_difficulty': 1
    }
}

# 奖励系统
REWARDS = {
    'star_threshold': {
        1: 60,   # 1星
        2: 80,   # 2星
        3: 100   # 3星
    },
    'coins_per_game': 10,
    'bonus_multiplier': 1.5
}

# 音效设置
SOUND_ENABLED = True
SOUND_VOLUME = 0.7

# 数据存储路径
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
SAVE_FILE = os.path.join(DATA_PATH, 'progress.json')

# 自适应难度设置
ADAPTIVE_SETTINGS = {
    'success_rate_target': 0.7,  # 目标成功率
    'min_games_before_adjust': 5,  # 调整难度前的最少游戏次数
    'difficulty_increase_threshold': 0.85,  # 成功率高于此值时增加难度
    'difficulty_decrease_threshold': 0.55,  # 成功率低于此值时降低难度
}

# 确保必要的目录存在
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(IMAGES_PATH, exist_ok=True)
os.makedirs(SOUNDS_PATH, exist_ok=True)
os.makedirs(FONTS_PATH, exist_ok=True)