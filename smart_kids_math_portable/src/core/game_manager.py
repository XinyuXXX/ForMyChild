import json
import os
from datetime import datetime
import datetime as dt
from typing import Dict, List, Optional
from ..config import SAVE_FILE, ADAPTIVE_SETTINGS


class GameProgress:
    """管理游戏进度和用户数据"""
    
    def __init__(self):
        self.data = self._load_progress()
        self._migrate_data()
        
    def _load_progress(self) -> Dict:
        """加载保存的进度数据"""
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 默认数据结构
        return {
            'player_name': '小朋友',
            'created_at': datetime.now().isoformat(),
            'total_coins': 0,
            'total_stars': 0,
            'games': {
                'find_difference': {
                    'level': 1,
                    'games_played': 0,
                    'games_won': 0,
                    'current_difficulty': 1,
                    'history': []
                },
                'counting': {
                    'level': 1,
                    'games_played': 0,
                    'games_won': 0,
                    'current_difficulty': 1,
                    'history': []
                },
                'simple_math': {
                    'level': 1,
                    'games_played': 0,
                    'games_won': 0,
                    'current_difficulty': 1,
                    'history': []
                },
                'music_theory': {
                    'level': 1,
                    'games_played': 0,
                    'games_won': 0,
                    'current_difficulty': 1,
                    'history': []
                },
                'staff_reading': {
                    'level': 1,
                    'games_played': 0,
                    'games_won': 0,
                    'current_difficulty': 1,
                    'history': []
                },
                'rhythm': {
                    'level': 1,
                    'games_played': 0,
                    'games_won': 0,
                    'current_difficulty': 1,
                    'history': []
                },
                'interval': {
                    'level': 1,
                    'games_played': 0,
                    'games_won': 0,
                    'current_difficulty': 1,
                    'history': []
                }
            },
            'achievements': [],
            'daily_streak': 0,
            'last_played': datetime.now().isoformat()
        }
    
    def save_progress(self):
        """保存进度数据"""
        self.data['last_played'] = datetime.now().isoformat()
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def _migrate_data(self):
        """迁移旧数据到新格式"""
        games = self.data.get('games', {})
        
        # 如果新游戏类型已存在，说明已经迁移过
        if 'staff_reading' in games and 'rhythm' in games and 'interval' in games:
            return
            
        # 如果有 music_theory 数据，复制到新的游戏类型
        if 'music_theory' in games:
            music_data = games['music_theory']
            
            # 创建新的游戏数据
            for game_type in ['staff_reading', 'rhythm', 'interval']:
                if game_type not in games:
                    games[game_type] = {
                        'level': music_data.get('level', 1),
                        'games_played': music_data.get('games_played', 0) // 3,
                        'games_won': music_data.get('games_won', 0) // 3,
                        'current_difficulty': music_data.get('current_difficulty', 1),
                        'history': []
                    }
        else:
            # 创建默认数据
            for game_type in ['staff_reading', 'rhythm', 'interval']:
                if game_type not in games:
                    games[game_type] = {
                        'level': 1,
                        'games_played': 0,
                        'games_won': 0,
                        'current_difficulty': 1,
                        'history': []
                    }
        
        # 保存迁移后的数据
        self.save_progress()
    
    def update_game_result(self, game_type: str, won: bool, score: int, 
                          time_taken: float, details: Optional[Dict] = None):
        """更新游戏结果"""
        game_data = self.data['games'][game_type]
        game_data['games_played'] += 1
        if won:
            game_data['games_won'] += 1
        
        # 记录历史
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'won': won,
            'score': score,
            'time_taken': time_taken,
            'difficulty': game_data['current_difficulty']
        }
        if details:
            history_entry['details'] = details
        
        game_data['history'].append(history_entry)
        
        # 只保留最近50条记录
        if len(game_data['history']) > 50:
            game_data['history'] = game_data['history'][-50:]
        
        # 更新难度
        self._adjust_difficulty(game_type)
        
        # 保存
        self.save_progress()
    
    def _adjust_difficulty(self, game_type: str):
        """根据表现自动调整难度"""
        game_data = self.data['games'][game_type]
        history = game_data['history']
        
        # 需要足够的游戏记录才调整难度
        if len(history) < ADAPTIVE_SETTINGS['min_games_before_adjust']:
            return
        
        # 计算最近游戏的成功率
        recent_games = history[-ADAPTIVE_SETTINGS['min_games_before_adjust']:]
        success_rate = sum(1 for g in recent_games if g['won']) / len(recent_games)
        
        current_difficulty = game_data['current_difficulty']
        
        if success_rate >= ADAPTIVE_SETTINGS['difficulty_increase_threshold']:
            # 提高难度
            game_data['current_difficulty'] = min(current_difficulty + 1, 10)
            print(f"难度提升到 {game_data['current_difficulty']}")
        elif success_rate <= ADAPTIVE_SETTINGS['difficulty_decrease_threshold']:
            # 降低难度
            game_data['current_difficulty'] = max(current_difficulty - 1, 1)
            print(f"难度降低到 {game_data['current_difficulty']}")
    
    def get_game_stats(self, game_type: str) -> Dict:
        """获取游戏统计信息"""
        game_data = self.data['games'][game_type]
        total = game_data['games_played']
        won = game_data['games_won']
        
        return {
            'level': game_data['level'],
            'games_played': total,
            'games_won': won,
            'win_rate': won / total if total > 0 else 0,
            'current_difficulty': game_data['current_difficulty'],
            'recent_performance': self._get_recent_performance(game_type)
        }
    
    def _get_recent_performance(self, game_type: str, n: int = 10) -> List[bool]:
        """获取最近n场游戏的胜负情况"""
        history = self.data['games'][game_type]['history']
        return [g['won'] for g in history[-n:]]
    
    def add_coins(self, amount: int):
        """增加金币"""
        self.data['total_coins'] += amount
        self.save_progress()
    
    def add_stars(self, amount: int):
        """增加星星"""
        self.data['total_stars'] += amount
        self.save_progress()
    
    def unlock_achievement(self, achievement_id: str):
        """解锁成就"""
        if achievement_id not in self.data['achievements']:
            self.data['achievements'].append(achievement_id)
            self.save_progress()
    
    def get_player_name(self) -> str:
        """获取玩家名字"""
        return self.data['player_name']
    
    def set_player_name(self, name: str):
        """设置玩家名字"""
        self.data['player_name'] = name
        self.save_progress()


