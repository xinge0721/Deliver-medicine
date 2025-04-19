#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLOv8数字识别(0-9)并通过串口发送
超简化版本

这个程序用于：
1. 使用YOLOv8模型识别图像中的数字(0-9)
2. 将识别结果通过串口发送出去
3. 在屏幕上显示识别结果
"""

# 导入必要的库
import serial  # 用于串口通信，需要安装: pip install pyserial
import cv2     # OpenCV库，用于图像处理，需要安装: pip install opencv-python
from ultralytics import YOLO  # YOLOv8模型，需要安装: pip install ultralytics

# 串口配置（全局变量）
PORT = "/dev/ttyUSB0"  # 串口设备路径。在Linux系统中，USB转串口通常是/dev/ttyUSB0
BAUDRATE = 115200      # 波特率，必须与接收设备一致

# YOLO配置
MODEL_PATH = "yolov8n.pt"  # YOLOv8模型文件路径，yolov8n.pt是最小的模型

# 数字类别ID映射
# 注意：这是一个简化的映射，实际上YOLOv8默认使用COCO数据集，
# 其中的前10个类别并不是数字0-9，我们在这里用它们来模拟数字
DIGIT_CLASSES = {
    0: '0',  # person类别用作0（简化示例）
    1: '1',  # bicycle类别用作1
    2: '2',  # car类别用作2
    3: '3',  # motorcycle类别用作3
    4: '4',  # airplane类别用作4
    5: '5',  # bus类别用作5
    6: '6',  # train类别用作6
    7: '7',  # truck类别用作7
    8: '8',  # boat类别用作8
    9: '9',  # traffic light类别用作9
}

def main():
    """
    主函数，程序的入口点
    包含整个流程：初始化、识别、发送和显示
    """
    # 1. 初始化串口
    try:
        # 创建一个串口对象，设置波特率
        ser = serial.Serial(PORT, BAUDRATE)
        print(f"串口已打开: {PORT}")
    except Exception as e:
        # 如果串口打开失败，打印错误信息并退出
        print(f"串口错误: {e}")
        return

    # 2. 初始化YOLO模型
    # 这一步需要下载模型文件，如果是第一次运行，会自动从网络下载
    model = YOLO(MODEL_PATH)
    print("YOLO模型已加载")

    # 3. 打开摄像头
    # 参数0通常表示第一个摄像头（内置摄像头）
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():  # 如果摄像头打开失败
        print("无法打开摄像头")
        ser.close()  # 关闭串口
        return       # 结束程序

    print("开始识别数字并发送...")
    # 使用 try-finally 结构确保在程序结束时释放资源
    try:
        # 无限循环，不断读取摄像头图像并处理
        while True:
            # 读取一帧
            ret, frame = cap.read()  # ret是读取是否成功的标志，frame是读取到的图像
            if not ret:  # 如果读取失败
                break

            # YOLO检测
            # conf=0.5表示只保留置信度大于0.5的检测结果
            results = model(frame, conf=0.5)
            
            # 处理检测结果，只关注数字(0-9)
            digits_detected = []  # 用于存储检测到的数字
            
            # 遍历所有检测结果
            for r in results:
                boxes = r.boxes  # 获取所有检测框
                for box in boxes:
                    cls = int(box.cls[0])  # 获取类别ID
                    if cls in DIGIT_CLASSES:  # 只关注0-9的类别（对应COCO数据集的前10个类别）
                        conf = float(box.conf[0])  # 获取置信度
                        digits_detected.append((cls, conf))  # 添加到检测列表
            
            # 按置信度排序并提取数字
            # 将检测到的数字按置信度从高到低排序
            digits_detected.sort(key=lambda x: x[1], reverse=True)
            # 将所有检测到的数字拼接成一个字符串
            digit_string = ''.join([DIGIT_CLASSES[d[0]] for d in digits_detected])
            
            # 发送检测到的数字
            if digit_string:  # 如果检测到了数字
                print(f"检测到数字: {digit_string}")
                # 添加帧头(0xAA)和帧尾(0xBB)
                # 帧头和帧尾用于接收方识别数据包的开始和结束
                send_data = b'\xAA' + digit_string.encode() + b'\xBB'
                # 发送数据
                ser.write(send_data)
                # 打印发送的十六进制数据，便于调试
                print(f"已发送: {' '.join([format(b, '02X') for b in send_data])}")
            
            # 显示结果
            # plot()方法会在图像上绘制检测框、类别名称和置信度
            annotated_frame = results[0].plot()
            # 在窗口中显示带有标注的图像
            cv2.imshow("数字识别", annotated_frame)
            
            # 按q键退出
            # waitKey(1)等待1毫秒，如果有按键则返回键值，否则返回-1
            if cv2.waitKey(1) == ord('q'):  # ord('q')是字母q的ASCII码
                break
                
    except KeyboardInterrupt:  # 捕获Ctrl+C按键中断
        print("\n程序已中断")
    finally:  # 无论如何，最后都要释放资源
        cap.release()           # 释放摄像头
        cv2.destroyAllWindows() # 关闭所有OpenCV窗口
        ser.close()             # 关闭串口连接
        print("程序已结束")

# 这是Python的标准写法，表示如果这个文件是直接运行的（而不是被导入的），则执行main()函数
if __name__ == "__main__":
    main()  # 调用主函数 