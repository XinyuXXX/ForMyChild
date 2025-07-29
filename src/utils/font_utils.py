import pygame
from ..config import FONTS

def get_chinese_font(size: int):
    """获取支持中文的字体"""
    try:
        font_path = FONTS['default']
        if font_path:
            return pygame.font.Font(font_path, size)
    except:
        pass
    
    # 如果加载失败，尝试使用pygame的中文字体
    try:
        return pygame.font.SysFont('microsoftyaheimicrosoftyaheiui', size)
    except:
        pass
    
    # 最后的备选方案
    return pygame.font.Font(None, size)