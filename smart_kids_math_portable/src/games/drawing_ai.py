#!/usr/bin/env python3
"""
AI增强版画画教学游戏
使用深度学习模型生成高质量简笔画，并提供适合儿童的分步教学
"""
import pygame
import numpy as np
import os
import json
import random
from typing import List, Dict, Tuple, Optional, Any
from ..config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, IMAGES_PATH
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak
from ..utils.ui_utils import SpeakerButton
from ..utils.emoji_utils import draw_happy_face, draw_star_eyes_face
from .base_game import BaseGame




class DrawingConfigLoader:
    """加载和管理绘画配置文件"""
    
    def __init__(self):
        self.config_dir = os.path.join('assets', 'drawing_configs')
        self.drawings_cache = {}
        
    def load_drawings_for_level(self, level: int) -> List[Dict[str, Any]]:
        """加载指定难度等级的所有画画配置"""
        if level in self.drawings_cache:
            return self.drawings_cache[level]
            
        config_file = os.path.join(self.config_dir, f'level_{level}_drawings.json')
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                drawings = data.get('drawings', [])
                self.drawings_cache[level] = drawings
                return drawings
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载配置文件失败 level {level}: {e}")
            return []
    
    def get_random_drawing(self, level: int) -> Optional[Dict[str, Any]]:
        """获取指定等级的随机画画配置"""
        drawings = self.load_drawings_for_level(level)
        if drawings:
            return random.choice(drawings)
        return None
    
    def convert_stroke_to_numpy(self, stroke: Dict[str, Any]) -> List[np.ndarray]:
        """将配置中的笔画转换为numpy数组"""
        stroke_type = stroke.get('type')
        
        if stroke_type == 'line':
            points = stroke.get('points', [])
            return [np.array(points, dtype=np.float32)]
            
        elif stroke_type == 'circle':
            center = stroke.get('center', [200, 200])
            radius = stroke.get('radius', 50)
            segments = stroke.get('segments', 36)
            angles = np.linspace(0, 2 * np.pi, segments + 1)
            points = []
            for angle in angles:
                x = center[0] + radius * np.cos(angle)
                y = center[1] + radius * np.sin(angle)
                points.append([x, y])
            return [np.array(points, dtype=np.float32)]
            
        elif stroke_type == 'rectangle':
            points = stroke.get('points', [])
            if len(points) >= 4:
                rect_points = points + [points[0]]  # 闭合矩形
                return [np.array(rect_points, dtype=np.float32)]
                
        elif stroke_type == 'polygon':
            points = stroke.get('points', [])
            closed = stroke.get('closed', True)
            if closed and len(points) > 0:
                points = points + [points[0]]  # 闭合多边形
            return [np.array(points, dtype=np.float32)]
            
        elif stroke_type == 'arc':
            center = stroke.get('center', [200, 200])
            radius = stroke.get('radius', 50)
            start_angle = np.radians(stroke.get('start_angle', 0))
            end_angle = np.radians(stroke.get('end_angle', 180))
            segments = 20
            angles = np.linspace(start_angle, end_angle, segments)
            points = []
            for angle in angles:
                x = center[0] + radius * np.cos(angle)
                y = center[1] + radius * np.sin(angle)
                points.append([x, y])
            return [np.array(points, dtype=np.float32)]
            
        return []


