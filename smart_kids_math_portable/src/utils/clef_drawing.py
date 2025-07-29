#!/usr/bin/env python3
"""
标准音乐谱号绘制函数
"""
import pygame
import math
from typing import Tuple


def draw_treble_clef(screen: pygame.Surface, x: int, y: int, color: Tuple[int, int, int], scale: float = 1.0):
    """
    绘制标准高音谱号（G谱号）
    x, y: 谱号中心位置（第二线）
    """
    # 调整坐标使y对准第二线
    base_x = x - 10 * scale
    base_y = y
    
    # 绘制主要的螺旋部分
    points = []
    
    # 底部圆圈
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        px = base_x + 15 * scale * math.cos(rad)
        py = base_y + 40 * scale + 15 * scale * math.sin(rad)
        points.append((int(px), int(py)))
    
    # 向上的主干
    for t in range(0, 100):
        progress = t / 100.0
        px = base_x + 5 * scale * math.sin(progress * math.pi * 2)
        py = base_y + 40 * scale - progress * 90 * scale
        points.append((int(px), int(py)))
    
    # 绘制曲线
    if len(points) > 2:
        pygame.draw.lines(screen, color, False, points, max(2, int(3 * scale)))
    
    # 中心的小圆圈（标记G音）
    pygame.draw.circle(screen, color, (int(base_x), int(base_y)), int(8 * scale), max(2, int(2 * scale)))
    
    # 顶部装饰
    top_y = base_y - 50 * scale
    pygame.draw.arc(screen, color, 
                   pygame.Rect(int(base_x - 10 * scale), int(top_y), 
                              int(20 * scale), int(15 * scale)), 
                   0, math.pi, max(2, int(3 * scale)))


def draw_bass_clef(screen: pygame.Surface, x: int, y: int, color: Tuple[int, int, int], scale: float = 1.0):
    """
    绘制标准低音谱号（F谱号）
    x, y: 谱号中心位置（第四线）
    """
    # 调整坐标使y对准第四线
    base_x = x - 20 * scale
    base_y = y
    
    # 绘制主体弧形
    # F谱号的主要部分是一个大的弧形
    arc_rect = pygame.Rect(int(base_x), int(base_y - 30 * scale), 
                          int(30 * scale), int(60 * scale))
    pygame.draw.arc(screen, color, arc_rect, -math.pi/2, math.pi/2, max(3, int(4 * scale)))
    
    # 绘制两个点（标记F音位置）
    dot_x = base_x + 40 * scale
    # 第一个点在第四线上方
    pygame.draw.circle(screen, color, (int(dot_x), int(base_y - 12 * scale)), int(4 * scale))
    # 第二个点在第四线下方
    pygame.draw.circle(screen, color, (int(dot_x), int(base_y + 12 * scale)), int(4 * scale))
    
    # 顶部的小弧
    top_arc_rect = pygame.Rect(int(base_x + 25 * scale), int(base_y - 35 * scale),
                               int(15 * scale), int(10 * scale))
    pygame.draw.arc(screen, color, top_arc_rect, 0, math.pi, max(2, int(2 * scale)))


def draw_alto_clef(screen: pygame.Surface, x: int, y: int, color: Tuple[int, int, int], scale: float = 1.0):
    """
    绘制中音谱号（C谱号）
    x, y: 谱号中心位置（第三线）
    """
    base_x = x - 15 * scale
    base_y = y
    
    # 绘制两条垂直线
    line_width = max(2, int(3 * scale))
    # 左边粗线
    pygame.draw.line(screen, color,
                    (int(base_x), int(base_y - 40 * scale)),
                    (int(base_x), int(base_y + 40 * scale)), 
                    int(line_width * 1.5))
    # 右边细线
    pygame.draw.line(screen, color,
                    (int(base_x + 8 * scale), int(base_y - 40 * scale)),
                    (int(base_x + 8 * scale), int(base_y + 40 * scale)), 
                    line_width)
    
    # 绘制两个弧形
    # 上弧
    pygame.draw.arc(screen, color,
                   pygame.Rect(int(base_x + 8 * scale), int(base_y - 25 * scale),
                              int(20 * scale), int(25 * scale)),
                   -math.pi/2, math.pi/2, line_width)
    # 下弧
    pygame.draw.arc(screen, color,
                   pygame.Rect(int(base_x + 8 * scale), int(base_y),
                              int(20 * scale), int(25 * scale)),
                   -math.pi/2, math.pi/2, line_width)