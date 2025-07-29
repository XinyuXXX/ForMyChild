#!/usr/bin/env python3
"""
DeepLineDrawing模型实现
基于论文: Learning to Simplify: Fully Convolutional Networks for Rough Sketch Cleanup
用于将图片转换为高质量的线条画
"""
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("PyTorch未安装，将使用传统图像处理方法")
import numpy as np
import cv2
from typing import Tuple, Optional


if TORCH_AVAILABLE:
    class ResidualBlock(nn.Module):
    """残差块"""
    def __init__(self, channels: int):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)
        
    def forward(self, x):
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual
        return F.relu(out)


class DeepLineDrawingNet(nn.Module):
    """DeepLineDrawing网络架构"""
    def __init__(self):
        super(DeepLineDrawingNet, self).__init__()
        
        # 编码器部分
        self.enc1 = nn.Sequential(
            nn.Conv2d(3, 64, 7, padding=3),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True)
        )
        
        self.enc2 = nn.Sequential(
            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            ResidualBlock(128),
            ResidualBlock(128)
        )
        
        self.enc3 = nn.Sequential(
            nn.Conv2d(128, 256, 3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            ResidualBlock(256),
            ResidualBlock(256),
            ResidualBlock(256)
        )
        
        self.enc4 = nn.Sequential(
            nn.Conv2d(256, 512, 3, stride=2, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            ResidualBlock(512),
            ResidualBlock(512),
            ResidualBlock(512)
        )
        
        # 瓶颈层
        self.bottleneck = nn.Sequential(
            ResidualBlock(512),
            ResidualBlock(512),
            ResidualBlock(512),
            ResidualBlock(512)
        )
        
        # 解码器部分
        self.dec4 = nn.Sequential(
            nn.ConvTranspose2d(512, 256, 3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True)
        )
        self.dec4_res = nn.Sequential(
            ResidualBlock(256),
            ResidualBlock(256)
        )
        
        self.dec3 = nn.Sequential(
            nn.ConvTranspose2d(256, 128, 3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True)
        )
        self.dec3_res = nn.Sequential(
            ResidualBlock(128),
            ResidualBlock(128)
        )
        
        self.dec2 = nn.Sequential(
            nn.ConvTranspose2d(128, 64, 3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True)
        )
        self.dec2_res = ResidualBlock(64)
        
        # 输出层
        self.output = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, 1),
            nn.Sigmoid()
        )
        
        # 边缘检测辅助分支
        self.edge_detector = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        # 编码
        e1 = self.enc1(x)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)
        
        # 瓶颈
        b = self.bottleneck(e4)
        
        # 解码（带跳跃连接）
        d4 = self.dec4(b)
        d4 = self.dec4_res(d4 + e3)  # 跳跃连接
        
        d3 = self.dec3(d4)
        d3 = self.dec3_res(d3 + e2)  # 跳跃连接
        
        d2 = self.dec2(d3)
        d2 = self.dec2_res(d2 + e1)  # 跳跃连接
        
        # 输出
        output = self.output(d2)
        edge = self.edge_detector(e1)  # 边缘检测辅助
        
        # 组合输出
        final_output = 0.8 * output + 0.2 * edge
        
        return final_output


