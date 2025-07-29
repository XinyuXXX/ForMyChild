#!/usr/bin/env python3
"""
增强的线条画生成器
使用OpenCV和传统图像处理技术生成高质量的线条画
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from scipy.ndimage import gaussian_filter, morphology
from skimage import feature, filters


class EnhancedLineDrawingProcessor:
    """增强的线条画处理器"""
    
    def __init__(self):
        self.style_params = {
            'simple': {
                'blur_size': 9,
                'canny_low': 100,
                'canny_high': 200,
                'line_width': 5,
                'detail_level': 0.2
            },
            'cartoon': {
                'blur_size': 5,
                'canny_low': 80,
                'canny_high': 180,
                'line_width': 3,
                'detail_level': 0.5
            },
            'sketch': {
                'blur_size': 3,
                'canny_low': 50,
                'canny_high': 150,
                'line_width': 2,
                'detail_level': 0.8
            }
        }
        
    def extract_edges_multiscale(self, image: np.ndarray) -> np.ndarray:
        """多尺度边缘提取"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # 多尺度边缘检测
        scales = [1.0, 1.5, 2.0]
        edges_list = []
        
        for scale in scales:
            # 调整图像大小
            scaled_size = (int(gray.shape[1] * scale), int(gray.shape[0] * scale))
            scaled = cv2.resize(gray, scaled_size)
            
            # 应用不同的边缘检测方法
            # Canny边缘
            canny_edges = cv2.Canny(scaled, 50, 150)
            
            # Sobel边缘
            sobelx = cv2.Sobel(scaled, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(scaled, cv2.CV_64F, 0, 1, ksize=3)
            sobel_edges = np.sqrt(sobelx**2 + sobely**2)
            sobel_edges = (sobel_edges / sobel_edges.max() * 255).astype(np.uint8)
            
            # 组合边缘
            combined = cv2.addWeighted(canny_edges, 0.7, sobel_edges, 0.3, 0)
            
            # 调整回原始大小
            edges = cv2.resize(combined, (gray.shape[1], gray.shape[0]))
            edges_list.append(edges)
            
        # 合并多尺度边缘
        final_edges = np.zeros_like(gray)
        for i, edges in enumerate(edges_list):
            weight = 1.0 / (i + 1)  # 给较小尺度更高权重
            final_edges = cv2.addWeighted(final_edges, 1, edges, weight, 0)
            
        return final_edges
        
    def apply_artistic_filter(self, image: np.ndarray) -> np.ndarray:
        """应用艺术滤镜"""
        # 双边滤波保留边缘
        filtered = cv2.bilateralFilter(image, 9, 75, 75)
        
        # 使用边缘保留滤波进一步平滑
        gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY) if len(filtered.shape) == 3 else filtered
        
        # 使用自适应双边滤波代替导向滤波
        smooth = cv2.bilateralFilter(gray, 15, 80, 80)
        
        return smooth
        
    def extract_contours_hierarchical(self, edges: np.ndarray) -> list:
        """分层提取轮廓"""
        # 形态学操作连接断开的边缘
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # 按层次组织轮廓
        main_contours = []
        detail_contours = []
        
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if hierarchy[0][i][3] == -1:  # 最外层轮廓
                if area > 500:
                    main_contours.append(contour)
            else:  # 内部轮廓
                if area > 100:
                    detail_contours.append(contour)
                    
        return main_contours, detail_contours
        
    def generate_line_drawing(self, image: np.ndarray, style: str = 'sketch') -> np.ndarray:
        """生成线条画"""
        params = self.style_params.get(style, self.style_params['sketch'])
        
        # 1. 预处理
        processed = self.apply_artistic_filter(image)
        
        # 2. 多尺度边缘提取
        edges = self.extract_edges_multiscale(image)
        
        # 3. 使用自适应阈值增强
        if len(processed.shape) == 3:
            gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        else:
            gray = processed
            
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        
        # 4. 组合边缘和自适应阈值
        combined = cv2.addWeighted(edges, 0.6, cv2.bitwise_not(adaptive), 0.4, 0)
        
        # 5. 应用高斯模糊
        blurred = cv2.GaussianBlur(combined, (params['blur_size'], params['blur_size']), 0)
        
        # 6. 最终边缘检测
        final_edges = cv2.Canny(blurred, params['canny_low'], params['canny_high'])
        
        # 7. 线条加粗
        kernel = np.ones((params['line_width'], params['line_width']), np.uint8)
        thick_lines = cv2.dilate(final_edges, kernel, iterations=1)
        
        # 8. 反转颜色（白底黑线）
        line_drawing = cv2.bitwise_not(thick_lines)
        
        # 9. 添加细节（根据style）
        if params['detail_level'] > 0.5:
            # 提取细节轮廓
            detail_edges = feature.canny(gray, sigma=2.0)
            detail_edges = (detail_edges * 255).astype(np.uint8)
            detail_edges = cv2.bitwise_not(detail_edges)
            
            # 混合细节
            alpha = params['detail_level'] - 0.5
            line_drawing = cv2.addWeighted(line_drawing, 1, detail_edges, alpha, 0)
            
        # 转换为3通道
        return cv2.cvtColor(line_drawing, cv2.COLOR_GRAY2BGR)
        

