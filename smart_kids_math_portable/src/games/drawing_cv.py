#!/usr/bin/env python3
"""
基于OpenCV的画画教学游戏
使用真实图片转换为简笔画，并提供分步教学
"""
import pygame
import cv2
import numpy as np
import os
from typing import List, Dict, Tuple, Optional
from PIL import Image
import io
from ..config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, IMAGES_PATH
from ..utils.font_utils import get_chinese_font
from ..utils.audio_utils import speak
from ..utils.ui_utils import SpeakerButton
from ..utils.emoji_utils import draw_happy_face, draw_star_eyes_face
from .base_game import BaseGame


class DrawingStep:
    """绘画步骤"""
    def __init__(self, name: str, contour: np.ndarray, description: str):
        self.name = name
        self.contour = contour
        self.description = description
        self.progress = 0.0


class DrawingCVGame(BaseGame):
    """基于OpenCV的画画游戏"""
    
    def __init__(self, difficulty: int = 1):
        super().__init__(difficulty)
        self.game_type = "drawing_cv"
        
        # 图片管理
        self.original_image = None
        self.sketch_image = None
        self.current_sketch = None
        self.steps: List[DrawingStep] = []
        self.current_step = 0
        
        # 游戏状态
        self.game_phase = 'select'  # select, original, sketch, steps, complete
        self.phase_timer = 0.0
        
        # 动画控制
        self.animation_progress = 0.0
        self.is_animating = False
        self.animation_speed = 0.3  # 每秒完成30%
        
        # UI元素
        self.image_buttons = []
        self.control_buttons = {}
        
        # 画布
        self.canvas = None
        self.canvas_rect = None
        
        # 反馈
        self.show_complete_feedback = False
        
        # 喇叭按钮
        self.speaker_buttons = []
        
        # 可用的图片
        self.available_images = []
        self.selected_image = None
        
        # 初始化
        self._load_available_images()
        
    def _load_available_images(self):
        """加载可用的图片列表"""
        image_dir = os.path.join(IMAGES_PATH, "drawing_tutorials", "real")
        
        # 预定义的图片列表
        self.available_images = [
            {"name": "太阳", "file": "sun.jpg", "difficulty": 1},
            {"name": "房子", "file": "house.jpg", "difficulty": 2},
            {"name": "树", "file": "tree.jpg", "difficulty": 2},
            {"name": "花朵", "file": "flower.jpg", "difficulty": 3},
            {"name": "汽车", "file": "car.jpg", "difficulty": 3},
            {"name": "小猫", "file": "cat.jpg", "difficulty": 4}
        ]
        
        # 检查哪些图片实际存在
        existing_images = []
        for img_info in self.available_images:
            path = os.path.join(image_dir, img_info["file"])
            if os.path.exists(path):
                existing_images.append(img_info)
        
        self.available_images = existing_images
        
        # 如果没有图片，创建示例
        if not self.available_images:
            self._create_sample_images()
            
    def _create_sample_images(self):
        """创建示例图片"""
        image_dir = os.path.join(IMAGES_PATH, "drawing_tutorials", "real")
        os.makedirs(image_dir, exist_ok=True)
        
        # 创建简单的示例图片
        sample_images = [
            ("circle.jpg", "圆形", self._create_circle_image),
            ("square.jpg", "正方形", self._create_square_image),
            ("triangle.jpg", "三角形", self._create_triangle_image)
        ]
        
        for filename, name, create_func in sample_images:
            path = os.path.join(image_dir, filename)
            if not os.path.exists(path):
                img = create_func()
                cv2.imwrite(path, img)
                self.available_images.append({
                    "name": name,
                    "file": filename,
                    "difficulty": 1
                })
                
    def _create_circle_image(self) -> np.ndarray:
        """创建圆形示例图片"""
        img = np.ones((400, 400, 3), dtype=np.uint8) * 255
        cv2.circle(img, (200, 200), 150, (255, 200, 0), -1)
        cv2.circle(img, (200, 200), 150, (0, 0, 0), 5)
        return img
        
    def _create_square_image(self) -> np.ndarray:
        """创建正方形示例图片"""
        img = np.ones((400, 400, 3), dtype=np.uint8) * 255
        cv2.rectangle(img, (50, 50), (350, 350), (0, 150, 255), -1)
        cv2.rectangle(img, (50, 50), (350, 350), (0, 0, 0), 5)
        return img
        
    def _create_triangle_image(self) -> np.ndarray:
        """创建三角形示例图片"""
        img = np.ones((400, 400, 3), dtype=np.uint8) * 255
        pts = np.array([[200, 50], [50, 350], [350, 350]], np.int32)
        cv2.fillPoly(img, [pts], (100, 255, 100))
        cv2.polylines(img, [pts], True, (0, 0, 0), 5)
        return img
        
    def _convert_to_sketch(self, image: np.ndarray) -> np.ndarray:
        """将图片转换为简笔画"""
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 应用双边滤波，保留边缘的同时减少噪声
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # 自适应阈值处理，更好地提取轮廓
        adaptive_thresh = cv2.adaptiveThreshold(filtered, 255, 
                                              cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
        
        # 使用形态学操作清理图像
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # 边缘检测
        edges = cv2.Canny(cleaned, 50, 150)
        
        # 膨胀边缘使线条更粗
        kernel_dilate = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel_dilate, iterations=1)
        
        # 反转颜色（白底黑线）
        sketch = cv2.bitwise_not(edges)
        
        # 转换为3通道
        sketch_3channel = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
        
        return sketch_3channel
        
    def _extract_contours(self, sketch: np.ndarray) -> List[np.ndarray]:
        """提取轮廓"""
        # 转换为灰度图
        gray = cv2.cvtColor(sketch, cv2.COLOR_BGR2GRAY)
        
        # 二值化 - 调整阈值
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        # 形态学操作连接断开的线条
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓 - 使用RETR_TREE获取所有轮廓
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # 调试：打印找到的轮廓数量
        print(f"找到 {len(contours)} 个原始轮廓")
        
        # 按面积排序，去除太小的轮廓
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        filtered_contours = []
        
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            # 降低面积阈值，保留更多轮廓
            if area > 50 and perimeter > 50:  # 降低阈值
                # 简化轮廓
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                filtered_contours.append(approx)
                print(f"轮廓 {i}: 面积={area:.0f}, 周长={perimeter:.0f}, 点数={len(approx)}")
                
                # 最多保留10个轮廓
                if len(filtered_contours) >= 10:
                    break
                    
        print(f"过滤后保留 {len(filtered_contours)} 个轮廓")
        return filtered_contours
        
    def _extract_contours_from_original(self, image: np.ndarray) -> List[np.ndarray]:
        """从原始图像提取轮廓（用于彩色图像）"""
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用CLAHE增强对比度
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # 使用Otsu's二值化
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"从原始图像找到 {len(contours)} 个轮廓")
        
        # 过滤和排序轮廓
        filtered_contours = []
        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            area = cv2.contourArea(contour)
            if area > 500:  # 更大的阈值
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                filtered_contours.append(approx)
                if len(filtered_contours) >= 5:
                    break
                    
        return filtered_contours
        
    def _create_default_steps(self, name: str):
        """创建默认的绘画步骤"""
        # 根据不同的图片类型创建预定义步骤
        h, w = self.sketch_image.shape[:2] if self.sketch_image is not None else (400, 400)
        cx, cy = w // 2, h // 2
        
        if "太阳" in name or "sun" in name.lower():
            # 太阳的步骤
            # 圆形
            circle_pts = []
            for angle in range(0, 360, 10):
                x = cx + int(80 * np.cos(np.radians(angle)))
                y = cy + int(80 * np.sin(np.radians(angle)))
                circle_pts.append([[x, y]])
            circle_contour = np.array(circle_pts, dtype=np.int32)
            
            # 光芒
            rays_pts = []
            for angle in range(0, 360, 30):
                x1 = cx + int(100 * np.cos(np.radians(angle)))
                y1 = cy + int(100 * np.sin(np.radians(angle)))
                x2 = cx + int(140 * np.cos(np.radians(angle)))
                y2 = cy + int(140 * np.sin(np.radians(angle)))
                rays_pts.extend([[[x1, y1]], [[x2, y2]]])
            rays_contour = np.array(rays_pts, dtype=np.int32)
            
            self.steps = [
                DrawingStep("圆形", circle_contour, "先画一个大圆圈"),
                DrawingStep("光芒", rays_contour, "加上太阳的光芒")
            ]
            
        elif "房子" in name or "house" in name.lower():
            # 房子的步骤
            # 主体
            body_pts = np.array([[[cx-100, cy-50]], [[cx+100, cy-50]], 
                                [[cx+100, cy+100]], [[cx-100, cy+100]]], dtype=np.int32)
            # 屋顶
            roof_pts = np.array([[[cx-120, cy-50]], [[cx, cy-120]], 
                                [[cx+120, cy-50]]], dtype=np.int32)
            
            self.steps = [
                DrawingStep("主体", body_pts, "先画一个正方形作为房子主体"),
                DrawingStep("屋顶", roof_pts, "画一个三角形作为屋顶")
            ]
            
        else:
            # 默认步骤 - 简单的框架
            outline_pts = np.array([[[50, 50]], [[w-50, 50]], 
                                   [[w-50, h-50]], [[50, h-50]]], dtype=np.int32)
            self.steps = [
                DrawingStep("轮廓", outline_pts, f"画出{name}的基本轮廓")
            ]
            
        print(f"为 {name} 创建了 {len(self.steps)} 个默认步骤")
        
    def _decompose_to_steps(self, contours: List[np.ndarray]) -> List[DrawingStep]:
        """将轮廓分解为绘画步骤"""
        steps = []
        
        # 根据轮廓的复杂度和位置分组
        if len(contours) == 0:
            return steps
            
        # 简单策略：按轮廓大小分步
        if len(contours) == 1:
            # 只有一个轮廓，分段绘制
            contour = contours[0]
            num_points = len(contour)
            
            if num_points > 20:
                # 分3步
                step1_pts = contour[:num_points//3]
                step2_pts = contour[num_points//3:2*num_points//3]
                step3_pts = contour[2*num_points//3:]
                
                steps.append(DrawingStep("轮廓起始", step1_pts, "先画出基本形状"))
                steps.append(DrawingStep("轮廓中段", step2_pts, "继续完成轮廓"))
                steps.append(DrawingStep("轮廓完成", step3_pts, "完成整个轮廓"))
            else:
                steps.append(DrawingStep("主轮廓", contour, "画出主要形状"))
                
        else:
            # 多个轮廓，每个作为一步
            for i, contour in enumerate(contours[:5]):  # 最多5步
                if i == 0:
                    steps.append(DrawingStep(f"主体轮廓", contour, "先画出主要部分"))
                else:
                    steps.append(DrawingStep(f"细节{i}", contour, f"添加细节部分"))
                    
        return steps
        
    def _load_and_process_image(self, image_info: Dict):
        """加载并处理图片"""
        path = os.path.join(IMAGES_PATH, "drawing_tutorials", "real", image_info["file"])
        
        # 读取图片
        self.original_image = cv2.imread(path)
        if self.original_image is None:
            return False
            
        # 调整大小
        max_size = 400
        h, w = self.original_image.shape[:2]
        scale = min(max_size / w, max_size / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        self.original_image = cv2.resize(self.original_image, (new_w, new_h))
        
        # 转换为简笔画
        self.sketch_image = self._convert_to_sketch(self.original_image)
        
        # 提取轮廓和步骤 - 使用原始图像和简笔画
        contours = self._extract_contours_from_original(self.original_image)
        if not contours:
            # 如果从原始图像提取失败，尝试从简笔画提取
            contours = self._extract_contours(self.sketch_image)
            
        self.steps = self._decompose_to_steps(contours)
        
        # 如果仍然没有步骤，创建默认步骤
        if not self.steps:
            self._create_default_steps(image_info["name"])
        
        # 初始化画布
        self._init_canvas()
        
        return True
        
    def _init_canvas(self):
        """初始化画布"""
        if self.sketch_image is not None:
            h, w = self.sketch_image.shape[:2]
            self.canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
            self.current_sketch = self.canvas.copy()
            
    def _opencv_to_pygame(self, cv_image: np.ndarray) -> pygame.Surface:
        """将OpenCV图像转换为Pygame Surface"""
        # OpenCV使用BGR，Pygame使用RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        # 转置图像（OpenCV和Pygame的坐标系不同）
        rgb_image = np.transpose(rgb_image, (1, 0, 2))
        
        # 创建Pygame surface
        surface = pygame.surfarray.make_surface(rgb_image)
        
        return surface
        
    def handle_click(self, pos: Tuple[int, int]):
        """处理点击事件"""
        # 检查喇叭按钮
        for button, text in self.speaker_buttons:
            if button.check_click(pos):
                speak(text)
                return
                
        if self.game_phase == 'select':
            # 选择图片
            for i, btn_rect in enumerate(self.image_buttons):
                if btn_rect.collidepoint(pos):
                    if i < len(self.available_images):
                        self.selected_image = self.available_images[i]
                        if self._load_and_process_image(self.selected_image):
                            self.game_phase = 'original'
                            self.phase_timer = 0
                            speak(f"让我们来学画{self.selected_image['name']}")
                    return
                    
        elif self.game_phase == 'original':
            # 查看简笔画
            self.game_phase = 'sketch'
            speak("这是简化后的简笔画")
            
        elif self.game_phase == 'sketch':
            # 开始分步教学
            if self.steps:
                self.game_phase = 'steps'
                self.current_step = 0
                self.animation_progress = 0
                self.is_animating = True
                speak(f"开始学习，{self.steps[0].description}")
            else:
                speak("没有检测到可绘制的轮廓")
                
        elif self.game_phase == 'steps':
            # 控制按钮
            if 'next' in self.control_buttons and self.control_buttons['next'].collidepoint(pos):
                if self.current_step < len(self.steps) - 1:
                    self.current_step += 1
                    self.animation_progress = 0
                    self.is_animating = True
                    speak(self.steps[self.current_step].description)
                else:
                    # 完成
                    self.game_phase = 'complete'
                    self.show_complete_feedback = True
                    speak(f"太棒了！你学会了画{self.selected_image['name']}")
                    
            elif 'prev' in self.control_buttons and self.control_buttons['prev'].collidepoint(pos):
                if self.current_step > 0:
                    self.current_step -= 1
                    self.animation_progress = 0
                    self.is_animating = True
                    speak(self.steps[self.current_step].description)
                    
            elif 'pause' in self.control_buttons and self.control_buttons['pause'].collidepoint(pos):
                self.is_animating = not self.is_animating
                speak("继续" if self.is_animating else "暂停")
                
        elif self.game_phase == 'complete':
            # 返回选择界面
            self.game_phase = 'select'
            self.selected_image = None
            self.steps = []
            speak("选择一个新的图片来学习")
            
    def update(self, dt: float):
        """更新游戏状态"""
        # 更新动画进度
        if self.is_animating and self.game_phase == 'steps':
            self.animation_progress = min(1.0, self.animation_progress + dt * self.animation_speed)
            
            # 更新画布
            if self.steps and self.current_step < len(self.steps):
                self._update_canvas()
                
        # 更新喇叭按钮
        mouse_pos = pygame.mouse.get_pos()
        for button, _ in self.speaker_buttons:
            button.update(mouse_pos)
            
    def _update_canvas(self):
        """更新画布"""
        if not self.canvas is not None:
            return
            
        # 清空当前草图
        self.current_sketch = self.canvas.copy()
        
        # 绘制已完成的步骤
        for i in range(self.current_step):
            if i < len(self.steps):
                cv2.drawContours(self.current_sketch, [self.steps[i].contour], -1, (0, 0, 0), 2)
                
        # 绘制当前步骤（根据进度）
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            if len(step.contour) > 0:
                # 根据进度绘制部分轮廓
                num_points = max(2, int(len(step.contour) * self.animation_progress))
                partial_contour = step.contour[:num_points]
                
                if len(partial_contour) >= 2:
                    for i in range(len(partial_contour) - 1):
                        cv2.line(self.current_sketch, 
                                tuple(partial_contour[i][0]), 
                                tuple(partial_contour[i+1][0]), 
                                (0, 0, 0), 2)
                        
    def draw(self, screen: pygame.Surface):
        """绘制游戏画面"""
        screen.fill(COLORS['background'])
        
        # 清空喇叭按钮
        self.speaker_buttons.clear()
        
        # 绘制标题
        title_font = get_chinese_font(self.scale_font_size(48))
        title = "学画画 - OpenCV版"
        title_surf = title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(self.get_center_x(), self.scale_value(50)))
        screen.blit(title_surf, title_rect)
        
        # 根据游戏阶段绘制
        if self.game_phase == 'select':
            self._draw_image_selection(screen)
        elif self.game_phase == 'original':
            self._draw_original_image(screen)
        elif self.game_phase == 'sketch':
            self._draw_sketch_image(screen)
        elif self.game_phase == 'steps':
            self._draw_steps(screen)
        elif self.game_phase == 'complete':
            self._draw_complete(screen)
            
        # 绘制所有喇叭按钮
        for button, _ in self.speaker_buttons:
            button.draw(screen)
            
    def _draw_image_selection(self, screen: pygame.Surface):
        """绘制图片选择界面"""
        self.image_buttons.clear()
        
        # 提示文字
        hint_font = get_chinese_font(self.scale_font_size(32))
        hint_text = "选择一个图片来学习画画"
        hint_surf = hint_font.render(hint_text, True, COLORS['text'])
        hint_rect = hint_surf.get_rect(center=(self.get_center_x(), self.scale_value(120)))
        screen.blit(hint_surf, hint_rect)
        
        # 绘制可选图片
        if not self.available_images:
            # 没有图片时的提示
            no_img_font = get_chinese_font(self.scale_font_size(24))
            no_img_text = "请在 assets/images/drawing_tutorials/real/ 目录下添加图片"
            no_img_surf = no_img_font.render(no_img_text, True, COLORS['secondary'])
            no_img_rect = no_img_surf.get_rect(center=(self.get_center_x(), self.get_center_y()))
            screen.blit(no_img_surf, no_img_rect)
            return
            
        # 图片按钮布局
        cols = 3
        rows = (len(self.available_images) + cols - 1) // cols
        
        button_width = self.scale_value(200)
        button_height = self.scale_value(150)
        spacing = self.scale_value(30)
        
        total_width = cols * button_width + (cols - 1) * spacing
        total_height = rows * button_height + (rows - 1) * spacing
        
        start_x = (self.window_width - total_width) // 2
        start_y = (self.window_height - total_height) // 2 + self.scale_value(30)
        
        label_font = get_chinese_font(self.scale_font_size(24))
        
        for i, img_info in enumerate(self.available_images):
            row = i // cols
            col = i % cols
            
            x = start_x + col * (button_width + spacing)
            y = start_y + row * (button_height + spacing)
            
            # 按钮矩形
            btn_rect = pygame.Rect(x, y, button_width, button_height)
            self.image_buttons.append(btn_rect)
            
            # 绘制按钮
            color = COLORS['primary'] if img_info['difficulty'] <= self.get_difficulty() else COLORS['disabled']
            pygame.draw.rect(screen, color, btn_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS['text'], btn_rect, 3, border_radius=10)
            
            # 图片名称
            name_surf = label_font.render(img_info['name'], True, COLORS['white'])
            name_rect = name_surf.get_rect(center=btn_rect.center)
            screen.blit(name_surf, name_rect)
            
            # 难度标记
            stars = "★" * img_info['difficulty']
            stars_surf = label_font.render(stars, True, COLORS['warning'])
            stars_rect = stars_surf.get_rect(centerx=btn_rect.centerx, 
                                            bottom=btn_rect.bottom - self.scale_value(10))
            screen.blit(stars_surf, stars_rect)
            
    def _draw_original_image(self, screen: pygame.Surface):
        """绘制原始图片"""
        if self.original_image is not None:
            # 转换并绘制图片
            pygame_img = self._opencv_to_pygame(self.original_image)
            img_rect = pygame_img.get_rect(center=(self.get_center_x(), self.get_center_y()))
            screen.blit(pygame_img, img_rect)
            
            # 标题
            label_font = get_chinese_font(self.scale_font_size(32))
            label_text = f"真实的{self.selected_image['name']}"
            label_surf = label_font.render(label_text, True, COLORS['text'])
            label_rect = label_surf.get_rect(center=(self.get_center_x(), self.scale_value(120)))
            screen.blit(label_surf, label_rect)
            
            # 提示
            hint_font = get_chinese_font(self.scale_font_size(24))
            hint_text = "点击查看简笔画"
            hint_surf = hint_font.render(hint_text, True, COLORS['secondary'])
            hint_rect = hint_surf.get_rect(center=(self.get_center_x(), 
                                                   self.window_height - self.scale_value(100)))
            screen.blit(hint_surf, hint_rect)
            
    def _draw_sketch_image(self, screen: pygame.Surface):
        """绘制简笔画"""
        if self.sketch_image is not None:
            # 转换并绘制图片
            pygame_img = self._opencv_to_pygame(self.sketch_image)
            img_rect = pygame_img.get_rect(center=(self.get_center_x(), self.get_center_y()))
            screen.blit(pygame_img, img_rect)
            
            # 标题
            label_font = get_chinese_font(self.scale_font_size(32))
            label_text = f"{self.selected_image['name']}的简笔画"
            label_surf = label_font.render(label_text, True, COLORS['text'])
            label_rect = label_surf.get_rect(center=(self.get_center_x(), self.scale_value(120)))
            screen.blit(label_surf, label_rect)
            
            # 提示
            hint_font = get_chinese_font(self.scale_font_size(24))
            hint_text = "点击开始分步学习" if self.steps else "没有检测到可绘制的轮廓"
            hint_surf = hint_font.render(hint_text, True, COLORS['secondary'])
            hint_rect = hint_surf.get_rect(center=(self.get_center_x(), 
                                                   self.window_height - self.scale_value(100)))
            screen.blit(hint_surf, hint_rect)
            
    def _draw_steps(self, screen: pygame.Surface):
        """绘制分步教学"""
        if self.current_sketch is not None:
            # 转换并绘制当前草图
            pygame_img = self._opencv_to_pygame(self.current_sketch)
            img_rect = pygame_img.get_rect(center=(self.get_center_x(), self.get_center_y()))
            self.canvas_rect = img_rect
            screen.blit(pygame_img, img_rect)
            
            # 绘制边框
            pygame.draw.rect(screen, COLORS['text'], img_rect, 2)
            
        # 步骤说明
        if self.current_step < len(self.steps):
            step_font = get_chinese_font(self.scale_font_size(32))
            step = self.steps[self.current_step]
            step_text = f"第{self.current_step + 1}步：{step.description}"
            step_surf = step_font.render(step_text, True, COLORS['primary'])
            step_rect = step_surf.get_rect(center=(self.get_center_x(), self.scale_value(120)))
            screen.blit(step_surf, step_rect)
            
            # 进度条
            progress_width = self.scale_value(400)
            progress_height = self.scale_value(20)
            progress_x = (self.window_width - progress_width) // 2
            progress_y = self.scale_value(160)
            
            # 背景
            pygame.draw.rect(screen, COLORS['disabled'], 
                           (progress_x, progress_y, progress_width, progress_height),
                           border_radius=10)
            
            # 进度
            filled_width = int(progress_width * self.animation_progress)
            if filled_width > 0:
                pygame.draw.rect(screen, COLORS['success'], 
                               (progress_x, progress_y, filled_width, progress_height),
                               border_radius=10)
                
        # 绘制控制按钮
        self._draw_control_buttons(screen)
        
    def _draw_control_buttons(self, screen: pygame.Surface):
        """绘制控制按钮"""
        self.control_buttons.clear()
        
        button_y = self.window_height - self.scale_value(80)
        button_width = self.scale_value(100)
        button_height = self.scale_value(50)
        spacing = self.scale_value(20)
        
        # 计算按钮位置
        buttons = ['prev', 'pause', 'next']
        total_width = len(buttons) * button_width + (len(buttons) - 1) * spacing
        start_x = (self.window_width - total_width) // 2
        
        button_font = get_chinese_font(self.scale_font_size(24))
        
        for i, btn_type in enumerate(buttons):
            x = start_x + i * (button_width + spacing)
            btn_rect = pygame.Rect(x, button_y, button_width, button_height)
            self.control_buttons[btn_type] = btn_rect
            
            # 按钮样式和文字
            if btn_type == 'prev':
                color = COLORS['secondary'] if self.current_step > 0 else COLORS['disabled']
                text = "上一步"
                enabled = self.current_step > 0
            elif btn_type == 'pause':
                color = COLORS['warning'] if self.is_animating else COLORS['success']
                text = "暂停" if self.is_animating else "继续"
                enabled = True
            else:  # next
                color = COLORS['primary']
                text = "完成" if self.current_step == len(self.steps) - 1 else "下一步"
                enabled = True
                
            # 绘制按钮
            if enabled:
                pygame.draw.rect(screen, color, btn_rect, border_radius=5)
                text_surf = button_font.render(text, True, COLORS['white'])
                text_rect = text_surf.get_rect(center=btn_rect.center)
                screen.blit(text_surf, text_rect)
            else:
                pygame.draw.rect(screen, COLORS['disabled'], btn_rect, 2, border_radius=5)
                text_surf = button_font.render(text, True, COLORS['disabled'])
                text_rect = text_surf.get_rect(center=btn_rect.center)
                screen.blit(text_surf, text_rect)
                
    def _draw_complete(self, screen: pygame.Surface):
        """绘制完成画面"""
        # 显示完整的草图
        if self.sketch_image is not None:
            pygame_img = self._opencv_to_pygame(self.sketch_image)
            img_rect = pygame_img.get_rect(center=(self.get_center_x(), self.get_center_y()))
            screen.blit(pygame_img, img_rect)
            
        # 庆祝效果
        if self.show_complete_feedback:
            draw_star_eyes_face(screen, self.get_center_x(), 
                               self.scale_value(150), self.scale_value(80))
            
            complete_font = get_chinese_font(self.scale_font_size(48))
            complete_text = "太棒了！"
            complete_surf = complete_font.render(complete_text, True, COLORS['success'])
            complete_rect = complete_surf.get_rect(center=(self.get_center_x(), 
                                                          self.window_height - self.scale_value(150)))
            screen.blit(complete_surf, complete_rect)
            
            hint_font = get_chinese_font(self.scale_font_size(24))
            hint_text = "点击选择新的图片"
            hint_surf = hint_font.render(hint_text, True, COLORS['secondary'])
            hint_rect = hint_surf.get_rect(center=(self.get_center_x(), 
                                                   self.window_height - self.scale_value(80)))
            screen.blit(hint_surf, hint_rect)
            
    def get_result(self) -> Dict:
        """获取游戏结果"""
        return {
            'completed': self.game_phase == 'complete',
            'score': 100 if self.game_phase == 'complete' else 0,
            'stars': 3 if self.game_phase == 'complete' else 0,
            'coins': 10 if self.game_phase == 'complete' else 0,
            'learned': self.selected_image['name'] if self.selected_image else "无"
        }