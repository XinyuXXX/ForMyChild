#!/usr/bin/env python3
"""
增强版设置界面 - 包含游戏难度设置
"""
import pygame
import datetime
from typing import Optional, Tuple, Dict
from ..config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak
from ..utils.ui_utils import SpeakerButton
from ..utils.emoji_utils import draw_happy_face


class EnhancedSettingsScreen:
    """增强版设置界面"""
    
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.done = False
        
        # 获取当前信息
        self.player_name = game_manager.progress.get_player_name()
        self.birth_date = game_manager.progress.data.get('birth_date', None)
        
        # 难度设置 - 默认值
        self.difficulty_settings = game_manager.progress.data.get('difficulty_settings', {
            'find_difference': 5,  # 找不同
            'counting': 5,         # 数一数
            'simple_math': 5,      # 算一算
            'staff_reading': 5,    # 五线谱
            'rhythm': 5,           # 节奏
            'interval': 5,         # 音程
            'drawing': 5           # 画画
        })
        
        # 输入状态
        self.editing_name = False
        self.editing_birth = False
        self.temp_name = self.player_name
        self.temp_birth_year = ""
        self.temp_birth_month = ""
        self.temp_birth_day = ""
        
        # 如果有生日信息，解析它
        if self.birth_date:
            try:
                year, month, day = self.birth_date.split('-')
                self.temp_birth_year = year
                self.temp_birth_month = month
                self.temp_birth_day = day
            except:
                pass
        
        # 滚动相关
        self.scroll_y = 0
        self.content_height = 1000  # 内容总高度
        self.visible_height = WINDOW_HEIGHT - 100  # 可见区域高度
        
        # 输入框（相对位置）
        self.name_box = pygame.Rect(WINDOW_WIDTH//2 - 200, 150, 400, 50)
        self.year_box = pygame.Rect(WINDOW_WIDTH//2 - 200, 270, 120, 50)
        self.month_box = pygame.Rect(WINDOW_WIDTH//2 - 40, 270, 80, 50)
        self.day_box = pygame.Rect(WINDOW_WIDTH//2 + 80, 270, 80, 50)
        
        # 按钮
        self.save_button = pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT - 70, 130, 50)
        self.cancel_button = pygame.Rect(WINDOW_WIDTH//2 + 20, WINDOW_HEIGHT - 70, 130, 50)
        
        # 难度滑块位置
        self.difficulty_sliders = {}
        self._create_difficulty_sliders()
        
        # 光标
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 播放欢迎语音
        speak("这里可以修改你的信息和游戏难度哦！")
        
    def _create_difficulty_sliders(self):
        """创建难度滑块"""
        start_y = 450
        games = [
            ('find_difference', '找不同'),
            ('counting', '数一数'),
            ('simple_math', '算一算'),
            ('staff_reading', '五线谱'),
            ('rhythm', '节奏'),
            ('interval', '音程'),
            ('drawing', '画画')
        ]
        
        for i, (game_id, game_name) in enumerate(games):
            y = start_y + i * 80
            slider_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, y, 300, 20)
            self.difficulty_sliders[game_id] = {
                'rect': slider_rect,
                'name': game_name,
                'value': self.difficulty_settings.get(game_id, 5)
            }
            
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """处理事件，返回'save'、'cancel'或None"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            # 转换为内容坐标
            content_y = mouse_y + self.scroll_y
            
            # 检查喇叭按钮
            for button, text in self.speaker_buttons:
                if button.check_click(event.pos):
                    speak(text)
                    return None
            
            # 检查输入框点击（需要考虑滚动）
            name_box_screen = self.name_box.copy()
            name_box_screen.y -= self.scroll_y
            
            year_box_screen = self.year_box.copy()
            year_box_screen.y -= self.scroll_y
            
            month_box_screen = self.month_box.copy()
            month_box_screen.y -= self.scroll_y
            
            day_box_screen = self.day_box.copy()
            day_box_screen.y -= self.scroll_y
            
            self.editing_name = name_box_screen.collidepoint(event.pos)
            self.editing_birth = False
            
            if year_box_screen.collidepoint(event.pos):
                self.editing_birth = 'year'
            elif month_box_screen.collidepoint(event.pos):
                self.editing_birth = 'month'
            elif day_box_screen.collidepoint(event.pos):
                self.editing_birth = 'day'
            
            # 检查难度滑块
            for game_id, slider_data in self.difficulty_sliders.items():
                slider_rect_screen = slider_data['rect'].copy()
                slider_rect_screen.y -= self.scroll_y
                
                if slider_rect_screen.collidepoint(event.pos):
                    # 计算新的难度值
                    rel_x = mouse_x - slider_rect_screen.x
                    new_value = max(1, min(10, int(rel_x / slider_rect_screen.width * 10) + 1))
                    slider_data['value'] = new_value
                    self.difficulty_settings[game_id] = new_value
                    speak(f"{slider_data['name']}难度设为{new_value}级")
            
            # 检查按钮
            if self.save_button.collidepoint(event.pos):
                if self._validate_and_save():
                    return 'save'
            elif self.cancel_button.collidepoint(event.pos):
                return 'cancel'
                
        elif event.type == pygame.MOUSEWHEEL:
            # 处理滚轮
            self.scroll_y = max(0, min(self.content_height - self.visible_height, 
                                      self.scroll_y - event.y * 30))
                                      
        elif event.type == pygame.KEYDOWN:
            if self.editing_name:
                if event.key == pygame.K_BACKSPACE:
                    self.temp_name = self.temp_name[:-1]
                elif event.key == pygame.K_RETURN:
                    self.editing_name = False
                elif len(self.temp_name) < 8 and event.unicode and event.unicode.isprintable():
                    self.temp_name += event.unicode
                    
            elif self.editing_birth:
                if event.key == pygame.K_BACKSPACE:
                    if self.editing_birth == 'year':
                        self.temp_birth_year = self.temp_birth_year[:-1]
                    elif self.editing_birth == 'month':
                        self.temp_birth_month = self.temp_birth_month[:-1]
                    elif self.editing_birth == 'day':
                        self.temp_birth_day = self.temp_birth_day[:-1]
                elif event.key == pygame.K_TAB:
                    # Tab键切换输入框
                    if self.editing_birth == 'year':
                        self.editing_birth = 'month'
                    elif self.editing_birth == 'month':
                        self.editing_birth = 'day'
                    else:
                        self.editing_birth = False
                elif event.unicode and event.unicode.isdigit():
                    if self.editing_birth == 'year' and len(self.temp_birth_year) < 4:
                        self.temp_birth_year += event.unicode
                    elif self.editing_birth == 'month' and len(self.temp_birth_month) < 2:
                        self.temp_birth_month += event.unicode
                    elif self.editing_birth == 'day' and len(self.temp_birth_day) < 2:
                        self.temp_birth_day += event.unicode
                        
        return None
    
    def update(self, dt: float):
        """更新界面状态"""
        # 更新光标闪烁
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
            
        # 更新喇叭按钮
        mouse_pos = pygame.mouse.get_pos()
        for button, _ in self.speaker_buttons:
            button.update(mouse_pos)
    
    def draw(self, screen: pygame.Surface):
        """绘制界面"""
        screen.fill(COLORS['background'])
        
        # 清空喇叭按钮列表
        self.speaker_buttons.clear()
        
        # 创建内容表面
        content_surface = pygame.Surface((WINDOW_WIDTH, self.content_height))
        content_surface.fill(COLORS['background'])
        
        # 标题
        title_font = get_chinese_font(48)
        title = "游戏设置"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, 50))
        content_surface.blit(title_surf, title_rect)
        
        # === 个人信息部分 ===
        section_font = get_chinese_font(36)
        info_title = section_font.render("个人信息", True, COLORS['primary'])
        content_surface.blit(info_title, (100, 100))
        
        # 名字部分
        label_font = get_chinese_font(28)
        name_label = label_font.render("小朋友的名字：", True, COLORS['text'])
        content_surface.blit(name_label, (self.name_box.x - 150, self.name_box.y + 12))
        
        # 名字输入框
        box_color = COLORS['primary'] if self.editing_name else COLORS['secondary']
        pygame.draw.rect(content_surface, COLORS['white'], self.name_box)
        pygame.draw.rect(content_surface, box_color, self.name_box, 3, border_radius=5)
        
        if self.temp_name:
            name_font = get_chinese_font(32)
            name_surf = name_font.render(self.temp_name, True, COLORS['text'])
            name_rect = name_surf.get_rect(center=self.name_box.center)
            content_surface.blit(name_surf, name_rect)
            
            if self.editing_name and self.cursor_visible:
                cursor_x = name_rect.right + 5
                pygame.draw.line(content_surface, COLORS['text'], 
                               (cursor_x, self.name_box.y + 10),
                               (cursor_x, self.name_box.y + 40), 2)
        
        # 生日部分
        birth_label = label_font.render("出生日期：", True, COLORS['text'])
        content_surface.blit(birth_label, (self.year_box.x - 150, self.year_box.y + 12))
        
        # 年份输入框
        year_color = COLORS['primary'] if self.editing_birth == 'year' else COLORS['secondary']
        pygame.draw.rect(content_surface, COLORS['white'], self.year_box)
        pygame.draw.rect(content_surface, year_color, self.year_box, 3, border_radius=5)
        
        year_text = self.temp_birth_year if self.temp_birth_year else "年份"
        year_color_text = COLORS['text'] if self.temp_birth_year else COLORS['light_gray']
        year_surf = label_font.render(year_text, True, year_color_text)
        year_rect = year_surf.get_rect(center=self.year_box.center)
        content_surface.blit(year_surf, year_rect)
        
        # 月份输入框
        month_color = COLORS['primary'] if self.editing_birth == 'month' else COLORS['secondary']
        pygame.draw.rect(content_surface, COLORS['white'], self.month_box)
        pygame.draw.rect(content_surface, month_color, self.month_box, 3, border_radius=5)
        
        month_text = self.temp_birth_month if self.temp_birth_month else "月"
        month_color_text = COLORS['text'] if self.temp_birth_month else COLORS['light_gray']
        month_surf = label_font.render(month_text, True, month_color_text)
        month_rect = month_surf.get_rect(center=self.month_box.center)
        content_surface.blit(month_surf, month_rect)
        
        # 日期输入框
        day_color = COLORS['primary'] if self.editing_birth == 'day' else COLORS['secondary']
        pygame.draw.rect(content_surface, COLORS['white'], self.day_box)
        pygame.draw.rect(content_surface, day_color, self.day_box, 3, border_radius=5)
        
        day_text = self.temp_birth_day if self.temp_birth_day else "日"
        day_color_text = COLORS['text'] if self.temp_birth_day else COLORS['light_gray']
        day_surf = label_font.render(day_text, True, day_color_text)
        day_rect = day_surf.get_rect(center=self.day_box.center)
        content_surface.blit(day_surf, day_rect)
        
        # 显示月龄
        if self.temp_birth_year and self.temp_birth_month and self.temp_birth_day:
            try:
                birth = datetime.date(int(self.temp_birth_year), 
                                    int(self.temp_birth_month), 
                                    int(self.temp_birth_day))
                today = datetime.date.today()
                months = (today.year - birth.year) * 12 + today.month - birth.month
                
                if months >= 0:
                    age_text = f"当前月龄：{months}个月"
                    age_surf = label_font.render(age_text, True, COLORS['success'])
                    age_rect = age_surf.get_rect(center=(WINDOW_WIDTH//2, 340))
                    content_surface.blit(age_surf, age_rect)
            except:
                pass
        
        # === 难度设置部分 ===
        diff_title = section_font.render("游戏难度设置", True, COLORS['primary'])
        content_surface.blit(diff_title, (100, 390))
        
        # 难度说明
        hint_font = get_chinese_font(20)
        hint_text = "拖动滑块调整各游戏难度（1-10级）"
        hint_surf = hint_font.render(hint_text, True, COLORS['secondary'])
        content_surface.blit(hint_surf, (WINDOW_WIDTH//2 - 150, 420))
        
        # 绘制难度滑块
        for game_id, slider_data in self.difficulty_sliders.items():
            self._draw_difficulty_slider(content_surface, slider_data)
        
        # 绘制内容到屏幕（考虑滚动）
        screen.blit(content_surface, (0, -self.scroll_y))
        
        # 绘制固定的按钮（不随滚动移动）
        # 保存按钮
        pygame.draw.rect(screen, COLORS['success'], self.save_button, border_radius=25)
        save_text = label_font.render("保存", True, COLORS['white'])
        save_rect = save_text.get_rect(center=self.save_button.center)
        screen.blit(save_text, save_rect)
        
        # 取消按钮
        pygame.draw.rect(screen, COLORS['secondary'], self.cancel_button, border_radius=25)
        cancel_text = label_font.render("取消", True, COLORS['white'])
        cancel_rect = cancel_text.get_rect(center=self.cancel_button.center)
        screen.blit(cancel_text, cancel_rect)
        
        # 绘制滚动条
        if self.content_height > self.visible_height:
            scrollbar_rect = pygame.Rect(WINDOW_WIDTH - 20, 50, 15, self.visible_height)
            pygame.draw.rect(screen, COLORS['light_gray'], scrollbar_rect)
            
            # 滚动条滑块
            scroll_ratio = self.scroll_y / (self.content_height - self.visible_height)
            thumb_height = max(30, self.visible_height * self.visible_height / self.content_height)
            thumb_y = 50 + scroll_ratio * (self.visible_height - thumb_height)
            thumb_rect = pygame.Rect(WINDOW_WIDTH - 20, thumb_y, 15, thumb_height)
            pygame.draw.rect(screen, COLORS['secondary'], thumb_rect)
        
        # 装饰
        draw_happy_face(screen, 50, 30, 40, color=(255, 182, 193))
        draw_happy_face(screen, WINDOW_WIDTH - 50, 30, 40, color=(135, 206, 235))
    
    def _draw_difficulty_slider(self, surface: pygame.Surface, slider_data: Dict):
        """绘制单个难度滑块"""
        label_font = get_chinese_font(24)
        value_font = get_chinese_font(20)
        
        # 游戏名称
        name_surf = label_font.render(slider_data['name'], True, COLORS['text'])
        surface.blit(name_surf, (slider_data['rect'].x - 100, slider_data['rect'].y - 5))
        
        # 滑块轨道
        pygame.draw.rect(surface, COLORS['light_gray'], slider_data['rect'], border_radius=10)
        
        # 滑块值
        value = slider_data['value']
        fill_width = int((value - 1) / 9 * slider_data['rect'].width)
        fill_rect = pygame.Rect(slider_data['rect'].x, slider_data['rect'].y, 
                               fill_width, slider_data['rect'].height)
        
        # 根据难度值选择颜色
        if value <= 3:
            color = COLORS['success']  # 简单 - 绿色
        elif value <= 7:
            color = COLORS['primary']  # 中等 - 蓝色
        else:
            color = COLORS['danger']   # 困难 - 红色
            
        pygame.draw.rect(surface, color, fill_rect, border_radius=10)
        
        # 滑块圆点
        thumb_x = slider_data['rect'].x + fill_width
        thumb_y = slider_data['rect'].centery
        pygame.draw.circle(surface, COLORS['white'], (thumb_x, thumb_y), 12)
        pygame.draw.circle(surface, color, (thumb_x, thumb_y), 10)
        
        # 显示数值
        value_text = f"{value}级"
        value_surf = value_font.render(value_text, True, COLORS['text'])
        value_rect = value_surf.get_rect(left=slider_data['rect'].right + 20, 
                                       centery=slider_data['rect'].centery)
        surface.blit(value_surf, value_rect)
        
        # 难度描述
        difficulty_names = {
            1: "超简单", 2: "很简单", 3: "简单",
            4: "较易", 5: "适中", 6: "稍难",
            7: "困难", 8: "很困难", 9: "超困难", 10: "极限"
        }
        desc_text = difficulty_names.get(value, "")
        desc_surf = value_font.render(desc_text, True, color)
        desc_rect = desc_surf.get_rect(left=value_rect.right + 20, 
                                      centery=slider_data['rect'].centery)
        surface.blit(desc_surf, desc_rect)
    
    def _validate_and_save(self) -> bool:
        """验证并保存数据"""
        if not self.temp_name:
            speak("请输入小朋友的名字")
            return False
        
        # 保存名字
        self.game_manager.progress.data['player_name'] = self.temp_name
        
        # 验证并保存生日
        if self.temp_birth_year and self.temp_birth_month and self.temp_birth_day:
            try:
                year = int(self.temp_birth_year)
                month = int(self.temp_birth_month)
                day = int(self.temp_birth_day)
                
                # 验证日期合法性
                birth_date = datetime.date(year, month, day)
                today = datetime.date.today()
                
                if birth_date > today:
                    speak("生日不能是未来的日期哦")
                    return False
                
                # 计算月龄
                months = (today.year - birth_date.year) * 12 + today.month - birth_date.month
                if months < 36:  # 小于3岁
                    speak("这个游戏适合3岁以上的小朋友哦")
                    return False
                elif months > 120:  # 大于10岁
                    speak("这个游戏是为3到10岁的小朋友设计的")
                    return False
                
                # 保存生日
                self.game_manager.progress.data['birth_date'] = f"{year}-{month:02d}-{day:02d}"
                
            except ValueError:
                speak("请输入正确的日期")
                return False
        
        # 保存难度设置
        self.game_manager.progress.data['difficulty_settings'] = self.difficulty_settings
        
        # 保存进度
        self.game_manager.progress.save_progress()
        speak(f"已保存{self.temp_name}的信息和游戏设置")
        return True
    
    def get_result(self) -> dict:
        """获取设置结果"""
        return {
            'name': self.temp_name,
            'birth_date': f"{self.temp_birth_year}-{self.temp_birth_month}-{self.temp_birth_day}" 
                        if all([self.temp_birth_year, self.temp_birth_month, self.temp_birth_day]) 
                        else None,
            'difficulty_settings': self.difficulty_settings
        }