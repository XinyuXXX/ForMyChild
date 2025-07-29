#!/usr/bin/env python3
import pygame
import sys
from src.config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE
from src.core.game_manager import GameManager
from src.ui.responsive_main_menu import ResponsiveMainMenu
from src.ui.name_input import NameInputScreen
from src.ui.enhanced_settings_screen import EnhancedSettingsScreen
from src.games.find_difference import FindDifferenceGame
from src.games.counting_game import CountingGame
from src.games.simple_math import SimpleMathGame
from src.games.music_theory import MusicTheoryGame
from src.games.staff_reading import StaffReadingGame
from src.games.rhythm_standalone import RhythmGame
from src.games.interval_game import IntervalGame
from src.games.drawing_ai import DrawingAIGame
from src.utils.audio_utils import is_speaking


class SmartKidsMath:
    """主程序类"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        
        # 游戏管理器
        self.game_manager = GameManager()
        
        # 界面
        self.name_input_screen = None
        self.main_menu = None
        self.settings_screen = None
        
        # 当前状态和游戏
        self.current_game = None
        self.current_game_type = None
        
        # 检查是否已有玩家名字
        player_name = self.game_manager.progress.get_player_name()
        if player_name and player_name != "小宝贝":
            # 已有名字，直接进入主菜单
            self.state = 'menu'
            self.main_menu = ResponsiveMainMenu(self.game_manager)
        else:
            # 需要输入名字
            self.state = 'name_input'
            self.name_input_screen = NameInputScreen()
        
    def run(self):
        """运行主循环"""
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    # 处理窗口大小调整
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                elif self.state == 'name_input' and self.name_input_screen:
                    # 名字输入界面处理自己的事件
                    name = self.name_input_screen.handle_event(event)
                    if name:
                        # 保存名字并进入主菜单
                        self.game_manager.progress.data['player_name'] = name
                        self.game_manager.progress.save_progress()
                        self.state = 'menu'
                        self.main_menu = ResponsiveMainMenu(self.game_manager)
                elif self.state == 'settings' and self.settings_screen:
                    # 设置界面处理自己的事件
                    result = self.settings_screen.handle_event(event)
                    if result == 'save':
                        # 保存设置并返回主菜单
                        self.state = 'menu'
                        self.main_menu = ResponsiveMainMenu(self.game_manager)  # 重新创建主菜单以更新信息
                        self.settings_screen = None
                    elif result == 'cancel':
                        # 取消设置
                        self.state = 'menu'
                        self.settings_screen = None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == 'game':
                            self.return_to_menu()
                        elif self.state == 'menu':
                            running = False
                    elif event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        # Ctrl+Q 退出
                        running = False
                elif event.type == pygame.USEREVENT + 1:
                    # 用于游戏内的定时事件
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                elif event.type == pygame.USEREVENT + 2:
                    # 找不同游戏的下一轮
                    pygame.time.set_timer(pygame.USEREVENT + 2, 0)
                    if self.state == 'game' and self.current_game_type == 'find_difference':
                        if hasattr(self.current_game, '_start_new_round'):
                            self.current_game._start_new_round()
                elif event.type == pygame.USEREVENT + 3:
                    # 音乐游戏的下一题
                    pygame.time.set_timer(pygame.USEREVENT + 3, 0)
                    if self.state == 'game' and self.current_game_type == 'music_theory':
                        if hasattr(self.current_game, '_start_new_round'):
                            self.current_game._start_new_round()
            
            # 更新
            self.update(dt)
            
            # 绘制
            self.draw()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
    
    def handle_click(self, pos):
        """处理鼠标点击"""
        if self.state == 'menu':
            result = self.main_menu.handle_click(pos)
            if result == 'quit':
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif result == 'settings':
                self.state = 'settings'
                self.settings_screen = EnhancedSettingsScreen(self.game_manager)
            elif result:
                self.start_game(result)
        elif self.state == 'game' and self.current_game:
            if hasattr(self.current_game, 'handle_click'):
                self.current_game.handle_click(pos)
    
    def update(self, dt):
        """更新游戏状态"""
        if self.state == 'name_input' and self.name_input_screen:
            self.name_input_screen.update(dt)
        elif self.state == 'menu' and self.main_menu:
            mouse_pos = pygame.mouse.get_pos()
            window_size = self.screen.get_size()
            self.main_menu.update(dt, mouse_pos, window_size)
        elif self.state == 'settings' and self.settings_screen:
            self.settings_screen.update(dt)
        elif self.state == 'game' and self.current_game:
            # 更新游戏窗口大小（如果游戏支持）
            if hasattr(self.current_game, 'update_window_size'):
                window_size = self.screen.get_size()
                self.current_game.update_window_size(window_size[0], window_size[1])
            self.current_game.update(dt)
            
            # 检查游戏是否结束
            if hasattr(self.current_game, 'game_complete') and self.current_game.game_complete:
                # 等待一段时间后返回菜单
                if not hasattr(self, 'end_game_timer'):
                    self.end_game_timer = 0
                    # 保存游戏结果
                    result = self.current_game.get_result()
                    won = result.get('completed', False) or result.get('score', 0) > 0
                    self.game_manager.end_game(won, result.get('score', 0), result)
                
                self.end_game_timer += dt
                # 等待语音播放完毕后再等待2秒，或者超时5秒
                if (not is_speaking() and self.end_game_timer > 2.0) or self.end_game_timer > 5.0:
                    del self.end_game_timer
                    self.return_to_menu()
    
    def draw(self):
        """绘制画面"""
        if self.state == 'name_input' and self.name_input_screen:
            self.name_input_screen.draw(self.screen)
        elif self.state == 'menu' and self.main_menu:
            self.main_menu.draw(self.screen)
        elif self.state == 'settings' and self.settings_screen:
            self.settings_screen.draw(self.screen)
        elif self.state == 'game' and self.current_game:
            self.current_game.draw(self.screen)
    
    def start_game(self, game_type):
        """开始游戏"""
        self.state = 'game'
        self.current_game_type = game_type
        
        # 获取难度
        difficulty = self.game_manager.get_difficulty(game_type)
        
        # 创建游戏实例
        if game_type == 'find_difference':
            self.current_game = FindDifferenceGame(difficulty)
        elif game_type == 'counting':
            self.current_game = CountingGame(difficulty)
        elif game_type == 'simple_math':
            self.current_game = SimpleMathGame(difficulty)
        elif game_type == 'music_theory':
            self.current_game = MusicTheoryGame(difficulty)
        elif game_type == 'staff_reading':
            self.current_game = StaffReadingGame(difficulty)
        elif game_type == 'rhythm':
            self.current_game = RhythmGame(difficulty)
        elif game_type == 'interval':
            self.current_game = IntervalGame(difficulty)
        elif game_type == 'drawing':
            # 使用AI增强版画画游戏
            self.current_game = DrawingAIGame(difficulty)
        
        # 记录游戏开始
        self.game_manager.start_game(game_type)
    
    def return_to_menu(self):
        """返回主菜单"""
        self.state = 'menu'
        self.current_game = None
        self.current_game_type = None


def main():
    """程序入口"""
    app = SmartKidsMath()
    app.run()


if __name__ == '__main__':
    main()