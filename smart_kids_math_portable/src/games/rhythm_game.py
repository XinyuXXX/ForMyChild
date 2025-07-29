#!/usr/bin/env python3
"""
节奏练习游戏
"""
import pygame
import random
import math
from typing import List, Dict, Tuple, Optional
from ..config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak, stop_speaking, is_speaking
from ..utils.ui_utils import SpeakerButton
from ..utils.emoji_utils import draw_happy_face, draw_sad_face, draw_star_eyes_face
from ..games.music_theory import RhythmPattern


class RhythmGame:
    """节奏练习游戏"""
    
    def __init__(self, difficulty: int = 1):
        self.difficulty = difficulty
        
        # 游戏状态
        self.score = 0
        self.round_number = 0
        self.rounds_total = 10
        self.game_complete = False
        
        # 题目相关
        self.current_question = None
        self.player_answer = None
        self.answer_options = []
        self.answer_buttons = []
        self.show_result_emoji = None
        self.feedback_timer = 0
        
        # 节奏模式定义
        self._init_rhythms()
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 播放欢迎语音
        speak("节奏游戏开始啦！让我们一起学习音符的节奏吧！")
        
        # 开始第一轮
        self._start_new_round()
        
    def _init_rhythms(self):
        """初始化节奏模式"""
        self.rhythm_patterns = [
            RhythmPattern([4], 'whole'),              # 全音符
            RhythmPattern([2, 2], 'half'),           # 二分音符
            RhythmPattern([1, 1, 1, 1], 'quarter'),  # 四分音符
            RhythmPattern([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5], 'eighth'),  # 八分音符
            RhythmPattern([3, 1], 'dotted_half'),    # 附点二分音符
            RhythmPattern([1.5, 0.5, 1.5, 0.5], 'dotted_quarter'),  # 附点四分音符
        ]
        
        # 根据难度选择节奏模式
        if self.difficulty <= 2:
            # 初级：只有全音符和二分音符
            self.available_rhythms = self.rhythm_patterns[:2]
        elif self.difficulty <= 3:
            # 中级：加入四分音符
            self.available_rhythms = self.rhythm_patterns[:3]
        else:
            # 高级：所有节奏
            self.available_rhythms = self.rhythm_patterns
            
    def _start_new_round(self):
        """开始新一轮"""
        self.round_number += 1
        self.player_answer = None
        self.show_result_emoji = None
        self.answer_options = []
        self.answer_buttons = []
        
        if self.round_number > self.rounds_total:
            self.game_complete = True
            speak(f"游戏结束！你的得分是{self.score}分。")
            return
            
        # 生成题目
        self._generate_question()
        
    def _generate_question(self):
        """生成节奏题目"""
        # 随机选择一个节奏模式
        self.current_question = random.choice(self.available_rhythms)
        
        # 生成选项
        self.answer_options = []
        self.answer_options.append(self.current_question.chinese_name)
        
        # 添加错误选项
        while len(self.answer_options) < 4:
            wrong_rhythm = random.choice(self.available_rhythms)
            if wrong_rhythm.chinese_name not in self.answer_options:
                self.answer_options.append(wrong_rhythm.chinese_name)
                
        random.shuffle(self.answer_options)
        
        # 创建答案按钮
        self._create_answer_buttons()
        
        # 语音提示
        speak("请看这个节奏，这是什么音符？")
        
    def _create_answer_buttons(self):
        """创建答案按钮"""
        self.answer_buttons = []
        button_width = 180
        button_height = 60
        spacing = 30
        total_width = 2 * button_width + spacing
        start_x = (WINDOW_WIDTH - total_width) // 2
        
        for i in range(len(self.answer_options)):
            row = i // 2
            col = i % 2
            x = start_x + col * (button_width + spacing)
            y = WINDOW_HEIGHT - 200 + row * (button_height + spacing)
            self.answer_buttons.append(pygame.Rect(x, y, button_width, button_height))
            
    def handle_click(self, pos: Tuple[int, int]):
        """处理点击事件"""
        # 检查喇叭按钮
        for button, text in self.speaker_buttons:
            if button.check_click(pos):
                speak(text)
                return
                
        if self.game_complete or self.show_result_emoji:
            return
            
        # 检查答案按钮
        for i, button in enumerate(self.answer_buttons):
            if button.collidepoint(pos):
                self.player_answer = self.answer_options[i]
                self._check_answer()
                break
                
    def _check_answer(self):
        """检查答案"""
        correct = self.player_answer == self.current_question.chinese_name
        
        if correct:
            self.score += 10
            self.show_result_emoji = 'happy'
            speak("答对了！真棒！")
            self.feedback_timer = 2.0
        else:
            self.show_result_emoji = 'sad'
            speak("再想想哦！")
            self.feedback_timer = 1.5
            
    def update(self, dt: float):
        """更新游戏状态"""
        # 更新反馈计时器
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            if self.feedback_timer <= 0:
                if self.show_result_emoji == 'happy':
                    self._start_new_round()
                else:
                    # 答错了清除反馈，让玩家继续尝试
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
        
        # 绘制标题
        title_font = get_chinese_font(48)
        title = "节奏练习"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, 50))
        screen.blit(title_surf, title_rect)
        
        # 在标题旁边添加喇叭按钮
        speaker_btn = SpeakerButton(WINDOW_WIDTH//2 + title_surf.get_width()//2 + 50, 50, 25)
        speaker_btn.draw(screen)
        self.speaker_buttons.append((speaker_btn, "现在是节奏练习环节"))
        
        if not self.game_complete:
            if self.current_question:
                # 绘制节奏题目
                self._draw_rhythm_question(screen)
                
                # 绘制答案选项
                self._draw_answer_options(screen)
            
            # 绘制反馈表情
            if self.show_result_emoji:
                if self.show_result_emoji == 'happy':
                    draw_happy_face(screen, WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50, 80)
                elif self.show_result_emoji == 'sad':
                    draw_sad_face(screen, WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50, 80)
                    
        # 绘制进度和分数
        info_font = get_chinese_font(32)
        progress_text = f"第 {self.round_number}/{self.rounds_total} 题"
        score_text = f"得分: {self.score}"
        
        screen.blit(info_font.render(progress_text, True, COLORS['text']), (20, WINDOW_HEIGHT - 40))
        screen.blit(info_font.render(score_text, True, COLORS['text']), (WINDOW_WIDTH - 150, WINDOW_HEIGHT - 40))
        
        # 绘制所有喇叭按钮
        for button, _ in self.speaker_buttons:
            button.draw(screen)
            
        # 游戏结束画面
        if self.game_complete:
            self._draw_game_complete(screen)
            
    def _draw_rhythm_question(self, screen: pygame.Surface):
        """绘制节奏题目"""
        # 检查当前题目是否有效
        if not self.current_question or not hasattr(self.current_question, 'pattern'):
            # 如果没有有效题目，重新生成
            self._generate_question()
            return
            
        # 绘制节奏模式
        pattern = self.current_question.pattern
        total_beats = sum(pattern)
        
        # 绘制小节线
        measure_y1 = WINDOW_HEIGHT // 2 - 50
        measure_y2 = WINDOW_HEIGHT // 2 + 50
        measure_x_start = 200
        measure_x_end = WINDOW_WIDTH - 200
        
        pygame.draw.line(screen, COLORS['text'], 
                       (measure_x_start, measure_y1), 
                       (measure_x_start, measure_y2), 3)
        pygame.draw.line(screen, COLORS['text'], 
                       (measure_x_end, measure_y1), 
                       (measure_x_end, measure_y2), 3)
                       
        # 绘制节奏
        x_step = (measure_x_end - measure_x_start) / total_beats
        current_x = measure_x_start + 50
        
        for beat in pattern:
            # 根据拍子长度绘制不同的音符
            if beat == 4:  # 全音符
                pygame.draw.ellipse(screen, COLORS['text'], 
                                  pygame.Rect(current_x - 20, WINDOW_HEIGHT//2 - 15, 40, 30), 3)
            elif beat == 2:  # 二分音符
                pygame.draw.ellipse(screen, COLORS['text'], 
                                  pygame.Rect(current_x - 15, WINDOW_HEIGHT//2 - 10, 30, 20))
                pygame.draw.line(screen, COLORS['text'], 
                               (current_x + 15, WINDOW_HEIGHT//2), 
                               (current_x + 15, WINDOW_HEIGHT//2 - 40), 3)
            elif beat == 3:  # 附点二分音符
                pygame.draw.ellipse(screen, COLORS['text'], 
                                  pygame.Rect(current_x - 15, WINDOW_HEIGHT//2 - 10, 30, 20))
                pygame.draw.line(screen, COLORS['text'], 
                               (current_x + 15, WINDOW_HEIGHT//2), 
                               (current_x + 15, WINDOW_HEIGHT//2 - 40), 3)
                # 附点
                pygame.draw.circle(screen, COLORS['text'], 
                                 (current_x + 30, WINDOW_HEIGHT//2), 3)
            elif beat == 1:  # 四分音符
                pygame.draw.ellipse(screen, COLORS['text'], 
                                  pygame.Rect(current_x - 15, WINDOW_HEIGHT//2 - 10, 30, 20))
                pygame.draw.line(screen, COLORS['text'], 
                               (current_x + 15, WINDOW_HEIGHT//2), 
                               (current_x + 15, WINDOW_HEIGHT//2 - 40), 3)
            elif beat == 1.5:  # 附点四分音符
                pygame.draw.ellipse(screen, COLORS['text'], 
                                  pygame.Rect(current_x - 15, WINDOW_HEIGHT//2 - 10, 30, 20))
                pygame.draw.line(screen, COLORS['text'], 
                               (current_x + 15, WINDOW_HEIGHT//2), 
                               (current_x + 15, WINDOW_HEIGHT//2 - 40), 3)
                # 附点
                pygame.draw.circle(screen, COLORS['text'], 
                                 (current_x + 30, WINDOW_HEIGHT//2), 3)
            elif beat == 0.5:  # 八分音符
                pygame.draw.ellipse(screen, COLORS['text'], 
                                  pygame.Rect(current_x - 10, WINDOW_HEIGHT//2 - 8, 20, 16))
                pygame.draw.line(screen, COLORS['text'], 
                               (current_x + 10, WINDOW_HEIGHT//2), 
                               (current_x + 10, WINDOW_HEIGHT//2 - 35), 3)
                # 符尾
                pygame.draw.arc(screen, COLORS['text'], 
                              pygame.Rect(current_x + 10, WINDOW_HEIGHT//2 - 35, 20, 20), 
                              -math.pi/2, 0, 3)
                              
            current_x += beat * x_step
            
    def _draw_answer_options(self, screen: pygame.Surface):
        """绘制答案选项"""
        button_font = get_chinese_font(28)
        
        for i, (button, option) in enumerate(zip(self.answer_buttons, self.answer_options)):
            # 确定按钮颜色
            if self.show_result_emoji:
                if option == self.current_question.chinese_name:
                    color = COLORS['success']
                else:
                    color = COLORS['danger'] if option == self.player_answer else COLORS['secondary']
            else:
                color = COLORS['primary']
                
            # 绘制按钮
            pygame.draw.rect(screen, color, button, border_radius=10)
            pygame.draw.rect(screen, COLORS['text'], button, 3, border_radius=10)
            
            # 绘制文字
            text_surf = button_font.render(option, True, COLORS['white'])
            text_rect = text_surf.get_rect(center=button.center)
            screen.blit(text_surf, text_rect)
            
    def _draw_game_complete(self, screen: pygame.Surface):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        result_font = get_chinese_font(72)
        score_percent = (self.score / (self.rounds_total * 10)) * 100
        
        if score_percent >= 80:
            result_text = "节奏大师！"
            color = COLORS['success']
            draw_star_eyes_face(screen, WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 200, 100)
        elif score_percent >= 60:
            result_text = "很不错哦！"
            color = COLORS['primary']
            draw_happy_face(screen, WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 200, 100)
        else:
            result_text = "继续努力！"
            color = COLORS['secondary']
            draw_happy_face(screen, WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 200, 100, color=(255, 165, 0))
            
        text_surf = result_font.render(result_text, True, color)
        text_rect = text_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
        screen.blit(text_surf, text_rect)
        
        score_font = get_chinese_font(48)
        score_surf = score_font.render(f"最终得分: {self.score}", True, COLORS['white'])
        score_rect = score_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 30))
        screen.blit(score_surf, score_rect)
        
    def get_result(self) -> Dict:
        """获取游戏结果"""
        return {
            'score': self.score,
            'rounds_played': self.round_number,
            'accuracy': (self.score / (self.round_number * 10)) * 100 if self.round_number > 0 else 0
        }