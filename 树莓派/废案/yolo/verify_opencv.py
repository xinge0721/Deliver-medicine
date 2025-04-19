#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import time
import os

print("开始验证OpenCV摄像头并保存图片...")

# 创建保存图片的目录
save_dir = "camera_images"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
    print(f"创建目录: {save_dir}")

# 检测是否支持GUI
has_gui_support = True
try:
    cv2.namedWindow("测试", cv2.WINDOW_NORMAL)
    cv2.destroyAllWindows()
    print("检测到GUI支持，将显示图像预览")
except cv2.error as e:
    has_gui_support = False
    print("未检测到GUI支持，将只保存图像而不显示预览")
    print(f"错误信息: {str(e)}")

# 打开默认摄像头（设备索引号0）
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("错误：无法打开摄像头")
    exit(1)

print("摄像头已打开，开始捕获图片...")
if has_gui_support:
    print("按'q'键退出程序")
    # 创建窗口
    cv2.namedWindow("摄像头预览", cv2.WINDOW_NORMAL)

# 捕获10张图片
for i in range(10):
    # 读取一帧画面
    ret, frame = cap.read()
    
    if not ret:
        print(f"错误：无法获取第{i+1}帧")
        break
    
    # 在画面上显示帧数（如果有GUI支持）
    if has_gui_support:
        cv2.putText(frame, f"Frame: {i+1}/10", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        # 显示到屏幕
        cv2.imshow("摄像头预览", frame)
    
    # 保存图片
    filename = f"{save_dir}/frame_{i+1}.jpg"
    cv2.imwrite(filename, frame)
    print(f"已保存图片: {filename}")
    
    # 等待一小段时间，并检查是否按下'q'键退出（如果有GUI支持）
    if has_gui_support:
        if cv2.waitKey(500) & 0xFF == ord('q'):
            print("用户中断程序")
            break
    else:
        # 如果没有GUI支持，使用time.sleep
        time.sleep(0.5)

# 释放资源
cap.release()
if has_gui_support:
    cv2.destroyAllWindows()

print("验证完成，共保存了图片在 camera_images 目录下")

# 持续显示模式（仅在有GUI支持时可选）
if has_gui_support:
    print("是否要进入持续显示模式？(Y/N)")
    choice = input().strip().lower()

    if choice == 'y':
        print("已进入持续显示模式，按'q'键退出")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("错误：无法打开摄像头")
            exit(1)
        
        cv2.namedWindow("持续显示", cv2.WINDOW_NORMAL)
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("错误：无法获取画面")
                break
            
            cv2.imshow("持续显示", frame)
            
            # 按'q'键退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("持续显示模式已退出") 