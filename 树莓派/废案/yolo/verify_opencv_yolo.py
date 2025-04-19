#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import time
import os
import sys
from ultralytics import YOLO

def verify_opencv_yolo(frames_to_capture=10):
    print("开始验证OpenCV和YOLOv8集成...")
    
    # 创建保存结果的文件夹
    results_dir = "yolo_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        print(f"创建目录: {results_dir}")
    
    try:
        # 加载YOLOv8模型
        print("加载YOLOv8模型...")
        model = YOLO("yolov8n.pt")  # 使用最小的模型
        print("YOLOv8模型加载成功")
        
        # 打开摄像头
        print("打开摄像头...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("错误: 无法打开摄像头")
            return False
            
        # 开始捕获和识别
        print(f"开始捕获和识别 {frames_to_capture} 帧...")
        
        frame_count = 0
        class_counts = {}
        
        for i in range(frames_to_capture):
            ret, frame = cap.read()
            if not ret:
                print("读取摄像头帧失败")
                break
                
            print(f"正在处理第 {i+1}/{frames_to_capture} 帧...")
            
            # YOLOv8目标检测
            results = model(frame, conf=0.5)  # 仅保留置信度大于0.5的检测结果
            
            # 在图像上绘制检测结果
            annotated_frame = results[0].plot()
            
            # 保存带检测结果的图像
            filename = f"{results_dir}/detection_{i+1}.jpg"
            cv2.imwrite(filename, annotated_frame)
            print(f"已保存检测结果: {filename}")
            
            # 统计检测到的物体
            result = results[0]
            frame_count += 1
            
            if len(result.boxes) > 0:
                for box in result.boxes:
                    class_id = int(box.cls[0].item())
                    class_name = model.names[class_id]
                    if class_name in class_counts:
                        class_counts[class_name] += 1
                    else:
                        class_counts[class_name] = 1
            
            # 保存检测数据到文本文件
            with open(f"{results_dir}/detection_{i+1}_data.txt", "w", encoding="utf-8") as f:
                f.write(f"帧 {i+1} 检测结果:\n")
                if len(result.boxes) > 0:
                    frame_classes = {}
                    for box in result.boxes:
                        class_id = int(box.cls[0].item())
                        confidence = float(box.conf[0].item())
                        class_name = model.names[class_id]
                        
                        if class_name in frame_classes:
                            frame_classes[class_name] += 1
                        else:
                            frame_classes[class_name] = 1
                        
                        # 获取边界框坐标
                        x1, y1, x2, y2 = [int(coord) for coord in box.xyxy[0].tolist()]
                        f.write(f"  - 物体: {class_name}, 置信度: {confidence:.2f}, 位置: ({x1}, {y1}, {x2}, {y2})\n")
                    
                    for class_name, count in frame_classes.items():
                        f.write(f"  共检测到 {count} 个 {class_name}\n")
                else:
                    f.write("  没有检测到物体\n")
            
            # 等待一小段时间
            time.sleep(0.5)
        
        # 保存总体统计数据
        with open(f"{results_dir}/summary.txt", "w", encoding="utf-8") as f:
            f.write("检测结果总体统计:\n")
            f.write(f"共处理 {frame_count} 帧图像\n")
            
            if class_counts:
                for class_name, count in class_counts.items():
                    f.write(f"共检测到 {count} 个 {class_name}\n")
            else:
                f.write("没有检测到任何物体\n")
        
        # 释放资源
        cap.release()
        
        print("\n检测结果统计:")
        if class_counts:
            for class_name, count in class_counts.items():
                print(f"  - 检测到 {count} 个 {class_name}")
        else:
            print("  没有检测到物体")
        
        print(f"\nOpenCV和YOLOv8集成验证成功！所有结果已保存到 {results_dir} 目录")
        return True
        
    except Exception as e:
        print(f"验证过程中出错: {e}")
        print("OpenCV和YOLOv8集成验证失败！")
        return False

if __name__ == "__main__":
    try:
        # 检查环境
        if not sys.platform.startswith('linux'):
            print("警告: 此脚本设计用于Linux环境（如树莓派），在其他平台上可能需要调整")
        
        # 默认捕获10帧，可通过命令行参数修改
        frames = 10
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            frames = int(sys.argv[1])
        
        # 验证OpenCV和YOLOv8集成
        verify_opencv_yolo(frames)
        
    except KeyboardInterrupt:
        print("\n验证被用户中断")
    finally:
        # 确保所有窗口都已关闭
        cv2.destroyAllWindows() 