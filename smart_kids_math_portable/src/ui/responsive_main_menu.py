import pygame
import math
from typing import Optional, Tuple, List, Dict
from ..config import COLORS, FONTS
from ..core.game_manager import GameManager
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak, stop_speaking
from ..utils.ui_utils import SpeakerButton


class ResponsiveGameCard:
    """响应式游戏卡片"""
    def __init__(self, text: str, game_type: str, icon: str, color: Tuple[int, int, int]):
        self.text = text
        self.game_type = game_type
        self.icon = icon
        self.color = color
        self.hover = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.visible = False
        self.rect = pygame.Rect(0, 0, 160, 140)
        
    def update_position(self, x: int, y: int):
        """更新位置"""
        self.rect.x = x
        self.rect.y = y
        
    def update(self, dt: float, mouse_pos: Tuple[int, int], visible: bool):
        """更新卡片状态"""
        self.visible = visible
        
        if visible:
            self.hover = self.rect.collidepoint(mouse_pos)
            self.target_scale = 1.05 if self.hover else 1.0
        else:
            self.hover = False
            self.target_scale = 0.8
            
        # 平滑缩放动画
        self.scale += (self.target_scale - self.scale) * 0.2
        
    def draw(self, screen: pygame.Surface, alpha: int = 255):
        """绘制卡片"""
        if not self.visible and self.scale < 0.1:
            return
            
        # 创建临时surface以支持透明度
        card_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # 计算缩放后的尺寸
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        
        # 绘制阴影
        shadow_color = (*COLORS['text'], int(30 * self.scale))
        pygame.draw.rect(card_surf, shadow_color, 
                        pygame.Rect(5, 5, scaled_width - 10, scaled_height - 10), 
                        border_radius=10)
        
        # 绘制卡片背景
        card_alpha = min(255, max(0, int(alpha * self.scale)))
        card_color = (*self.color, card_alpha) if len(self.color) == 3 else self.color
        pygame.draw.rect(card_surf, card_color,
                        pygame.Rect(0, 0, scaled_width - 10, scaled_height - 10),
                        border_radius=10)
        
        # 绘制图标
        if self.scale > 0.5:
            icon_alpha = min(255, max(0, int(alpha * self.scale)))
            self._draw_icon(card_surf, scaled_width // 2, scaled_height // 2 - 20, 
                          icon_alpha)
        
        # 绘制文字
        if self.scale > 0.7:
            font_size = int(24 * self.scale)
            font = get_chinese_font(font_size)
            text_alpha = min(255, max(0, int(alpha * self.scale)))
            text_surf = font.render(self.text, True, COLORS['white'])
            text_surf.set_alpha(text_alpha)
            text_rect = text_surf.get_rect(center=(scaled_width // 2, scaled_height - 30))
            card_surf.blit(text_surf, text_rect)
        
        # 缩放并绘制到屏幕
        if self.scale != 1.0:
            scaled_surf = pygame.transform.scale(card_surf, (scaled_width, scaled_height))
            screen.blit(scaled_surf, 
                       (self.rect.x + (self.rect.width - scaled_width) // 2,
                        self.rect.y + (self.rect.height - scaled_height) // 2))
        else:
            screen.blit(card_surf, self.rect)
            
    def _draw_icon(self, surface: pygame.Surface, x: int, y: int, alpha: int):
        """绘制图标"""
        icon_color = (*COLORS['white'], alpha)
        
        if self.icon == 'find_difference':
            # 放大镜图标
            pygame.draw.circle(surface, icon_color, (x, y), 25, 3)
            pygame.draw.line(surface, icon_color, 
                           (x + 17, y + 17),
                           (x + 30, y + 30), 3)
        elif self.icon == 'counting':
            # 数字图标
            font = pygame.font.Font(None, 48)
            text = "123"
            text_surf = font.render(text, True, icon_color)
            text_rect = text_surf.get_rect(center=(x, y))
            surface.blit(text_surf, text_rect)
        elif self.icon == 'math':
            # 加号图标
            size = 35
            pygame.draw.line(surface, icon_color,
                           (x - size//2, y),
                           (x + size//2, y), 4)
            pygame.draw.line(surface, icon_color,
                           (x, y - size//2),
                           (x, y + size//2), 4)
        elif self.icon == 'staff':
            # 五线谱图标
            for i in range(5):
                line_y = y - 10 + i * 5
                pygame.draw.line(surface, icon_color,
                               (x - 25, line_y),
                               (x + 25, line_y), 1)
            # 音符
            pygame.draw.ellipse(surface, icon_color, 
                              pygame.Rect(x - 5, y - 8, 10, 8))
        elif self.icon == 'rhythm':
            # 节奏图标
            pygame.draw.ellipse(surface, icon_color, 
                              pygame.Rect(x - 10, y - 6, 20, 12))
            pygame.draw.line(surface, icon_color,
                           (x + 10, y),
                           (x + 10, y - 25), 3)
        elif self.icon == 'interval':
            # 音程图标
            pygame.draw.ellipse(surface, icon_color, 
                              pygame.Rect(x - 20, y - 5, 12, 10))
            pygame.draw.ellipse(surface, icon_color, 
                              pygame.Rect(x + 8, y - 10, 12, 10))
        elif self.icon == 'drawing':
            # 画笔图标
            # 画笔主体
            pygame.draw.line(surface, icon_color,
                           (x - 15, y + 15),
                           (x + 10, y - 10), 4)
            # 画笔尖
            pygame.draw.polygon(surface, icon_color, [
                (x + 10, y - 10),
                (x + 15, y - 15),
                (x + 20, y - 10),
                (x + 15, y - 5)
            ])
            # 画线
            pygame.draw.arc(surface, icon_color,
                          pygame.Rect(x - 25, y, 30, 20),
                          0, 3.14, 3)


class ResponsiveGroup:
    """响应式游戏组"""
    def __init__(self, name: str, color: Tuple[int, int, int], games: List[Dict]):
        self.name = name
        self.color = color
        self.games = games
        self.expanded = False
        self.expand_progress = 0.0
        self.hover = False
        self.cards = []
        self.header_rect = pygame.Rect(0, 0, 800, 80)
        
        # 创建游戏卡片
        for game in self.games:
            card = ResponsiveGameCard(
                game['name'], game['type'], game['icon'], game['color']
            )
            self.cards.append(card)
            
    def update_layout(self, y: int, window_width: int):
        """更新布局（响应式）"""
        self.header_rect.y = y
        self.header_rect.x = max(50, (window_width - 900) // 2)
        self.header_rect.width = min(window_width - 100, 900)
        
        # 更新卡片布局
        card_width = 160
        card_height = 140
        spacing = 20
        
        # 根据窗口宽度计算每行显示的卡片数
        available_width = self.header_rect.width
        cards_per_row = max(1, available_width // (card_width + spacing))
        
        # 重新计算卡片位置
        for i, card in enumerate(self.cards):
            row = i // cards_per_row
            col = i % cards_per_row
            
            # 计算这一行的卡片总宽度，使其居中
            cards_in_row = min(len(self.cards) - row * cards_per_row, cards_per_row)
            row_width = cards_in_row * card_width + (cards_in_row - 1) * spacing
            start_x = self.header_rect.x + (self.header_rect.width - row_width) // 2
            
            x = start_x + col * (card_width + spacing)
            y_offset = 100 if self.expanded else 40
            card_y = y + y_offset + row * (card_height + spacing)
            
            card.update_position(x, int(card_y))
            
    def update(self, dt: float, mouse_pos: Tuple[int, int]):
        """更新组状态"""
        # 检查鼠标悬停
        self.hover = self.header_rect.collidepoint(mouse_pos)
        
        # 更新展开动画
        target_progress = 1.0 if self.expanded else 0.0
        self.expand_progress += (target_progress - self.expand_progress) * 0.15
        
        # 更新游戏卡片
        for card in self.cards:
            card.update(dt, mouse_pos, self.expand_progress > 0.1)
            
    def draw(self, screen: pygame.Surface, speaker_buttons: List):
        """绘制组"""
        # 绘制组背景
        bg_height = 80 + int(160 * self.expand_progress)
        bg_rect = pygame.Rect(self.header_rect.x, self.header_rect.y, 
                            self.header_rect.width, bg_height)
        
        # 背景颜色（根据悬停状态）
        bg_alpha = 40 if self.hover else 20
        bg_color = (*self.color, bg_alpha)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, bg_color, bg_surf.get_rect(), border_radius=15)
        screen.blit(bg_surf, bg_rect)
        
        # 绘制组头部
        header_color = self.color if self.hover else COLORS['text']
        
        # 组名
        title_font = get_chinese_font(36)
        title_surf = title_font.render(self.name, True, header_color)
        title_x = self.header_rect.x + 50
        title_y = self.header_rect.centery
        title_rect = title_surf.get_rect(midleft=(title_x, title_y))
        screen.blit(title_surf, title_rect)
        
        # 游戏数量标签
        count_font = get_chinese_font(24)
        count_text = f"{len(self.games)} 个游戏"
        count_surf = count_font.render(count_text, True, COLORS['text'])
        count_rect = count_surf.get_rect(midleft=(title_x + title_surf.get_width() + 20, title_y))
        screen.blit(count_surf, count_rect)
        
        # 展开/折叠箭头
        arrow_x = self.header_rect.right - 50
        arrow_y = self.header_rect.centery
        arrow_angle = -90 + 90 * self.expand_progress  # 从右指向下
        self._draw_arrow(screen, arrow_x, arrow_y, arrow_angle, header_color)
        
        # 添加喇叭按钮
        speaker_btn = SpeakerButton(title_x + title_surf.get_width() + count_surf.get_width() + 50, 
                                  title_y, 20)
        speaker_btn.draw(screen)
        speaker_buttons.append((speaker_btn, f"这是{self.name}类游戏，包含{len(self.games)}个游戏"))
        
        # 绘制游戏卡片（带透明度动画）
        card_alpha = int(255 * self.expand_progress)
        for card in self.cards:
            card.draw(screen, card_alpha)
            
    def _draw_arrow(self, screen: pygame.Surface, x: int, y: int, angle: float, color: Tuple[int, int, int]):
        """绘制箭头"""
        size = 15
        angle_rad = math.radians(angle)
        
        # 计算箭头三个点
        tip_x = x + size * math.cos(angle_rad)
        tip_y = y + size * math.sin(angle_rad)
        
        left_angle = angle_rad + math.radians(150)
        left_x = tip_x + size * 0.7 * math.cos(left_angle)
        left_y = tip_y + size * 0.7 * math.sin(left_angle)
        
        right_angle = angle_rad - math.radians(150)
        right_x = tip_x + size * 0.7 * math.cos(right_angle)
        right_y = tip_y + size * 0.7 * math.sin(right_angle)
        
        # 绘制箭头
        pygame.draw.polygon(screen, color, [
            (int(tip_x), int(tip_y)),
            (int(left_x), int(left_y)),
            (int(right_x), int(right_y))
        ])
        
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """处理点击事件"""
        # 检查组头部点击（展开/折叠）
        if self.header_rect.collidepoint(pos):
            self.expanded = not self.expanded
            speak(f"{self.name}{'已展开' if self.expanded else '已折叠'}")
            return None
            
        # 检查游戏卡片点击
        if self.expanded:
            for card in self.cards:
                if card.rect.collidepoint(pos) and card.visible:
                    return card.game_type
                    
        return None
        
    def get_height(self) -> int:
        """获取组的高度（用于计算下一个组的位置）"""
        if self.expand_progress < 0.01:
            return 90
        # 计算需要的行数
        cards_per_row = max(1, self.header_rect.width // 180)
        rows = (len(self.cards) + cards_per_row - 1) // cards_per_row
        return 90 + int((rows * 160) * self.expand_progress)


class ResponsiveMainMenu:
    """响应式主菜单（无滚动条）"""
    def __init__(self, game_manager: GameManager):
        self.game_manager = game_manager
        self.animation_time = 0
        self.window_width = 1024
        self.window_height = 768
        
        # 定义游戏分组
        self.groups = [
            ResponsiveGroup("数理逻辑", COLORS['primary'], [
                {'name': '数一数', 'type': 'counting', 'icon': 'counting', 'color': COLORS['primary']},
                {'name': '算一算', 'type': 'simple_math', 'icon': 'math', 'color': COLORS['secondary']},
            ]),
            ResponsiveGroup("乐理", COLORS['accent'], [
                {'name': '五线谱', 'type': 'staff_reading', 'icon': 'staff', 'color': COLORS['accent']},
                {'name': '节奏', 'type': 'rhythm', 'icon': 'rhythm', 'color': COLORS['success']},
                {'name': '音程', 'type': 'interval', 'icon': 'interval', 'color': COLORS['warning']},
            ]),
            ResponsiveGroup("视觉加工", COLORS['danger'], [
                {'name': '找不同', 'type': 'find_difference', 'icon': 'find_difference', 'color': COLORS['danger']},
                {'name': '学画画', 'type': 'drawing', 'icon': 'drawing', 'color': COLORS['warning']},
            ]),
        ]
        
        # 默认展开第一个组
        self.groups[0].expanded = True
        
        # 退出按钮（固定位置）
        self.quit_button = pygame.Rect(0, 0, 100, 40)
        self.quit_hover = False
        
        # 设置按钮（固定位置）
        self.settings_button = pygame.Rect(0, 0, 100, 40)
        self.settings_hover = False
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 播放欢迎语音
        name = self.game_manager.progress.get_player_name()
        speak(f"欢迎{name}小朋友！点击类别查看游戏，再点击游戏开始吧！")
        
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """处理点击事件"""
        # 检查喇叭按钮
        for button, text in self.speaker_buttons:
            if button.check_click(pos):
                speak(text)
                return None
        
        # 检查退出按钮
        if self.quit_button.collidepoint(pos):
            return 'quit'
        
        # 检查设置按钮
        if self.settings_button.collidepoint(pos):
            speak("进入设置界面")
            return 'settings'
            
        # 检查游戏组
        for group in self.groups:
            game_type = group.handle_click(pos)
            if game_type:
                # 播放相应的语音提示
                voice_map = {
                    'find_difference': "让我们一起来找不同吧！",
                    'counting': "让我们一起来数数吧！",
                    'simple_math': "让我们一起来做数学题吧！",
                    'staff_reading': "让我们一起来认识五线谱吧！",
                    'rhythm': "让我们一起来学习节奏吧！",
                    'interval': "让我们一起来学习音程吧！",
                    'drawing': "让我们一起来学画画吧！"
                }
                speak(voice_map.get(game_type, "开始游戏！"))
                return game_type
                
        return None
        
    def update(self, dt: float, mouse_pos: Tuple[int, int], window_size: Tuple[int, int]):
        """更新菜单状态"""
        self.animation_time += dt
        self.window_width, self.window_height = window_size
        
        # 更新按钮位置
        self.quit_button.x = self.window_width - 120
        self.quit_button.y = self.window_height - 60
        self.settings_button.x = 20
        self.settings_button.y = self.window_height - 60
        
        # 更新按钮悬停状态
        self.quit_hover = self.quit_button.collidepoint(mouse_pos)
        self.settings_hover = self.settings_button.collidepoint(mouse_pos)
        
        # 更新组布局
        current_y = 180
        for group in self.groups:
            group.update_layout(current_y, self.window_width)
            current_y += group.get_height() + 20
            group.update(dt, mouse_pos)
            
        # 更新喇叭按钮
        for button, _ in self.speaker_buttons:
            button.update(mouse_pos)
            
    def draw(self, screen: pygame.Surface):
        """绘制菜单"""
        # 绘制背景
        screen.fill(COLORS['background'])
        
        # 清空喇叭按钮列表
        self.speaker_buttons.clear()
        
        # 绘制装饰性背景
        self._draw_background_decorations(screen)
        
        # 绘制标题
        title_font = get_chinese_font(64)
        title = "聪明小宝贝"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(self.window_width//2, 80))
        screen.blit(title_surf, title_rect)
        
        # 标题喇叭按钮
        speaker_btn = SpeakerButton(self.window_width//2 + title_surf.get_width()//2 + 60, 
                                  80, 30)
        speaker_btn.draw(screen)
        name = self.game_manager.progress.get_player_name()
        self.speaker_buttons.append((speaker_btn, f"欢迎{name}小朋友！点击类别查看游戏，再点击游戏开始吧！"))
        
        # 副标题
        subtitle_font = get_chinese_font(28)
        subtitle = "点击展开游戏类别"
        subtitle_surf = subtitle_font.render(subtitle, True, COLORS['text'])
        subtitle_rect = subtitle_surf.get_rect(center=(self.window_width//2, 130))
        screen.blit(subtitle_surf, subtitle_rect)
        
        # 绘制游戏组
        for group in self.groups:
            group.draw(screen, self.speaker_buttons)
            
        # 绘制固定元素
        self._draw_player_info(screen)
        self._draw_bottom_buttons(screen)
        
        # 绘制所有喇叭按钮
        for button, _ in self.speaker_buttons:
            button.draw(screen)
            
    def _draw_background_decorations(self, screen: pygame.Surface):
        """绘制背景装饰"""
        # 绘制渐变圆圈
        circles = [
            {'x': 0.15, 'y': 0.33, 'radius': 100, 'color': (255, 183, 77, 30)},
            {'x': 0.85, 'y': 0.46, 'radius': 120, 'color': (121, 134, 203, 30)},
            {'x': 0.2, 'y': 0.72, 'radius': 80, 'color': (129, 199, 132, 30)},
            {'x': 0.8, 'y': 0.26, 'radius': 90, 'color': (239, 83, 80, 30)},
        ]
        
        for circle in circles:
            # 使用相对位置
            x = int(self.window_width * circle['x'])
            y = int(self.window_height * circle['y'])
            
            # 绘制多层渐变圆圈
            for i in range(3):
                radius = circle['radius'] - i * 20
                alpha = 30 - i * 10
                color = circle['color'][:3] + (alpha,)
                
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (radius, radius), radius)
                
                # 添加动画效果
                offset = math.sin(self.animation_time + i) * 5
                screen.blit(surf, (x - radius + offset, y - radius))
                
    def _draw_player_info(self, screen: pygame.Surface):
        """绘制玩家信息"""
        info_font = get_chinese_font(28)
        
        # 玩家名字
        name = self.game_manager.progress.get_player_name()
        name_text = f"小朋友：{name}"
        name_surf = info_font.render(name_text, True, COLORS['text'])
        screen.blit(name_surf, (20, 20))
        
        # 月龄
        birth_date = self.game_manager.progress.data.get('birth_date', None)
        if birth_date:
            try:
                import datetime
                year, month, day = birth_date.split('-')
                birth = datetime.date(int(year), int(month), int(day))
                today = datetime.date.today()
                months = (today.year - birth.year) * 12 + today.month - birth.month
                
                age_text = f"月龄：{months}个月"
                age_surf = info_font.render(age_text, True, COLORS['secondary'])
                screen.blit(age_surf, (20, 55))
            except:
                pass
        
        # 金币和星星
        coins = self.game_manager.progress.data['total_coins']
        stars = self.game_manager.progress.data['total_stars']
        
        # 金币
        coin_x = self.window_width - 200
        pygame.draw.circle(screen, COLORS['primary'], (coin_x, 35), 12)
        pygame.draw.circle(screen, (255, 215, 0), (coin_x, 35), 10)
        coins_surf = info_font.render(str(coins), True, COLORS['text'])
        screen.blit(coins_surf, (coin_x + 20, 23))
        
        # 星星
        star_x = self.window_width - 100
        self._draw_star(screen, star_x, 35, 12, COLORS['accent'])
        stars_surf = info_font.render(str(stars), True, COLORS['text'])
        screen.blit(stars_surf, (star_x + 20, 23))
    
    def _draw_star(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int]):
        """绘制星星"""
        points = []
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            radius = size if i % 2 == 0 else size * 0.5
            point_x = x + radius * math.cos(angle)
            point_y = y + radius * math.sin(angle)
            points.append((point_x, point_y))
        pygame.draw.polygon(screen, color, points)
        
    def _draw_bottom_buttons(self, screen: pygame.Surface):
        """绘制底部按钮"""
        # 退出按钮
        button_color = COLORS['danger'] if self.quit_hover else COLORS['secondary']
        pygame.draw.rect(screen, button_color, self.quit_button, border_radius=5)
        quit_font = get_chinese_font(24)
        quit_text = quit_font.render("退出游戏", True, COLORS['white'])
        quit_rect = quit_text.get_rect(center=self.quit_button.center)
        screen.blit(quit_text, quit_rect)
        
        # 设置按钮
        settings_color = COLORS['primary'] if self.settings_hover else COLORS['secondary']
        pygame.draw.rect(screen, settings_color, self.settings_button, border_radius=5)
        settings_font = get_chinese_font(24)
        settings_text = settings_font.render("设置", True, COLORS['white'])
        settings_rect = settings_text.get_rect(center=self.settings_button.center)
        screen.blit(settings_text, settings_rect)
        
        # 提示文字
        hint_font = get_chinese_font(20)
        hint_text = hint_font.render("按 ESC 或 Ctrl+Q 也可退出", True, COLORS['text'])
        hint_rect = hint_text.get_rect(center=(self.window_width//2, self.window_height - 20))
        screen.blit(hint_text, hint_rect)