class LineDrawingSimplifier:
    """线条画简化器 - 用于生成适合儿童的简单线条"""
    
    @staticmethod
    def simplify_for_kids(line_drawing: np.ndarray, level: int = 1) -> np.ndarray:
        """简化线条画以适合儿童
        level: 1-5, 1最简单，5最复杂
        """
        gray = cv2.cvtColor(line_drawing, cv2.COLOR_BGR2GRAY) if len(line_drawing.shape) == 3 else line_drawing
        
        # 根据等级设置参数
        params = {
            1: {'blur': 11, 'threshold': 200, 'dilate': 5, 'min_length': 100},
            2: {'blur': 9, 'threshold': 180, 'dilate': 4, 'min_length': 80},
            3: {'blur': 7, 'threshold': 160, 'dilate': 3, 'min_length': 60},
            4: {'blur': 5, 'threshold': 140, 'dilate': 2, 'min_length': 40},
            5: {'blur': 3, 'threshold': 120, 'dilate': 1, 'min_length': 20}
        }
        
        p = params.get(level, params[3])
        
        # 1. 强模糊去除细节
        blurred = cv2.GaussianBlur(gray, (p['blur'], p['blur']), 0)
        
        # 2. 二值化
        _, binary = cv2.threshold(blurred, p['threshold'], 255, cv2.THRESH_BINARY)
        
        # 3. 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
        
        # 4. 提取轮廓并过滤
        contours, _ = cv2.findContours(cv2.bitwise_not(cleaned), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 创建新的画布
        result = np.ones_like(gray) * 255
        
        # 只绘制足够大的轮廓
        for contour in contours:
            length = cv2.arcLength(contour, True)
            if length > p['min_length']:
                # 简化轮廓
                epsilon = 0.02 * length
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # 绘制简化后的轮廓
                cv2.drawContours(result, [approx], -1, 0, p['dilate'])
                
        # 5. 平滑线条
        result = cv2.medianBlur(result, 3)
        
        # 转换为3通道
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        

class StrokeDecomposer:
    """笔画分解器 - 将复杂图形分解为简单笔画"""
    
    @staticmethod
    def decompose_shape(contour: np.ndarray, shape_type: str = 'unknown') -> list:
        """根据形状类型分解轮廓"""
        if shape_type == 'circle':
            return StrokeDecomposer._decompose_circle(contour)
        elif shape_type == 'rectangle':
            return StrokeDecomposer._decompose_rectangle(contour)
        elif shape_type == 'triangle':
            return StrokeDecomposer._decompose_triangle(contour)
        else:
            return StrokeDecomposer._decompose_generic(contour)
            
    @staticmethod
    def _decompose_circle(contour: np.ndarray) -> list:
        """分解圆形"""
        # 圆形通常分为4个弧段
        n_points = len(contour)
        segment_size = n_points // 4
        
        strokes = []
        for i in range(4):
            start = i * segment_size
            end = (i + 1) * segment_size if i < 3 else n_points
            stroke = contour[start:end]
            if len(stroke) > 2:
                strokes.append(stroke)
                
        return strokes
        
    @staticmethod
    def _decompose_rectangle(contour: np.ndarray) -> list:
        """分解矩形"""
        # 找到4个角点
        rect = cv2.minAreaRect(contour)
        corners = cv2.boxPoints(rect).astype(np.int32)
        
        # 创建4条边
        strokes = []
        for i in range(4):
            start = corners[i]
            end = corners[(i + 1) % 4]
            # 创建直线
            stroke = np.array([start, end])
            strokes.append(stroke)
            
        return strokes
        
    @staticmethod
    def _decompose_triangle(contour: np.ndarray) -> list:
        """分解三角形"""
        # 简化为3个顶点
        epsilon = 0.1 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if len(approx) >= 3:
            # 取前3个点作为三角形顶点
            vertices = approx[:3].squeeze()
            
            # 创建3条边
            strokes = []
            for i in range(3):
                start = vertices[i]
                end = vertices[(i + 1) % 3]
                stroke = np.array([start, end])
                strokes.append(stroke)
                
        else:
            strokes = [contour]
            
        return strokes
        
    @staticmethod
    def _decompose_generic(contour: np.ndarray) -> list:
        """通用分解方法"""
        # 检测拐点
        curvature = StrokeDecomposer._compute_curvature(contour)
        split_points = StrokeDecomposer._find_split_points(curvature)
        
        # 根据拐点分割
        strokes = []
        start = 0
        for split in split_points:
            if split - start > 5:  # 最少5个点
                strokes.append(contour[start:split])
            start = split
            
        # 添加最后一段
        if len(contour) - start > 5:
            strokes.append(contour[start:])
            
        return strokes if strokes else [contour]
        
    @staticmethod
    def _compute_curvature(contour: np.ndarray) -> np.ndarray:
        """计算轮廓的曲率"""
        if len(contour) < 3:
            return np.zeros(len(contour))
            
        # 计算一阶和二阶导数
        dx = np.gradient(contour[:, 0])
        dy = np.gradient(contour[:, 1])
        ddx = np.gradient(dx)
        ddy = np.gradient(dy)
        
        # 曲率公式
        numerator = np.abs(dx * ddy - dy * ddx)
        denominator = np.power(dx**2 + dy**2, 1.5)
        
        # 避免除零
        curvature = np.zeros_like(numerator)
        mask = denominator > 1e-6
        curvature[mask] = numerator[mask] / denominator[mask]
        
        return curvature
        
    @staticmethod
    def _find_split_points(curvature: np.ndarray, threshold: float = 0.5) -> list:
        """找到曲率峰值作为分割点"""
        # 平滑曲率
        from scipy.signal import savgol_filter
        if len(curvature) > 10:
            smoothed = savgol_filter(curvature, min(11, len(curvature) // 2 * 2 + 1), 3)
        else:
            smoothed = curvature
            
        # 找到局部最大值
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(smoothed, height=threshold * np.max(smoothed))
        
        return peaks.tolist()