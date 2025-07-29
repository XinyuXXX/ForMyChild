#!/usr/bin/env python3
"""
音乐乐理游戏
包括节奏、音程、五线谱等音乐基础知识
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
from ..utils.music_utils import play_note, init_pygame_mixer
from ..utils.clef_drawing import draw_treble_clef, draw_bass_clef


class MusicNote:
    """音符类"""
    def __init__(self, note_name: str, octave: int, staff_position: int, frequency: float):
        self.note_name = note_name  # C, D, E, F, G, A, B
        self.octave = octave  # 八度
        self.staff_position = staff_position  # 在五线谱上的位置
        self.frequency = frequency  # 频率（Hz）
        self.chinese_name = self._get_chinese_name()
        
    def _get_chinese_name(self) -> str:
        """获取音符的中文名"""
        note_names = {
            'C': 'Do (哆)',
            'D': 'Re (来)',
            'E': 'Mi (咪)',
            'F': 'Fa (发)',
            'G': 'Sol (索)',
            'A': 'La (拉)',
            'B': 'Si (西)'
        }
        return note_names.get(self.note_name, self.note_name)


class RhythmPattern:
    """节奏模式类"""
    def __init__(self, pattern: List[float], name: str):
        self.pattern = pattern  # 节奏模式，数字表示拍子长度
        self.name = name
        self.chinese_name = self._get_chinese_name()
        
    def _get_chinese_name(self) -> str:
        """获取节奏的中文名"""
        rhythm_names = {
            'whole': '全音符',
            'half': '二分音符',
            'quarter': '四分音符',
            'eighth': '八分音符',
            'dotted_half': '附点二分音符',
            'dotted_quarter': '附点四分音符'
        }
        return rhythm_names.get(self.name, self.name)


class MusicTheoryGame:
    """音乐乐理游戏主类"""
    
    def __init__(self, difficulty: int = 1):
        self.difficulty = difficulty
        
        # 游戏模式
        self.modes = ['staff_reading', 'rhythm', 'interval']  # 五线谱识谱、节奏、音程
        self.current_mode = 'staff_reading'  # 默认从五线谱开始
        self.mode_index = 0
        
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
        
        # 节奏模式定义
        self._init_rhythms()
        
        # 五线谱位置
        self.staff_y = WINDOW_HEIGHT // 2
        self.staff_x_start = 150
        self.staff_x_end = WINDOW_WIDTH - 150
        self.line_spacing = 25
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 初始化音频
        try:
            init_pygame_mixer()
        except Exception as e:
            print(f"音频初始化失败: {e}")
        
        # 播放欢迎语音（不阻塞）
        speak("音乐游戏开始啦！让我们一起学习音乐知识吧！")
        
        # 开始第一轮
        self._start_new_round()
        
    def _init_notes(self):
        """初始化音符"""
        # 基础音符（C4到B5）
        self.notes = [
            MusicNote('C', 4, 0, 261.63),   # 下加一线
            MusicNote('D', 4, 1, 293.66),   # 第一线下
            MusicNote('E', 4, 2, 329.63),   # 第一线
            MusicNote('F', 4, 3, 349.23),   # 第一间
            MusicNote('G', 4, 4, 392.00),   # 第二线
            MusicNote('A', 4, 5, 440.00),   # 第二间
            MusicNote('B', 4, 6, 493.88),   # 第三线
            MusicNote('C', 5, 7, 523.25),   # 第三间
            MusicNote('D', 5, 8, 587.33),   # 第四线
            MusicNote('E', 5, 9, 659.25),   # 第四间
            MusicNote('F', 5, 10, 698.46),  # 第五线
            MusicNote('G', 5, 11, 783.99),  # 第五线上
            MusicNote('A', 5, 12, 880.00),  # 上加一间
            MusicNote('B', 5, 13, 987.77),  # 上加一线
        ]
        
        # 根据难度选择音符范围
        if self.difficulty <= 2:
            # 初级：只学习C4到G4
            self.available_notes = self.notes[:5]
        elif self.difficulty <= 3:
            # 中级：C4到C5
            self.available_notes = self.notes[:8]
        else:
            # 高级：所有音符
            self.available_notes = self.notes
            
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
        self.answer_options = []  # 清空答案选项
        self.answer_buttons = []  # 清空按钮
        
        if self.round_number > self.rounds_total:
            self.game_complete = True
            speak(f"游戏结束！你的得分是{self.score}分。")
            return
            
        # 每3轮切换一次模式（在生成题目之前）
        if self.round_number > 1 and (self.round_number - 1) % 3 == 0:
            self.mode_index = (self.mode_index + 1) % len(self.modes)
            self.current_mode = self.modes[self.mode_index]
            mode_names = {
                'staff_reading': '五线谱认识',
                'rhythm': '节奏练习',
                'interval': '音程训练'
            }
            speak(f"现在进入{mode_names[self.current_mode]}环节！")
            
        # 根据当前模式生成题目
        try:
            if self.current_mode == 'staff_reading':
                self._generate_staff_question()
            elif self.current_mode == 'rhythm':
                self._generate_rhythm_question()
            elif self.current_mode == 'interval':
                self._generate_interval_question()
        except Exception as e:
            print(f"生成题目时出错: {e}")
            # 如果出错，默认生成五线谱题目
            self.current_mode = 'staff_reading'
            self._generate_staff_question()
            
    def _generate_staff_question(self):
        """生成五线谱识谱题目"""
        # 随机选择一个音符
        self.current_question = random.choice(self.available_notes)
        
        # 生成选项（使用音名）
        self.answer_options = []
        self.answer_options.append(self.current_question.note_name)
        
        # 添加错误选项
        all_note_names = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        while len(self.answer_options) < 4:
            wrong_note = random.choice(all_note_names)
            if wrong_note not in self.answer_options:
                self.answer_options.append(wrong_note)
                
        random.shuffle(self.answer_options)
        
        # 创建答案按钮
        self._create_answer_buttons()
        
        # 语音提示
        speak("请看五线谱上的音符，这是什么音？")
        
    def _generate_rhythm_question(self):
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
        
    def _generate_interval_question(self):
        """生成音程题目"""
        # 选择两个音符
        note1 = random.choice(self.available_notes)
        interval_steps = random.randint(1, 5) if self.difficulty <= 2 else random.randint(1, 8)
        
        note1_index = self.notes.index(note1)
        note2_index = min(note1_index + interval_steps, len(self.notes) - 1)
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
                
                # 如果是五线谱模式，播放对应的音
                if self.current_mode == 'staff_reading' and len(self.answer_options[i]) == 1:
                    # 播放中央八度的音
                    play_note(self.answer_options[i], 4)
                
                self._check_answer()
                break
                
    def _check_answer(self):
        """检查答案"""
        correct = False
        
        if self.current_mode == 'staff_reading':
            correct = self.player_answer == self.current_question.note_name
        elif self.current_mode == 'rhythm':
            correct = self.player_answer == self.current_question.chinese_name
        elif self.current_mode == 'interval':
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
        mode_names = {
            'staff_reading': '五线谱认识',
            'rhythm': '节奏练习',
            'interval': '音程训练'
        }
        title = mode_names.get(self.current_mode, '音乐游戏')
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, 50))
        screen.blit(title_surf, title_rect)
        
        # 在标题旁边添加喇叭按钮
        speaker_btn = SpeakerButton(WINDOW_WIDTH//2 + title_surf.get_width()//2 + 50, 50, 25)
        speaker_btn.draw(screen)
        self.speaker_buttons.append((speaker_btn, f"现在是{title}环节"))
        
        if not self.game_complete:
            if self.current_question:
                # 根据模式绘制不同的内容
                if self.current_mode == 'staff_reading':
                    self._draw_staff_question(screen)
                elif self.current_mode == 'rhythm':
                    self._draw_rhythm_question(screen)
                elif self.current_mode == 'interval':
                    self._draw_interval_question(screen)
                    
                # 绘制答案选项
                self._draw_answer_options(screen)
            else:
                # 如果没有题目，显示加载中
                loading_font = get_chinese_font(36)
                loading_text = loading_font.render("正在准备题目...", True, COLORS['text'])
                loading_rect = loading_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
                screen.blit(loading_text, loading_rect)
            
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
        
    def _draw_staff_question(self, screen: pygame.Surface):
        """绘制五线谱题目"""
        # 根据音符高度决定显示高音谱号还是低音谱号
        if self.current_question.octave < 4 or (self.current_question.octave == 4 and self.current_question.note_name in ['C', 'D', 'E']):
            self._draw_staff(screen, 'bass')
        else:
            self._draw_staff(screen, 'treble')
        
        # 绘制音符
        note_x = WINDOW_WIDTH // 2
        note_y = self.staff_y - (self.current_question.staff_position - 4) * self.line_spacing // 2
        
        # 音符头
        pygame.draw.ellipse(screen, COLORS['text'], 
                          pygame.Rect(note_x - 15, note_y - 10, 30, 20))
        
        # 符干
        pygame.draw.line(screen, COLORS['text'], 
                       (note_x + 15, note_y), 
                       (note_x + 15, note_y - 40), 3)
                       
        # 如果需要，绘制加线
        if self.current_question.staff_position < 2:  # 下加线
            for i in range(0, self.current_question.staff_position - 1, -2):
                y = self.staff_y - (i - 4) * self.line_spacing // 2
                pygame.draw.line(screen, COLORS['text'], 
                               (note_x - 25, y), 
                               (note_x + 25, y), 2)
        elif self.current_question.staff_position > 10:  # 上加线
            for i in range(12, self.current_question.staff_position + 1, 2):
                y = self.staff_y - (i - 4) * self.line_spacing // 2
                pygame.draw.line(screen, COLORS['text'], 
                               (note_x - 25, y), 
                               (note_x + 25, y), 2)
                               
    def _draw_rhythm_question(self, screen: pygame.Surface):
        """绘制节奏题目"""
        # 检查当前题目是否有效
        if not self.current_question or not hasattr(self.current_question, 'pattern'):
            # 如果没有有效题目，重新生成
            self._generate_rhythm_question()
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
            
    def _draw_interval_question(self, screen: pygame.Surface):
        """绘制音程题目"""
        # 绘制五线谱（默认高音谱号）
        self._draw_staff(screen, 'treble')
        
        # 绘制两个音符
        note1 = self.current_question['note1']
        note2 = self.current_question['note2']
        
        # 第一个音符
        note1_x = WINDOW_WIDTH // 2 - 80
        note1_y = self.staff_y - (note1.staff_position - 4) * self.line_spacing // 2
        
        pygame.draw.ellipse(screen, COLORS['text'], 
                          pygame.Rect(note1_x - 15, note1_y - 10, 30, 20))
        pygame.draw.line(screen, COLORS['text'], 
                       (note1_x + 15, note1_y), 
                       (note1_x + 15, note1_y - 40), 3)
                       
        # 第二个音符
        note2_x = WINDOW_WIDTH // 2 + 80
        note2_y = self.staff_y - (note2.staff_position - 4) * self.line_spacing // 2
        
        pygame.draw.ellipse(screen, COLORS['text'], 
                          pygame.Rect(note2_x - 15, note2_y - 10, 30, 20))
        pygame.draw.line(screen, COLORS['text'], 
                       (note2_x + 15, note2_y), 
                       (note2_x + 15, note2_y - 40), 3)
                       
        # 绘制连线
        pygame.draw.line(screen, COLORS['primary'], 
                       (note1_x + 20, note1_y), 
                       (note2_x - 20, note2_y), 2)
                       
    def _draw_answer_options(self, screen: pygame.Surface):
        """绘制答案选项"""
        button_font = get_chinese_font(28)
        
        for i, (button, option) in enumerate(zip(self.answer_buttons, self.answer_options)):
            # 确定按钮颜色
            if self.show_result_emoji:
                if self.current_mode == 'staff_reading' and option == self.current_question.note_name:
                    color = COLORS['success']
                elif self.current_mode == 'rhythm' and option == self.current_question.chinese_name:
                    color = COLORS['success']
                elif self.current_mode == 'interval':
                    interval_steps = self.current_question['interval']
                    interval_names = {1: '二度', 2: '三度', 3: '四度', 4: '五度', 5: '六度', 6: '七度', 7: '八度', 8: '八度以上'}
                    correct_answer = interval_names.get(interval_steps, f'{interval_steps}度')
                    if option == correct_answer:
                        color = COLORS['success']
                    else:
                        color = COLORS['danger'] if option == self.player_answer else COLORS['secondary']
                else:
                    color = COLORS['danger'] if option == self.player_answer else COLORS['secondary']
            else:
                color = COLORS['primary']
                
            # 绘制按钮
            pygame.draw.rect(screen, color, button, border_radius=10)
            pygame.draw.rect(screen, COLORS['text'], button, 3, border_radius=10)
            
            # 绘制文字
            # 如果是单个字母（音名），使用更大的字体
            if len(option) == 1:
                note_font = pygame.font.Font(None, 48)
                text_surf = note_font.render(option, True, COLORS['white'])
            else:
                text_surf = button_font.render(option, True, COLORS['white'])
            text_rect = text_surf.get_rect(center=button.center)
            screen.blit(text_surf, text_rect)
            
            # 在按钮下方添加小喇叭图标（仅对音名按钮）
            if self.current_mode == 'staff_reading' and len(option) == 1:
                speaker_size = 15
                speaker_x = button.centerx
                speaker_y = button.bottom - 10
                # 绘制小喇叭
                pygame.draw.polygon(screen, COLORS['white'], 
                                  [(speaker_x - speaker_size//2, speaker_y - speaker_size//4),
                                   (speaker_x - speaker_size//2, speaker_y + speaker_size//4),
                                   (speaker_x, speaker_y + speaker_size//2),
                                   (speaker_x, speaker_y - speaker_size//2)], 2)
            
    def _draw_game_complete(self, screen: pygame.Surface):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        result_font = get_chinese_font(72)
        score_percent = (self.score / (self.rounds_total * 10)) * 100
        
        if score_percent >= 80:
            result_text = "音乐小天才！"
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
    
    def _draw_treble_clef(self, screen: pygame.Surface, x: int, y: int):
        """绘制高音谱号"""
        # 使用标准高音谱号绘制函数
        draw_treble_clef(screen, x, y + self.line_spacing, COLORS['text'], 0.8)
    
    def _draw_bass_clef(self, screen: pygame.Surface, x: int, y: int):
        """绘制低音谱号"""
        # 使用标准低音谱号绘制函数
        draw_bass_clef(screen, x, y - self.line_spacing, COLORS['text'], 0.8)