class DeepLineDrawingProcessor:
    """DeepLineDrawing处理器"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = DeepLineDrawingNet().to(self.device)
        self.model.eval()
        
        # 加载预训练权重
        if model_path:
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                print("成功加载DeepLineDrawing模型")
            except:
                print("模型加载失败，使用随机初始化权重")
                
    def preprocess_image(self, image: np.ndarray, target_size: Tuple[int, int] = (512, 512)) -> torch.Tensor:
        """预处理图像"""
        # 调整大小
        h, w = image.shape[:2]
        image_resized = cv2.resize(image, target_size)
        
        # 归一化到[0, 1]
        image_normalized = image_resized.astype(np.float32) / 255.0
        
        # 转换为tensor
        image_tensor = torch.from_numpy(image_normalized).permute(2, 0, 1).unsqueeze(0)
        
        return image_tensor.to(self.device), (h, w)
        
    def postprocess_output(self, output: torch.Tensor, original_size: Tuple[int, int]) -> np.ndarray:
        """后处理输出"""
        # 转换为numpy
        output_np = output.squeeze().cpu().numpy()
        
        # 反转颜色（白底黑线）
        output_np = 1.0 - output_np
        
        # 应用阈值清理
        output_np = np.where(output_np > 0.5, output_np, 0)
        
        # 转换为uint8
        output_np = (output_np * 255).astype(np.uint8)
        
        # 恢复原始大小
        output_resized = cv2.resize(output_np, (original_size[1], original_size[0]))
        
        # 应用形态学操作清理线条
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        output_cleaned = cv2.morphologyEx(output_resized, cv2.MORPH_CLOSE, kernel)
        output_cleaned = cv2.morphologyEx(output_cleaned, cv2.MORPH_OPEN, kernel)
        
        return output_cleaned
        
    def extract_clean_lines(self, sketch: np.ndarray) -> np.ndarray:
        """提取干净的线条"""
        # 使用自适应阈值
        if len(sketch.shape) == 3:
            sketch_gray = cv2.cvtColor(sketch, cv2.COLOR_BGR2GRAY)
        else:
            sketch_gray = sketch
            
        # 细化线条
        _, binary = cv2.threshold(sketch_gray, 127, 255, cv2.THRESH_BINARY)
        skeleton = cv2.ximgproc.thinning(binary)
        
        # 平滑处理
        smoothed = cv2.medianBlur(skeleton, 3)
        
        return smoothed
        
    def generate_line_drawing(self, image: np.ndarray) -> np.ndarray:
        """生成线条画"""
        with torch.no_grad():
            # 预处理
            input_tensor, original_size = self.preprocess_image(image)
            
            # 推理
            output = self.model(input_tensor)
            
            # 后处理
            line_drawing = self.postprocess_output(output, original_size)
            
            # 提取干净线条
            clean_lines = self.extract_clean_lines(line_drawing)
            
            # 转换为3通道
            line_drawing_3ch = cv2.cvtColor(clean_lines, cv2.COLOR_GRAY2BGR)
            
        return line_drawing_3ch
        
    def generate_with_style(self, image: np.ndarray, style: str = 'sketch') -> np.ndarray:
        """根据风格生成线条画"""
        # 基础线条画
        base_lines = self.generate_line_drawing(image)
        
        if style == 'sketch':
            # 素描风格 - 添加纹理
            texture = np.random.normal(0, 10, base_lines.shape).astype(np.uint8)
            styled = cv2.addWeighted(base_lines, 0.9, texture, 0.1, 0)
            
        elif style == 'cartoon':
            # 卡通风格 - 加粗线条
            kernel = np.ones((3, 3), np.uint8)
            styled = cv2.dilate(base_lines, kernel, iterations=1)
            
        elif style == 'simple':
            # 简单风格 - 极简线条
            gray = cv2.cvtColor(base_lines, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            styled = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            
        else:
            styled = base_lines
            
        return styled
        

class LineDrawingSimplifier:
    """线条画简化器 - 用于生成适合儿童的简单线条"""
    
    @staticmethod
    def simplify_for_kids(line_drawing: np.ndarray, level: int = 1) -> np.ndarray:
        """简化线条画以适合儿童
        level: 1-5, 1最简单，5最复杂
        """
        gray = cv2.cvtColor(line_drawing, cv2.COLOR_BGR2GRAY)
        
        if level == 1:
            # 最简单 - 只保留主要轮廓
            # 强模糊
            blurred = cv2.GaussianBlur(gray, (9, 9), 0)
            # 高阈值边缘检测
            edges = cv2.Canny(blurred, 100, 200)
            # 膨胀使线条更粗
            kernel = np.ones((5, 5), np.uint8)
            thick = cv2.dilate(edges, kernel, iterations=2)
            
        elif level == 2:
            # 简单 - 保留主要形状
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            edges = cv2.Canny(blurred, 80, 180)
            kernel = np.ones((3, 3), np.uint8)
            thick = cv2.dilate(edges, kernel, iterations=2)
            
        elif level == 3:
            # 中等 - 保留更多细节
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 60, 150)
            kernel = np.ones((3, 3), np.uint8)
            thick = cv2.dilate(edges, kernel, iterations=1)
            
        elif level == 4:
            # 较复杂 - 保留大部分细节
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            edges = cv2.Canny(blurred, 50, 120)
            kernel = np.ones((2, 2), np.uint8)
            thick = cv2.dilate(edges, kernel, iterations=1)
            
        else:
            # 最复杂 - 保留所有细节
            edges = cv2.Canny(gray, 30, 100)
            thick = edges
            
        # 反转颜色（白底黑线）
        result = cv2.bitwise_not(thick)
        
        # 转换为3通道
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        

def create_pretrained_model():
    """创建一个预训练的模型（用于演示）"""
    model = DeepLineDrawingNet()
    
    # 初始化权重（使用Xavier初始化）
    def init_weights(m):
        if isinstance(m, nn.Conv2d) or isinstance(m, nn.ConvTranspose2d):
            nn.init.xavier_uniform_(m.weight)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.BatchNorm2d):
            nn.init.constant_(m.weight, 1)
            nn.init.constant_(m.bias, 0)
            
    model.apply(init_weights)
    
    return model