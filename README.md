# GameVision Overlay (GVO)

GameVision Overlay 是一个基于 YOLOv8 的实时游戏目标检测覆盖显示工具。它可以在不影响游戏操作的情况下，实时检测和显示游戏中的目标对象。

## 特性

- 实时目标检测和显示
- 支持 4K (3840x2160) 分辨率
- 透明覆盖层，不影响游戏操作
- 实时位置校准功能
- 调试模式支持
- FPS 监控
- 自动保存校准配置

## 环境要求

- Python 3.8+
- CUDA 支持（推荐）

## 依赖库

```bash
pip install ultralytics
pip install pygame
pip install numpy
pip install pillow
pip install pywin32
