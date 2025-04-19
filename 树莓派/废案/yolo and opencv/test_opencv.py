#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试OpenCV是否安装成功
"""

import cv2
import numpy as np
import time
import os

def test_opencv_version():
    print(f"OpenCV版本: {cv2.__version__}")
    return True

def test_read_image():
    try:
        # 创建一个测试图像
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        img[:] = (255, 0, 0)  # 蓝色背景
        
        # 添加文字
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, 'OpenCV Test', (50, 150), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # 保存图像
        cv2.imwrite('opencv_test_image.jpg', img)
        print("成功创建测试图像: opencv_test_image.jpg")
        
        # 读取图像
        read_img = cv2.imread('opencv_test_image.jpg')
        if read_img is None:
            print("无法读取测试图像")
            return False
        
        print("成功读取测试图像")
        return True
    
    except Exception as e:
        print(f"图像读写测试失败: {e}")
        return False

def test_video_capture():
    try:
        # 尝试打开摄像头
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("无法打开摄像头，这在无头环境中是正常的")
            return True
        
        # 读取一帧
        ret, frame = cap.read()
        
        # 释放摄像头
        cap.release()
        
        if ret:
            # 保存帧
            cv2.imwrite('camera_test.jpg', frame)
            print("成功从摄像头捕获图像: camera_test.jpg")
        else:
            print("无法从摄像头读取帧，但摄像头已成功打开")
        
        return True
    
    except Exception as e:
        print(f"摄像头测试失败: {e}")
        print("这在无头环境中是正常的，不影响OpenCV的其他功能")
        return True  # 返回True因为这不是一个关键错误

def test_image_processing():
    try:
        # 创建测试图像
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        img[100:200, 100:200] = (0, 255, 0)  # 绿色方块
        
        # 应用高斯模糊
        blurred = cv2.GaussianBlur(img, (15, 15), 0)
        
        # 边缘检测
        edges = cv2.Canny(img, 100, 200)
        
        # 保存结果
        cv2.imwrite('original.jpg', img)
        cv2.imwrite('blurred.jpg', blurred)
        cv2.imwrite('edges.jpg', edges)
        
        print("图像处理测试成功")
        print("保存的测试文件: original.jpg, blurred.jpg, edges.jpg")
        return True
    
    except Exception as e:
        print(f"图像处理测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("OpenCV测试程序")
    print("=" * 50)
    
    start_time = time.time()
    
    tests = [
        ("OpenCV版本检查", test_opencv_version),
        ("图像读写测试", test_read_image),
        ("摄像头测试", test_video_capture),
        ("图像处理测试", test_image_processing)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n测试: {test_name}")
        print("-" * 30)
        result = test_func()
        print(f"结果: {'通过' if result else '失败'}")
        all_passed = all_passed and result
    
    end_time = time.time()
    
    print("\n" + "=" * 50)
    print(f"总测试用时: {end_time - start_time:.2f}秒")
    print(f"总体结果: {'全部通过' if all_passed else '存在失败项'}")
    print("=" * 50) 