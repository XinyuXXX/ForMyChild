#!/usr/bin/env python3
"""
玩家名字输入界面
"""
import pygame
import math
from typing import Optional
from ..config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak
from ..utils.ui_utils import SpeakerButton


class NameInputScreen:
    """名字输入界面"""
    
    def __init__(self):
        self.name = ""
        self.cursor_visible = True
        self.cursor_timer = 0
        self.max_name_length = 8
        self.done = False
        
        # 创建输入框
        self.input_box = pygame.Rect(WINDOW_WIDTH//2 - 200, WINDOW_HEIGHT//2 - 30, 400, 60)
        
        # 创建确认按钮
        self.confirm_button = pygame.Rect(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 60, 200, 50)
        self.confirm_hover = False
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 播放欢迎语音
        speak("请输入你的名字，小朋友！")
        
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """处理事件，返回确认的名字或None"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查喇叭按钮
            for button, text in self.speaker_buttons:
                if button.check_click(event.pos):
                    speak(text)
                    return None
            
            # 检查确认按钮
            if self.confirm_button.collidepoint(event.pos) and self.name:
                speak(f"欢迎{self.name}小朋友！让我们开始游戏吧！")
                return self.name
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.name:
                # 回车确认
                speak(f"欢迎{self.name}小朋友！让我们开始游戏吧！")
                return self.name
            elif event.key == pygame.K_BACKSPACE:
                # 删除字符
                self.name = self.name[:-1]
            else:
                # 添加字符
                if len(self.name) < self.max_name_length:
                    # 支持中文输入
                    if event.unicode and event.unicode.isprintable():
                        self.name += event.unicode
                        
        return None
    
    def update(self, dt: float):
        """更新界面状态"""
        # 更新光标闪烁
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
            
        # 更新按钮悬停状态
        mouse_pos = pygame.mouse.get_pos()
        self.confirm_hover = self.confirm_button.collidepoint(mouse_pos)
        
        # 更新喇叭按钮
        for button, _ in self.speaker_buttons:
            button.update(mouse_pos)
    
    def draw(self, screen: pygame.Surface):
        """绘制界面"""
        screen.fill(COLORS['background'])
        
        # 清空喇叭按钮列表
        self.speaker_buttons.clear()
        
        # 绘制标题
        title_font = get_chinese_font(64)
        title = "请告诉我你的名字"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 150))
        screen.blit(title_surf, title_rect)
        
        # 在标题旁添加喇叭按钮
        speaker_btn = SpeakerButton(WINDOW_WIDTH//2 + title_surf.get_width()//2 + 50, WINDOW_HEIGHT//2 - 150, 30)
        speaker_btn.draw(screen)
        self.speaker_buttons.append((speaker_btn, "请输入你的名字，小朋友！"))
        
        # 绘制提示文字
        hint_font = get_chinese_font(32)
        hint = "使用拼音或中文输入你的名字"
        hint_surf = hint_font.render(hint, True, COLORS['secondary'])
        hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 80))
        screen.blit(hint_surf, hint_rect)
        
        # 绘制输入框
        pygame.draw.rect(screen, COLORS['white'], self.input_box)
        pygame.draw.rect(screen, COLORS['primary'], self.input_box, 3, border_radius=10)
        
        # 绘制输入的名字
        if self.name:
            name_font = get_chinese_font(48)
            name_surf = name_font.render(self.name, True, COLORS['text'])
            name_rect = name_surf.get_rect(center=self.input_box.center)
            screen.blit(name_surf, name_rect)
            
            # 绘制光标
            if self.cursor_visible:
                cursor_x = name_rect.right + 5
                cursor_y1 = self.input_box.y + 10
                cursor_y2 = self.input_box.y + self.input_box.height - 10
                pygame.draw.line(screen, COLORS['text'], (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
        else:
            # 显示占位符
            placeholder_font = get_chinese_font(36)
            placeholder = "在这里输入..."
            placeholder_surf = placeholder_font.render(placeholder, True, COLORS['light_gray'])
            placeholder_rect = placeholder_surf.get_rect(center=self.input_box.center)
            screen.blit(placeholder_surf, placeholder_rect)
            
            # 绘制光标
            if self.cursor_visible:
                cursor_x = self.input_box.x + 20
                cursor_y1 = self.input_box.y + 10
                cursor_y2 = self.input_box.y + self.input_box.height - 10
                pygame.draw.line(screen, COLORS['text'], (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
        
        # 绘制确认按钮
        if self.name:
            button_color = COLORS['success'] if self.confirm_hover else COLORS['primary']
            pygame.draw.rect(screen, button_color, self.confirm_button, border_radius=25)
            
            confirm_font = get_chinese_font(32)
            confirm_text = "开始游戏"
            confirm_surf = confirm_font.render(confirm_text, True, COLORS['white'])
            confirm_rect = confirm_surf.get_rect(center=self.confirm_button.center)
            screen.blit(confirm_surf, confirm_rect)
        
        # 绘制装饰
        self._draw_decorations(screen)
        
        # 绘制所有喇叭按钮
        for button, _ in self.speaker_buttons:
            button.draw(screen)
    
    def _draw_decorations(self, screen: pygame.Surface):
        """绘制装饰性元素"""
        # 左上角的笑脸
        self._draw_smiley(screen, 100, 100, 60, COLORS['primary'])
        
        # 右上角的星星
        self._draw_star(screen, WINDOW_WIDTH - 100, 100, 30, COLORS['accent'])
        
        # 左下角的心形
        self._draw_heart(screen, 100, WINDOW_HEIGHT - 100, 40, (255, 105, 180))
        
        # 右下角的花朵
        self._draw_flower(screen, WINDOW_WIDTH - 100, WINDOW_HEIGHT - 100, 40)
    
    def _draw_smiley(self, screen: pygame.Surface, x: int, y: int, size: int, color):
        """绘制笑脸"""
        # 脸
        pygame.draw.circle(screen, color, (x, y), size)
        pygame.draw.circle(screen, COLORS['white'], (x, y), size - 5)
        
        # 眼睛
        eye_y = y - size//4
        pygame.draw.circle(screen, COLORS['text'], (x - size//3, eye_y), size//8)
        pygame.draw.circle(screen, COLORS['text'], (x + size//3, eye_y), size//8)
        
        # 笑嘴
        mouth_rect = pygame.Rect(x - size//3, y, size//1.5, size//2)
        pygame.draw.arc(screen, COLORS['text'], mouth_rect, math.pi/6, 5*math.pi/6, 3)
    
    def _draw_star(self, screen: pygame.Surface, x: int, y: int, size: int, color):
        """绘制星星"""
        import math
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
    
    def _draw_heart(self, screen: pygame.Surface, x: int, y: int, size: int, color):
        """绘制心形"""
        # 两个圆形
        pygame.draw.circle(screen, color, (x - size//4, y - size//4), size//3)
        pygame.draw.circle(screen, color, (x + size//4, y - size//4), size//3)
        # 三角形
        points = [
            (x - size//2, y),
            (x, y + size//2),
            (x + size//2, y)
        ]
        pygame.draw.polygon(screen, color, points)
    
    def _draw_flower(self, screen: pygame.Surface, x: int, y: int, size: int):
        """绘制花朵"""
        # 花瓣
        import math
        for i in range(5):
            angle = i * math.pi * 2 / 5
            petal_x = x + size//2 * math.cos(angle)
            petal_y = y + size//2 * math.sin(angle)
            pygame.draw.circle(screen, (255, 192, 203), (int(petal_x), int(petal_y)), size//3)
        # 花心
        pygame.draw.circle(screen, (255, 255, 0), (x, y), size//4)