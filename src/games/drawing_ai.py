"""基于AI的画画游戏 - 使用配置文件的简笔画分步演示"""

import pygame
import json
import os
from typing import List, Dict, Tuple, Any, Optional
import math
import random
from ..config import COLORS, EMOJI_COLORS
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak, stop_speaking, is_speaking
from ..utils.ui_utils import SpeakerButton
from ..utils.emoji_utils import draw_happy_face, draw_sad_face
from .base_game import BaseGame


class DrawingConfigLoader:
    """加载和管理画画配置文件"""
    
    def __init__(self):
        self.configs = {}
        self.load_all_configs()
    
    def load_all_configs(self):
        """加载所有难度等级的配置文件"""
        config_dir = os.path.join(os.path.dirname(__file__), '../../assets/drawing_configs')
        
        for level in range(1, 11):  # 支持1-10级
            config_file = os.path.join(config_dir, f'level_{level}_drawings.json')
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        self.configs[level] = json.load(f)
                        print(f"成功加载难度{level}的配置文件")
                except Exception as e:
                    print(f"加载难度{level}配置文件失败: {e}")
    
    def get_drawings_for_level(self, level: int) -> List[Dict[str, Any]]:
        """获取指定难度的所有画画"""
        if level in self.configs:
            return self.configs[level].get('drawings', [])
        return []
    
    def get_random_drawing(self, level: int) -> Optional[Dict[str, Any]]:
        """随机获取一个指定难度的画画"""
        drawings = self.get_drawings_for_level(level)
        if drawings:
            return random.choice(drawings)
        return None
    
    def convert_stroke_to_points(self, stroke: Dict[str, Any]) -> List[List[Tuple[float, float]]]:
        """将配置中的笔画转换为点列表"""
        stroke_type = stroke.get('type')
        
        if stroke_type == 'line':
            points = stroke.get('points', [])
            return [[(p[0], p[1]) for p in points]]
            
        elif stroke_type == 'circle':
            center = stroke.get('center', [200, 200])
            radius = stroke.get('radius', 50)
            segments = stroke.get('segments', 36)
            points = []
            for i in range(segments + 1):
                angle = (i / segments) * 2 * math.pi
                x = center[0] + radius * math.cos(angle)
                y = center[1] + radius * math.sin(angle)
                points.append((x, y))
            return [points]
            
        elif stroke_type == 'rectangle':
            points = stroke.get('points', [])
            if len(points) >= 4:
                rect_points = [(p[0], p[1]) for p in points]
                rect_points.append(rect_points[0])  # 闭合矩形
                return [rect_points]
                
        elif stroke_type == 'polygon':
            points = stroke.get('points', [])
            closed = stroke.get('closed', True)
            poly_points = [(p[0], p[1]) for p in points]
            if closed and len(poly_points) > 0:
                poly_points.append(poly_points[0])  # 闭合多边形
            return [poly_points]
            
        elif stroke_type == 'arc':
            center = stroke.get('center', [200, 200])
            radius = stroke.get('radius', 50)
            start_angle = math.radians(stroke.get('start_angle', 0))
            end_angle = math.radians(stroke.get('end_angle', 180))
            segments = 20
            points = []
            for i in range(segments):
                angle = start_angle + (end_angle - start_angle) * i / (segments - 1)
                x = center[0] + radius * math.cos(angle)
                y = center[1] + radius * math.sin(angle)
                points.append((x, y))
            return [points]
            
        return []


