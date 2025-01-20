from ultralytics import YOLO
import numpy as np
from PIL import ImageGrab
import win32gui
import win32con
import win32api
import pygame
import time
import json
import os
import ctypes

class OverlayBox:
    def __init__(self):
        pygame.init()
        # 设置4K分辨率
        self.screen_width = 3840
        self.screen_height = 2160
        
        # DPI感知设置
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        
        # 初始化偏移校准
        self.calibration_file = 'calibration.json'
        self.offset_x = 0
        self.offset_y = 0
        self.load_calibration()
        
        # 创建4K分辨率的透明窗口
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), 
                                            pygame.NOFRAME | pygame.DOUBLEBUF | pygame.HWSURFACE)
        self.hwnd = pygame.display.get_wm_info()["window"]
        
        # 设置窗口属性
        self.set_window_attributes()
        
        # 初始化YOLO模型
        self.model = YOLO('best.pt')
        self.running = True
        self.debug_mode = False
        
        # 性能监控
        self.last_fps_time = time.time()
        self.frame_count = 0
        self.fps = 0
        
        # 4K适配的UI比例
        self.ui_scale = 2
        
        # 颜色设置
        self.colors = {
            'box': (0, 255, 0),
            'text': (255, 255, 255),
            'debug': (255, 0, 0)
        }

    def load_calibration(self):
        """加载校准数据"""
        try:
            if os.path.exists(self.calibration_file):
                with open(self.calibration_file, 'r') as f:
                    data = json.load(f)
                    self.offset_x = data.get('offset_x', 0)
                    self.offset_y = data.get('offset_y', 0)
        except Exception as e:
            print(f"加载校准数据失败: {e}")

    def save_calibration(self):
        """保存校准数据"""
        try:
            with open(self.calibration_file, 'w') as f:
                json.dump({
                    'offset_x': self.offset_x,
                    'offset_y': self.offset_y
                }, f)
        except Exception as e:
            print(f"保存校准数据失败: {e}")

    def adjust_coordinates(self, x, y):
        """根据偏移量调整坐标"""
        return x + self.offset_x, y + self.offset_y

    def set_window_attributes(self):
        """设置窗口属性"""
        win_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, 
                             win_style | win32con.WS_EX_LAYERED | 
                             win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST)
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 
                             self.screen_width, self.screen_height, 
                             win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE)
        win32gui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(0,0,0), 0, win32con.LWA_COLORKEY)

    def update_fps(self):
        """更新FPS计数"""
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time > 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current_time

    def handle_input(self):
        """处理用户输入"""
        keys = pygame.key.get_pressed()
        
        # 调整偏移量
        if keys[pygame.K_LEFT]:
            self.offset_x -= 1
        if keys[pygame.K_RIGHT]:
            self.offset_x += 1
        if keys[pygame.K_UP]:
            self.offset_y -= 1
        if keys[pygame.K_DOWN]:
            self.offset_y += 1
        
        # 其他控制
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F1:
                    self.debug_mode = not self.debug_mode
                elif event.key == pygame.K_s:
                    self.save_calibration()
                    print("校准数据已保存")

    def draw_boxes(self, boxes: list):
        """绘制检测框，适配4K分辨率"""
        self.screen.fill((0,0,0))
        
        for box in boxes:
            try:
                b = box.xyxy[0]
                conf = float(box.conf)
                cls = int(box.cls)
                
                if conf > 0.5:
                    x1, y1, x2, y2 = map(int, b)
                    x1, y1 = self.adjust_coordinates(x1, y1)
                    x2, y2 = self.adjust_coordinates(x2, y2)
                    
                    # 4K适配：增加线条粗细
                    line_thickness = max(2, int(3 * self.ui_scale))
                    pygame.draw.rect(self.screen, self.colors['box'], 
                                   (x1, y1, x2-x1, y2-y1), line_thickness)
                    
                    # 4K适配：增加字体大小
                    font_size = int(24 * self.ui_scale)
                    font = pygame.font.Font(None, font_size)
                    label = f"{self.model.names[cls]} {conf:.2f}"
                    text = font.render(label, True, self.colors['text'])
                    self.screen.blit(text, (x1, y1-font_size))
            except Exception as e:
                print(f"绘制错误: {e}")
                continue

    def draw_debug_info(self):
        """绘制调试信息，适配4K分辨率"""
        if self.debug_mode:
            font = pygame.font.Font(None, int(36 * self.ui_scale))
            debug_info = [
                f"FPS: {self.fps}",
                f"分辨率: {self.screen_width}x{self.screen_height}",
                f"偏移量 X: {self.offset_x}",
                f"偏移量 Y: {self.offset_y}",
                "按键说明:",
                "F1: 调试模式",
                "方向键: 调整偏移",
                "S: 保存校准",
                "ESC: 退出"
            ]
            
            for i, text in enumerate(debug_info):
                surface = font.render(text, True, self.colors['debug'])
                self.screen.blit(surface, (20, 20 + i * (40 * self.ui_scale)))

    def run(self):
        """主循环"""
        try:
            while self.running:
                self.handle_input()
                
                # 屏幕捕获
                screen = np.array(ImageGrab.grab())
                
                # YOLO检测
                results = self.model(screen)
                
                # 绘制检测框
                for r in results:
                    self.draw_boxes(r.boxes)
                
                self.update_fps()
                self.draw_debug_info()
                
                pygame.display.flip()
                pygame.time.Clock().tick(60)
                
        except Exception as e:
            print(f"运行错误: {e}")
        finally:
            pygame.quit()

if __name__ == "__main__":
    try:
        detector = OverlayBox()
        detector.run()
    except Exception as e:
        print(f"主程序错误: {e}")
