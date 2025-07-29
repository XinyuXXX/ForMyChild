#!/usr/bin/env python3
"""
表情绘制工具
"""
import pygame
import math
from typing import Tuple
from ..config import COLORS


def draw_happy_face(screen: pygame.Surface, x: int, y: int, size: int, 
                   color: Tuple[int, int, int] = None, bg_color: Tuple[int, int, int] = None):
    """
    绘制笑脸
    Args:
        screen: pygame屏幕
        x, y: 中心位置
        size: 大小
        color: 主色调，默认黄色
        bg_color: 背景色，默认白色
    """
    if color is None:
        color = (255, 215, 0)  # 金黄色
    if bg_color is None:
        bg_color = COLORS['white']
    
    # 脸的轮廓
    pygame.draw.circle(screen, color, (x, y), size)
    pygame.draw.circle(screen, bg_color, (x, y), size - 5)
    
    # 眼睛
    eye_size = size // 8
    eye_y = y - size // 4
    eye_distance = size // 3
    
    # 左眼
    pygame.draw.circle(screen, COLORS['text'], (x - eye_distance, eye_y), eye_size)
    # 右眼
    pygame.draw.circle(screen, COLORS['text'], (x + eye_distance, eye_y), eye_size)
    
    # 笑嘴 - 使用圆弧
    mouth_width = size//2
    mouth_height = size//3
    mouth_rect = pygame.Rect(x - mouth_width//2, y + size//6, mouth_width, mouth_height)
    pygame.draw.arc(screen, COLORS['text'], mouth_rect, math.pi, 2*math.pi, max(3, size//15))
    
    # 添加腮红效果
    blush_size = size // 5
    blush_y = y + size // 10
    pygame.draw.circle(screen, (255, 192, 203, 100), (x - size//2, blush_y), blush_size)
    pygame.draw.circle(screen, (255, 192, 203, 100), (x + size//2, blush_y), blush_size)


def draw_sad_face(screen: pygame.Surface, x: int, y: int, size: int,
                 color: Tuple[int, int, int] = None, bg_color: Tuple[int, int, int] = None):
    """
    绘制哭脸
    Args:
        screen: pygame屏幕
        x, y: 中心位置
        size: 大小
        color: 主色调，默认蓝色
        bg_color: 背景色，默认白色
    """
    if color is None:
        color = (135, 206, 235)  # 天蓝色
    if bg_color is None:
        bg_color = COLORS['white']
    
    # 脸的轮廓
    pygame.draw.circle(screen, color, (x, y), size)
    pygame.draw.circle(screen, bg_color, (x, y), size - 5)
    
    # 眼睛（带眼泪）
    eye_size = size // 8
    eye_y = y - size // 4
    eye_distance = size // 3
    
    # 左眼
    pygame.draw.circle(screen, COLORS['text'], (x - eye_distance, eye_y), eye_size)
    # 右眼
    pygame.draw.circle(screen, COLORS['text'], (x + eye_distance, eye_y), eye_size)
    
    # 眼泪
    tear_size = size // 10
    tear_y = eye_y + eye_size + tear_size
    # 左眼泪
    pygame.draw.circle(screen, (100, 200, 255), (x - eye_distance, tear_y), tear_size)
    pygame.draw.polygon(screen, (100, 200, 255), [
        (x - eye_distance, tear_y - tear_size),
        (x - eye_distance - tear_size, tear_y + tear_size),
        (x - eye_distance + tear_size, tear_y + tear_size)
    ])
    # 右眼泪
    pygame.draw.circle(screen, (100, 200, 255), (x + eye_distance, tear_y), tear_size)
    pygame.draw.polygon(screen, (100, 200, 255), [
        (x + eye_distance, tear_y - tear_size),
        (x + eye_distance - tear_size, tear_y + tear_size),
        (x + eye_distance + tear_size, tear_y + tear_size)
    ])
    
    # 哭嘴 - 向下的圆弧
    mouth_width = size//2
    mouth_height = size//3
    mouth_rect = pygame.Rect(x - mouth_width//2, y, mouth_width, mouth_height)
    pygame.draw.arc(screen, COLORS['text'], mouth_rect, 0, math.pi, max(3, size//15))



def draw_thinking_face(screen: pygame.Surface, x: int, y: int, size: int,
                      color: Tuple[int, int, int] = None, bg_color: Tuple[int, int, int] = None):
    """
    绘制思考表情
    Args:
        screen: pygame屏幕
        x, y: 中心位置
        size: 大小
        color: 主色调，默认橙色
        bg_color: 背景色，默认白色
    """
    if color is None:
        color = (255, 165, 0)  # 橙色
    if bg_color is None:
        bg_color = COLORS['white']
    
    # 脸的轮廓
    pygame.draw.circle(screen, color, (x, y), size)
    pygame.draw.circle(screen, bg_color, (x, y), size - 5)
    
    # 眼睛（一只眯着）
    eye_size = size // 8
    eye_y = y - size // 4
    eye_distance = size // 3
    
    # 左眼（眯着）
    pygame.draw.line(screen, COLORS['text'], 
                    (x - eye_distance - eye_size, eye_y),
                    (x - eye_distance + eye_size, eye_y), 3)
    # 右眼（睁开）
    pygame.draw.circle(screen, COLORS['text'], (x + eye_distance, eye_y), eye_size)
    
    # 嘴巴（一条线）
    mouth_y = y + size // 4
    pygame.draw.line(screen, COLORS['text'],
                    (x - size//4, mouth_y),
                    (x + size//6, mouth_y - size//8), 3)
    
    # 问号
    question_font = pygame.font.Font(None, size//2)
    question = question_font.render("?", True, COLORS['text'])
    question_rect = question.get_rect(center=(x + size, y - size//2))
    screen.blit(question, question_rect)


def draw_star_eyes_face(screen: pygame.Surface, x: int, y: int, size: int,
                       color: Tuple[int, int, int] = None, bg_color: Tuple[int, int, int] = None):
    """
    绘制星星眼表情（非常开心）
    Args:
        screen: pygame屏幕
        x, y: 中心位置
        size: 大小
        color: 主色调，默认粉色
        bg_color: 背景色，默认白色
    """
    if color is None:
        color = (255, 182, 193)  # 粉色
    if bg_color is None:
        bg_color = COLORS['white']
    
    # 脸的轮廓
    pygame.draw.circle(screen, color, (x, y), size)
    pygame.draw.circle(screen, bg_color, (x, y), size - 5)
    
    # 星星眼
    eye_y = y - size // 4
    eye_distance = size // 3
    star_size = size // 6
    
    # 左眼星星
    _draw_small_star(screen, x - eye_distance, eye_y, star_size, (255, 215, 0))
    # 右眼星星
    _draw_small_star(screen, x + eye_distance, eye_y, star_size, (255, 215, 0))
    
    # 大笑嘴
    mouth_width = size//1.5
    mouth_height = size//2.5

    mouth_rect = pygame.Rect(x - mouth_width//2, y + size//6, mouth_width, mouth_height)
    pygame.draw.arc(screen, COLORS['text'], mouth_rect, math.pi, 2*math.pi, max(3, size//15))
    

    # 添加光晕效果
    for i in range(3):
        alpha = 50 - i * 15
        halo_size = size + i * 10
        halo_surf = pygame.Surface((halo_size * 2, halo_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(halo_surf, (*color, alpha), (halo_size, halo_size), halo_size)
        screen.blit(halo_surf, (x - halo_size, y - halo_size))


def _draw_small_star(screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int]):
    """绘制小星星"""
    points = []
    for i in range(10):
        angle = math.pi * i / 5 - math.pi / 2
        if i % 2 == 0:
            radius = size
        else:
            radius = size * 0.5
        px = x + radius * math.cos(angle)
        py = y + radius * math.sin(angle)
        points.append((px, py))
    pygame.draw.polygon(screen, color, points)