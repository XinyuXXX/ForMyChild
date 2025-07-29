#!/usr/bin/env python3
"""
五线谱识谱游戏
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


class StaffReadingGame:
    """五线谱识谱游戏"""
    
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
        
        # 加载图片
        self.treble_clef_img = None
        self.bass_clef_img = None
        self.keyboard_img = None
        self._load_images()
        
        # 初始化音频
        try:
            init_pygame_mixer()
        except Exception as e:
            print(f"音频初始化失败: {e}")
        
        # 播放欢迎语音
        speak("五线谱游戏开始啦！让我们一起认识音符吧！")
        
        # 开始第一轮
        self._start_new_round()
        
    def _init_notes(self):
        """初始化音符"""
        # 五线谱音符位置定义 - 高音谱号和低音谱号
        # 高音谱号：第一线(底线)=E4, 第二线=G4, 第三线=B4, 第四线=D5, 第五线=F5
        # 低音谱号：第一线=G2, 第二线=B2, 第三线=D3, 第四线=F3, 第五线=A3
        
        # 创建包含3个八度的音符（C3到B5），对应键盘的21个白键
        self.notes = [
            # 低音区（C3-B3） - 使用低音谱号显示
            MusicNote('C', 3, -6, 130.81),  # 低音谱号第二间
            MusicNote('D', 3, -5, 146.83),  # 低音谱号第三线
            MusicNote('E', 3, -4, 164.81),  # 低音谱号第三间
            MusicNote('F', 3, -3, 174.61),  # 低音谱号第四线
            MusicNote('G', 3, -2, 196.00),  # 低音谱号第四间
            MusicNote('A', 3, -1, 220.00),  # 低音谱号第五线
            MusicNote('B', 3, 0, 246.94),   # 低音谱号第五线上
            
            # 中音区（C4-B4） - 使用高音谱号显示
            MusicNote('C', 4, -2, 261.63),  # 高音谱号下加一线
            MusicNote('D', 4, -1, 293.66),  # 高音谱号第一线下方的间
            MusicNote('E', 4, 0, 329.63),   # 高音谱号第一线
            MusicNote('F', 4, 1, 349.23),   # 高音谱号第一间
            MusicNote('G', 4, 2, 392.00),   # 高音谱号第二线
            MusicNote('A', 4, 3, 440.00),   # 高音谱号第二间
            MusicNote('B', 4, 4, 493.88),   # 高音谱号第三线
            
            # 高音区（C5-B5） - 使用高音谱号显示
            MusicNote('C', 5, 5, 523.25),   # 高音谱号第三间
            MusicNote('D', 5, 6, 587.33),   # 高音谱号第四线
            MusicNote('E', 5, 7, 659.25),   # 高音谱号第四间
            MusicNote('F', 5, 8, 698.46),   # 高音谱号第五线
            MusicNote('G', 5, 9, 783.99),   # 高音谱号第五线上方的间
            MusicNote('A', 5, 10, 880.00),  # 高音谱号上加一线的间
            MusicNote('B', 5, 11, 987.77),  # 高音谱号上加一线
        ]
        
        # 根据难度选择音符范围（1-10级）
        difficulty_ranges = {
            1: (7, 10),   # C4-E4 (3个音符)
            2: (7, 12),   # C4-G4 (5个音符)
            3: (7, 14),   # C4-B4 (7个音符)
            4: (5, 14),   # G3-B4 (9个音符)
            5: (4, 15),   # F3-C5 (11个音符)
            6: (3, 16),   # E3-D5 (13个音符)
            7: (2, 17),   # D3-E5 (15个音符)
            8: (1, 18),   # C3-F5 (17个音符)
            9: (0, 19),   # C3-G5 (19个音符)
            10: (0, 21)   # C3-B5 (21个音符，全部)
        }
        
        start, end = difficulty_ranges.get(self.difficulty, (7, 14))
        self.available_notes = self.notes[start:end]
            
    def _load_images(self):
        """加载所需图片"""
        try:
            # 获取assets目录路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            treble_path = os.path.join(base_dir, 'assets', 'images', 'treble_clef.jpeg')
            bass_path = os.path.join(base_dir, 'assets', 'images', 'bass_clef.jpeg')
            keyboard_path = os.path.join(base_dir, 'assets', 'images', 'keyboard2.png')
            
            # 加载谱号图片
            if os.path.exists(treble_path):
                self.treble_clef_img = pygame.image.load(treble_path).convert()
                # 使用白色作为透明色
                self.treble_clef_img.set_colorkey((255, 255, 255))
            if os.path.exists(bass_path):
                self.bass_clef_img = pygame.image.load(bass_path).convert()
                # 使用白色作为透明色
                self.bass_clef_img.set_colorkey((255, 255, 255))
            
            # 加载键盘图片
            if os.path.exists(keyboard_path):
                self.keyboard_img = pygame.image.load(keyboard_path).convert_alpha()
        except Exception as e:
            print(f"加载图片失败: {e}")
            
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
        """生成五线谱识谱题目"""
        # 随机选择一个音符
        self.current_question = random.choice(self.available_notes)
        
        # 初始化键盘映射
        self._create_key_mapping()
        
        # 语音提示
        speak("请看五线谱上的音符，这是什么音？")
        
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
            
        # 检查键盘点击
        note, octave = self._get_key_from_position(pos[0], pos[1])
        if note and octave:
            # 播放对应的音
            # 找到对应音符的频率
            for n in self.notes:
                if n.note_name == note and n.octave == octave:
                    play_note(note, octave)
                    break
                    
            # 检查答案（需要检查音名和八度）
            self.player_answer = (note, octave)
            self._check_answer()
                
    def _check_answer(self):
        """检查答案"""
        # 检查音名和八度都正确
        if isinstance(self.player_answer, tuple):
            correct = (self.player_answer[0] == self.current_question.note_name and 
                      self.player_answer[1] == self.current_question.octave)
        else:
            correct = False
        
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
        title = "五线谱认识"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, 50))
        screen.blit(title_surf, title_rect)
        
        # 在标题旁边添加喇叭按钮
        speaker_btn = SpeakerButton(WINDOW_WIDTH//2 + title_surf.get_width()//2 + 50, 50, 25)
        speaker_btn.draw(screen)
        self.speaker_buttons.append((speaker_btn, "现在是五线谱认识环节"))
        
        if not self.game_complete:
            if self.current_question:
                # 绘制五线谱和音符
                self._draw_staff_question(screen)
                
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
        
    def _draw_staff_question(self, screen: pygame.Surface):
        """绘制五线谱题目"""
        # 根据音符决定使用哪个谱号
        if self.current_question.octave == 3:
            # C3-B3使用低音谱号
            self._draw_staff(screen, 'bass')
            # 低音谱号位置映射：第一线=G2, 第二线=B2, 第三线=D3, 第四线=F3, 第五线=A3
            # C3在第二间，D3在第三线，E3在第三间，F3在第四线，G3在第四间，A3在第五线，B3在第五线上
            bass_positions = {
                'C': 3,   # 第二间
                'D': 4,   # 第三线
                'E': 5,   # 第三间
                'F': 6,   # 第四线
                'G': 7,   # 第四间
                'A': 8,   # 第五线
                'B': 9,   # 第五线上
            }
            note_position = bass_positions[self.current_question.note_name]
            note_y = self.staff_y + self.line_spacing * 2 - (note_position * self.line_spacing // 2)
        else:
            # C4-B5使用高音谱号
            self._draw_staff(screen, 'treble')
            # 高音谱号位置已经正确
            note_y = self.staff_y + self.line_spacing * 2 - (self.current_question.staff_position * self.line_spacing // 2)
        
        # 绘制音符
        note_x = WINDOW_WIDTH // 2
        
        # 音符头
        pygame.draw.ellipse(screen, COLORS['text'], 
                          pygame.Rect(note_x - 15, note_y - 10, 30, 20))
        
        # 符干
        pygame.draw.line(screen, COLORS['text'], 
                       (note_x + 15, note_y), 
                       (note_x + 15, note_y - 40), 3)
                       
        # 如果需要，绘制加线
        if self.current_question.staff_position < 0:  # 下加线
            # C4在-2位置，需要一条下加线
            for i in range(-2, self.current_question.staff_position - 1, -2):
                y = self.staff_y + self.line_spacing * 2 - (i * self.line_spacing // 2)
                pygame.draw.line(screen, COLORS['text'], 
                               (note_x - 25, y), 
                               (note_x + 25, y), 2)
        elif self.current_question.staff_position > 8:  # 上加线
            # F5在位置8（第五线），所以大于8需要上加线
            for i in range(10, self.current_question.staff_position + 1, 2):
                y = self.staff_y + self.line_spacing * 2 - (i * self.line_spacing // 2)
                pygame.draw.line(screen, COLORS['text'], 
                               (note_x - 25, y), 
                               (note_x + 25, y), 2)
                               
    def _draw_answer_options(self, screen: pygame.Surface):
        """绘制21键钢琴键盘作为答案选项"""
        # 自定义绘制21键键盘
        keyboard_width = int(WINDOW_WIDTH * 0.9)
        keyboard_height = 120
        keyboard_x = (WINDOW_WIDTH - keyboard_width) // 2
        keyboard_y = WINDOW_HEIGHT - keyboard_height - 30
        
        # 存储键盘位置供点击检测使用
        self.keyboard_rect = pygame.Rect(keyboard_x, keyboard_y, keyboard_width, keyboard_height)
        
        # 绘制键盘背景
        pygame.draw.rect(screen, (240, 240, 240), self.keyboard_rect)
        pygame.draw.rect(screen, COLORS['text'], self.keyboard_rect, 2)
        
        # 绘制21个白键
        self._draw_custom_keyboard(screen, keyboard_x, keyboard_y, keyboard_width, keyboard_height)
        
        # 高亮显示正确答案（如果显示结果）
        if self.show_result_emoji and self.current_question:
            self._highlight_key(screen, self.current_question.note_name, 
                              self.current_question.octave, keyboard_x, keyboard_y, 
                              keyboard_width, keyboard_height, COLORS['success'])
                                  
    def _draw_custom_keyboard(self, screen: pygame.Surface, kb_x: int, kb_y: int, 
                             kb_width: int, kb_height: int):
        """绘制自定义21键钢琴键盘"""
        # 21个白键
        white_key_width = kb_width / 21
        white_key_height = kb_height * 0.9
        
        # 字体
        label_font = get_chinese_font(16)
        octave_font = get_chinese_font(12)
        
        # 绘制白键
        white_keys = []
        for i in range(21):
            x = kb_x + i * white_key_width
            key_rect = pygame.Rect(x, kb_y, white_key_width - 2, white_key_height)
            pygame.draw.rect(screen, COLORS['white'], key_rect)
            pygame.draw.rect(screen, COLORS['text'], key_rect, 1)
            
            # 确定音名和八度
            octave = 3 + (i // 7)  # C3, C4, C5
            note_index = i % 7
            note_names = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
            note = note_names[note_index]
            
            # 绘制音名
            note_surf = label_font.render(note, True, COLORS['text'])
            note_rect = note_surf.get_rect(centerx=x + white_key_width/2, 
                                          bottom=kb_y + white_key_height - 5)
            screen.blit(note_surf, note_rect)
            
            # 绘制八度数字
            octave_surf = octave_font.render(str(octave), True, COLORS['secondary'])
            octave_rect = octave_surf.get_rect(centerx=x + white_key_width/2,
                                              bottom=note_rect.top - 2)
            screen.blit(octave_surf, octave_rect)
            
            white_keys.append({'rect': key_rect, 'note': note, 'octave': octave})
        
        # 绘制黑键
        black_key_width = white_key_width * 0.6
        black_key_height = kb_height * 0.6
        black_key_pattern = [1, 1, 0, 1, 1, 1, 0]  # C#, D#, -, F#, G#, A#, -
        
        for octave_num in range(3):
            for i in range(7):
                if black_key_pattern[i]:
                    key_index = octave_num * 7 + i
                    if key_index < 20:  # 最后一个黑键是A#5
                        x = kb_x + (key_index + 0.7) * white_key_width
                        key_rect = pygame.Rect(x, kb_y, black_key_width, black_key_height)
                        pygame.draw.rect(screen, COLORS['text'], key_rect)
                        
                        # 黑键音名
                        note_names_sharp = ['C#', 'D#', '', 'F#', 'G#', 'A#', '']
                        note = note_names_sharp[i]
                        if note:
                            note_surf = label_font.render(note, True, COLORS['white'])
                            note_rect = note_surf.get_rect(center=(x + black_key_width/2,
                                                                  kb_y + black_key_height/2))
                            screen.blit(note_surf, note_rect)
        
        # 添加区域标签
        region_font = get_chinese_font(14)
        regions = [
            ("低音区", kb_x + 3.5 * white_key_width, kb_y - 20),
            ("中音区", kb_x + 10.5 * white_key_width, kb_y - 20),
            ("高音区", kb_x + 17.5 * white_key_width, kb_y - 20)
        ]
        
        for text, x, y in regions:
            surf = region_font.render(text, True, COLORS['primary'])
            rect = surf.get_rect(center=(x, y))
            screen.blit(surf, rect)
                             
    def _create_key_mapping(self):
        """创建键位映射，21个键从C3到B5"""
        # 21个键的映射
        self.key_mapping = []
        notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        
        # C3-B3
        for i, note in enumerate(notes):
            self.key_mapping.append({'note': note, 'octave': 3})
        
        # C4-B4
        for i, note in enumerate(notes):
            self.key_mapping.append({'note': note, 'octave': 4})
            
        # C5-B5
        for i, note in enumerate(notes):
            self.key_mapping.append({'note': note, 'octave': 5})
            
    def _get_key_from_position(self, x: int, y: int) -> tuple:
        """根据点击位置获取对应的音符"""
        if not hasattr(self, 'keyboard_rect') or not self.keyboard_rect.collidepoint((x, y)):
            return None, None
            
        # 计算相对位置
        rel_x = x - self.keyboard_rect.x
        rel_y = y - self.keyboard_rect.y
        
        # 白键宽度（21个白键）
        white_key_width = self.keyboard_rect.width / 21
        
        # 黑键高度约占键盘高度的60%
        black_key_height = self.keyboard_rect.height * 0.6
        
        # 先检查是否点击在黑键上
        if rel_y < black_key_height:
            # 黑键位置（相对于白键）
            black_key_positions = []
            for octave_num in range(3):
                octave = 3 + octave_num
                base = octave_num * 7
                black_key_positions.extend([
                    (base + 0.7, 'C#', octave),
                    (base + 1.7, 'D#', octave),
                    (base + 3.7, 'F#', octave),
                    (base + 4.7, 'G#', octave),
                    (base + 5.7, 'A#', octave),
                ])
            
            for pos, note, octave in black_key_positions:
                black_x = pos * white_key_width
                if abs(rel_x - black_x) < white_key_width * 0.3:
                    return note, octave
        
        # 检查白键
        white_key_index = int(rel_x / white_key_width)
        if 0 <= white_key_index < 21:
            # 白键映射
            octave = 3 + (white_key_index // 7)
            note_index = white_key_index % 7
            note_names = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
            return note_names[note_index], octave
                
        return None, None
        
    def _highlight_key(self, screen: pygame.Surface, note: str, octave: int, 
                      kb_x: int, kb_y: int, kb_width: int, kb_height: int, color):
        """高亮显示指定的键"""
        # 白键宽度
        white_key_width = kb_width / 21
        
        # 计算键的位置
        if '#' not in note:  # 白键
            # 计算白键索引
            note_names = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
            note_index = note_names.index(note)
            octave_offset = (octave - 3) * 7
            key_index = octave_offset + note_index
            
            if 0 <= key_index < 21:
                # 绘制高亮框
                x = kb_x + key_index * white_key_width
                highlight_rect = pygame.Rect(
                    x + 2,
                    kb_y + kb_height * 0.7,  # 白键下部
                    white_key_width - 4,
                    kb_height * 0.2
                )
                pygame.draw.rect(screen, color, highlight_rect, 3)
            
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