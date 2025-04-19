#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLOv8检测并通过串口发送结果
适用于Ubuntu 20.04系统
以二进制格式发送数据，适合STM32接收处理

这个程序用于：
1. 使用YOLOv8模型进行对象检测（如人、车等）
2. 将检测结果转换为二进制格式
3. 通过串口发送给STM32单片机
"""

# 导入必要的库
import serial  # 用于串口通信，需要安装: pip install pyserial
import time    # 用于添加延时
import cv2     # OpenCV库，用于图像处理，需要安装: pip install opencv-python
import numpy as np  # 数值计算库，需要安装: pip install numpy
import struct  # 用于处理二进制数据的库，Python标准库
from ultralytics import YOLO  # YOLOv8模型，需要安装: pip install ultralytics

# 串口配置（全局变量）
PORT = "/dev/ttyUSB0"  # 默认串口设备路径。在Linux系统中，USB转串口通常是/dev/ttyUSB0
BAUDRATE = 115200      # 波特率，必须与接收设备一致

# YOLO配置
MODEL_PATH = "yolov8n.pt"  # YOLOv8模型文件路径，yolov8n.pt是最小的模型
CONFIDENCE = 0.25       # 置信度阈值，只有高于此值的检测结果才会被处理
CAMERA_ID = 0           # 摄像头ID，通常内置摄像头为0，外接摄像头从1开始

# 帧格式常量（自定义通信协议）
FRAME_HEADER = b'\xAA\xBB'  # 帧头，2字节，用于标记数据包的开始
FRAME_FOOTER = b'\xCC\xDD'  # 帧尾，2字节，用于标记数据包的结束
DEVICE_ID = 0x01            # 设备ID，用于区分不同设备，这里是1号设备

def setup_serial():
    """
    设置并打开串口连接
    
    这个函数尝试打开指定的串口设备，并配置通信参数。
    如果成功，返回串口对象；如果失败，返回None。
    
    返回:
        ser: 串口对象，如果打开失败则返回None
    """
    try:
        # 创建一个串口对象，设置各种参数
        ser = serial.Serial(
            port=PORT,             # 串口设备路径
            baudrate=BAUDRATE,     # 波特率
            bytesize=serial.EIGHTBITS,  # 数据位，通常是8位
            parity=serial.PARITY_NONE,  # 校验位，通常是无校验
            stopbits=serial.STOPBITS_ONE,  # 停止位，通常是1位
            timeout=1              # 读取超时时间，单位是秒
        )
        # 如果成功打开，打印成功信息
        print(f"成功打开串口: {PORT} (波特率: {BAUDRATE})")
        return ser
    except Exception as e:
        # 如果出错（例如设备不存在或被占用），打印错误信息
        print(f"串口连接错误: {str(e)}")
        return None  # 返回None表示失败

def send_data(ser, data):
    """
    发送二进制数据到串口
    
    参数:
        ser: 串口对象，由setup_serial()函数返回
        data: 要发送的二进制数据
    
    返回:
        bytes_sent: 成功发送的字节数，如果发送失败则返回0
    """
    try:
        # 发送数据到串口，write方法会返回发送的字节数
        bytes_sent = ser.write(data)
        
        # 打印发送信息，将每个字节转换为两位的十六进制显示
        hex_data = ' '.join(format(b, '02X') for b in data)
        print(f"已发送 {bytes_sent} 字节: {hex_data}")
        
        return bytes_sent
    except Exception as e:
        # 如果发送出错，打印错误信息
        print(f"发送数据错误: {str(e)}")
        return 0

def format_detection_binary(results):
    """
    将检测结果格式化为紧凑的二进制格式，适合STM32处理
    
    二进制格式:
    - 帧头: 2字节 (0xAA 0xBB)
    - 设备ID: 1字节
    - 检测目标数量: 1字节
    - 对于每个检测目标:
      - 类别ID: 1字节
      - 置信度: 1字节 (0-255)
      - 边界框坐标: 8字节 (x1, y1, x2, y2各占2字节，归一化为0-65535)
    - 校验和: 1字节 (所有数据的异或结果)
    - 帧尾: 2字节 (0xCC 0xDD)
    
    参数:
        results: YOLOv8检测结果对象
        
    返回:
        binary_data: 格式化后的二进制数据
    """
    # 初始化一个空的字节数组，用于存储要发送的数据
    binary_data = bytearray()
    
    # 添加帧头 (2字节)，标记数据包的开始
    binary_data.extend(FRAME_HEADER)
    
    # 添加设备ID (1字节)
    binary_data.append(DEVICE_ID)
    
    # 收集所有检测对象
    detections = []
    
    # 处理每一帧的结果
    for r in results:
        boxes = r.boxes  # 获取所有检测到的对象的边界框
        
        for box in boxes:
            # 获取坐标 (像素值)
            x1, y1, x2, y2 = box.xyxy[0].tolist()  # xyxy格式：左上角和右下角坐标
            frame_height, frame_width = r.orig_shape  # 获取原始图像尺寸
            
            # 归一化坐标为0-1之间的值（方便传输和不同设备显示）
            x1 = x1 / frame_width
            y1 = y1 / frame_height
            x2 = x2 / frame_width
            y2 = y2 / frame_height
            
            # 获取置信度 (0-1范围)
            conf = float(box.conf[0])
            
            # 获取类别ID
            cls = int(box.cls[0])
            
            # 添加到检测列表
            detections.append((cls, conf, x1, y1, x2, y2))
    
    # 添加检测目标数量 (1字节，最多255个)
    detection_count = min(len(detections), 255)  # 确保不超过一个字节能表示的最大值
    binary_data.append(detection_count)
    
    # 添加每个检测目标的数据
    for cls, conf, x1, y1, x2, y2 in detections[:detection_count]:
        # 类别ID (1字节)
        binary_data.append(cls)
        
        # 置信度 (1字节, 转换到0-255范围)
        conf_byte = int(conf * 255)  # 将0-1的置信度映射到0-255
        binary_data.append(conf_byte)
        
        # 边界框坐标 (8字节, 每个坐标2字节, 范围0-65535)
        for coord in [x1, y1, x2, y2]:
            # 将0-1范围转换为0-65535 (2字节能表示的范围)
            coord_val = int(coord * 65535)
            # 添加坐标的两个字节 (高字节在前，低字节在后，即大端序)
            binary_data.append((coord_val >> 8) & 0xFF)  # 高8位
            binary_data.append(coord_val & 0xFF)        # 低8位
    
    # 计算校验和 (所有已添加数据的异或结果)
    # 校验和用于接收方确认数据完整性
    checksum = 0
    for b in binary_data:
        checksum ^= b  # ^= 是异或赋值运算符
    
    # 添加校验和 (1字节)
    binary_data.append(checksum)
    
    # 添加帧尾 (2字节)，标记数据包的结束
    binary_data.extend(FRAME_FOOTER)
    
    # 将bytearray转换为bytes类型返回
    return bytes(binary_data)

def main():
    """
    主函数，程序的入口点
    """
    print("正在初始化YOLOv8模型...")
    try:
        # 加载YOLO模型
        # 这一步需要下载模型文件，如果是第一次运行，会自动从网络下载
        model = YOLO(MODEL_PATH)
        print(f"成功加载模型: {MODEL_PATH}")
    except Exception as e:
        # 如果模型加载失败，打印错误信息并退出
        print(f"加载模型失败: {str(e)}")
        return
    
    # 设置串口
    ser = setup_serial()
    if not ser:  # 如果串口设置失败
        return   # 结束程序
    
    # 打开摄像头
    print(f"正在打开摄像头 ID: {CAMERA_ID}")
    cap = cv2.VideoCapture(CAMERA_ID)  # 创建一个VideoCapture对象
    
    if not cap.isOpened():  # 如果摄像头打开失败
        print("无法打开摄像头")
        ser.close()  # 关闭串口
        return       # 结束程序
    
    print("开始检测并发送结果...")
    print("数据格式: 二进制格式，适用于STM32解析")
    print("格式说明:\n  帧头(2字节) + 设备ID(1字节) + 目标数量(1字节) + [类别ID(1字节) + 置信度(1字节) + 坐标x1,y1,x2,y2(8字节)] + 校验和(1字节) + 帧尾(2字节)")
    
    # 使用 try-finally 结构确保在程序结束时释放资源
    try:
        # 无限循环，不断读取摄像头图像并处理
        while True:
            # 读取一帧图像
            ret, frame = cap.read()  # ret是读取是否成功的标志，frame是读取到的图像
            if not ret:  # 如果读取失败
                print("无法读取摄像头帧")
                break
            
            # YOLOv8检测
            # 将当前帧送入模型进行检测，conf是置信度阈值
            results = model(frame, conf=CONFIDENCE)
            
            # 格式化结果为二进制
            binary_data = format_detection_binary(results)
            
            # 发送结果
            if binary_data:  # 如果有检测结果
                send_data(ser, binary_data)
            
            # 显示检测结果（可选）
            # plot()方法会在图像上绘制检测框、类别名称和置信度
            annotated_frame = results[0].plot()
            cv2.imshow("YOLOv8 Detection", annotated_frame)  # 在窗口中显示带有标注的图像
            
            # 按 'q' 键退出
            # waitKey(1)等待1毫秒，如果有按键则返回键值，否则返回-1
            if cv2.waitKey(1) == ord('q'):  # ord('q')是字母q的ASCII码
                break
                
            # 控制发送频率
            time.sleep(0.1)  # 暂停0.1秒，避免CPU占用过高和数据发送过快
            
    except KeyboardInterrupt:  # 捕获Ctrl+C按键中断
        print("\n程序已中断")
    finally:  # 无论如何，最后都要释放资源
        # 释放资源
        cap.release()           # 释放摄像头
        cv2.destroyAllWindows() # 关闭所有OpenCV窗口
        ser.close()             # 关闭串口连接
        print("串口已关闭")

# 这是Python的标准写法，表示如果这个文件是直接运行的（而不是被导入的），则执行main()函数
if __name__ == "__main__":
    main()  # 调用主函数 