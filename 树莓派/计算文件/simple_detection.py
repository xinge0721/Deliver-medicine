from ultralytics import YOLO
import cv2
import numpy as np
import time

def main():
    # 1. 加载YOLO模型
    print("正在加载模型...")
    model = YOLO("best.pt")
    print("模型加载完成")
    
    # 2. 配置识别参数
    confidence_threshold = 0.25
    
    # 3. 打开摄像头
    print("正在打开摄像头...")
    cap = cv2.VideoCapture(0)  # 尝试默认摄像头
    
    if not cap.isOpened():
        print("无法打开默认摄像头，尝试其他摄像头...")
        for camera_idx in [1, 2]:
            cap = cv2.VideoCapture(camera_idx)
            if cap.isOpened():
                print(f"成功打开摄像头 {camera_idx}")
                break
        
        if not cap.isOpened():
            print("无法打开任何摄像头，程序退出")
            return
    
    print("摄像头已打开，开始识别")
    print("按 'q' 键退出程序")
    print(f"模型类别: {model.names}")
    
    # 创建窗口
    cv2.namedWindow("检测结果", cv2.WINDOW_NORMAL)
    
    while True:
        # 4. 读取摄像头帧
        ret, frame = cap.read()
        if not ret:
            print("无法读取视频帧")
            break
        
        # 5. 目标识别
        results = model(frame, conf=confidence_threshold)
        
        # 6. 显示结果
        if len(results) > 0:
            # 在原始帧上绘制结果
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # 获取边界框坐标
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    
                    # 获取类别ID和置信度
                    cls_id = int(box.cls.cpu().numpy()[0])
                    conf = float(box.conf.cpu().numpy()[0])
                    
                    # 获取类别名称 - 直接使用模型的类别名称
                    class_name = model.names[cls_id]
                    
                    # 为不同类别设置不同颜色
                    colors = [(0, 255, 0), (0, 0, 255), (255, 0, 0), 
                              (255, 255, 0), (0, 255, 255), (255, 0, 255),
                              (128, 0, 255), (255, 128, 0), (0, 128, 255), (128, 128, 0)]
                    color = colors[cls_id % len(colors)]
                    
                    # 确保坐标在图像范围内
                    h, w = frame.shape[:2]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w-1, x2), min(h-1, y2)
                    
                    # 绘制边界框
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    # 绘制标签
                    label = f"{class_name}: {conf:.2f}"
                    
                    # 计算标签背景的尺寸
                    (text_width, text_height), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    
                    # 调整标签位置，确保不超出图像边界
                    if y1 < text_height + 10:
                        label_y1 = y1
                        label_y2 = y1 + text_height + 10
                        text_y = y1 + text_height + 5
                    else:
                        label_y1 = y1 - text_height - 10
                        label_y2 = y1
                        text_y = y1 - 5
                    
                    # 绘制标签背景
                    cv2.rectangle(frame, (x1, label_y1), (x1 + text_width + 10, label_y2), color, -1)
                    
                    # 绘制标签文字
                    cv2.putText(frame, label, (x1 + 5, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                               0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # 显示结果
        cv2.imshow("检测结果", frame)
        
        # 检测按键
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    print("程序已退出")

if __name__ == "__main__":
    main() 