class StrokeExtractor:
    """笔画提取器 - 将轮廓转换为适合儿童绘制的笔画"""
    
    @staticmethod
    def smooth_stroke(points: np.ndarray, window_size: int = 5) -> np.ndarray:
        """平滑笔画"""
        if len(points) < window_size:
            return points
            
        # 分别对x和y坐标进行平滑
        x_smooth = savgol_filter(points[:, 0], window_size, 2, mode='nearest')
        y_smooth = savgol_filter(points[:, 1], window_size, 2, mode='nearest')
        
        return np.column_stack([x_smooth, y_smooth])
    
    @staticmethod
    def simplify_stroke(points: np.ndarray, tolerance: float = 5.0) -> np.ndarray:
        """简化笔画 - 使用 Ramer-Douglas-Peucker 算法"""
        if len(points) < 3:
            return points
            
        # 使用OpenCV的approxPolyDP进行简化
        points_int = points.astype(np.int32)
        simplified = cv2.approxPolyDP(points_int, tolerance, False)
        
        return simplified.squeeze()
    
    @staticmethod
    def decompose_complex_shape(contour: np.ndarray) -> List[np.ndarray]:
        """将复杂形状分解为简单笔画"""
        strokes = []
        
        # 计算轮廓的凸包
        hull = cv2.convexHull(contour)
        
        # 如果轮廓接近凸包，作为一个笔画
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(contour)
        
        if contour_area > 0 and hull_area / contour_area < 1.2:
            strokes.append(contour)
        else:
            # 找到凹陷点并分割
            defects = cv2.convexityDefects(contour, cv2.convexHull(contour, returnPoints=False))
            
            if defects is not None:
                # 根据凹陷深度分割轮廓
                split_points = []
                for i in range(defects.shape[0]):
                    _, _, _, d = defects[i, 0]
                    if d > 1000:  # 深度阈值
                        split_points.append(i)
                
                # 如果有分割点，创建子笔画
                if split_points:
                    # 简单地将轮廓分成几部分
                    n_points = len(contour)
                    segment_size = n_points // (len(split_points) + 1)
                    
                    for i in range(len(split_points) + 1):
                        start = i * segment_size
                        end = min((i + 1) * segment_size, n_points)
                        if end - start > 3:
                            strokes.append(contour[start:end])
                else:
                    strokes.append(contour)
            else:
                strokes.append(contour)
        
        return strokes


class DrawingStep:
    """绘画步骤"""
    def __init__(self, name: str, strokes: List[np.ndarray], description: str, 
                 color: Tuple[int, int, int] = (0, 0, 0)):
        self.name = name
        self.strokes = strokes
        self.description = description
        self.color = color
        self.progress = 0.0


