#!/usr/bin/env python3
"""
画画教学游戏
帮助4岁儿童提高观察力和绘画能力
"""
import pygame
import math
import os
from typing import List, Dict, Tuple, Optional, Callable
from ..config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, IMAGES_PATH
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak, stop_speaking, is_speaking
from ..utils.ui_utils import SpeakerButton
from ..utils.emoji_utils import draw_happy_face, draw_star_eyes_face
from .base_game import BaseGame


class DrawingStep:
    """绘画步骤"""
    def __init__(self, description: str, draw_func: Callable, duration: float = 2.0):
        self.description = description  # 步骤描述
        self.draw_func = draw_func      # 绘制函数
        self.duration = duration        # 动画持续时间
        self.progress = 0.0            # 当前进度 (0-1)
        
    def update(self, dt: float):
        """更新步骤进度"""
        if self.progress < 1.0:
            self.progress = min(1.0, self.progress + dt / self.duration)
            
    def reset(self):
        """重置步骤"""
        self.progress = 0.0


class DrawingTutorial:
    """绘画教程"""
    def __init__(self, name: str, category: str, difficulty: int):
        self.name = name
        self.category = category  # 动物、人物、物品、自然、场景、故事
        self.difficulty = difficulty
        self.steps: List[DrawingStep] = []
        self.real_image_path = None
        self.colors = []
        
    def add_step(self, description: str, draw_func: Callable, duration: float = 2.0):
        """添加绘画步骤"""
        self.steps.append(DrawingStep(description, draw_func, duration))


