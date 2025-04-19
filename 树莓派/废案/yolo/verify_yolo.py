#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from ultralytics import YOLO
import cv2

print("开始验证YOLOv8配置...")

# 检查1.jpg是否存在
if not os.path.exists("1.jpg"):
    print("错误: 未找到1.jpg文件，请确保该文件在脚本同一目录下")
    exit(1)

try:
    # 加载YOLOv8模型
    start_time = time.time()
    print("正在加载YOLOv8模型...")
    model = YOLO("yolov8n.pt")  # 使用最小的模型
    print(f"模型加载耗时: {time.time() - start_time:.2f}秒")

    # 读取图像
    img = cv2.imread("1.jpg")
    if img is None:
        print("错误: 无法读取1.jpg图像文件")
        exit(1)

    print(f"图像大小: {img.shape}")

    # 运行推理
    print("正在进行目标检测...")
    start_time = time.time()
    results = model(img)
    print(f"推理耗时: {time.time() - start_time:.2f}秒")

    # 处理结果
    result = results[0]
    detections = []
    
    for box in result.boxes:
        class_id = box.cls[0].item()
        class_name = model.names[int(class_id)]
        confidence = box.conf[0].item()
        if confidence > 0.5:  # 只保留置信度大于0.5的检测结果
            x1, y1, x2, y2 = [round(x) for x in box.xyxy[0].tolist()]
            detections.append({
                "class": class_name,
                "confidence": confidence,
                "box": [x1, y1, x2, y2]
            })
    
    print(f"检测到 {len(detections)} 个目标:")
    for i, det in enumerate(detections):
        print(f"  {i+1}. {det['class']} (置信度: {det['confidence']:.2f})")
        
    # 在图像上绘制检测结果
    for det in detections:
        box = det["box"]
        label = f"{det['class']} {det['confidence']:.2f}"
        color = (0, 255, 0)  # 绿色边框
        cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), color, 2)
        cv2.putText(img, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # 保存结果图像
    output_file = "result_yolo.jpg"
    cv2.imwrite(output_file, img)
    print(f"检测结果已保存到 {output_file}")
    
    print("YOLOv8验证成功！")

except Exception as e:
    print(f"验证过程中出错: {e}")
    print("YOLOv8验证失败！") 