class DrawingStep:
    """画画步骤类"""
    
    def __init__(self, name: str, strokes: List[List[Tuple[float, float]]], description: str, 
                 color: Tuple[int, int, int] = (0, 0, 0), stroke_config: Any = None):
        self.name = name
        self.strokes = strokes
        self.description = description
        self.color = color
        self.stroke_config = stroke_config  # 保存原始配置用于判断形状类型（可以是单个dict或list）
        self.progress = 0.0
        self.completed = False
        
    def update(self, dt: float, speed: float = 2.0):
        """更新绘制进度"""
        if not self.completed:
            self.progress += speed * dt
            if self.progress >= 1.0:
                self.progress = 1.0
                self.completed = True
                
    def draw(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)):
        """绘制当前步骤"""
        if self.progress <= 0:
            return
            
        for i, stroke in enumerate(self.strokes):
            if len(stroke) < 2:
                continue
                
            # 判断是否为闭合形状
            is_closed = False
            if self.stroke_config:
                # 如果stroke_config是列表，获取对应的配置
                config = self.stroke_config[i] if isinstance(self.stroke_config, list) and i < len(self.stroke_config) else self.stroke_config
                if isinstance(config, dict):
                    stroke_type = config.get('type')
                    is_closed = stroke_type in ['circle', 'polygon', 'rectangle'] and config.get('closed', True)
            
            # 转换点坐标
            points = [(p[0] + offset[0], p[1] + offset[1]) for p in stroke]
            
            if is_closed and len(points) > 2:
                # 闭合形状：先填充再画边框
                # 先填充颜色
                if self.color != (255, 255, 255):
                    pygame.draw.polygon(surface, self.color, points, 0)
                # 再画黑色边框
                pygame.draw.polygon(surface, (0, 0, 0), points, 3)
            else:
                # 非闭合形状：只画线条
                if len(points) == 2:
                    pygame.draw.line(surface, self.color, points[0], points[1], 5)
                elif len(points) > 2:
                    # 根据进度绘制部分笔画
                    total_points = len(points)
                    points_to_draw = int(total_points * self.progress)
                    if points_to_draw >= 2:
                        pygame.draw.lines(surface, self.color, False, points[:points_to_draw], 5)


