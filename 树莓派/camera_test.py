#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
摄像头YOLO对象检测程序
"""

import cv2
import time
import numpy as np
from ultralytics import YOLO
import torch
import traceback

# YOLO模型路径
MODEL_PATH = "best.pt"  # 如果模型在其他位置，请修改这个路径

# ===== 使用OpenCV和YOLO进行对象检测 =====
def test_with_yolo():
    print("使用OpenCV和YOLO模型打开摄像头...")
    
    # 加载YOLO模型
    try:
        print(f"正在加载YOLO模型 (路径: {MODEL_PATH})...")
        import os
        # 检查模型文件是否存在
        if not os.path.exists(MODEL_PATH):
            print(f"错误: 模型文件 {MODEL_PATH} 不存在!")
            return
            
        model = YOLO(MODEL_PATH)
        print("YOLO模型加载成功")
        
        # 打印模型类别信息
        print("\n===== YOLO模型类别信息 =====")
        model_classes = model.names
        print(f"模型包含 {len(model_classes)} 个类别:")
        for idx, class_name in model_classes.items():
            print(f"  类别ID {idx}: {class_name}")
        print("=============================\n")
    except Exception as e:
        print(f"错误: 无法加载YOLO模型: {e}")
        traceback.print_exc()
        return
    
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    
    # 设置摄像头参数
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # 使用MJPG编码可能会更稳定
    
    if not cap.isOpened():
        print("错误: 无法打开摄像头!")
        return
    
    print("摄像头已打开，按'q'键退出")
    
    # 创建一个空白的全黑图像，用作显示窗口的初始图像
    blank_image = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.imshow('YOLO', blank_image)
    
    # 预热YOLO模型
    dummy_img = np.zeros((320, 320, 3), dtype=np.uint8)
    print("预热YOLO模型...")
    model.predict(dummy_img, conf=0.25, imgsz=320)
    
    # 等待摄像头初始化并丢弃前几帧
    print("等待摄像头初始化...")
    for _ in range(10):
        cap.read()
        time.sleep(0.05)
    
    def preprocess_frame(frame):
        """预处理帧以确保其适合YOLO推理"""
        if frame is None:
            return None
            
        # 确保帧不为空且尺寸合适
        if frame.size == 0 or frame.shape[0] <= 0 or frame.shape[1] <= 0:
            return None
            
        # 如果需要，调整图像大小为标准尺寸
        try:
            # 使用固定大小进行调整，避免resize错误
            frame = cv2.resize(frame, (640, 480))
            return frame
        except Exception as e:
            print(f"预处理帧时出错: {e}")
            return None
    
    try:
        frame_count = 0
        while True:
            # 读取一帧
            ret, frame = cap.read()
            frame_count += 1
            
            # 每10帧打印一次状态
            if frame_count % 10 == 0:
                print(f"已处理 {frame_count} 帧")
            
            if not ret:
                print("错误: 无法读取摄像头帧!")
                time.sleep(0.1)  # 短暂暂停后再尝试
                continue
            
            # 预处理帧
            processed_frame = preprocess_frame(frame)
            if processed_frame is None:
                print("警告: 获取到无效帧，跳过本次处理")
                cv2.imshow('YOLO', blank_image)  # 显示空白图像
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue
            
            # 复制一份显示用的帧
            display_frame = processed_frame.copy()
            
            try:
                # 降低置信度阈值以检测更多对象
                results = model.predict(processed_frame, conf=0.25, iou=0.45, verbose=True)
                
                # 解析检测结果并在图像上绘制
                detections = []
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        # 提取边界框坐标
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        # 计算边界框中心坐标
                        center_x = (x1 + x2) // 2
                        
                        # 提取置信度和类别
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        
                        # 获取类别名称
                        class_name = model.names[cls]
                        
                        # 在图像上绘制边界框
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        # 添加类别标签和置信度
                        label = f"{class_name}: {conf:.2f}"
                        cv2.putText(display_frame, label, (x1, y1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        # 添加到当前检测结果列表
                        detections.append({
                            'class': class_name,
                            'confidence': conf,
                            'box': [x1, y1, x2, y2],
                            'center_x': center_x
                        })
                
                # 打印检测结果
                if detections:
                    print(f"检测到 {len(detections)} 个对象:")
                    for det in detections:
                        print(f"  类别: {det['class']}, 置信度: {det['confidence']:.4f}")
                elif frame_count % 30 == 0:  # 每30帧在没检测到物体时打印一次提示
                    print("未检测到任何对象")
                
                # 显示帧
                cv2.imshow('YOLO', display_frame)
            except Exception as e:
                print(f"处理帧时发生错误: {e}")
                traceback.print_exc()  # 打印完整错误堆栈
                # 仍然显示原始帧
                cv2.imshow('YOLO', frame)
            
            # 按'q'键退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        # 释放资源
        cap.release()
        cv2.destroyAllWindows()
        print("摄像头已关闭")

# ===== 保存一张照片并进行检测 =====
def capture_and_detect():
    print("尝试使用OpenCV拍摄一张照片并进行YOLO检测...")
    
    # 加载YOLO模型
    try:
        print(f"正在加载YOLO模型 (路径: {MODEL_PATH})...")
        import os
        # 检查模型文件是否存在
        if not os.path.exists(MODEL_PATH):
            print(f"错误: 模型文件 {MODEL_PATH} 不存在!")
            return
            
        model = YOLO(MODEL_PATH)
        print("YOLO模型加载成功")
        
        # 打印模型类别信息
        print("\n===== YOLO模型类别信息 =====")
        model_classes = model.names
        print(f"模型包含 {len(model_classes)} 个类别:")
        for idx, class_name in model_classes.items():
            print(f"  类别ID {idx}: {class_name}")
        print("=============================\n")
    except Exception as e:
        print(f"错误: 无法加载YOLO模型: {e}")
        traceback.print_exc()
        return
    
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # 使用MJPG编码
    
    if not cap.isOpened():
        print("错误: 无法打开摄像头!")
        return
    
    # 等待摄像头初始化
    print("等待摄像头初始化...")
    time.sleep(2)
    
    # 丢弃前几帧（让摄像头稳定）
    for _ in range(10):
        cap.read()
        time.sleep(0.05)
    
    valid_frame = None
    max_attempts = 5
    
    # 尝试多次获取有效帧
    for attempt in range(max_attempts):
        print(f"尝试获取有效帧 (第 {attempt+1}/{max_attempts} 次)")
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0 and frame.shape[0] > 0 and frame.shape[1] > 0:
            valid_frame = frame.copy()
            break
        time.sleep(0.5)
    
    # 释放摄像头
    cap.release()
    
    if valid_frame is None:
        print("错误: 无法获取有效的摄像头帧!")
        return
    
    # 保存照片
    cv2.imwrite('yolo_detection_test.jpg', valid_frame)
    print("照片已保存为 'yolo_detection_test.jpg'")
    
    try:
        # 降低置信度阈值以检测更多对象
        results = model.predict(valid_frame, conf=0.25, iou=0.45, verbose=True)
        
        # 在图像上绘制检测结果
        detection_count = 0
        for r in results:
            boxes = r.boxes
            detection_count = len(boxes)
            for box in boxes:
                # 提取边界框坐标
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # 提取置信度和类别
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                
                # 获取类别名称
                class_name = model.names[cls]
                
                # 在图像上绘制边界框
                cv2.rectangle(valid_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # 添加类别标签和置信度
                label = f"{class_name}: {conf:.2f}"
                cv2.putText(valid_frame, label, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                print(f"检测到 {class_name}, 置信度: {conf:.4f}")
        
        if detection_count == 0:
            print("警告: 未检测到任何对象，这可能是因为:")
            print("1. 模型路径不正确")
            print("2. 模型与当前场景不匹配")
            print("3. 置信度阈值太高")
            print("4. 图像质量问题")
        
        # 保存带有检测结果的图像
        cv2.imwrite('yolo_detection_result.jpg', valid_frame)
        print("检测结果已保存为 'yolo_detection_result.jpg'")
        
        # 显示检测结果
        cv2.imshow('YOLO', valid_frame)
        print("按任意键关闭窗口...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"执行YOLO检测时发生错误: {e}")
        traceback.print_exc()  # 打印完整的错误堆栈
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print("摄像头YOLO对象检测程序")
    print("============================")
    print("1. 使用OpenCV和YOLO进行实时检测")
    print("2. 拍摄一张照片并进行YOLO检测")
    print("============================")
    
    choice = input("请选择测试方式 (1/2): ")
    
    if choice == '1':
        test_with_yolo()
    elif choice == '2':
        capture_and_detect()
    else:
        print("无效选择!") 