"""
游戏基类 - 提供窗口大小自适应功能
"""
import pygame
from typing import Tuple, Dict, Optional


class BaseGame:
    """所有游戏的基类"""
    
    def __init__(self, difficulty: int = 1):
        self.difficulty = difficulty
        self.window_width = 1024  # 默认宽度
        self.window_height = 768  # 默认高度
        self.scale_factor = 1.0   # 缩放因子
        
    def update_window_size(self, width: int, height: int):
        """更新窗口大小"""
        self.window_width = width
        self.window_height = height
        # 计算缩放因子（基于1024x768的设计尺寸）
        self.scale_factor = min(width / 1024, height / 768)
        
    def scale_value(self, value: float) -> int:
        """根据窗口大小缩放数值"""
        return int(value * self.scale_factor)
        
    def scale_pos(self, x: float, y: float) -> Tuple[int, int]:
        """根据窗口大小缩放位置"""
        # 使用相对位置
        return int(x * self.window_width / 1024), int(y * self.window_height / 768)
        
    def scale_font_size(self, base_size: int) -> int:
        """根据窗口大小缩放字体"""
        return max(12, int(base_size * self.scale_factor))
        
    def get_center_x(self) -> int:
        """获取窗口中心X坐标"""
        return self.window_width // 2
        
    def get_center_y(self) -> int:
        """获取窗口中心Y坐标"""
        return self.window_height // 2
        
    def get_screen_width(self) -> int:
        """获取窗口宽度"""
        return self.window_width
        
    def get_screen_height(self) -> int:
        """获取窗口高度"""
        return self.window_height
        
    def get_difficulty(self) -> int:
        """获取当前难度"""
        return self.difficulty
        
    # 子类需要实现的方法
    def handle_click(self, pos: Tuple[int, int]):
        """处理点击事件"""
        raise NotImplementedError
        
    def update(self, dt: float):
        """更新游戏状态"""
        raise NotImplementedError
        
    def draw(self, screen: pygame.Surface):
        """绘制游戏画面"""
        raise NotImplementedError
        
    def get_result(self) -> Dict:
        """获取游戏结果"""
        raise NotImplementedError