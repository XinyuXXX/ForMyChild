#!/usr/bin/env python3
"""
UI工具函数
"""
import pygame
from typing import Tuple, Optional
from ..config import COLORS


class SpeakerButton:
    """喇叭按钮类"""
    
    def __init__(self, x: int, y: int, size: int = 30):
        """
        初始化喇叭按钮
        Args:
            x: 中心X坐标
            y: 中心Y坐标
            size: 按钮大小
        """
        self.x = x
        self.y = y
        self.size = size
        self.rect = pygame.Rect(x - size//2, y - size//2, size, size)
        self.hover = False
        self.is_playing = False
        
    def update(self, mouse_pos: Tuple[int, int]):
        """更新按钮状态"""
        self.hover = self.rect.collidepoint(mouse_pos)
        
    def draw(self, screen: pygame.Surface):
        """绘制喇叭图标"""
        # 背景圆圈
        bg_color = COLORS['primary'] if self.hover else COLORS['secondary']
        if self.is_playing:
            bg_color = COLORS['success']
            
        pygame.draw.circle(screen, bg_color, (self.x, self.y), self.size//2)
        pygame.draw.circle(screen, COLORS['white'], (self.x, self.y), self.size//2 - 2)
        
        # 喇叭主体
        speaker_color = bg_color
        
        # 喇叭锥形部分
        cone_points = [
            (self.x - self.size//4, self.y - self.size//6),
            (self.x - self.size//4, self.y + self.size//6),
            (self.x, self.y + self.size//4),
            (self.x, self.y - self.size//4)
        ]
        pygame.draw.polygon(screen, speaker_color, cone_points)
        
        # 喇叭口
        rect = pygame.Rect(self.x - self.size//3, self.y - self.size//6, 
                          self.size//6, self.size//3)
        pygame.draw.rect(screen, speaker_color, rect)
        
        # 声波（如果正在播放）
        if self.is_playing or self.hover:
            for i in range(3):
                x_offset = self.x + self.size//4 + i * 4
                y_start = self.y - 3 - i * 2
                y_end = self.y + 3 + i * 2
                pygame.draw.line(screen, speaker_color, 
                               (x_offset, y_start), (x_offset, y_end), 2)
    
    def check_click(self, pos: Tuple[int, int]) -> bool:
        """检查是否被点击"""
        return self.rect.collidepoint(pos)


def draw_speaker_icon(screen: pygame.Surface, x: int, y: int, size: int = 20, 
                     color: Optional[Tuple[int, int, int]] = None, active: bool = False):
    """
    绘制简单的喇叭图标
    Args:
        screen: pygame屏幕
        x, y: 图标中心位置
        size: 图标大小
        color: 颜色，默认使用primary色
        active: 是否处于激活状态（显示声波）
    """
    if color is None:
        color = COLORS['primary']
    
    # 喇叭锥形部分
    cone_points = [
        (x - size//2, y - size//3),
        (x - size//2, y + size//3),
        (x - size//6, y + size//2),
        (x - size//6, y - size//2)
    ]
    pygame.draw.polygon(screen, color, cone_points)
    
    # 喇叭口
    rect = pygame.Rect(x - size//2 - size//4, y - size//3, size//4, size//3 * 2)
    pygame.draw.rect(screen, color, rect)
    
    # 声波
    if active:
        for i in range(3):
            arc_size = size + i * 8
            arc_rect = pygame.Rect(x - arc_size//2, y - arc_size//2, arc_size, arc_size)
            pygame.draw.arc(screen, color, arc_rect, -0.5, 0.5, 2)
            pygame.draw.arc(screen, color, arc_rect, 2.6, 3.6, 2)