class DrawingTutorialGame(BaseGame):
    """画画教学游戏"""
    
    def __init__(self, difficulty: int = 1):
        super().__init__(difficulty)
        
        # 游戏状态
        self.current_tutorial = None
        self.current_step = 0
        self.is_paused = True  # 默认暂停，等待用户操作
        self.show_real_image = True
        self.show_simple_drawing = False
        self.show_steps = False
        self.game_phase = 'real_image'  # real_image, simple_drawing, steps, complete
        
        # 教程库
        self.tutorials = self._create_tutorials()
        
        # 选择当前教程
        self._select_tutorial()
        
        # UI元素
        self.pause_button = None
        self.next_button = None
        self.prev_button = None
        self.restart_button = None
        self.ui_buttons_created = False  # 标记是否已创建按钮
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 反馈
        self.show_complete_feedback = False
        self.feedback_timer = 0
        
        # 播放欢迎语音
        speak("欢迎来到画画教学！我们一起来学画画吧！")
        
    def _create_tutorials(self) -> List[DrawingTutorial]:
        """创建教程库"""
        tutorials = []
        
        # 难度1：简单的圆形太阳
        if self.difficulty <= 2:
            sun_tutorial = DrawingTutorial("太阳", "自然", 1)
            sun_tutorial.colors = [(255, 215, 0)]  # 金黄色
            
            def draw_sun_circle(screen, x, y, progress):
                # 画圆形
                if progress > 0:
                    radius = int(50 * progress)
                    pygame.draw.circle(screen, (255, 215, 0), (x, y), radius, 3)
                    if progress >= 1.0:
                        pygame.draw.circle(screen, (255, 215, 0), (x, y), 50)
                        
            def draw_sun_rays(screen, x, y, progress):
                # 画光线
                if progress > 0:
                    for i in range(8):
                        angle = i * math.pi / 4
                        if i / 8 <= progress:
                            start_x = x + 60 * math.cos(angle)
                            start_y = y + 60 * math.sin(angle)
                            end_x = x + 80 * math.cos(angle)
                            end_y = y + 80 * math.sin(angle)
                            pygame.draw.line(screen, (255, 215, 0), 
                                           (int(start_x), int(start_y)), 
                                           (int(end_x), int(end_y)), 3)
                            
            sun_tutorial.add_step("画一个圆圈", lambda s, x, y, p: draw_sun_circle(s, x, y, p), 2.0)
            sun_tutorial.add_step("加上光芒", lambda s, x, y, p: draw_sun_rays(s, x, y, p), 3.0)
            tutorials.append(sun_tutorial)
            
        # 难度2-3：简单的房子
        if 2 <= self.difficulty <= 4:
            house_tutorial = DrawingTutorial("房子", "物品", 2)
            house_tutorial.colors = [(139, 69, 19), (255, 0, 0)]  # 棕色和红色
            
            def draw_house_base(screen, x, y, progress):
                # 画房子主体（正方形）
                if progress > 0:
                    size = int(80 * progress)
                    rect = pygame.Rect(x - size//2, y - size//2 + 20, size, size)
                    pygame.draw.rect(screen, (139, 69, 19), rect, 3)
                    if progress >= 1.0:
                        pygame.draw.rect(screen, (139, 69, 19), rect)
                        
            def draw_house_roof(screen, x, y, progress):
                # 画屋顶（三角形）
                if progress > 0:
                    points = [
                        (x, y - 60),
                        (x - 50, y - 20),
                        (x + 50, y - 20)
                    ]
                    if progress < 1.0:
                        # 逐步画线
                        if progress > 0.33:
                            pygame.draw.line(screen, (255, 0, 0), points[0], points[1], 3)
                        if progress > 0.66:
                            pygame.draw.line(screen, (255, 0, 0), points[1], points[2], 3)
                        if progress > 0.99:
                            pygame.draw.line(screen, (255, 0, 0), points[2], points[0], 3)
                    else:
                        pygame.draw.polygon(screen, (255, 0, 0), points)
                        
            def draw_house_door(screen, x, y, progress):
                # 画门
                if progress > 0:
                    door_height = int(30 * progress)
                    door_rect = pygame.Rect(x - 15, y + 60 - door_height, 30, door_height)
                    pygame.draw.rect(screen, (101, 67, 33), door_rect)
                    
            house_tutorial.add_step("画一个正方形作为房子", lambda s, x, y, p: draw_house_base(s, x, y, p), 2.0)
            house_tutorial.add_step("画三角形屋顶", lambda s, x, y, p: draw_house_roof(s, x, y, p), 3.0)
            house_tutorial.add_step("加上门", lambda s, x, y, p: draw_house_door(s, x, y, p), 2.0)
            tutorials.append(house_tutorial)
            
        # 难度3-5：简单的笑脸
        if 3 <= self.difficulty <= 5:
            face_tutorial = DrawingTutorial("笑脸", "人物", 3)
            face_tutorial.colors = [(255, 220, 177), (0, 0, 0), (255, 0, 0)]
            
            def draw_face_circle(screen, x, y, progress):
                # 画脸的圆形
                if progress > 0:
                    radius = int(60 * progress)
                    pygame.draw.circle(screen, (255, 220, 177), (x, y), radius, 3)
                    if progress >= 1.0:
                        pygame.draw.circle(screen, (255, 220, 177), (x, y), 60)
                        
            def draw_face_eyes(screen, x, y, progress):
                # 画眼睛
                if progress > 0:
                    eye_radius = int(8 * progress)
                    if progress > 0.5:
                        pygame.draw.circle(screen, (0, 0, 0), (x - 20, y - 10), eye_radius)
                    if progress >= 1.0:
                        pygame.draw.circle(screen, (0, 0, 0), (x + 20, y - 10), eye_radius)
                        
            def draw_face_smile(screen, x, y, progress):
                # 画笑容
                if progress > 0:
                    # 使用贝塞尔曲线或弧线画笑脸
                    angle_start = math.pi * 0.2
                    angle_end = math.pi * 0.8
                    angle = angle_start + (angle_end - angle_start) * progress
                    points = []
                    for i in range(int(20 * progress)):
                        t = i / 19 if progress >= 1.0 else i / max(1, int(20 * progress) - 1)
                        current_angle = angle_start + (angle - angle_start) * t
                        px = x + 30 * math.cos(current_angle)
                        py = y + 30 * math.sin(current_angle)
                        points.append((int(px), int(py)))
                    if len(points) > 1:
                        pygame.draw.lines(screen, (255, 0, 0), False, points, 3)
                        
            face_tutorial.add_step("画一个大圆作为脸", lambda s, x, y, p: draw_face_circle(s, x, y, p), 2.0)
            face_tutorial.add_step("画两个小圆作为眼睛", lambda s, x, y, p: draw_face_eyes(s, x, y, p), 2.0)
            face_tutorial.add_step("画一个弧线作为笑脸", lambda s, x, y, p: draw_face_smile(s, x, y, p), 2.0)
            tutorials.append(face_tutorial)
            
        # 难度4-6：小猫
        if 4 <= self.difficulty <= 6:
            cat_tutorial = DrawingTutorial("小猫", "动物", 4)
            cat_tutorial.colors = [(255, 165, 0), (0, 0, 0), (255, 192, 203)]
            
            def draw_cat_head(screen, x, y, progress):
                # 画猫头（圆形）
                if progress > 0:
                    radius = int(50 * progress)
                    pygame.draw.circle(screen, (255, 165, 0), (x, y), radius, 3)
                    if progress >= 1.0:
                        pygame.draw.circle(screen, (255, 165, 0), (x, y), 50)
                        
            def draw_cat_ears(screen, x, y, progress):
                # 画猫耳朵
                if progress > 0:
                    # 左耳
                    if progress > 0.5:
                        left_ear = [
                            (x - 40, y - 30),
                            (x - 50, y - 60),
                            (x - 20, y - 45)
                        ]
                        pygame.draw.polygon(screen, (255, 165, 0), left_ear)
                    # 右耳
                    if progress >= 1.0:
                        right_ear = [
                            (x + 40, y - 30),
                            (x + 50, y - 60),
                            (x + 20, y - 45)
                        ]
                        pygame.draw.polygon(screen, (255, 165, 0), right_ear)
                        
            def draw_cat_face_features(screen, x, y, progress):
                # 画猫的五官
                if progress > 0:
                    # 眼睛
                    if progress > 0.3:
                        pygame.draw.circle(screen, (0, 0, 0), (x - 15, y - 5), 5)
                        pygame.draw.circle(screen, (0, 0, 0), (x + 15, y - 5), 5)
                    # 鼻子
                    if progress > 0.6:
                        pygame.draw.polygon(screen, (255, 192, 203), 
                                          [(x, y + 5), (x - 5, y - 2), (x + 5, y - 2)])
                    # 嘴巴
                    if progress >= 1.0:
                        pygame.draw.arc(screen, (0, 0, 0), 
                                      pygame.Rect(x - 15, y, 15, 15), 
                                      0, math.pi, 2)
                        pygame.draw.arc(screen, (0, 0, 0), 
                                      pygame.Rect(x, y, 15, 15), 
                                      0, math.pi, 2)
                                      
            cat_tutorial.add_step("画一个圆作为猫头", lambda s, x, y, p: draw_cat_head(s, x, y, p), 2.0)
            cat_tutorial.add_step("加上三角形耳朵", lambda s, x, y, p: draw_cat_ears(s, x, y, p), 2.0)
            cat_tutorial.add_step("画上眼睛鼻子和嘴巴", lambda s, x, y, p: draw_cat_face_features(s, x, y, p), 3.0)
            tutorials.append(cat_tutorial)
            
        # 难度5-7：小树
        if 5 <= self.difficulty <= 7:
            tree_tutorial = DrawingTutorial("小树", "自然", 5)
            tree_tutorial.colors = [(139, 69, 19), (34, 139, 34)]
            
            def draw_tree_trunk(screen, x, y, progress):
                # 画树干
                if progress > 0:
                    trunk_height = int(60 * progress)
                    trunk_rect = pygame.Rect(x - 15, y, 30, trunk_height)
                    pygame.draw.rect(screen, (139, 69, 19), trunk_rect)
                    
            def draw_tree_leaves(screen, x, y, progress):
                # 画树叶（三个圆形组成树冠）
                if progress > 0:
                    # 底部圆
                    if progress > 0.33:
                        pygame.draw.circle(screen, (34, 139, 34), (x, y - 20), 35)
                    # 左圆
                    if progress > 0.66:
                        pygame.draw.circle(screen, (34, 139, 34), (x - 25, y - 40), 30)
                    # 右圆
                    if progress >= 1.0:
                        pygame.draw.circle(screen, (34, 139, 34), (x + 25, y - 40), 30)
                        
            tree_tutorial.add_step("画树干", lambda s, x, y, p: draw_tree_trunk(s, x, y, p), 2.0)
            tree_tutorial.add_step("画树冠", lambda s, x, y, p: draw_tree_leaves(s, x, y, p), 3.0)
            tutorials.append(tree_tutorial)
            
        # 难度6以上：简单场景
        if self.difficulty >= 6:
            scene_tutorial = DrawingTutorial("公园场景", "场景", 6)
            scene_tutorial.colors = [(135, 206, 235), (34, 139, 34), (255, 215, 0)]
            
            def draw_scene_sky(screen, x, y, progress):
                # 画天空背景
                if progress > 0:
                    sky_height = int(200 * progress)
                    sky_rect = pygame.Rect(x - 150, y - 150, 300, sky_height)
                    pygame.draw.rect(screen, (135, 206, 235), sky_rect)
                    
            def draw_scene_ground(screen, x, y, progress):
                # 画地面
                if progress > 0:
                    ground_height = int(100 * progress)
                    ground_rect = pygame.Rect(x - 150, y + 50, 300, ground_height)
                    pygame.draw.rect(screen, (34, 139, 34), ground_rect)
                    
            def draw_scene_sun(screen, x, y, progress):
                # 画太阳
                if progress > 0:
                    sun_radius = int(30 * progress)
                    pygame.draw.circle(screen, (255, 215, 0), (x + 100, y - 100), sun_radius)
                    
            scene_tutorial.add_step("画蓝色天空", lambda s, x, y, p: draw_scene_sky(s, x, y, p), 2.0)
            scene_tutorial.add_step("画绿色草地", lambda s, x, y, p: draw_scene_ground(s, x, y, p), 2.0)
            scene_tutorial.add_step("加上太阳", lambda s, x, y, p: draw_scene_sun(s, x, y, p), 2.0)
            tutorials.append(scene_tutorial)
            
        return tutorials
        
    def _select_tutorial(self):
        """根据难度选择教程"""
        suitable_tutorials = [t for t in self.tutorials if t.difficulty <= self.difficulty]
        if suitable_tutorials:
            import random
            self.current_tutorial = random.choice(suitable_tutorials)
            self.current_step = 0
            # 重置所有步骤
            for step in self.current_tutorial.steps:
                step.reset()
                
    def _create_ui_buttons(self):
        """创建UI按钮"""
        if self.ui_buttons_created:
            return  # 如果已经创建过，就不再创建
            
        button_y = self.window_height - self.scale_value(80)
        button_width = self.scale_value(100)
        button_height = self.scale_value(50)
        spacing = self.scale_value(20)
        
        # 计算按钮位置
        total_width = 4 * button_width + 3 * spacing
        start_x = (self.window_width - total_width) // 2
        
        # 暂停/继续按钮
        self.pause_button = pygame.Rect(start_x, button_y, button_width, button_height)
        
        # 上一步按钮
        self.prev_button = pygame.Rect(start_x + button_width + spacing, button_y, 
                                       button_width, button_height)
        
        # 下一步按钮
        self.next_button = pygame.Rect(start_x + 2 * (button_width + spacing), button_y, 
                                       button_width, button_height)
        
        # 重新开始按钮
        self.restart_button = pygame.Rect(start_x + 3 * (button_width + spacing), button_y, 
                                         button_width, button_height)
                                         
        self.ui_buttons_created = True  # 标记已创建
                                         
    def handle_click(self, pos: Tuple[int, int]):
        """处理点击事件"""
        # 检查喇叭按钮
        for button, text in self.speaker_buttons:
            if button.check_click(pos):
                speak(text)
                return
                
        # 在不同阶段处理不同的点击
        if self.game_phase == 'real_image':
            # 点击任意位置进入下一阶段
            self.game_phase = 'simple_drawing'
            speak("这是简笔画的样子")
        elif self.game_phase == 'simple_drawing':
            # 点击进入步骤教学
            self.game_phase = 'steps'
            self.is_paused = True
            speak(f"现在让我们一步一步学习画{self.current_tutorial.name}")
        elif self.game_phase == 'steps':
            # 检查UI按钮
            if self.pause_button and self.pause_button.collidepoint(pos):
                self.is_paused = not self.is_paused
                if self.is_paused:
                    speak("已暂停，请跟着画")
                else:
                    speak("继续播放")
            elif self.prev_button and self.prev_button.collidepoint(pos):
                if self.current_step > 0:
                    self.current_step -= 1
                    self.current_tutorial.steps[self.current_step].reset()
                    speak(self.current_tutorial.steps[self.current_step].description)
            elif self.next_button and self.next_button.collidepoint(pos):
                if self.current_step < len(self.current_tutorial.steps) - 1:
                    self.current_step += 1
                    if self.current_step < len(self.current_tutorial.steps):
                        speak(self.current_tutorial.steps[self.current_step].description)
                elif self.current_step == len(self.current_tutorial.steps) - 1:
                    # 最后一步，直接完成当前步骤并进入完成阶段
                    self.current_tutorial.steps[self.current_step].progress = 1.0
                    self.game_phase = 'complete'
                    self.show_complete_feedback = True
                    speak(f"太棒了！你学会了画{self.current_tutorial.name}！")
            elif self.restart_button and self.restart_button.collidepoint(pos):
                self.current_step = 0
                for step in self.current_tutorial.steps:
                    step.reset()
                speak("让我们重新开始")
        elif self.game_phase == 'complete':
            # 完成后点击选择新教程
            self._select_tutorial()
            self.game_phase = 'real_image'
            self.show_complete_feedback = False
            speak(f"让我们来学画{self.current_tutorial.name}")
                    
    def update(self, dt: float):
        """更新游戏状态"""
        # 更新当前步骤动画
        if self.game_phase == 'steps' and not self.is_paused:
            if self.current_step < len(self.current_tutorial.steps):
                current = self.current_tutorial.steps[self.current_step]
                current.update(dt)
                
                # 自动进入下一步
                if current.progress >= 1.0 and self.current_step < len(self.current_tutorial.steps) - 1:
                    self.current_step += 1
                    speak(self.current_tutorial.steps[self.current_step].description)
                    
        # 更新反馈计时器
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            
        # 更新喇叭按钮
        mouse_pos = pygame.mouse.get_pos()
        for button, _ in self.speaker_buttons:
            button.update(mouse_pos)
            
    def draw(self, screen: pygame.Surface):
        """绘制游戏画面"""
        screen.fill(COLORS['background'])
        
        # 清空喇叭按钮列表
        self.speaker_buttons.clear()
        
        # 绘制标题
        title_font = get_chinese_font(self.scale_font_size(48))
        title = f"学画画 - {self.current_tutorial.name}"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(self.get_center_x(), self.scale_value(50)))
        screen.blit(title_surf, title_rect)
        
        # 添加喇叭按钮
        speaker_btn = SpeakerButton(
            self.get_center_x() + title_surf.get_width()//2 + self.scale_value(50),
            self.scale_value(50),
            self.scale_value(25)
        )
        speaker_btn.draw(screen)
        self.speaker_buttons.append((speaker_btn, f"让我们来学画{self.current_tutorial.name}"))
        
        # 根据游戏阶段绘制不同内容
        center_x = self.get_center_x()
        center_y = self.get_center_y()
        
        if self.game_phase == 'real_image':
            # 显示真实物品（这里用文字代替，实际可以加载图片）
            self._draw_real_object(screen, center_x, center_y)
            
            # 提示文字
            hint_font = get_chinese_font(self.scale_font_size(24))
            hint_text = "点击查看简笔画"
            hint_surf = hint_font.render(hint_text, True, COLORS['secondary'])
            hint_rect = hint_surf.get_rect(center=(center_x, center_y + self.scale_value(150)))
            screen.blit(hint_surf, hint_rect)
            
        elif self.game_phase == 'simple_drawing':
            # 显示完整的简笔画
            self._draw_complete_drawing(screen, center_x, center_y)
            
            # 显示使用的颜色
            self._draw_color_palette(screen)
            
            # 提示文字
            hint_font = get_chinese_font(self.scale_font_size(24))
            hint_text = "点击开始学习步骤"
            hint_surf = hint_font.render(hint_text, True, COLORS['secondary'])
            hint_rect = hint_surf.get_rect(center=(center_x, center_y + self.scale_value(150)))
            screen.blit(hint_surf, hint_rect)
            
        elif self.game_phase == 'steps':
            # 显示步骤教学
            self._draw_step_by_step(screen, center_x, center_y)
            
            # 绘制UI按钮
            self._create_ui_buttons()
            self._draw_ui_buttons(screen)
            
            # 显示当前步骤说明
            if self.current_step < len(self.current_tutorial.steps):
                step_font = get_chinese_font(self.scale_font_size(32))
                step_text = self.current_tutorial.steps[self.current_step].description
                step_surf = step_font.render(step_text, True, COLORS['primary'])
                step_rect = step_surf.get_rect(center=(center_x, self.scale_value(120)))
                screen.blit(step_surf, step_rect)
                
                # 步骤进度
                progress_text = f"步骤 {self.current_step + 1}/{len(self.current_tutorial.steps)}"
                progress_surf = step_font.render(progress_text, True, COLORS['text'])
                progress_rect = progress_surf.get_rect(topright=(self.window_width - self.scale_value(20), 
                                                                 self.scale_value(20)))
                screen.blit(progress_surf, progress_rect)
                
        elif self.game_phase == 'complete':
            # 显示完成画面
            self._draw_complete_drawing(screen, center_x, center_y)
            
            # 显示庆祝
            if self.show_complete_feedback:
                draw_star_eyes_face(screen, center_x, center_y - self.scale_value(150), 
                                   self.scale_value(100))
                
                complete_font = get_chinese_font(self.scale_font_size(48))
                complete_text = "太棒了！"
                complete_surf = complete_font.render(complete_text, True, COLORS['success'])
                complete_rect = complete_surf.get_rect(center=(center_x, center_y + self.scale_value(150)))
                screen.blit(complete_surf, complete_rect)
                
                hint_font = get_chinese_font(self.scale_font_size(24))
                hint_text = "点击学习新的画画"
                hint_surf = hint_font.render(hint_text, True, COLORS['secondary'])
                hint_rect = hint_surf.get_rect(center=(center_x, center_y + self.scale_value(200)))
                screen.blit(hint_surf, hint_rect)
                
        # 绘制所有喇叭按钮
        for button, _ in self.speaker_buttons:
            button.draw(screen)
            
    def _draw_real_object(self, screen: pygame.Surface, x: int, y: int):
        """绘制真实物品（示意）"""
        # 这里用简单图形代表真实物品
        # 实际应用中可以加载真实照片
        if self.current_tutorial.name == "太阳":
            # 画一个渐变的太阳
            for i in range(60, 0, -2):
                color = (255, 255 - (60-i)*2, 0)
                pygame.draw.circle(screen, color, (x, y), i)
        elif self.current_tutorial.name == "房子":
            # 画一个更真实的房子
            # 房体
            pygame.draw.rect(screen, (205, 133, 63), 
                           pygame.Rect(x-60, y-40, 120, 100))
            # 屋顶
            pygame.draw.polygon(screen, (139, 0, 0),
                              [(x-80, y-40), (x, y-100), (x+80, y-40)])
            # 窗户
            pygame.draw.rect(screen, (135, 206, 235),
                           pygame.Rect(x-40, y-20, 30, 30))
            pygame.draw.rect(screen, (135, 206, 235),
                           pygame.Rect(x+10, y-20, 30, 30))
            # 门
            pygame.draw.rect(screen, (101, 67, 33),
                           pygame.Rect(x-20, y+10, 40, 50))
        # 其他物品类似...
        
    def _draw_complete_drawing(self, screen: pygame.Surface, x: int, y: int):
        """绘制完整的简笔画"""
        # 绘制所有步骤的最终效果
        for step in self.current_tutorial.steps:
            step.draw_func(screen, x, y, 1.0)
            
    def _draw_step_by_step(self, screen: pygame.Surface, x: int, y: int):
        """绘制分步教学"""
        # 绘制已完成的步骤
        for i in range(self.current_step):
            self.current_tutorial.steps[i].draw_func(screen, x, y, 1.0)
            
        # 绘制当前步骤（带动画）
        if self.current_step < len(self.current_tutorial.steps):
            current = self.current_tutorial.steps[self.current_step]
            current.draw_func(screen, x, y, current.progress)
            
    def _draw_color_palette(self, screen: pygame.Surface):
        """绘制颜色调色板"""
        palette_y = self.window_height - self.scale_value(150)
        color_size = self.scale_value(40)
        spacing = self.scale_value(10)
        
        # 计算起始位置
        total_width = len(self.current_tutorial.colors) * (color_size + spacing) - spacing
        start_x = (self.window_width - total_width) // 2
        
        # 绘制颜色提示
        label_font = get_chinese_font(self.scale_font_size(20))
        label_text = "使用的颜色："
        label_surf = label_font.render(label_text, True, COLORS['text'])
        label_rect = label_surf.get_rect(center=(self.get_center_x(), 
                                                palette_y - self.scale_value(30)))
        screen.blit(label_surf, label_rect)
        
        # 绘制颜色块
        for i, color in enumerate(self.current_tutorial.colors):
            x = start_x + i * (color_size + spacing)
            color_rect = pygame.Rect(x, palette_y, color_size, color_size)
            pygame.draw.rect(screen, color, color_rect)
            pygame.draw.rect(screen, COLORS['text'], color_rect, 2)
            
    def _draw_ui_buttons(self, screen: pygame.Surface):
        """绘制UI按钮"""
        button_font = get_chinese_font(self.scale_font_size(24))
        
        # 暂停/继续按钮
        if self.pause_button:
            pause_text = "继续" if self.is_paused else "暂停"
            pause_color = COLORS['success'] if self.is_paused else COLORS['secondary']
            pygame.draw.rect(screen, pause_color, self.pause_button, border_radius=5)
            pause_surf = button_font.render(pause_text, True, COLORS['white'])
            pause_rect = pause_surf.get_rect(center=self.pause_button.center)
            screen.blit(pause_surf, pause_rect)
            
        # 上一步按钮
        if self.prev_button:
            prev_color = COLORS['primary'] if self.current_step > 0 else COLORS['disabled']
            pygame.draw.rect(screen, prev_color, self.prev_button, border_radius=5)
            prev_surf = button_font.render("上一步", True, COLORS['white'])
            prev_rect = prev_surf.get_rect(center=self.prev_button.center)
            screen.blit(prev_surf, prev_rect)
            
        # 下一步按钮
        if self.next_button:
            next_text = "下一步"
            if self.current_step == len(self.current_tutorial.steps) - 1:
                current = self.current_tutorial.steps[self.current_step]
                if current.progress >= 1.0:
                    next_text = "完成"
            next_color = COLORS['primary']
            pygame.draw.rect(screen, next_color, self.next_button, border_radius=5)
            next_surf = button_font.render(next_text, True, COLORS['white'])
            next_rect = next_surf.get_rect(center=self.next_button.center)
            screen.blit(next_surf, next_rect)
            
        # 重新开始按钮
        if self.restart_button:
            pygame.draw.rect(screen, COLORS['warning'], self.restart_button, border_radius=5)
            restart_surf = button_font.render("重新开始", True, COLORS['white'])
            restart_rect = restart_surf.get_rect(center=self.restart_button.center)
            screen.blit(restart_surf, restart_rect)
            
    def get_result(self) -> Dict:
        """获取游戏结果"""
        return {
            'completed_tutorials': 1,  # 实际应用中可以记录完成的教程数
            'current_tutorial': self.current_tutorial.name,
            'difficulty': self.difficulty
        }