class DrawingAIGame(BaseGame):
    """AI增强版画画游戏"""
    
    def __init__(self, difficulty: int = 1):
        super().__init__(difficulty)
        self.game_type = "drawing_ai"
        
        # 配置加载器
        self.config_loader = DrawingConfigLoader()
        
        # 难度等级直接对应配置文件等级 (1-5)
        # 如果难度超过5，则使用等级5的配置
        self.config_level = min(5, max(1, self.difficulty))
        
        # 画布和步骤管理
        self.canvas_surface = None  # Pygame surface instead of numpy array
        self.steps: List[DrawingStep] = []
        self.current_step = 0
        
        # 游戏状态
        self.game_phase = 'select'  # select, preview, steps, complete
        self.preview_timer = 0
        self.preview_duration = 2000  # 2秒预览时间
        
        # 动画控制
        self.stroke_progress = 0.0
        self.current_stroke_index = 0
        self.animation_speed = 1.0 + (10 - self.difficulty) * 0.05  # 根据难度调整速度
        
        # UI元素
        self.drawing_buttons = []
        self.control_buttons = {}
        
        # 画布
        self.canvas_size = (400, 400)
        self.canvas_rect = None
        
        # 可用的画画配置
        self.available_drawings = []
        self.selected_drawing = None
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 初始化
        self._load_available_drawings()
        
            
    def _load_available_drawings(self):
        """加载可用的画画配置"""
        # 从配置文件加载画画
        self.available_drawings = self.config_loader.load_drawings_for_level(self.config_level)
        
        # 如果没有配置文件，提供默认选项
        if not self.available_drawings:
            print(f"Warning: No drawings found for level {self.config_level}")
            # 提供一个简单的默认圆形
            self.available_drawings = [{
                "id": "default_circle",
                "name": "圆形",
                "type": "circle",
                "steps": [{
                    "name": "圆圈",
                    "description": "画一个大大的圆圈",
                    "color": [255, 200, 0],
                    "strokes": [{
                        "type": "circle",
                        "center": [200, 200],
                        "radius": 80,
                        "segments": 36
                    }]
                }]
            }]
            
        
        
        
    def _load_and_process_drawing(self, drawing_config: Dict[str, Any]):
        """加载并处理画画配置"""
        # 为画布设置默认大小
        self.canvas_size = (400, 400)
        
        # 从配置文件创建绘画步骤
        self.steps = []
        for step_config in drawing_config.get('steps', []):
            # 转换笔画数据
            strokes = []
            for stroke_config in step_config.get('strokes', []):
                stroke_arrays = self.config_loader.convert_stroke_to_numpy(stroke_config)
                strokes.extend(stroke_arrays)
            
            # 创建步骤对象
            # 配置文件使用RGB格式，Pygame也使用RGB格式
            rgb_color = step_config.get('color', [0, 0, 0])
            step = DrawingStep(
                name=step_config.get('name', ''),
                strokes=strokes,
                description=step_config.get('description', ''),
                color=tuple(rgb_color)  # 直接使用RGB
            )
            self.steps.append(step)
        
        # 初始化画布
        self._init_canvas_simple()
        
        return True
        
        
            
    def _init_canvas_simple(self):
        """简单初始化画布"""
        self.canvas_surface = pygame.Surface(self.canvas_size)
        self.canvas_surface.fill((255, 255, 255))  # White background
            
    def handle_click(self, pos: Tuple[int, int]):
        """处理点击事件"""
        # 检查喇叭按钮
        for button, text in self.speaker_buttons:
            if button.check_click(pos):
                speak(text)
                return
                
        if self.game_phase == 'select':
            # 选择画画
            for i, btn_rect in enumerate(self.drawing_buttons):
                if btn_rect.collidepoint(pos):
                    if i < len(self.available_drawings):
                        self.selected_drawing = self.available_drawings[i]
                        if self._load_and_process_drawing(self.selected_drawing):
                            # 先显示预览
                            self.game_phase = 'preview'
                            speak(f"看看我们要画的{self.selected_drawing['name']}")
                    return
                    
        elif self.game_phase == 'preview':
            # 点击后进入分步教学
            self.game_phase = 'steps'
            self.current_step = 0
            self.current_stroke_index = 0
            self.stroke_progress = 0
            speak(f"开始学画画。{self.steps[0].description if self.steps else '开始吧'}")
            
        elif self.game_phase == 'steps':
            # 控制按钮
            if 'prev' in self.control_buttons and self.control_buttons['prev'].collidepoint(pos):
                if self.current_step > 0:
                    self.current_step -= 1
                    self.current_stroke_index = 0
                    self.stroke_progress = 0
                    speak(self.steps[self.current_step].description)
                    
            elif 'next' in self.control_buttons and self.control_buttons['next'].collidepoint(pos):
                if self.current_step < len(self.steps) - 1:
                    self.current_step += 1
                    self.current_stroke_index = 0
                    self.stroke_progress = 0
                    speak(self.steps[self.current_step].description)
                else:
                    # 完成
                    self.game_phase = 'complete'
                    speak(f"太棒了！你学会了画{self.selected_drawing['name']}！")
                    
            elif 'restart' in self.control_buttons and self.control_buttons['restart'].collidepoint(pos):
                self.current_step = 0
                self.current_stroke_index = 0
                self.stroke_progress = 0
                self._init_canvas_simple()
                speak("重新开始")
                
        elif self.game_phase == 'complete':
            # 返回选择界面
            self.game_phase = 'select'
            self.selected_drawing = None
            self.steps = []
            speak("选择一个新的图片来学习")
            
    def update(self, dt: float):
        """更新游戏状态"""
        # 更新动画进度
        if self.game_phase == 'steps' and self.steps:
            current_step = self.steps[self.current_step]
            
            if self.current_stroke_index < len(current_step.strokes):
                # 更新当前笔画的进度
                self.stroke_progress = min(1.0, self.stroke_progress + dt * self.animation_speed)
                
                # 如果当前笔画完成，进入下一笔画
                if self.stroke_progress >= 1.0:
                    self.current_stroke_index += 1
                    self.stroke_progress = 0
                    
        # 更新喇叭按钮
        mouse_pos = pygame.mouse.get_pos()
        for button, _ in self.speaker_buttons:
            button.update(mouse_pos)
            
    def draw(self, screen: pygame.Surface):
        """绘制游戏画面"""
        screen.fill(COLORS['background'])
        
        # 清空喇叭按钮
        self.speaker_buttons.clear()
        
        # 绘制标题
        title_font = get_chinese_font(self.scale_font_size(48))
        title = "学画画"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(self.get_center_x(), self.scale_value(50)))
        screen.blit(title_surf, title_rect)
        
        # 根据游戏阶段绘制
        if self.game_phase == 'select':
            self._draw_image_selection(screen)
        elif self.game_phase == 'preview':
            self._draw_preview(screen)
        elif self.game_phase == 'steps':
            self._draw_steps(screen)
        elif self.game_phase == 'complete':
            self._draw_complete(screen)
            
        # 绘制所有喇叭按钮
        for button, _ in self.speaker_buttons:
            button.draw(screen)
            
    def _draw_image_selection(self, screen: pygame.Surface):
        """绘制画画选择界面"""
        self.drawing_buttons.clear()
        
        # 提示文字
        hint_font = get_chinese_font(self.scale_font_size(32))
        hint_text = "选择一个你喜欢的图案"
        hint_surf = hint_font.render(hint_text, True, COLORS['text'])
        hint_rect = hint_surf.get_rect(center=(self.get_center_x(), self.scale_value(120)))
        screen.blit(hint_surf, hint_rect)
        
        # 按钮布局
        cols = 3
        button_size = self.scale_value(180)
        spacing = self.scale_value(40)
        
        # 根据实际画画数量计算布局
        num_drawings = len(self.available_drawings)
        if num_drawings == 0:
            return
            
        rows = (num_drawings + cols - 1) // cols
        total_width = min(cols, num_drawings) * button_size + (min(cols, num_drawings) - 1) * spacing
        total_height = rows * button_size + (rows - 1) * spacing
        
        start_x = (self.window_width - total_width) // 2
        start_y = (self.window_height - total_height) // 2 + self.scale_value(30)
        
        label_font = get_chinese_font(self.scale_font_size(28))
        
        # 根据配置等级确定颜色
        level_colors = {
            1: COLORS['success'],    # 绿色 - 简单
            2: COLORS['primary'],    # 蓝色 - 中等  
            3: COLORS['primary'],    # 蓝色 - 中等
            4: COLORS['warning'],    # 橙色 - 较难
            5: COLORS['warning']     # 橙色 - 较难
        }
        
        for i, drawing_info in enumerate(self.available_drawings):
            row = i // cols
            col = i % cols
            
            x = start_x + col * (button_size + spacing)
            y = start_y + row * (button_size + spacing)
            
            # 按钮矩形
            btn_rect = pygame.Rect(x, y, button_size, button_size)
            self.drawing_buttons.append(btn_rect)
            
            # 绘制按钮
            color = level_colors.get(self.config_level, COLORS['primary'])
            pygame.draw.rect(screen, color, btn_rect, border_radius=15)
            pygame.draw.rect(screen, COLORS['text'], btn_rect, 3, border_radius=15)
            
            # 绘制图标（根据类型）
            icon_color = COLORS['white']
            cx = btn_rect.centerx
            cy = btn_rect.centery - self.scale_value(20)
            
            drawing_type = drawing_info.get('type', 'circle')
            if drawing_type == 'circle':
                pygame.draw.circle(screen, icon_color, (cx, cy), self.scale_value(40), 5)
            elif drawing_type == 'rectangle':
                pygame.draw.rect(screen, icon_color, 
                               (cx - self.scale_value(35), cy - self.scale_value(25),
                                self.scale_value(70), self.scale_value(50)), 5)
            elif drawing_type == 'triangle':
                pts = [(cx, cy - self.scale_value(30)),
                       (cx - self.scale_value(35), cy + self.scale_value(25)),
                       (cx + self.scale_value(35), cy + self.scale_value(25))]
                pygame.draw.polygon(screen, icon_color, pts, 5)
            elif drawing_type == 'flower':
                # 花朵图标
                pygame.draw.circle(screen, icon_color, (cx, cy), self.scale_value(20), 5)
                for angle in range(0, 360, 72):
                    px = cx + int(20 * np.cos(np.radians(angle)))
                    py = cy + int(20 * np.sin(np.radians(angle)))
                    pygame.draw.circle(screen, icon_color, (px, py), self.scale_value(10), 3)
            elif drawing_type == 'car':
                # 汽车图标
                pygame.draw.rect(screen, icon_color,
                               (cx - self.scale_value(30), cy - self.scale_value(10),
                                self.scale_value(60), self.scale_value(20)), 3)
                pygame.draw.circle(screen, icon_color, 
                                 (cx - self.scale_value(15), cy + self.scale_value(10)), 
                                 self.scale_value(8), 3)
                pygame.draw.circle(screen, icon_color,
                                 (cx + self.scale_value(15), cy + self.scale_value(10)),
                                 self.scale_value(8), 3)
            elif drawing_type == 'animal':
                # 动物图标（猫脸）
                pygame.draw.circle(screen, icon_color, (cx, cy), self.scale_value(25), 5)
                # 耳朵
                pts1 = [(cx - self.scale_value(20), cy - self.scale_value(20)),
                        (cx - self.scale_value(25), cy - self.scale_value(35)),
                        (cx - self.scale_value(10), cy - self.scale_value(25))]
                pts2 = [(cx + self.scale_value(20), cy - self.scale_value(20)),
                        (cx + self.scale_value(25), cy - self.scale_value(35)),
                        (cx + self.scale_value(10), cy - self.scale_value(25))]
                pygame.draw.polygon(screen, icon_color, pts1, 3)
                pygame.draw.polygon(screen, icon_color, pts2, 3)
            else:
                # 默认图标
                pygame.draw.circle(screen, icon_color, (cx, cy), self.scale_value(30), 5)
            
            # 名称
            name_surf = label_font.render(drawing_info['name'], True, COLORS['white'])
            name_rect = name_surf.get_rect(centerx=btn_rect.centerx, 
                                          bottom=btn_rect.bottom - self.scale_value(15))
            screen.blit(name_surf, name_rect)
            
    def _draw_preview(self, screen: pygame.Surface):
        """绘制图案全貌预览"""
        # 画布位置
        canvas_x = (self.window_width - self.canvas_size[0]) // 2
        canvas_y = self.scale_value(150)
        preview_rect = pygame.Rect(canvas_x, canvas_y, *self.canvas_size)
        
        # 创建预览画布
        preview_surface = pygame.Surface(self.canvas_size)
        preview_surface.fill((255, 255, 255))
        
        # 绘制完整图案
        for step in self.steps:
            color = step.color  # Already in BGR from config loader
            for stroke in step.strokes:
                if len(stroke) >= 2:
                    points = [(int(p[0]), int(p[1])) for p in stroke]
                    if len(points) > 2:
                        # Draw as polygon if closed shape
                        first_point = points[0]
                        last_point = points[-1]
                        if abs(first_point[0] - last_point[0]) < 5 and abs(first_point[1] - last_point[1]) < 5:
                            pygame.draw.polygon(preview_surface, color, points, 0)
                        else:
                            # Draw as lines
                            pygame.draw.lines(preview_surface, color, False, points, 5)
                    else:
                        # Draw single line
                        pygame.draw.line(preview_surface, color, points[0], points[1], 5)
                               
        # 显示预览
        screen.blit(preview_surface, preview_rect)
        
        # 绘制边框
        pygame.draw.rect(screen, COLORS['primary'], preview_rect, 3)
        
        # 标题
        label_font = get_chinese_font(self.scale_font_size(36))
        label_text = f"我们要画的{self.selected_drawing['name']}"
        label_surf = label_font.render(label_text, True, COLORS['text'])
        label_rect = label_surf.get_rect(center=(self.get_center_x(), self.scale_value(110)))
        screen.blit(label_surf, label_rect)
        
        # 提示
        hint_font = get_chinese_font(self.scale_font_size(28))
        hint_text = "点击开始学习"
        hint_surf = hint_font.render(hint_text, True, COLORS['secondary'])
        hint_rect = hint_surf.get_rect(center=(self.get_center_x(), 
                                               self.window_height - self.scale_value(80)))
        screen.blit(hint_surf, hint_rect)
        
        # 添加喇叭按钮
        speaker_btn = SpeakerButton(
            label_rect.right + self.scale_value(20),
            self.scale_value(110),
            self.scale_value(25)
        )
        speaker_btn.draw(screen)
        self.speaker_buttons.append((speaker_btn, f"这是{self.selected_drawing['name']}的样子"))
            
            
    def _draw_steps(self, screen: pygame.Surface):
        """绘制分步教学"""
        # 画布位置
        canvas_x = (self.window_width - self.canvas_size[0]) // 2
        canvas_y = self.scale_value(180)
        self.canvas_rect = pygame.Rect(canvas_x, canvas_y, *self.canvas_size)
        
        # 清空画布
        self.canvas_surface.fill((255, 255, 255))
        
        # 绘制已完成的步骤
        for i in range(self.current_step):
            step = self.steps[i]
            color = step.color
            for stroke in step.strokes:
                if len(stroke) >= 2:
                    points = [(int(p[0]), int(p[1])) for p in stroke]
                    if len(points) > 2:
                        # Check if it's a closed shape
                        first_point = points[0]
                        last_point = points[-1]
                        if abs(first_point[0] - last_point[0]) < 5 and abs(first_point[1] - last_point[1]) < 5:
                            pygame.draw.polygon(self.canvas_surface, color, points, 0)
                        else:
                            pygame.draw.lines(self.canvas_surface, color, False, points, 5)
                    else:
                        pygame.draw.line(self.canvas_surface, color, points[0], points[1], 5)
                               
        # 绘制当前步骤的动画
        if self.current_step < len(self.steps):
            current_step = self.steps[self.current_step]
            color = current_step.color
            
            # 绘制已完成的笔画
            for i in range(self.current_stroke_index):
                if i < len(current_step.strokes):
                    stroke = current_step.strokes[i]
                    if len(stroke) >= 2:
                        points = [(int(p[0]), int(p[1])) for p in stroke]
                        if len(points) > 2:
                            first_point = points[0]
                            last_point = points[-1]
                            if abs(first_point[0] - last_point[0]) < 5 and abs(first_point[1] - last_point[1]) < 5:
                                pygame.draw.polygon(self.canvas_surface, color, points, 0)
                            else:
                                pygame.draw.lines(self.canvas_surface, color, False, points, 5)
                        else:
                            pygame.draw.line(self.canvas_surface, color, points[0], points[1], 5)
                                   
            # 绘制当前笔画的动画
            if self.current_stroke_index < len(current_step.strokes):
                stroke = current_step.strokes[self.current_stroke_index]
                if len(stroke) >= 2:
                    # 计算要绘制的点数
                    num_points = max(2, int(len(stroke) * self.stroke_progress))
                    
                    # 绘制部分笔画
                    points = [(int(stroke[j][0]), int(stroke[j][1])) for j in range(num_points)]
                    if len(points) >= 2:
                        pygame.draw.lines(self.canvas_surface, color, False, points, 5)
                               
                    # 绘制引导点（当前绘制位置）
                    if num_points < len(stroke):
                        guide_pos = (int(stroke[num_points - 1][0]), int(stroke[num_points - 1][1]))
                        pygame.draw.circle(self.canvas_surface, (255, 0, 0), guide_pos, 8)
                        
        # 显示画布
        screen.blit(self.canvas_surface, self.canvas_rect)
        
        # 绘制边框
        pygame.draw.rect(screen, COLORS['text'], self.canvas_rect, 3)
        
        # 步骤说明
        if self.current_step < len(self.steps):
            step_font = get_chinese_font(self.scale_font_size(36))
            step = self.steps[self.current_step]
            step_text = f"第{self.current_step + 1}步：{step.description}"
            step_surf = step_font.render(step_text, True, COLORS['primary'])
            step_rect = step_surf.get_rect(center=(self.get_center_x(), self.scale_value(130)))
            screen.blit(step_surf, step_rect)
            
            # 添加喇叭按钮
            speaker_btn = SpeakerButton(
                step_rect.right + self.scale_value(20),
                self.scale_value(130),
                self.scale_value(25)
            )
            speaker_btn.draw(screen)
            self.speaker_buttons.append((speaker_btn, step.description))
            
        # 绘制控制按钮
        self._draw_control_buttons(screen)
        
    def _draw_control_buttons(self, screen: pygame.Surface):
        """绘制控制按钮"""
        self.control_buttons.clear()
        
        button_y = self.window_height - self.scale_value(80)
        button_width = self.scale_value(120)
        button_height = self.scale_value(50)
        spacing = self.scale_value(30)
        
        # 计算按钮位置
        buttons = ['prev', 'next', 'restart']
        total_width = len(buttons) * button_width + (len(buttons) - 1) * spacing
        start_x = (self.window_width - total_width) // 2
        
        button_font = get_chinese_font(self.scale_font_size(28))
        
        # 上一步按钮
        prev_rect = pygame.Rect(start_x, button_y, button_width, button_height)
        self.control_buttons['prev'] = prev_rect
        
        if self.current_step > 0:
            pygame.draw.rect(screen, COLORS['secondary'], prev_rect, border_radius=10)
            prev_text = button_font.render("上一步", True, COLORS['white'])
        else:
            pygame.draw.rect(screen, COLORS['disabled'], prev_rect, 2, border_radius=10)
            prev_text = button_font.render("上一步", True, COLORS['disabled'])
            
        prev_text_rect = prev_text.get_rect(center=prev_rect.center)
        screen.blit(prev_text, prev_text_rect)
        
        # 下一步按钮
        next_rect = pygame.Rect(start_x + button_width + spacing, button_y, 
                               button_width, button_height)
        self.control_buttons['next'] = next_rect
        
        next_label = "完成啦" if self.current_step == len(self.steps) - 1 else "下一步"
        pygame.draw.rect(screen, COLORS['primary'], next_rect, border_radius=10)
        next_text = button_font.render(next_label, True, COLORS['white'])
        next_text_rect = next_text.get_rect(center=next_rect.center)
        screen.blit(next_text, next_text_rect)
        
        # 重新开始按钮
        restart_rect = pygame.Rect(start_x + 2 * (button_width + spacing), button_y,
                                  button_width, button_height)
        self.control_buttons['restart'] = restart_rect
        
        pygame.draw.rect(screen, COLORS['warning'], restart_rect, border_radius=10)
        restart_text = button_font.render("重新开始", True, COLORS['white'])
        restart_text_rect = restart_text.get_rect(center=restart_rect.center)
        screen.blit(restart_text, restart_text_rect)
        
    def _draw_complete(self, screen: pygame.Surface):
        """绘制完成画面"""
        # 显示完成的画作
        if self.canvas_surface is not None:
            img_rect = self.canvas_surface.get_rect(center=(self.get_center_x(), self.get_center_y()))
            screen.blit(self.canvas_surface, img_rect)
            pygame.draw.rect(screen, COLORS['success'], img_rect, 5)
            
        # 庆祝效果
        draw_star_eyes_face(screen, self.get_center_x(), 
                           self.scale_value(150), self.scale_value(80))
                           
        complete_font = get_chinese_font(self.scale_font_size(48))
        complete_text = "太棒了！"
        complete_surf = complete_font.render(complete_text, True, COLORS['success'])
        complete_rect = complete_surf.get_rect(center=(self.get_center_x(), 
                                                      self.window_height - self.scale_value(150)))
        screen.blit(complete_surf, complete_rect)
        
        hint_font = get_chinese_font(self.scale_font_size(28))
        hint_text = "点击画下一个"
        hint_surf = hint_font.render(hint_text, True, COLORS['secondary'])
        hint_rect = hint_surf.get_rect(center=(self.get_center_x(), 
                                               self.window_height - self.scale_value(80)))
        screen.blit(hint_surf, hint_rect)
        
        
    def get_result(self) -> Dict:
        """获取游戏结果"""
        return {
            'completed': self.game_phase == 'complete',
            'score': 100 if self.game_phase == 'complete' else 0,
            'stars': 3 if self.game_phase == 'complete' else 0,
            'coins': 10 if self.game_phase == 'complete' else 0,
            'learned': self.selected_drawing['name'] if self.selected_drawing else "无"
        }