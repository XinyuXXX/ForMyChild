import pygame
import random
import math
from typing import List, Tuple, Dict
from ..config import COLORS
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak, stop_speaking, is_speaking
from ..utils.ui_utils import SpeakerButton
from ..utils.emoji_utils import draw_happy_face, draw_sad_face, draw_thinking_face
from .base_game import BaseGame


class DifferenceObject:
    """可以产生差异的对象"""
    def __init__(self, x: int, y: int, size: int, shape: str, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.size = size
        self.shape = shape
        self.color = color
        self.rect = pygame.Rect(x - size//2, y - size//2, size, size)
        self.found = False
        
    def draw(self, screen: pygame.Surface):
        """绘制对象"""
        # 定义轮廓颜色（深色）
        outline_color = (50, 50, 50)
        outline_width = 3
        
        if self.shape == 'circle':
            # 先画轮廓，再画填充
            pygame.draw.circle(screen, outline_color, (self.x, self.y), self.size//2, outline_width)
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.size//2 - outline_width)
        elif self.shape == 'square':
            # 先画轮廓
            pygame.draw.rect(screen, outline_color, self.rect, outline_width)
            # 再画内部
            inner_rect = pygame.Rect(self.rect.x + outline_width, 
                                   self.rect.y + outline_width,
                                   self.rect.width - 2*outline_width,
                                   self.rect.height - 2*outline_width)
            pygame.draw.rect(screen, self.color, inner_rect)
        elif self.shape == 'triangle':
            points = [
                (self.x, self.y - self.size//2),
                (self.x - self.size//2, self.y + self.size//2),
                (self.x + self.size//2, self.y + self.size//2)
            ]
            # 先画轮廓
            pygame.draw.polygon(screen, outline_color, points, outline_width)
            # 计算内部三角形的点
            center_x = sum(p[0] for p in points) / 3
            center_y = sum(p[1] for p in points) / 3
            inner_points = []
            for px, py in points:
                # 向中心缩小
                dx = px - center_x
                dy = py - center_y
                scale = 0.85  # 缩小比例
                inner_points.append((center_x + dx * scale, center_y + dy * scale))
            pygame.draw.polygon(screen, self.color, inner_points)
        elif self.shape == 'star':
            self._draw_star(screen)
            
    def _draw_star(self, screen: pygame.Surface):
        """绘制星星"""
        angle = -math.pi / 2
        points = []
        for i in range(10):
            r = self.size // 2 if i % 2 == 0 else self.size // 4
            x = self.x + r * math.cos(angle)
            y = self.y + r * math.sin(angle)
            points.append((x, y))
            angle += math.pi / 5
        
        # 先画轮廓
        outline_color = (50, 50, 50)
        pygame.draw.polygon(screen, outline_color, points, 3)
        
        # 再画内部（稍微缩小）
        center_x = self.x
        center_y = self.y
        inner_points = []
        angle = -math.pi / 2
        for i in range(10):
            r = (self.size // 2 if i % 2 == 0 else self.size // 4) * 0.85
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            inner_points.append((x, y))
            angle += math.pi / 5
        pygame.draw.polygon(screen, self.color, inner_points)
        
    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """检查点是否在对象内"""
        return self.rect.collidepoint(pos)


class FindDifferenceGame(BaseGame):
    """找不同游戏（响应式版本）"""
    
    def __init__(self, difficulty: int = 1):
        super().__init__(difficulty)
        self._needs_regeneration = False
        
        # 根据难度设置游戏参数（1-10级）
        difficulty_params = {
            1: {'objects': 3, 'differences': 1, 'time': 60},   # 超简单
            2: {'objects': 4, 'differences': 1, 'time': 55},   # 很简单
            3: {'objects': 5, 'differences': 2, 'time': 50},   # 简单
            4: {'objects': 6, 'differences': 2, 'time': 45},   # 较易
            5: {'objects': 7, 'differences': 3, 'time': 40},   # 适中
            6: {'objects': 8, 'differences': 3, 'time': 35},   # 稍难
            7: {'objects': 9, 'differences': 4, 'time': 30},   # 困难
            8: {'objects': 10, 'differences': 4, 'time': 25},  # 很困难
            9: {'objects': 11, 'differences': 5, 'time': 20},  # 超困难
            10: {'objects': 12, 'differences': 5, 'time': 15}  # 极限
        }
        
        params = difficulty_params.get(difficulty, difficulty_params[5])
        self.objects_count = params['objects']
        self.differences_count = params['differences']
        self.time_limit = params['time']
        
        # 游戏状态
        self.left_objects: List[DifferenceObject] = []
        self.right_objects: List[DifferenceObject] = []
        self.differences: List[int] = []
        self.found_differences: List[int] = []
        self.score = 0
        self.time_remaining = self.time_limit
        self.game_complete = False
        self.start_time = pygame.time.get_ticks()
        
        # 多轮游戏设置
        self.round_number = 0
        self.rounds_total = 10  # 总共10个题目
        self.round_complete = False
        self.round_time_limit = 30  # 每轮30秒
        self.round_time_remaining = self.round_time_limit
        
        # 可用的形状和颜色
        self.shapes = ['circle', 'square', 'triangle', 'star']
        self.colors = [
            (255, 99, 71),   # 番茄红
            (60, 179, 113),  # 中海绿
            (106, 90, 205),  # 石板蓝
            (255, 165, 0),   # 橙色
            (255, 20, 147),  # 深粉红
            (64, 224, 208),  # 青绿色
            (255, 215, 0),   # 金色
        ]
        
        # 提示功能
        self.show_hint = False
        self.hint_timer = 0
        self.hint_countdown = 0
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 表情反馈
        self.show_result_emoji = None
        self.emoji_timer = 0
        
        # 等待语音标志
        self.waiting_for_next_round = False
        self.wait_timer = 0
        
        # 开始第一轮
        self._start_new_round()
        
    def update_window_size(self, width: int, height: int):
        """更新窗口大小时重新计算对象位置"""
        old_width = self.window_width
        old_height = self.window_height
        super().update_window_size(width, height)
        
        # 如果窗口大小改变了，重新调整对象位置
        if old_width != width or old_height != height:
            self._rescale_objects(old_width, old_height)
        
    def _start_new_round(self):
        """开始新一轮"""
        self.round_number += 1
        self.round_complete = False
        self.round_time_remaining = self.round_time_limit
        self.found_differences = []
        self.show_hint = False
        self.hint_timer = 0
        self.show_result_emoji = None
        
        if self.round_number > self.rounds_total:
            self.game_complete = True
            speak(f"游戏结束！你总共答对了{self.score}题！")
            return
            
        # 逐渐增加难度
        if self.round_number > 3:
            # 每3关增加一个物体，最多10个
            self.objects_count = min(10, 3 + (self.round_number - 1) // 3)
        if self.round_number > 5:
            # 第5关后增加不同点
            self.differences_count = min(3, 1 + (self.round_number - 5) // 3)
            
        # 生成新的对象
        self._generate_objects()
        
        # 播放新一轮提示
        speak(f"第{self.round_number}题，请找出{self.differences_count}个不同的地方！")
        
        # 在10秒后自动显示提示
        self.hint_countdown = 10
        
    def _rescale_objects(self, old_width: int, old_height: int):
        """重新缩放对象位置以适应新窗口大小"""
        if not self.left_objects or not self.right_objects:
            return
            
        # 计算缩放比例
        width_scale = self.window_width / old_width
        height_scale = self.window_height / old_height
        
        # 重新计算中心点
        old_center_x = old_width // 2
        new_center_x = self.window_width // 2
        
        # 调整左边对象
        for obj in self.left_objects:
            # 计算相对于左边中心的偏移
            old_left_center = old_center_x // 2
            relative_x = obj.x - old_left_center
            
            # 应用到新的左边中心
            new_left_center = new_center_x // 2
            obj.x = int(new_left_center + relative_x * width_scale)
            obj.y = int(obj.y * height_scale)
            
            # 更新矩形
            obj.rect = pygame.Rect(obj.x - obj.size//2, obj.y - obj.size//2, obj.size, obj.size)
            
        # 调整右边对象
        for i, obj in enumerate(self.right_objects):
            if obj is not None:
                # 使用与左边对象相同的相对位置
                left_obj = self.left_objects[i]
                old_left_center = old_center_x // 2
                relative_x = left_obj.x - old_left_center
                
                # 应用到新的右边中心
                new_right_center = new_center_x + (new_center_x // 2)
                obj.x = int(new_right_center + relative_x * width_scale)
                obj.y = int(obj.y * height_scale)
                
                # 更新矩形
                obj.rect = pygame.Rect(obj.x - obj.size//2, obj.y - obj.size//2, obj.size, obj.size)
    
    def _generate_objects(self):
        """生成左右两边的对象"""
        self.left_objects = []
        self.right_objects = []
        self.differences = []
        
        # 计算布局（响应式）
        center_x = self.get_center_x()
        center_y = self.get_center_y()
        
        # 左右两个区域的中心（确保对称）
        left_center_x = center_x // 2
        right_center_x = center_x + (center_x // 2)
        
        # 游戏区域大小（留出边距）
        # 每个半边的可用宽度（留出中间分隔线和边距）
        half_width = center_x - self.scale_value(50)  # 50像素边距
        area_width = int(half_width * 0.8)  # 使用80%的半边宽度
        area_height = int(self.window_height * 0.6)  # 使用60%的高度
        
        # 物体大小（根据窗口大小调整）
        min_size = self.scale_value(40)
        max_size = self.scale_value(80)
        
        # 生成左边的对象
        attempts = 0
        while len(self.left_objects) < self.objects_count and attempts < 100:
            attempts += 1
            
            # 确保对象在左半边的边界内
            x = left_center_x + random.randint(-area_width//2, area_width//2)
            y = center_y + random.randint(-area_height//2, area_height//2)
            
            # 确保不会超出左边界和中线
            margin = self.scale_value(30)
            x = max(margin + max_size//2, min(x, center_x - margin - max_size//2))
            y = max(self.scale_value(150), min(y, self.window_height - self.scale_value(150)))
            size = random.randint(min_size, max_size)
            shape = random.choice(self.shapes)
            color = random.choice(self.colors)
            
            new_obj = DifferenceObject(x, y, size, shape, color)
            
            # 检查是否与其他对象重叠
            overlap = False
            for obj in self.left_objects:
                if self._objects_overlap(new_obj, obj):
                    overlap = True
                    break
                    
            if not overlap:
                self.left_objects.append(new_obj)
                
        # 复制到右边（初始相同）
        for i, obj in enumerate(self.left_objects):
            # 计算对称位置：相对于左边中心的偏移，应用到右边中心
            relative_x = obj.x - left_center_x
            new_x = right_center_x + relative_x
            
            new_obj = DifferenceObject(
                new_x,
                obj.y,
                obj.size,
                obj.shape,
                obj.color
            )
            self.right_objects.append(new_obj)
            
        # 创建差异
        available_indices = list(range(len(self.right_objects)))
        random.shuffle(available_indices)
        
        for i in range(min(self.differences_count, len(available_indices))):
            diff_index = available_indices[i]
            self.differences.append(diff_index)
            
            # 随机选择差异类型
            diff_type = random.choice(['missing', 'color', 'shape', 'size'])
            
            if diff_type == 'missing':
                # 右边缺少这个对象
                self.right_objects[diff_index] = None
            elif diff_type == 'color':
                # 改变颜色
                new_color = random.choice([c for c in self.colors if c != self.right_objects[diff_index].color])
                self.right_objects[diff_index].color = new_color
            elif diff_type == 'shape':
                # 改变形状
                new_shape = random.choice([s for s in self.shapes if s != self.right_objects[diff_index].shape])
                self.right_objects[diff_index].shape = new_shape
            elif diff_type == 'size':
                # 改变大小（更明显的差异）
                old_size = self.right_objects[diff_index].size
                # 增加30-40%的大小差异
                size_change = random.choice([-0.35, -0.3, 0.3, 0.35])
                new_size = int(old_size * (1 + size_change))
                new_size = max(min_size, min(new_size, max_size))
                self.right_objects[diff_index].size = new_size
                # 更新矩形
                obj = self.right_objects[diff_index]
                obj.rect = pygame.Rect(obj.x - new_size//2, obj.y - new_size//2, new_size, new_size)
                
    def _objects_overlap(self, obj1: DifferenceObject, obj2: DifferenceObject) -> bool:
        """检查两个对象是否重叠"""
        return obj1.rect.colliderect(obj2.rect)
        
    def handle_click(self, pos: Tuple[int, int]):
        """处理鼠标点击"""
        if self.game_complete or self.round_complete:
            return
            
        # 检查喇叭按钮
        for button, text in self.speaker_buttons:
            if button.check_click(pos):
                speak(text)
                return
                
        # 获取中心点
        center_x = self.get_center_x()
        
        # 检查是否点击在右边区域
        if pos[0] > center_x:
            # 检查是否点击到了差异
            for i, obj in enumerate(self.right_objects):
                if i in self.differences and i not in self.found_differences:
                    if obj is None:
                        # 检查是否点击了缺失对象的位置
                        left_obj = self.left_objects[i]
                        # 计算对称位置
                        left_center_x = center_x // 2
                        right_center_x = center_x + (center_x // 2)
                        relative_x = left_obj.x - left_center_x
                        expected_x = right_center_x + relative_x
                        
                        test_rect = pygame.Rect(
                            expected_x - left_obj.size//2,
                            left_obj.y - left_obj.size//2,
                            left_obj.size,
                            left_obj.size
                        )
                        if test_rect.collidepoint(pos):
                            self._found_difference(i)
                            return
                    elif obj.contains_point(pos):
                        self._found_difference(i)
                        return
                        
    def _found_difference(self, index: int):
        """找到了一个差异"""
        self.found_differences.append(index)
        
        # 显示开心表情
        self.show_result_emoji = 'happy'
        self.emoji_timer = 1.5
        
        if len(self.found_differences) == len(self.differences):
            # 找到了所有差异
            self.score += 1
            self.round_complete = True
            speak("太棒了！你找到了所有不同的地方！")
            # 标记需要等待语音
            self.waiting_for_next_round = True
            self.wait_timer = 0
        else:
            # 还有差异未找到
            remaining = len(self.differences) - len(self.found_differences)
            speak(f"很好！还有{remaining}个不同的地方！")
            
    def update(self, dt: float):
        """更新游戏状态"""
        if self.game_complete:
            return
            
        # 处理等待语音播放完毕
        if self.waiting_for_next_round:
            self.wait_timer += dt
            # 等待语音播放完毕后再等1.5秒，确保声音完全结束
            if (not is_speaking() and self.wait_timer > 1.5) or self.wait_timer > 5.0:
                self.waiting_for_next_round = False
                self._start_new_round()
                return
            
        # 更新时间
        if not self.round_complete:
            self.round_time_remaining -= dt
            
            if self.round_time_remaining <= 0:
                # 时间到了，但不直接进入下一题
                speak("时间到了！再试试看！")
                # 重置时间，让玩家继续尝试
                self.round_time_remaining = self.round_time_limit
                
        # 更新提示倒计时
        if self.hint_countdown > 0 and not self.round_complete:
            self.hint_countdown -= dt
            if self.hint_countdown <= 0 and len(self.found_differences) < len(self.differences):
                self.show_hint = True
                self.hint_timer = 3  # 显示3秒
                
        # 更新提示计时器
        if self.hint_timer > 0:
            self.hint_timer -= dt
            if self.hint_timer <= 0:
                self.show_hint = False
                
        # 更新表情计时器
        if self.emoji_timer > 0:
            self.emoji_timer -= dt
            if self.emoji_timer <= 0:
                self.show_result_emoji = None
                
        # 更新喇叭按钮
        mouse_pos = pygame.mouse.get_pos()
        for button, _ in self.speaker_buttons:
            button.update(mouse_pos)
            
    def draw(self, screen: pygame.Surface):
        """绘制游戏画面"""
        screen.fill(COLORS['background'])
        
        # 清空喇叭按钮列表
        self.speaker_buttons.clear()
        
        if self.game_complete:
            self._draw_game_complete(screen)
            return
            
        # 获取窗口尺寸
        center_x = self.get_center_x()
        center_y = self.get_center_y()
        
        # 绘制标题
        title_font = get_chinese_font(self.scale_font_size(48))
        title = f"找不同 - 第 {self.round_number}/{self.rounds_total} 题"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(center_x, self.scale_value(50)))
        screen.blit(title_surf, title_rect)
        
        # 添加喇叭按钮
        speaker_btn = SpeakerButton(
            center_x + title_surf.get_width()//2 + self.scale_value(50),
            self.scale_value(50),
            self.scale_value(25)
        )
        speaker_btn.draw(screen)
        self.speaker_buttons.append((speaker_btn, f"请找出{self.differences_count}个不同的地方"))
        
        # 绘制分隔线
        pygame.draw.line(screen, COLORS['text'], 
                        (center_x, self.scale_value(100)), 
                        (center_x, self.window_height - self.scale_value(100)), 
                        2)
                        
        # 绘制左右标签
        label_font = get_chinese_font(self.scale_font_size(32))
        left_label = label_font.render("原图", True, COLORS['primary'])
        right_label = label_font.render("找不同", True, COLORS['secondary'])
        
        screen.blit(left_label, left_label.get_rect(
            center=(center_x//2, self.scale_value(100))
        ))
        screen.blit(right_label, right_label.get_rect(
            center=(center_x + center_x//2, self.scale_value(100))
        ))
        
        # 绘制对象
        for obj in self.left_objects:
            obj.draw(screen)
            
        for i, obj in enumerate(self.right_objects):
            if obj is not None:
                # 如果已找到，高亮显示
                if i in self.found_differences:
                    pygame.draw.circle(screen, COLORS['success'], 
                                     (obj.x, obj.y), 
                                     obj.size//2 + self.scale_value(10), 3)
                obj.draw(screen)
            elif i in self.found_differences:
                # 如果是消失的对象且已找到，画一个圆圈标记
                left_obj = self.left_objects[i]
                # 计算对称位置
                center_x = self.get_center_x()
                left_center_x = center_x // 2
                right_center_x = center_x + (center_x // 2)
                relative_x = left_obj.x - left_center_x
                marker_x = right_center_x + relative_x
                
                pygame.draw.circle(screen, COLORS['success'], 
                                 (marker_x, left_obj.y), 
                                 left_obj.size//2 + self.scale_value(10), 3)
                # 画一个叉表示消失
                cross_size = self.scale_value(15)
                pygame.draw.line(screen, COLORS['danger'],
                               (marker_x - cross_size, left_obj.y - cross_size),
                               (marker_x + cross_size, left_obj.y + cross_size), 3)
                pygame.draw.line(screen, COLORS['danger'],
                               (marker_x + cross_size, left_obj.y - cross_size),
                               (marker_x - cross_size, left_obj.y + cross_size), 3)
                
        # 绘制提示
        if self.show_hint:
            for i in self.differences:
                if i not in self.found_differences:
                    obj = self.left_objects[i]
                    # 在左边对象周围画圈提示
                    pygame.draw.circle(screen, COLORS['warning'], 
                                     (obj.x, obj.y), 
                                     obj.size//2 + self.scale_value(15), 3)
                    break  # 只提示一个
                    
        # 绘制进度
        self._draw_progress(screen)
        
        # 绘制表情反馈
        if self.show_result_emoji:
            emoji_x = center_x
            emoji_y = center_y
            emoji_size = self.scale_value(100)
            
            if self.show_result_emoji == 'happy':
                draw_happy_face(screen, emoji_x, emoji_y, emoji_size)
            elif self.show_result_emoji == 'sad':
                draw_sad_face(screen, emoji_x, emoji_y, emoji_size)
                
        # 绘制所有喇叭按钮
        for button, _ in self.speaker_buttons:
            button.draw(screen)
            
    def _draw_progress(self, screen: pygame.Surface):
        """绘制进度信息"""
        info_font = get_chinese_font(self.scale_font_size(28))
        
        # 已找到的差异
        found_text = f"已找到: {len(self.found_differences)}/{len(self.differences)}"
        found_surf = info_font.render(found_text, True, COLORS['text'])
        screen.blit(found_surf, (self.scale_value(20), self.window_height - self.scale_value(60)))
        
        # 得分
        score_text = f"得分: {self.score}/{self.round_number-1}"
        score_surf = info_font.render(score_text, True, COLORS['text'])
        screen.blit(score_surf, (self.scale_value(20), self.window_height - self.scale_value(30)))
        
        # 时间
        time_text = f"时间: {int(self.round_time_remaining)}秒"
        time_color = COLORS['danger'] if self.round_time_remaining < 10 else COLORS['text']
        time_surf = info_font.render(time_text, True, time_color)
        screen.blit(time_surf, (self.window_width - self.scale_value(150), 
                               self.window_height - self.scale_value(40)))
                               
    def _draw_game_complete(self, screen: pygame.Surface):
        """绘制游戏结束画面"""
        center_x = self.get_center_x()
        center_y = self.get_center_y()
        
        # 半透明背景
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # 结果文字
        result_font = get_chinese_font(self.scale_font_size(72))
        score_percent = (self.score / self.rounds_total) * 100
        
        if score_percent >= 80:
            result_text = "太棒了！"
            color = COLORS['success']
            draw_happy_face(screen, center_x, center_y - self.scale_value(150), self.scale_value(100))
        elif score_percent >= 60:
            result_text = "很不错哦！"
            color = COLORS['primary']
            draw_thinking_face(screen, center_x, center_y - self.scale_value(150), self.scale_value(100))
        else:
            result_text = "继续努力！"
            color = COLORS['secondary']
            draw_sad_face(screen, center_x, center_y - self.scale_value(150), self.scale_value(100))
            
        text_surf = result_font.render(result_text, True, color)
        text_rect = text_surf.get_rect(center=(center_x, center_y))
        screen.blit(text_surf, text_rect)
        
        # 得分详情
        score_font = get_chinese_font(self.scale_font_size(36))
        score_text = f"答对了 {self.score} / {self.rounds_total} 题"
        score_surf = score_font.render(score_text, True, COLORS['white'])
        score_rect = score_surf.get_rect(center=(center_x, center_y + self.scale_value(80)))
        screen.blit(score_surf, score_rect)
        
    def get_result(self) -> Dict:
        """获取游戏结果"""
        return {
            'score': self.score,
            'total': self.rounds_total,
            'accuracy': (self.score / self.rounds_total) * 100
        }