class GameManager:
    """游戏管理器"""
    
    def __init__(self):
        self.progress = GameProgress()
        self.current_game = None
        self.sound_enabled = True
        self.music_enabled = True
    
    def start_game(self, game_type: str):
        """开始新游戏"""
        self.current_game = {
            'type': game_type,
            'start_time': datetime.now(),
            'score': 0,
            'completed': False
        }
    
    def end_game(self, won: bool, score: int, details: Optional[Dict] = None):
        """结束游戏"""
        if not self.current_game:
            return
        
        time_taken = (datetime.now() - self.current_game['start_time']).total_seconds()
        
        self.progress.update_game_result(
            self.current_game['type'],
            won,
            score,
            time_taken,
            details
        )
        
        # 计算奖励
        if won:
            base_coins = 10
            difficulty = self.progress.data['games'][self.current_game['type']]['current_difficulty']
            coins = int(base_coins * (1 + difficulty * 0.1))
            self.progress.add_coins(coins)
            
            # 星星奖励
            if score >= 90:
                self.progress.add_stars(3)
            elif score >= 70:
                self.progress.add_stars(2)
            else:
                self.progress.add_stars(1)
        
        self.current_game = None
    
    def get_difficulty(self, game_type: str) -> int:
        """获取当前游戏难度（1-10级）"""
        # 首先检查是否有自定义难度设置
        difficulty_settings = self.progress.data.get('difficulty_settings', {})
        
        if game_type in difficulty_settings:
            # 使用自定义难度（1-10级）
            return min(max(difficulty_settings[game_type], 1), 10)
        
        # 如果没有自定义设置，根据月龄计算基础难度
        birth_date = self.progress.data.get('birth_date', None)
        base_difficulty = 5  # 默认中等难度
        
        if birth_date:
            try:
                year, month, day = birth_date.split('-')
                birth = dt.date(int(year), int(month), int(day))
                today = dt.date.today()
                months = (today.year - birth.year) * 12 + today.month - birth.month
                
                # 根据月龄设置基础难度（1-10级）
                if months < 42:      # 3.5岁以下
                    base_difficulty = 1
                elif months < 48:    # 3.5-4岁
                    base_difficulty = 2
                elif months < 54:    # 4-4.5岁
                    base_difficulty = 3
                elif months < 60:    # 4.5-5岁
                    base_difficulty = 4
                elif months < 66:    # 5-5.5岁
                    base_difficulty = 5
                elif months < 72:    # 5.5-6岁
                    base_difficulty = 6
                elif months < 84:    # 6-7岁
                    base_difficulty = 7
                elif months < 96:    # 7-8岁
                    base_difficulty = 8
                elif months < 108:   # 8-9岁
                    base_difficulty = 9
                else:                # 9岁以上
                    base_difficulty = 10
            except:
                pass
        
        # 根据游戏记录微调难度
        game_data = self.progress.data['games'].get(game_type, {})
        
        # 根据胜率调整
        played = game_data.get('games_played', 0)
        if played > 3:
            won = game_data.get('games_won', 0)
            win_rate = won / played
            if win_rate > 0.9:  # 胜率超过90%，提高2级
                base_difficulty = min(base_difficulty + 2, 10)
            elif win_rate > 0.8:  # 胜率超过80%，提高1级
                base_difficulty = min(base_difficulty + 1, 10)
            elif win_rate < 0.2:  # 胜率低于20%，降低2级
                base_difficulty = max(base_difficulty - 2, 1)
            elif win_rate < 0.3:  # 胜率低于30%，降低1级
                base_difficulty = max(base_difficulty - 1, 1)
        
        return min(max(base_difficulty, 1), 10)  # 难度范围1-10
    
    def toggle_sound(self):
        """切换音效"""
        self.sound_enabled = not self.sound_enabled
    
    def toggle_music(self):
        """切换背景音乐"""
        self.music_enabled = not self.music_enabled