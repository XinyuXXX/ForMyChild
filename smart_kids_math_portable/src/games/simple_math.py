import pygame
import random
from typing import List, Dict, Tuple, Optional
from ..config import COLORS
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak, stop_speaking, is_speaking
from ..utils.ui_utils import SpeakerButton
from ..utils.emoji_utils import draw_happy_face, draw_sad_face
from .base_game import BaseGame


class SimpleMathGame(BaseGame):
    """简单数学游戏（响应式版本）"""
    
    def __init__(self, difficulty: int = 1):
        super().__init__(difficulty)
        
        # 根据难度设置游戏参数（1-10级）
        difficulty_params = {
            1: {'max': 5, 'ops': ['+'], 'negative': False},         # 超简单：0-5的加法
            2: {'max': 8, 'ops': ['+'], 'negative': False},         # 很简单：0-8的加法
            3: {'max': 10, 'ops': ['+'], 'negative': False},        # 简单：0-10的加法
            4: {'max': 10, 'ops': ['+', '-'], 'negative': False},   # 较易：0-10的加减法（无负数）
            5: {'max': 15, 'ops': ['+', '-'], 'negative': False},   # 适中：0-15的加减法（无负数）
            6: {'max': 20, 'ops': ['+', '-'], 'negative': False},   # 稍难：0-20的加减法（无负数）
            7: {'max': 30, 'ops': ['+', '-'], 'negative': True},    # 困难：0-30的加减法（可负数）
            8: {'max': 50, 'ops': ['+', '-'], 'negative': True},    # 很困难：0-50的加减法
            9: {'max': 80, 'ops': ['+', '-'], 'negative': True},    # 超困难：0-80的加减法
            10: {'max': 100, 'ops': ['+', '-'], 'negative': True}   # 极限：0-100的加减法
        }
        
        params = difficulty_params.get(difficulty, difficulty_params[5])
        self.max_number = params['max']
        self.operations = params['ops']
        self.allow_negative = params['negative']
        
        # 游戏状态
        self.current_question = None
        self.correct_answer = 0
        self.player_answer = ""
        self.score = 0
        self.round_number = 0
        self.rounds_total = 10
        self.game_complete = False
        
        # 答案选项
        self.answer_options = []
        self.answer_buttons = []
        
        # 表情反馈
        self.show_result_emoji = None
        self.emoji_timer = 0
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 等待语音标志
        self.waiting_for_voice = False
        self.voice_timer = 0
        self.pending_next_round = False
        
        # 开始第一轮
        self._start_new_round()
        
    def _start_new_round(self):
        """开始新一轮"""
        self.round_number += 1
        self.player_answer = ""
        self.show_result_emoji = None
        self.emoji_timer = 0
        self.waiting_for_voice = False
        self.voice_timer = 0
        self.pending_next_round = False
        
        if self.round_number > self.rounds_total:
            self.game_complete = True
            speak(f"游戏结束！你答对了{self.score}题！")
            return
            
        # 生成新题目
        self._generate_question()
        
        # 创建答案选项
        self._create_answer_options()
        
        # 语音提示
        question_for_speech = self.current_question.replace("-", "减").replace("+", "加").replace("=", "等于").replace("?", "")
        speak(f"第{self.round_number}题，{question_for_speech}")
        
    def _generate_question(self):
        """生成数学题目"""
        operation = random.choice(self.operations)
        
        if operation == '+':
            # 加法
            num1 = random.randint(0, self.max_number)
            num2 = random.randint(0, self.max_number - num1)
            self.correct_answer = num1 + num2
            self.current_question = f"{num1} + {num2} = ?"
            self.num1 = num1
            self.num2 = num2
            self.operation = operation
        else:
            # 减法
            if self.allow_negative:
                # 允许负数结果
                num1 = random.randint(0, self.max_number)
                num2 = random.randint(0, self.max_number)
            else:
                # 确保结果非负
                num1 = random.randint(0, self.max_number)
                num2 = random.randint(0, num1)
            self.correct_answer = num1 - num2
            self.current_question = f"{num1} - {num2} = ?"
            self.num1 = num1
            self.num2 = num2
            self.operation = operation
            
    def _create_answer_options(self):
        """创建答案选项（响应式布局）"""
        self.answer_options = [self.correct_answer]
        
        # 生成错误选项
        while len(self.answer_options) < 4:
            # 在正确答案附近生成错误选项
            offset = random.randint(-3, 3)
            wrong_answer = self.correct_answer + offset
            
            # 确保答案非负且不重复
            if wrong_answer >= 0 and wrong_answer not in self.answer_options:
                self.answer_options.append(wrong_answer)
                
        # 随机排序
        random.shuffle(self.answer_options)
        
        # 创建按钮（响应式布局）
        self.answer_buttons = []
        button_width = self.scale_value(100)
        button_height = self.scale_value(60)
        spacing = self.scale_value(20)
        
        # 2x2布局
        total_width = 2 * button_width + spacing
        total_height = 2 * button_height + spacing
        start_x = (self.window_width - total_width) // 2
        
        # 动态计算按钮位置
        # 如果有视觉辅助（数字<=20），需要更多空间
        if hasattr(self, 'num1') and hasattr(self, 'num2') and self.num1 <= 20 and self.num2 <= 20:
            # 计算视觉辅助需要的高度
            max_num = max(self.num1, self.num2)
            cols = 10 if max_num > 10 else 5
            rows_needed = (max_num - 1) // cols + 1
            visual_aids_height = self.scale_value(180 + rows_needed * 25)
            # 确保按钮在视觉辅助下方，并留有足够边距
            start_y = min(visual_aids_height + self.scale_value(60), 
                         self.window_height - total_height - self.scale_value(60))
        else:
            # 没有视觉辅助时，按钮居中偏下
            start_y = self.get_center_y() + self.scale_value(100)
        
        for i, option in enumerate(self.answer_options):
            row = i // 2
            col = i % 2
            x = start_x + col * (button_width + spacing)
            y = start_y + row * (button_height + spacing)
            
            button_rect = pygame.Rect(x, y, button_width, button_height)
            self.answer_buttons.append({
                'rect': button_rect,
                'value': option
            })
            
    def handle_click(self, pos: Tuple[int, int]):
        """处理点击"""
        if self.game_complete or self.show_result_emoji:
            return
            
        # 检查喇叭按钮
        for button, text in self.speaker_buttons:
            if button.check_click(pos):
                speak(text)
                return
                
        # 检查答案按钮
        for btn in self.answer_buttons:
            if btn['rect'].collidepoint(pos):
                self._check_answer(btn['value'])
                return
                
    def _check_answer(self, answer: int):
        """检查答案"""
        if answer == self.correct_answer:
            self.score += 1
            self.show_result_emoji = 'happy'
            speak("答对了！真棒！")
            self.emoji_timer = 2
        else:
            self.show_result_emoji = 'sad'
            speak("再想想哦！")
            self.emoji_timer = 1.5  # 错误时显示时间短一些
        
    def update(self, dt: float):
        """更新游戏状态"""
        if self.game_complete:
            return
            
        # 处理语音等待
        if self.waiting_for_voice:
            self.voice_timer += dt
            # 等待语音播放完毕后再等0.5秒，或超时3秒
            if (not is_speaking() and self.voice_timer > 0.5) or self.voice_timer > 3.0:
                self.waiting_for_voice = False
                if hasattr(self, 'pending_next_round') and self.pending_next_round:
                    self.pending_next_round = False
                    self._start_new_round()
            
        # 更新表情计时器
        if self.emoji_timer > 0:
            self.emoji_timer -= dt
            if self.emoji_timer <= 0:
                if self.show_result_emoji == 'happy':
                    # 答对了，等待语音播放完毕后才进入下一题
                    self.show_result_emoji = None
                    self.waiting_for_voice = True
                    self.voice_timer = 0
                    self.pending_next_round = True
                else:
                    # 答错了只清除表情，继续当前题目
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
            
        # 绘制标题
        title_font = get_chinese_font(self.scale_font_size(48))
        title = f"算一算 - 第 {self.round_number}/{self.rounds_total} 题"
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
        self.speaker_buttons.append((speaker_btn, f"第{self.round_number}题"))
        
        # 绘制题目
        if self.current_question and not self.show_result_emoji:
            # 根据题目长度动态调整字体大小
            base_font_size = 72
            question_font = get_chinese_font(self.scale_font_size(base_font_size))
            question_surf = question_font.render(self.current_question, True, COLORS['text'])
            
            # 如果题目太宽，减小字体
            max_width = self.window_width - self.scale_value(200)  # 留出边距
            while question_surf.get_width() > max_width and base_font_size > 36:
                base_font_size -= 4
                question_font = get_chinese_font(self.scale_font_size(base_font_size))
                question_surf = question_font.render(self.current_question, True, COLORS['text'])
            
            question_rect = question_surf.get_rect(center=(self.get_center_x(), 
                                                         self.scale_value(120)))
            screen.blit(question_surf, question_rect)
            
            # 题目喇叭按钮
            q_speaker_btn = SpeakerButton(
                min(question_rect.right + self.scale_value(30), self.window_width - self.scale_value(60)),
                question_rect.centery,
                self.scale_value(30)
            )
            q_speaker_btn.draw(screen)
            self.speaker_buttons.append((q_speaker_btn, self.current_question.replace("-", "减").replace("+", "加").replace("=", "等于").replace("?", "")))
            
            # 绘制图案辅助
            self._draw_visual_aids(screen)
            
        # 绘制答案选项
        if not self.show_result_emoji:
            self._draw_answer_options(screen)
            
        # 绘制表情反馈
        if self.show_result_emoji:
            # 只有答对时才显示正确的算式
            if self.show_result_emoji == 'happy' and self.current_question:
                result_question = self.current_question.replace("?", str(self.correct_answer))
                # 使用相同的自适应字体大小
                base_font_size = 72
                result_font = get_chinese_font(self.scale_font_size(base_font_size))
                result_surf = result_font.render(result_question, True, COLORS['success'])
                
                # 确保不超出屏幕
                max_width = self.window_width - self.scale_value(200)
                while result_surf.get_width() > max_width and base_font_size > 36:
                    base_font_size -= 4
                    result_font = get_chinese_font(self.scale_font_size(base_font_size))
                    result_surf = result_font.render(result_question, True, COLORS['success'])
                
                result_rect = result_surf.get_rect(center=(self.get_center_x(), 
                                                         self.scale_value(200)))
                screen.blit(result_surf, result_rect)
            
            # 绘制表情
            emoji_size = self.scale_value(80)
            emoji_y = self.get_center_y() + self.scale_value(50)
            if self.show_result_emoji == 'happy':
                draw_happy_face(screen, self.get_center_x(), emoji_y, emoji_size)
            elif self.show_result_emoji == 'sad':
                draw_sad_face(screen, self.get_center_x(), emoji_y, emoji_size)
                
        # 绘制得分
        score_font = get_chinese_font(self.scale_font_size(32))
        completed_rounds = max(0, self.round_number - 1)
        score_text = f"得分: {self.score}/{completed_rounds}"
        score_surf = score_font.render(score_text, True, COLORS['text'])
        screen.blit(score_surf, (self.scale_value(20), self.window_height - self.scale_value(40)))
        
        # 绘制所有喇叭按钮
        for button, _ in self.speaker_buttons:
            button.draw(screen)
            
    def _draw_answer_options(self, screen: pygame.Surface):
        """绘制答案选项"""
        button_font = get_chinese_font(self.scale_font_size(48))
        
        for btn in self.answer_buttons:
            # 按钮背景
            pygame.draw.rect(screen, COLORS['primary'], btn['rect'], border_radius=10)
            pygame.draw.rect(screen, COLORS['text'], btn['rect'], 3, border_radius=10)
            
            # 按钮文字
            text = str(btn['value'])
            text_surf = button_font.render(text, True, COLORS['white'])
            text_rect = text_surf.get_rect(center=btn['rect'].center)
            screen.blit(text_surf, text_rect)
            
    def _draw_visual_aids(self, screen: pygame.Surface):
        """绘制图案辅助"""
        if not hasattr(self, 'num1') or not hasattr(self, 'operation'):
            return
            
        # 只有数字较小时才显示图案（大于20不显示）
        if self.num1 > 20 or self.num2 > 20:
            return
            
        # 图案大小和间距（响应式）
        item_size = self.scale_value(20)
        spacing = self.scale_value(25)
        base_y = self.scale_value(180)
        
        # 使用更多列来减少行数
        cols = 10 if self.num1 > 10 or self.num2 > 10 else 5
        
        # 计算第一组起始位置，使其居中
        group1_cols = min(cols, self.num1)
        group1_width = group1_cols * spacing
        group1_start_x = self.get_center_x() - self.scale_value(120) - group1_width // 2
        
        # 绘制第一组数字的图案（苹果）
        for i in range(self.num1):
            x = group1_start_x + (i % cols) * spacing
            y = base_y + (i // cols) * spacing
            # 绘制苹果
            pygame.draw.circle(screen, (255, 0, 0), (x, y), item_size//2)
            pygame.draw.rect(screen, (139, 69, 19), 
                           (x - 2, y - item_size//2 - 5, 4, 8))
        
        # 绘制运算符号
        op_x = self.get_center_x()
        op_y = base_y + self.scale_value(20)
        op_font = get_chinese_font(self.scale_font_size(36))
        op_surf = op_font.render(self.operation, True, COLORS['text'])
        op_rect = op_surf.get_rect(center=(op_x, op_y))
        screen.blit(op_surf, op_rect)
        
        # 计算第二组起始位置
        group2_cols = min(cols, self.num2)
        group2_width = group2_cols * spacing
        group2_start_x = self.get_center_x() + self.scale_value(120) - group2_width // 2
        
        # 绘制第二组数字的图案（香蕉）
        for i in range(self.num2):
            x = group2_start_x + (i % cols) * spacing
            y = base_y + (i // cols) * spacing
            # 绘制香蕉（简化为黄色椭圆）
            pygame.draw.ellipse(screen, (255, 255, 0), 
                              pygame.Rect(x - item_size//2, y - item_size//3,
                                        item_size, item_size*2//3))
            
        # 对于减法，在第二组上画叉
        if self.operation == '-':
            for i in range(self.num2):
                x = group2_start_x + (i % cols) * spacing
                y = base_y + (i // cols) * spacing
                # 画红色叉叉
                cross_size = item_size // 2
                pygame.draw.line(screen, COLORS['danger'],
                               (x - cross_size, y - cross_size),
                               (x + cross_size, y + cross_size), 3)
                pygame.draw.line(screen, COLORS['danger'],
                               (x + cross_size, y - cross_size),
                               (x - cross_size, y + cross_size), 3)
            
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
            result_text = "数学小天才！"
            color = COLORS['success']
            draw_happy_face(screen, self.get_center_x(), 
                          self.get_center_y() - self.scale_value(150), 
                          self.scale_value(100))
        elif score_percent >= 60:
            result_text = "很不错哦！"
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