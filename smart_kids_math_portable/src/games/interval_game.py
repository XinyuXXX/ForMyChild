#!/usr/bin/env python3
"""
音程训练游戏
"""
import pygame
import random
import math
import os
from typing import List, Dict, Tuple, Optional
from ..config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak, stop_speaking, is_speaking
from ..utils.ui_utils import SpeakerButton
from ..utils.emoji_utils import draw_happy_face, draw_sad_face, draw_star_eyes_face
from ..utils.music_utils import play_note, init_pygame_mixer
from ..games.music_theory import MusicNote


class IntervalGame:
    """音程训练游戏"""
    
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
        
        # 音符定义（C4到B5）
        self._init_notes()
        
        # 五线谱位置
        self.staff_y = WINDOW_HEIGHT // 2
        self.staff_x_start = 150
        self.staff_x_end = WINDOW_WIDTH - 150
        self.line_spacing = 25
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 加载谱号图片
        self.treble_clef_img = None
        self.bass_clef_img = None
        self._load_clef_images()
        
        # 初始化音频
        try:
            init_pygame_mixer()
        except Exception as e:
            print(f"音频初始化失败: {e}")
        
        # 播放欢迎语音
        speak("音程游戏开始啦！让我们一起学习音符之间的距离吧！")
        
        # 开始第一轮
        self._start_new_round()
        
    def _init_notes(self):
        """初始化音符"""
        # 五线谱音符位置定义 - 与五线谱游戏保持一致
        # 高音谱号：第一线(底线)=E4, 第二线=G4, 第三线=B4, 第四线=D5, 第五线=F5
        # 创建包含2个八度的音符（C4到B5）
        self.notes = [
            # 中音区（C4-B4）
            MusicNote('C', 4, -2, 261.63),  # 高音谱号下加一线
            MusicNote('D', 4, -1, 293.66),  # 高音谱号第一线下方的间
            MusicNote('E', 4, 0, 329.63),   # 高音谱号第一线
            MusicNote('F', 4, 1, 349.23),   # 高音谱号第一间
            MusicNote('G', 4, 2, 392.00),   # 高音谱号第二线
            MusicNote('A', 4, 3, 440.00),   # 高音谱号第二间
            MusicNote('B', 4, 4, 493.88),   # 高音谱号第三线
            
            # 高音区（C5-B5）
            MusicNote('C', 5, 5, 523.25),   # 高音谱号第三间
            MusicNote('D', 5, 6, 587.33),   # 高音谱号第四线
            MusicNote('E', 5, 7, 659.25),   # 高音谱号第四间
            MusicNote('F', 5, 8, 698.46),   # 高音谱号第五线
            MusicNote('G', 5, 9, 783.99),   # 高音谱号第五线上方的间
            MusicNote('A', 5, 10, 880.00),  # 高音谱号上加一线的间
            MusicNote('B', 5, 11, 987.77),  # 高音谱号上加一线
        ]
        
        # 根据难度选择音符范围和音程类型（1-10级）
        difficulty_settings = {
            1: {'notes': self.notes[2:5], 'intervals': [1, 2]},         # 超简单：E4-G4，只有2度和3度
            2: {'notes': self.notes[0:5], 'intervals': [1, 2, 3]},      # 很简单：C4-G4，2-4度
            3: {'notes': self.notes[0:7], 'intervals': [1, 2, 3, 4]},   # 简单：C4-B4，2-5度
            4: {'notes': self.notes[0:8], 'intervals': [1, 2, 3, 4, 5]}, # 较易：C4-C5，2-6度
            5: {'notes': self.notes[0:10], 'intervals': [1, 2, 3, 4, 5, 6]}, # 适中：C4-E5，2-7度
            6: {'notes': self.notes[0:12], 'intervals': [1, 2, 3, 4, 5, 6, 7]}, # 稍难：C4-G5，2-8度
            7: {'notes': self.notes[:], 'intervals': [1, 2, 3, 4, 5, 6, 7]}, # 困难：全音域，2-8度
            8: {'notes': self.notes[:], 'intervals': [1, 2, 3, 4, 5, 6, 7, 8]}, # 很困难：+9度
            9: {'notes': self.notes[:], 'intervals': [1, 2, 3, 4, 5, 6, 7, 8, 9]}, # 超困难：+10度
            10: {'notes': self.notes[:], 'intervals': list(range(1, 12))} # 极限：所有音程
        }
        
        settings = difficulty_settings.get(self.difficulty, difficulty_settings[5])
        self.available_notes = settings['notes']
        self.available_intervals = settings['intervals']
        
    def _load_clef_images(self):
        """加载谱号图片"""
        try:
            # 获取assets目录路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            treble_path = os.path.join(base_dir, 'assets', 'images', 'treble_clef.jpeg')
            bass_path = os.path.join(base_dir, 'assets', 'images', 'bass_clef.jpeg')
            
            # 加载图片
            if os.path.exists(treble_path):
                self.treble_clef_img = pygame.image.load(treble_path).convert()
                # 使用白色作为透明色
                self.treble_clef_img.set_colorkey((255, 255, 255))
            if os.path.exists(bass_path):
                self.bass_clef_img = pygame.image.load(bass_path).convert()
                # 使用白色作为透明色
                self.bass_clef_img.set_colorkey((255, 255, 255))
        except Exception as e:
            print(f"加载谱号图片失败: {e}")
            
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
        """生成音程题目"""
        # 选择第一个音符
        note1 = random.choice(self.available_notes[:-1])  # 确保有空间生成音程
        
        # 选择音程大小
        interval_steps = random.choice(self.available_intervals)
        
        note1_index = self.notes.index(note1)
        note2_index = min(note1_index + interval_steps, len(self.notes) - 1)
        
        # 确保第二个音符在可用范围内
        if note2_index < len(self.notes) and self.notes[note2_index] in self.available_notes:
            note2 = self.notes[note2_index]
        else:
            # 如果超出范围，向下找一个音符
            note2_index = max(note1_index - interval_steps, 0)
            note2 = self.notes[note2_index]
        
        self.current_question = {
            'note1': note1,
            'note2': note2,
            'interval': interval_steps
        }
        
        # 音程名称
        interval_names = {
            1: '二度',
            2: '三度',
            3: '四度',
            4: '五度',
            5: '六度',
            6: '七度',
            7: '八度',
            8: '八度以上'
        }
        
        correct_answer = interval_names.get(interval_steps, f'{interval_steps}度')
        
        # 生成选项
        self.answer_options = [correct_answer]
        
        # 添加错误选项
        for wrong_interval in [1, 2, 3, 4, 5]:
            if wrong_interval != interval_steps:
                self.answer_options.append(interval_names.get(wrong_interval, f'{wrong_interval}度'))
                if len(self.answer_options) >= 4:
                    break
                    
        random.shuffle(self.answer_options)
        
        # 创建答案按钮
        self._create_answer_buttons()
        
        # 语音提示
        speak("请看这两个音符之间的音程是几度？")
        
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
        interval_steps = self.current_question['interval']
        interval_names = {1: '二度', 2: '三度', 3: '四度', 4: '五度', 5: '六度', 6: '七度', 7: '八度', 8: '八度以上'}
        correct_answer = interval_names.get(interval_steps, f'{interval_steps}度')
        correct = self.player_answer == correct_answer
        
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
        title = "音程训练"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, 50))
        screen.blit(title_surf, title_rect)
        
        # 在标题旁边添加喇叭按钮
        speaker_btn = SpeakerButton(WINDOW_WIDTH//2 + title_surf.get_width()//2 + 50, 50, 25)
        speaker_btn.draw(screen)
        self.speaker_buttons.append((speaker_btn, "现在是音程训练环节"))
        
        if not self.game_complete:
            if self.current_question:
                # 绘制音程题目
                self._draw_interval_question(screen)
                
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
            
    def _draw_staff(self, screen: pygame.Surface, clef_type: str = 'treble'):
        """绘制五线谱"""
        # 绘制五条线
        for i in range(5):
            y = self.staff_y - (i - 2) * self.line_spacing
            pygame.draw.line(screen, COLORS['text'], 
                           (self.staff_x_start, y), 
                           (self.staff_x_end, y), 2)
                           
        # 根据类型绘制谱号
        if clef_type == 'treble':
            self._draw_treble_clef(screen, self.staff_x_start + 30, self.staff_y)
        elif clef_type == 'bass':
            self._draw_bass_clef(screen, self.staff_x_start + 30, self.staff_y)
        
    def _draw_treble_clef(self, screen: pygame.Surface, x: int, y: int):
        """绘制高音谱号"""
        if self.treble_clef_img:
            # 计算合适的缩放大小
            # 高音谱号应该覆盖从第一线下方到第五线上方，约4.5个line_spacing高度
            target_height = int(self.line_spacing * 4.5)
            target_width = int(target_height * 0.5)  # 高音谱号宽高比约1:2
            
            # 缩放图片
            scaled_img = pygame.transform.scale(self.treble_clef_img, (target_width, target_height))
            
            # 绘制在正确位置（高音谱号的中心应该在第二线，即G音位置）
            img_rect = scaled_img.get_rect()
            img_rect.centerx = x
            img_rect.centery = y + self.line_spacing  # 第二线位置
            screen.blit(scaled_img, img_rect)
            
    def _draw_bass_clef(self, screen: pygame.Surface, x: int, y: int):
        """绘制低音谱号"""
        if self.bass_clef_img:
            # 计算合适的缩放大小
            # 低音谱号应该覆盖从第二线到第五线，约3个line_spacing高度
            target_height = int(self.line_spacing * 3)
            target_width = int(target_height * 0.8)  # 低音谱号宽高比约0.8:1
            
            # 缩放图片
            scaled_img = pygame.transform.scale(self.bass_clef_img, (target_width, target_height))
            
            # 绘制在正确位置（低音谱号的中心应该在第四线，即F音位置）
            img_rect = scaled_img.get_rect()
            img_rect.centerx = x
            img_rect.centery = y - self.line_spacing  # 第四线位置
            screen.blit(scaled_img, img_rect)
        
    def _draw_interval_question(self, screen: pygame.Surface):
        """绘制音程题目"""
        # 只使用高音谱号（因为只有C4-B5）
        self._draw_staff(screen, 'treble')
        
        # 绘制两个音符
        note1 = self.current_question['note1']
        note2 = self.current_question['note2']
        
        # 第一个音符
        note1_x = WINDOW_WIDTH // 2 - 80
        # 使用与五线谱游戏相同的位置计算
        note1_y = self.staff_y + self.line_spacing * 2 - (note1.staff_position * self.line_spacing // 2)
        
        pygame.draw.ellipse(screen, COLORS['text'], 
                          pygame.Rect(note1_x - 15, note1_y - 10, 30, 20))
        pygame.draw.line(screen, COLORS['text'], 
                       (note1_x + 15, note1_y), 
                       (note1_x + 15, note1_y - 40), 3)
                       
        # 第二个音符
        note2_x = WINDOW_WIDTH // 2 + 80
        # 使用与五线谱游戏相同的位置计算
        note2_y = self.staff_y + self.line_spacing * 2 - (note2.staff_position * self.line_spacing // 2)
        
        pygame.draw.ellipse(screen, COLORS['text'], 
                          pygame.Rect(note2_x - 15, note2_y - 10, 30, 20))
        pygame.draw.line(screen, COLORS['text'], 
                       (note2_x + 15, note2_y), 
                       (note2_x + 15, note2_y - 40), 3)
        
        # 绘制加线（第一个音符）
        if note1.staff_position < 0:  # 下加线
            for i in range(-2, note1.staff_position - 1, -2):
                y = self.staff_y + self.line_spacing * 2 - (i * self.line_spacing // 2)
                pygame.draw.line(screen, COLORS['text'], 
                               (note1_x - 25, y), 
                               (note1_x + 25, y), 2)
        elif note1.staff_position > 8:  # 上加线
            for i in range(10, note1.staff_position + 1, 2):
                y = self.staff_y + self.line_spacing * 2 - (i * self.line_spacing // 2)
                pygame.draw.line(screen, COLORS['text'], 
                               (note1_x - 25, y), 
                               (note1_x + 25, y), 2)
                
        # 绘制加线（第二个音符）
        if note2.staff_position < 0:  # 下加线
            for i in range(-2, note2.staff_position - 1, -2):
                y = self.staff_y + self.line_spacing * 2 - (i * self.line_spacing // 2)
                pygame.draw.line(screen, COLORS['text'], 
                               (note2_x - 25, y), 
                               (note2_x + 25, y), 2)
        elif note2.staff_position > 8:  # 上加线
            for i in range(10, note2.staff_position + 1, 2):
                y = self.staff_y + self.line_spacing * 2 - (i * self.line_spacing // 2)
                pygame.draw.line(screen, COLORS['text'], 
                               (note2_x - 25, y), 
                               (note2_x + 25, y), 2)
                       
        # 绘制连线
        pygame.draw.line(screen, COLORS['primary'], 
                       (note1_x + 20, note1_y), 
                       (note2_x - 20, note2_y), 2)
                       
        # 添加播放按钮
        play_button_y = self.staff_y + 80
        play_btn1 = SpeakerButton(note1_x, play_button_y, 20)
        play_btn2 = SpeakerButton(note2_x, play_button_y, 20)
        play_btn1.draw(screen)
        play_btn2.draw(screen)
        self.speaker_buttons.append((play_btn1, f"播放第一个音符{note1.note_name}"))
        self.speaker_buttons.append((play_btn2, f"播放第二个音符{note2.note_name}"))
        
    def _draw_answer_options(self, screen: pygame.Surface):
        """绘制答案选项"""
        button_font = get_chinese_font(28)
        
        for i, (button, option) in enumerate(zip(self.answer_buttons, self.answer_options)):
            # 确定按钮颜色
            if self.show_result_emoji:
                interval_steps = self.current_question['interval']
                interval_names = {1: '二度', 2: '三度', 3: '四度', 4: '五度', 5: '六度', 6: '七度', 7: '八度', 8: '八度以上'}
                correct_answer = interval_names.get(interval_steps, f'{interval_steps}度')
                if option == correct_answer:
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
            result_text = "音程达人！"
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