class DrawingAIGame(BaseGame):
    """基于AI的画画游戏"""
    
    def __init__(self, difficulty: int = 5):
        super().__init__(difficulty)
        self.config_loader = DrawingConfigLoader()
        
        # 难度映射到配置文件等级
        self.config_level = min(10, max(1, self.difficulty))
        
        # 游戏状态
        self.game_phase = 'select'  # 'select', 'preview', 'steps', 'complete'
        self.current_drawing = None
        self.drawing_name = ""
        self.current_step_index = 0
        self.auto_play = False
        self.step_completed = False
        
        # 画布
        self.canvas_surface = None  # Pygame surface
        
        # UI元素
        self.drawing_buttons = []
        self.button_size = self.scale_value(200)
        self.button_spacing = self.scale_value(20)
        
        # 控制按钮
        self.prev_button = None
        self.next_button = None
        self.play_button = None
        self.restart_button = None
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 语音状态
        self.last_voice_text = ""
        self.voice_playing = False
        
        # 选择可用的画画
        self._select_available_drawings()
        
        # 创建空白画布
        self._reset_canvas()
        
    def _reset_canvas(self):
        """重置画布"""
        self.canvas_surface = pygame.Surface((self.scale_value(600), self.scale_value(500)))
        self.canvas_surface.fill((255, 255, 255))  # White background
        
    def _draw_shape(self, surface: pygame.Surface, points: list, color: tuple, is_closed: bool = False, fill_white: bool = True):
        """绘制形状，闭合形状先画边框再填充
        
        Args:
            surface: 绘制表面
            points: 点列表
            color: 颜色
            is_closed: 是否闭合形状
            fill_white: 是否填充白色（用于处理重叠）
        """
        if len(points) < 2:
            return
            
        if is_closed and len(points) > 2:
            # 闭合形状
            # 先填充颜色
            if color == (255, 255, 255) and fill_white:
                # 白色形状也填充，用于覆盖之前的内容
                pygame.draw.polygon(surface, color, points, 0)
            elif color != (255, 255, 255):
                # 非白色形状正常填充
                pygame.draw.polygon(surface, color, points, 0)
            
            # 再画边框
            pygame.draw.polygon(surface, (0, 0, 0), points, 3)
        else:
            # 非闭合形状，直接画线
            if len(points) > 2:
                pygame.draw.lines(surface, color, False, points, 5)
            else:
                pygame.draw.line(surface, color, points[0], points[1], 5)
    
    def _select_available_drawings(self):
        """选择当前难度可用的画画"""
        self.available_drawings = self.config_loader.get_drawings_for_level(self.config_level)
        if not self.available_drawings:
            # 如果当前难度没有配置，尝试使用默认难度
            self.config_level = 3
            self.available_drawings = self.config_loader.get_drawings_for_level(self.config_level)
    
    def _start_drawing(self, drawing_config: Dict[str, Any]):
        """开始画画"""
        self.current_drawing = []
        self.drawing_name = drawing_config.get('name', '未命名')
        
        # 转换配置为DrawingStep对象，合并同一步骤的所有笔画
        for step_config in drawing_config.get('steps', []):
            step_name = step_config.get('name', '')
            description = step_config.get('description', '')
            color = tuple(step_config.get('color', [0, 0, 0]))
            
            # 收集这一步的所有笔画
            step_strokes = []
            step_stroke_configs = []
            
            for stroke_config in step_config.get('strokes', []):
                stroke_points = self.config_loader.convert_stroke_to_points(stroke_config)
                for points in stroke_points:
                    step_strokes.append(points)
                    step_stroke_configs.append(stroke_config)
            
            # 创建一个包含所有笔画的步骤
            if step_strokes:
                step = DrawingStep(
                    name=step_name,
                    strokes=step_strokes,
                    description=description,
                    color=color,
                    stroke_config=step_stroke_configs  # 保存所有笔画的配置
                )
                self.current_drawing.append(step)
        
        self.current_step_index = 0
        self.step_completed = False
        self.game_phase = 'preview'
        self._reset_canvas()
        
        # 创建控制按钮
        self._create_control_buttons()
        
        # 播放介绍语音
        speak(f"我们来画{self.drawing_name}吧！")
    
    def _create_control_buttons(self):
        """创建控制按钮"""
        button_y = self.get_screen_height() - self.scale_value(70)
        button_width = self.scale_value(100)
        button_height = self.scale_value(50)
        button_spacing = self.scale_value(20)
        
        # 计算按钮总宽度
        total_width = button_width * 4 + button_spacing * 3
        start_x = (self.get_screen_width() - total_width) // 2
        
        # 播放/暂停按钮（放在最左边）
        self.play_button = pygame.Rect(
            start_x, button_y, button_width, button_height
        )
        
        # 上一步按钮
        self.prev_button = pygame.Rect(
            start_x + button_width + button_spacing, button_y,
            button_width, button_height
        )
        
        # 下一步按钮
        self.next_button = pygame.Rect(
            start_x + (button_width + button_spacing) * 2, button_y,
            button_width, button_height
        )
        
        # 重新开始按钮
        self.restart_button = pygame.Rect(
            start_x + (button_width + button_spacing) * 3, button_y,
            button_width, button_height
        )
    
    def _draw_preview(self):
        """绘制预览（显示完成的画）"""
        # 快速绘制所有步骤
        for step in self.current_drawing:
            step.progress = 1.0
            step.completed = True
            step.draw(self.canvas_surface)
    
    def handle_click(self, pos: Tuple[int, int]):
        """处理点击事件"""
        stop_speaking()
        
        # 检查喇叭按钮
        for button, text in self.speaker_buttons:
            if button.check_click(pos):
                if not self.voice_playing:
                    self.voice_playing = True
                    self.last_voice_text = text
                    speak(text)
                return
        
        if self.game_phase == 'select':
            # 选择画画
            for i, button_rect in enumerate(self.drawing_buttons):
                if button_rect.collidepoint(pos):
                    if i < len(self.available_drawings):
                        self._start_drawing(self.available_drawings[i])
                    return
                    
        elif self.game_phase in ['preview', 'steps']:
            # 检查控制按钮
            if self.prev_button and self.prev_button.collidepoint(pos):
                self._prev_step()
            elif self.next_button and self.next_button.collidepoint(pos):
                self._next_step()
            elif self.play_button and self.play_button.collidepoint(pos):
                if self.game_phase == 'preview':
                    # 从预览模式进入步骤模式并开始播放
                    self.game_phase = 'steps'
                    self.current_step_index = 0
                    self._reset_canvas()
                    self.auto_play = True
                    # 播放第一步的说明
                    if self.current_drawing and len(self.current_drawing) > 0:
                        speak(f"开始画画！{self.current_drawing[0].description}")
                elif self.game_phase == 'steps':
                    # 在步骤模式下切换播放/暂停
                    self.auto_play = not self.auto_play
                    if self.auto_play and self.step_completed and self.current_step_index < len(self.current_drawing) - 1:
                        # 如果当前步骤已完成且不是最后一步，立即进入下一步
                        self._next_step()
            elif self.restart_button and self.restart_button.collidepoint(pos):
                self._restart()
                
        elif self.game_phase == 'complete':
            # 返回选择界面
            self.game_phase = 'select'
            self.current_drawing = None
            self.drawing_name = ""
            self.speaker_buttons.clear()
    
    def _prev_step(self):
        """上一步"""
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self._redraw_up_to_current_step()
            self.step_completed = False
            self.auto_play = False
    
    def _next_step(self):
        """下一步"""
        if self.game_phase == 'preview':
            # 从预览进入步骤模式
            self.game_phase = 'steps'
            self.current_step_index = 0
            self._reset_canvas()
        elif self.current_step_index < len(self.current_drawing) - 1:
            # 完成当前步骤并进入下一步
            if self.current_drawing:
                self.current_drawing[self.current_step_index].progress = 1.0
                self.current_drawing[self.current_step_index].completed = True
            self.current_step_index += 1
            self.step_completed = False
        elif self.current_step_index == len(self.current_drawing) - 1:
            # 完成最后一步
            if self.current_drawing:
                self.current_drawing[self.current_step_index].progress = 1.0
                self.current_drawing[self.current_step_index].completed = True
            self.game_phase = 'complete'
            self.auto_play = False
    
    def _restart(self):
        """重新开始"""
        self.game_phase = 'preview'
        self.current_step_index = 0
        self.auto_play = False
        self.step_completed = False
        self._reset_canvas()
        
        # 重置所有步骤
        for step in self.current_drawing:
            step.progress = 0.0
            step.completed = False
    
    def _redraw_up_to_current_step(self):
        """重绘到当前步骤"""
        self._reset_canvas()
        for i in range(self.current_step_index):
            self.current_drawing[i].progress = 1.0
            self.current_drawing[i].completed = True
            self.current_drawing[i].draw(self.canvas_surface)
        
        # 重置当前步骤
        if self.current_step_index < len(self.current_drawing):
            self.current_drawing[self.current_step_index].progress = 0.0
            self.current_drawing[self.current_step_index].completed = False
    
    def update(self, dt: float):
        """更新游戏状态"""
        # 更新语音状态
        if self.voice_playing and not is_speaking():
            self.voice_playing = False
        
        # 更新所有喇叭按钮
        mouse_pos = pygame.mouse.get_pos()
        for button, _ in self.speaker_buttons:
            button.update(mouse_pos)
        
        if self.game_phase == 'steps' and self.current_drawing:
            if self.current_step_index < len(self.current_drawing):
                current_step = self.current_drawing[self.current_step_index]
                
                # 更新当前步骤
                current_step.update(dt, speed=2.0)
                
                # 检查步骤是否完成
                if current_step.completed and not self.step_completed:
                    self.step_completed = True
                    
                    # 播放完成音效和语音提示
                    if self.current_step_index < len(self.current_drawing) - 1:
                        # 不是最后一步
                        next_step = self.current_drawing[self.current_step_index + 1]
                        speak(f"很好！接下来{next_step.description}")
                    
                    # 自动播放模式下自动进入下一步
                    if self.auto_play:
                        pygame.time.set_timer(pygame.USEREVENT + 1, 1500)  # 1.5秒后下一步
    
    def draw(self, screen: pygame.Surface):
        """绘制游戏画面"""
        screen.fill(COLORS['background'])
        
        # 清空喇叭按钮
        self.speaker_buttons.clear()
        
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
        
        # 计算起始位置使按钮居中
        total_width = cols * button_size + (cols - 1) * spacing
        total_height = rows * button_size + (rows - 1) * spacing
        start_x = (self.get_screen_width() - total_width) // 2
        start_y = (self.get_screen_height() - total_height) // 2 + self.scale_value(50)
        
        # 创建按钮
        for i, drawing in enumerate(self.available_drawings):
            row = i // cols
            col = i % cols
            
            x = start_x + col * (button_size + spacing)
            y = start_y + row * (button_size + spacing)
            
            button_rect = pygame.Rect(x, y, button_size, button_size)
            self.drawing_buttons.append(button_rect)
            
            # 绘制按钮背景
            pygame.draw.rect(screen, COLORS['white'], button_rect)
            pygame.draw.rect(screen, COLORS['primary'], button_rect, 3)
            
            # 绘制缩略图
            thumb_surface = pygame.Surface((button_size - 20, button_size - 40))
            thumb_surface.fill((255, 255, 255))
            
            # 快速绘制所有步骤作为缩略图
            for step_config in drawing.get('steps', []):
                color = tuple(step_config.get('color', [0, 0, 0]))
                for stroke_config in step_config.get('strokes', []):
                    stroke_points = self.config_loader.convert_stroke_to_points(stroke_config)
                    for points in stroke_points:
                        if len(points) >= 2:
                            # 缩放点到缩略图大小
                            scale_factor = (button_size - 20) / 400
                            scaled_points = [
                                (int((p[0] - 100) * scale_factor + 10),
                                 int((p[1] - 100) * scale_factor + 10))
                                for p in points
                            ]
                            
                            stroke_type = stroke_config.get('type')
                            is_closed = stroke_type in ['circle', 'polygon', 'rectangle'] and stroke_config.get('closed', True)
                            
                            if is_closed and len(scaled_points) > 2:
                                if color != (255, 255, 255):
                                    pygame.draw.polygon(thumb_surface, color, scaled_points, 0)
                                pygame.draw.polygon(thumb_surface, (0, 0, 0), scaled_points, 2)
                            else:
                                if len(scaled_points) == 2:
                                    pygame.draw.line(thumb_surface, color, scaled_points[0], scaled_points[1], 3)
                                else:
                                    pygame.draw.lines(thumb_surface, color, False, scaled_points, 3)
            
            screen.blit(thumb_surface, (x + 10, y + 10))
            
            # 绘制名称
            name_font = get_chinese_font(self.scale_font_size(20))
            name_text = drawing.get('name', '未命名')
            name_surf = name_font.render(name_text, True, COLORS['text'])
            name_rect = name_surf.get_rect(centerx=button_rect.centerx, 
                                          bottom=button_rect.bottom - 5)
            screen.blit(name_surf, name_rect)
    
    def _draw_preview(self, screen: pygame.Surface):
        """绘制预览界面"""
        # 标题
        title_font = get_chinese_font(self.scale_font_size(36))
        title = f"我们来画{self.drawing_name}"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(self.get_center_x(), self.scale_value(50)))
        screen.blit(title_surf, title_rect)
        
        # 创建标题旁的喇叭按钮
        speaker_x = title_rect.right + self.scale_value(10)
        speaker_y = title_rect.centery
        title_speaker = SpeakerButton(speaker_x, speaker_y, self.scale_value(30))
        self.speaker_buttons.append((title_speaker, title))
        
        # 绘制预览画布
        canvas_x = (self.get_screen_width() - self.canvas_surface.get_width()) // 2
        canvas_y = self.scale_value(100)
        
        # 画布背景
        canvas_rect = pygame.Rect(canvas_x - 5, canvas_y - 5,
                                self.canvas_surface.get_width() + 10,
                                self.canvas_surface.get_height() + 10)
        pygame.draw.rect(screen, COLORS['secondary'], canvas_rect)
        
        # 绘制预览
        temp_surface = self.canvas_surface.copy()
        for step in self.current_drawing:
            step.progress = 1.0
            step.draw(temp_surface)
        
        screen.blit(temp_surface, (canvas_x, canvas_y))
        
        # 绘制控制按钮
        self._draw_control_buttons(screen)
        
        # 提示文字
        hint_font = get_chinese_font(self.scale_font_size(24))
        hint_text = "点击播放按钮开始学习"
        hint_surf = hint_font.render(hint_text, True, COLORS['text'])
        hint_rect = hint_surf.get_rect(center=(self.get_center_x(), 
                                              canvas_y + self.canvas_surface.get_height() + self.scale_value(30)))
        screen.blit(hint_surf, hint_rect)
    
    def _draw_steps(self, screen: pygame.Surface):
        """绘制分步教学界面"""
        # 标题和步骤信息
        title_font = get_chinese_font(self.scale_font_size(28))
        if self.current_step_index < len(self.current_drawing):
            current_step = self.current_drawing[self.current_step_index]
            step_info = f"第{self.current_step_index + 1}步：{current_step.description}"
        else:
            step_info = "完成！"
        
        title_surf = title_font.render(step_info, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(self.get_center_x(), self.scale_value(50)))
        screen.blit(title_surf, title_rect)
        
        # 创建步骤说明旁的喇叭按钮
        speaker_x = title_rect.right + self.scale_value(10)
        speaker_y = title_rect.centery
        step_speaker = SpeakerButton(speaker_x, speaker_y, self.scale_value(30))
        self.speaker_buttons.append((step_speaker, step_info))
        
        # 绘制画布
        canvas_x = (self.get_screen_width() - self.canvas_surface.get_width()) // 2
        canvas_y = self.scale_value(100)
        
        # 画布背景
        canvas_rect = pygame.Rect(canvas_x - 5, canvas_y - 5,
                                self.canvas_surface.get_width() + 10,
                                self.canvas_surface.get_height() + 10)
        pygame.draw.rect(screen, COLORS['secondary'], canvas_rect)
        
        # 绘制之前的步骤和当前步骤
        temp_surface = self.canvas_surface.copy()
        
        # 绘制所有已完成的步骤
        for i in range(self.current_step_index + 1):
            if i < len(self.current_drawing):
                self.current_drawing[i].draw(temp_surface)
        
        screen.blit(temp_surface, (canvas_x, canvas_y))
        
        # 绘制控制按钮
        self._draw_control_buttons(screen)
        
        # 进度信息
        progress_font = get_chinese_font(self.scale_font_size(20))
        progress_text = f"进度：{self.current_step_index + 1}/{len(self.current_drawing)}"
        progress_surf = progress_font.render(progress_text, True, COLORS['text'])
        progress_rect = progress_surf.get_rect(right=self.get_screen_width() - self.scale_value(20),
                                             top=self.scale_value(20))
        screen.blit(progress_surf, progress_rect)
    
    def _draw_complete(self, screen: pygame.Surface):
        """绘制完成界面"""
        # 标题
        title_font = get_chinese_font(self.scale_font_size(36))
        title = "太棒了！你完成了！"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(self.get_center_x(), self.scale_value(50)))
        screen.blit(title_surf, title_rect)
        
        # 绘制完成的画
        canvas_x = (self.get_screen_width() - self.canvas_surface.get_width()) // 2
        canvas_y = self.scale_value(100)
        
        # 画布背景
        canvas_rect = pygame.Rect(canvas_x - 5, canvas_y - 5,
                                self.canvas_surface.get_width() + 10,
                                self.canvas_surface.get_height() + 10)
        pygame.draw.rect(screen, COLORS['secondary'], canvas_rect)
        
        screen.blit(self.canvas_surface, (canvas_x, canvas_y))
        
        # 绘制笑脸
        face_size = self.scale_value(80)
        face_x = self.get_center_x()
        face_y = canvas_y + self.canvas_surface.get_height() + self.scale_value(50)
        draw_happy_face(screen, face_x, face_y, face_size, EMOJI_COLORS['happy'])
        
        # 提示文字
        hint_font = get_chinese_font(self.scale_font_size(24))
        hint_text = "点击任意位置返回"
        hint_surf = hint_font.render(hint_text, True, COLORS['text'])
        hint_rect = hint_surf.get_rect(center=(self.get_center_x(), 
                                              self.get_screen_height() - self.scale_value(50)))
        screen.blit(hint_surf, hint_rect)
        
        # 播放完成语音
        if not self.voice_playing:
            self.voice_playing = True
            speak("太棒了！你画得真好看！")
    
    def _draw_control_buttons(self, screen: pygame.Surface):
        """绘制控制按钮"""
        button_font = get_chinese_font(self.scale_font_size(20))
        
        # 播放/暂停按钮
        if self.play_button:
            # 播放状态时显示绿色，非播放状态显示主色
            color = COLORS['success'] if self.auto_play else COLORS['primary']
            pygame.draw.rect(screen, color, self.play_button)
            pygame.draw.rect(screen, COLORS['text'], self.play_button, 2)
            
            text = "暂停" if self.auto_play else "播放"
            text_surf = button_font.render(text, True, COLORS['white'])
            text_rect = text_surf.get_rect(center=self.play_button.center)
            screen.blit(text_surf, text_rect)
        
        # 上一步按钮
        if self.prev_button:
            # 禁用时显示灰色，启用时显示主色
            color = COLORS['disabled'] if self.current_step_index == 0 and self.game_phase == 'steps' else COLORS['primary']
            pygame.draw.rect(screen, color, self.prev_button)
            pygame.draw.rect(screen, COLORS['text'], self.prev_button, 2)
            
            text = "上一步"
            text_surf = button_font.render(text, True, COLORS['white'])
            text_rect = text_surf.get_rect(center=self.prev_button.center)
            screen.blit(text_surf, text_rect)
        
        # 下一步按钮
        if self.next_button:
            # 禁用时显示灰色，启用时显示主色
            color = COLORS['disabled'] if (self.game_phase == 'steps' and 
                                          self.current_step_index >= len(self.current_drawing) - 1) else COLORS['primary']
            pygame.draw.rect(screen, color, self.next_button)
            pygame.draw.rect(screen, COLORS['text'], self.next_button, 2)
            
            text = "下一步"
            text_surf = button_font.render(text, True, COLORS['white'])
            text_rect = text_surf.get_rect(center=self.next_button.center)
            screen.blit(text_surf, text_rect)
        
        # 重新开始按钮
        if self.restart_button:
            pygame.draw.rect(screen, COLORS['accent'], self.restart_button)
            pygame.draw.rect(screen, COLORS['text'], self.restart_button, 2)
            
            text = "重新开始"
            text_surf = button_font.render(text, True, COLORS['white'])
            text_rect = text_surf.get_rect(center=self.restart_button.center)
            screen.blit(text_surf, text_rect)
    
    def get_result(self) -> Dict[str, Any]:
        """获取游戏结果"""
        return {
            'completed': self.game_phase == 'complete',
            'drawing_name': self.drawing_name,
            'steps_completed': self.current_step_index + 1 if self.current_drawing else 0,
            'total_steps': len(self.current_drawing) if self.current_drawing else 0
        }
    
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.USEREVENT + 1 and self.auto_play:
            # 自动播放下一步
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # 取消定时器
            self._next_step()