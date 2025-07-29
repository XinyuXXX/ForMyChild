import pygame
import random
import math
from typing import List, Dict, Tuple
from ..config import COLORS
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak, stop_speaking, is_speaking
from ..utils.ui_utils import SpeakerButton
from ..utils.emoji_utils import draw_happy_face, draw_sad_face
from .base_game import BaseGame


class CountingObject:
    """可数的对象"""
    def __init__(self, x: int, y: int, size: int, image_type: str):
        self.x = x
        self.y = y
        self.size = size
        self.image_type = image_type
        self.visible = True
        
    def draw(self, screen: pygame.Surface):
        """绘制对象"""
        if not self.visible:
            return
            
        if self.image_type == 'apple':
            # 绘制苹果
            pygame.draw.circle(screen, (255, 0, 0), (self.x, self.y), self.size//2)
            pygame.draw.rect(screen, (139, 69, 19), 
                           (self.x - 2, self.y - self.size//2 - 5, 4, 8))
        elif self.image_type == 'star':
            # 绘制星星
            self._draw_star(screen)
        elif self.image_type == 'heart':
            # 绘制爱心
            self._draw_heart(screen)
        elif self.image_type == 'flower':
            # 绘制花朵
            self._draw_flower(screen)
            
    def _draw_star(self, screen: pygame.Surface):
        """绘制星星"""
        import math
        points = []
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            radius = self.size // 2 if i % 2 == 0 else self.size // 4
            x = self.x + radius * math.cos(angle)
            y = self.y + radius * math.sin(angle)
            points.append((x, y))
        pygame.draw.polygon(screen, (255, 215, 0), points)
        
    def _draw_heart(self, screen: pygame.Surface):
        """绘制爱心"""
        # 简化的爱心形状
        size = self.size // 2
        pygame.draw.circle(screen, (255, 105, 180), 
                         (self.x - size//2, self.y - size//2), size//2)
        pygame.draw.circle(screen, (255, 105, 180), 
                         (self.x + size//2, self.y - size//2), size//2)
        points = [
            (self.x - size, self.y),
            (self.x, self.y + size),
            (self.x + size, self.y)
        ]
        pygame.draw.polygon(screen, (255, 105, 180), points)
        
    def _draw_flower(self, screen: pygame.Surface):
        """绘制花朵"""
        # 花瓣
        petal_color = (255, 182, 193)
        for i in range(5):
            angle = i * 72 * 3.14159 / 180
            px = self.x + self.size // 3 * math.cos(angle)
            py = self.y + self.size // 3 * math.sin(angle)
            pygame.draw.circle(screen, petal_color, (int(px), int(py)), self.size // 4)
        # 花心
        pygame.draw.circle(screen, (255, 255, 0), (self.x, self.y), self.size // 5)


class CountingGame(BaseGame):
    """数一数游戏（响应式版本）"""
    
    def __init__(self, difficulty: int = 1):
        super().__init__(difficulty)
        
        # 根据难度设置游戏参数（1-10级）
        difficulty_params = {
            1: {'min': 1, 'max': 3, 'show_time': 5.0},    # 超简单：1-3个，显示5秒
            2: {'min': 1, 'max': 5, 'show_time': 5.0},    # 很简单：1-5个，显示5秒
            3: {'min': 2, 'max': 7, 'show_time': 6.0},    # 简单：2-7个，显示6秒
            4: {'min': 3, 'max': 9, 'show_time': 7.0},    # 较易：3-9个，显示7秒
            5: {'min': 4, 'max': 12, 'show_time': 8.0},   # 适中：4-12个，显示8秒
            6: {'min': 5, 'max': 15, 'show_time': 9.0},   # 稍难：5-15个，显示9秒
            7: {'min': 6, 'max': 18, 'show_time': 10.0},  # 困难：6-18个，显示10秒
            8: {'min': 8, 'max': 20, 'show_time': 10.0},  # 很困难：8-20个，显示10秒
            9: {'min': 10, 'max': 25, 'show_time': 10.0}, # 超困难：10-25个，显示10秒
            10: {'min': 12, 'max': 30, 'show_time': 10.0} # 极限：12-30个，显示10秒
        }
        
        params = difficulty_params.get(difficulty, difficulty_params[5])
        self.min_count = params['min']
        self.max_count = params['max']
        self.show_time = params['show_time']
        
        # 游戏状态
        self.objects: List[CountingObject] = []
        self.correct_count = 0
        self.player_answer = ""
        self.score = 0
        self.round_number = 0
        self.rounds_total = 10
        self.game_complete = False
        
        # 答案按钮
        self.answer_buttons = []
        self.submit_button = None
        self.clear_button = None
        
        # 计时器
        self.show_timer = 0
        self.is_showing = True
        self.wait_for_answer = False
        
        # 对象类型
        self.object_types = ['apple', 'star', 'heart', 'flower']
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 表情反馈
        self.show_result_emoji = None
        self.emoji_timer = 0
        
        # 等待语音标志
        self.waiting_for_voice = False
        self.voice_timer = 0
        
        # 开始第一轮
        self._start_new_round()
        
    def _start_new_round(self):
        """开始新一轮"""
        self.round_number += 1
        self.player_answer = ""
        self.wait_for_answer = False
        self.show_result_emoji = None
        
        if self.round_number > self.rounds_total:
            self.game_complete = True
            speak(f"游戏结束！你答对了{self.score}题！")
            return
            
        # 生成新的对象
        self.correct_count = random.randint(self.min_count, self.max_count)
        self.objects = []
        
        # 选择这一轮的对象类型
        object_type = random.choice(self.object_types)
        
        # 生成对象位置（响应式布局）
        self._generate_objects(object_type)
        
        # 开始显示计时
        self.show_timer = self.show_time
        self.is_showing = True
        
        # 语音提示
        type_names = {
            'apple': '苹果',
            'star': '星星', 
            'heart': '爱心',
            'flower': '花朵'
        }
        speak(f"第{self.round_number}题，请数一数有几个{type_names[object_type]}？")
        
    def _generate_objects(self, object_type: str):
        """生成对象（响应式布局）"""
        # 确保窗口尺寸有效
        if self.window_width <= 0 or self.window_height <= 0:
            self.window_width = 1024
            self.window_height = 768
            
        # 计算游戏区域
        margin = self.scale_value(100)
        area_width = max(200, self.window_width - 2 * margin)
        area_height = max(200, self.window_height - self.scale_value(300))  # 留出顶部和底部空间
        
        # 对象大小
        obj_size = self.scale_value(60)
        
        # 使用网格布局
        cols = min(5, max(3, area_width // (obj_size + self.scale_value(20))))
        rows = (self.correct_count + cols - 1) // cols
        
        # 计算网格间距
        h_spacing = area_width // cols
        v_spacing = area_height // max(rows, 1)
        
        # 居中整个网格
        grid_width = cols * h_spacing
        grid_height = rows * v_spacing
        start_x = (self.window_width - grid_width) // 2 + h_spacing // 2
        start_y = (self.window_height - grid_height) // 2
        
        # 生成对象
        for i in range(self.correct_count):
            row = i // cols
            col = i % cols
            
            # 添加一些随机偏移，让布局更自然
            x = start_x + col * h_spacing + random.randint(-10, 10)
            y = start_y + row * v_spacing + random.randint(-10, 10)
            
            obj = CountingObject(x, y, obj_size, object_type)
            self.objects.append(obj)
            
    def _create_answer_buttons(self):
        """创建答案按钮（响应式）"""
        self.answer_buttons = []
        
        # 数字按钮布局
        button_size = self.scale_value(60)
        spacing = self.scale_value(10)
        
        # 计算按钮起始位置（底部居中）
        total_width = 10 * button_size + 9 * spacing
        start_x = (self.window_width - total_width) // 2
        button_y = self.window_height - self.scale_value(150)
        
        # 创建0-9的按钮
        for i in range(10):
            x = start_x + i * (button_size + spacing)
            rect = pygame.Rect(x, button_y, button_size, button_size)
            self.answer_buttons.append({'rect': rect, 'value': str(i)})
            
        # 提交和清除按钮
        button_width = self.scale_value(100)
        button_height = self.scale_value(40)
        
        self.submit_button = pygame.Rect(
            self.window_width // 2 - button_width - self.scale_value(20),
            self.window_height - self.scale_value(60),
            button_width, button_height
        )
        
        self.clear_button = pygame.Rect(
            self.window_width // 2 + self.scale_value(20),
            self.window_height - self.scale_value(60),
            button_width, button_height
        )
        
    def handle_click(self, pos: Tuple[int, int]):
        """处理点击"""
        if self.game_complete:
            return
            
        # 检查喇叭按钮
        for button, text in self.speaker_buttons:
            if button.check_click(pos):
                speak(text)
                return
                
        if self.wait_for_answer:
            # 检查数字按钮
            for btn in self.answer_buttons:
                if btn['rect'].collidepoint(pos):
                    if len(self.player_answer) < 2:  # 最多两位数
                        self.player_answer += btn['value']
                        speak(btn['value'])
                    return
                    
            # 检查提交按钮
            if self.submit_button and self.submit_button.collidepoint(pos):
                if self.player_answer:
                    self._check_answer()
                return
                
            # 检查清除按钮
            if self.clear_button and self.clear_button.collidepoint(pos):
                self.player_answer = ""
                speak("已清除")
                return
                
    def _check_answer(self):
        """检查答案"""
        try:
            answer = int(self.player_answer)
            if answer == self.correct_count:
                self.score += 1
                self.show_result_emoji = 'happy'
                speak(f"答对了！是{self.correct_count}个！")
                self.emoji_timer = 2
            else:
                self.show_result_emoji = 'sad'
                speak("再数数看！")
                self.emoji_timer = 1.5
                # 清空输入，让玩家重新输入
                self.player_answer = ""
                # 答错后需要重新显示物体
                self.wait_for_answer = False
                self.is_showing = True
                self.show_timer = self.show_time
        except:
            return
        
    def update(self, dt: float):
        """更新游戏状态"""
        if self.game_complete:
            return
            
        # 更新显示计时器
        if self.is_showing:
            self.show_timer -= dt
            if self.show_timer <= 0:
                self.is_showing = False
                self.wait_for_answer = True
                # 创建答案按钮
                self._create_answer_buttons()
                speak("现在请输入你数到的数量")
                self.waiting_for_voice = True
                self.voice_timer = 0
                
        # 处理语音等待
        if self.waiting_for_voice:
            self.voice_timer += dt
            # 等待语音播放完毕，或超时3秒
            if not is_speaking() or self.voice_timer > 3.0:
                self.waiting_for_voice = False
                
        # 更新表情计时器
        if self.emoji_timer > 0:
            self.emoji_timer -= dt
            if self.emoji_timer <= 0:
                if self.show_result_emoji == 'happy':
                    # 答对了，等待语音播放完毕后才进入下一题
                    self.show_result_emoji = None
                    self.waiting_for_voice = True
                    self.voice_timer = 0
                    # 设置一个延迟任务
                    self.pending_next_round = True
                else:
                    # 答错了清除表情，物体已经在_check_answer中设置为重新显示
                    self.show_result_emoji = None
                    
        # 处理延迟的下一轮
        if hasattr(self, 'pending_next_round') and self.pending_next_round and not self.waiting_for_voice:
            self.pending_next_round = False
            self._start_new_round()
                
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
            
        # 绘制标题
        title_font = get_chinese_font(self.scale_font_size(48))
        title = f"数一数 - 第 {self.round_number}/{self.rounds_total} 题"
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
        
        if self.objects and self.objects[0].image_type:
            type_names = {
                'apple': '苹果',
                'star': '星星',
                'heart': '爱心',
                'flower': '花朵'
            }
            obj_name = type_names.get(self.objects[0].image_type, '')
            self.speaker_buttons.append((speaker_btn, f"请数一数有几个{obj_name}"))
        
        # 绘制对象（显示阶段或答错时显示）
        if self.is_showing or (self.show_result_emoji == 'sad'):
            for obj in self.objects:
                obj.draw(screen)
                
        # 绘制倒计时（显示阶段）
        if self.is_showing:
            timer_font = get_chinese_font(self.scale_font_size(48))
            timer_text = f"{int(self.show_timer + 1)}"
            timer_surf = timer_font.render(timer_text, True, COLORS['danger'])
            timer_rect = timer_surf.get_rect(right=self.window_width - self.scale_value(20), 
                                            top=self.scale_value(20))
            screen.blit(timer_surf, timer_rect)
            
        # 绘制答案输入界面（答题阶段）
        if self.wait_for_answer and not self.show_result_emoji:
            self._draw_answer_interface(screen)
            
        # 绘制表情反馈
        if self.show_result_emoji:
            emoji_size = self.scale_value(100)
            if self.show_result_emoji == 'happy':
                draw_happy_face(screen, self.get_center_x(), self.get_center_y(), emoji_size)
            elif self.show_result_emoji == 'sad':
                draw_sad_face(screen, self.get_center_x(), self.get_center_y(), emoji_size)
                
        # 绘制得分
        score_font = get_chinese_font(self.scale_font_size(32))
        score_text = f"得分: {self.score}"
        score_surf = score_font.render(score_text, True, COLORS['text'])
        screen.blit(score_surf, (self.scale_value(20), self.scale_value(100)))
        
        # 绘制所有喇叭按钮
        for button, _ in self.speaker_buttons:
            button.draw(screen)
            
    def _draw_answer_interface(self, screen: pygame.Surface):
        """绘制答案输入界面"""
        # 显示当前输入
        answer_font = get_chinese_font(self.scale_font_size(72))
        display_text = self.player_answer if self.player_answer else "?"
        answer_surf = answer_font.render(display_text, True, COLORS['primary'])
        answer_rect = answer_surf.get_rect(center=(self.get_center_x(), self.get_center_y()))
        screen.blit(answer_surf, answer_rect)
        
        # 绘制数字按钮
        button_font = get_chinese_font(self.scale_font_size(36))
        for btn in self.answer_buttons:
            # 按钮背景
            pygame.draw.rect(screen, COLORS['primary'], btn['rect'], border_radius=5)
            # 按钮文字
            text_surf = button_font.render(btn['value'], True, COLORS['white'])
            text_rect = text_surf.get_rect(center=btn['rect'].center)
            screen.blit(text_surf, text_rect)
            
        # 绘制提交按钮
        if self.submit_button:
            color = COLORS['success'] if self.player_answer else COLORS['secondary']
            pygame.draw.rect(screen, color, self.submit_button, border_radius=5)
            submit_text = button_font.render("提交", True, COLORS['white'])
            submit_rect = submit_text.get_rect(center=self.submit_button.center)
            screen.blit(submit_text, submit_rect)
            
        # 绘制清除按钮
        if self.clear_button:
            pygame.draw.rect(screen, COLORS['danger'], self.clear_button, border_radius=5)
            clear_text = button_font.render("清除", True, COLORS['white'])
            clear_rect = clear_text.get_rect(center=self.clear_button.center)
            screen.blit(clear_text, clear_rect)
            
    def _draw_game_complete(self, screen: pygame.Surface):
        """绘制游戏结束画面"""
        # 半透明背景
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # 结果
        result_font = get_chinese_font(self.scale_font_size(72))
        score_percent = (self.score / self.rounds_total) * 100
        
        if score_percent >= 80:
            result_text = "太棒了！"
            color = COLORS['success']
            draw_happy_face(screen, self.get_center_x(), 
                          self.get_center_y() - self.scale_value(150), 
                          self.scale_value(100))
        elif score_percent >= 60:
            result_text = "很不错！"
            color = COLORS['primary']
            draw_happy_face(screen, self.get_center_x(), 
                          self.get_center_y() - self.scale_value(150), 
                          self.scale_value(100))
        else:
            result_text = "继续努力！"
            color = COLORS['secondary']
            draw_sad_face(screen, self.get_center_x(), 
                        self.get_center_y() - self.scale_value(150), 
                        self.scale_value(100))
            
        text_surf = result_font.render(result_text, True, color)
        text_rect = text_surf.get_rect(center=(self.get_center_x(), self.get_center_y()))
        screen.blit(text_surf, text_rect)
        
        # 得分
        score_font = get_chinese_font(self.scale_font_size(36))
        score_text = f"答对了 {self.score} / {self.rounds_total} 题"
        score_surf = score_font.render(score_text, True, COLORS['white'])
        score_rect = score_surf.get_rect(center=(self.get_center_x(), 
                                               self.get_center_y() + self.scale_value(80)))
        screen.blit(score_surf, score_rect)
        
    def get_result(self) -> Dict:
        """获取游戏结果"""
        return {
            'score': self.score,
            'total': self.rounds_total,
            'accuracy': (self.score / self.rounds_total) * 100 if self.rounds_total > 0 else 0
        }