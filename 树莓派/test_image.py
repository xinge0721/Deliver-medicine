import cv2
from ultralytics import YOLO
import time
import threading
import queue
import os
import signal
import sys
import serial
import numpy as np
import json

# 全局变量定义
# ==========================================================
# 用于存储识别结果的全局变量，按线程ID分类
detection_results = {}
for thread_id in range(1, 4):  # 3个线程
    detection_results[thread_id] = {}

# 线程同步变量
detection_lock = threading.Lock()  # 用于保护检测结果写入的互斥锁
result_event = threading.Event()  # 用于通知主线程所有检测完成的事件

# 存储首次识别的标准结果
first_detected_number = None  # 第一次检测到的数字
first_detection_completed = False  # 标记是否已完成首次检测

# 串口配置
PORT = '/dev/ttyUSB0'  # Linux设备路径
BAUDRATE = 115200        # 常用波特率
# ==========================================================

def process_thread(thread_id, frame_queue, results_dict):
    """
    YOLO检测线程函数 - 从队列获取图像并执行目标检测
    
    参数:
        thread_id: 线程ID（1-3）
        frame_queue: 包含待处理图像的队列
        results_dict: 存储检测结果的字典，格式为{线程ID: [{类别, 置信度, 边界框},...]}
    """
    print(f"YOLO线程 {thread_id} 启动")
    while True:
        try:
            # 从输入队列获取一帧
            frame_index, frame = frame_queue.get()
            if frame_index == -1:  # 结束信号
                print(f"线程 {thread_id} 收到结束信号")
                break
                
            # 使用YOLO模型进行检测
            results = yolo_models[thread_id-1].predict(frame, conf=0.7, imgsz=320, iou=0.45, max_det=10)
            
            # 处理检测结果 - 提取关键信息
            current_detections = []
            if len(results) > 0:
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        # 提取边界框坐标
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # 计算边界框中心坐标
                        center_x = (x1 + x2) // 2
                        
                        # 提取置信度和类别
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        
                        # 获取类别名称
                        class_name = yolo_models[thread_id-1].names[cls]
                        
                        # 添加到当前检测结果列表
                        current_detections.append({
                            'class': class_name,
                            'confidence': conf,
                            'box': [x1, y1, x2, y2],
                            'center_x': center_x  # 添加中心x坐标用于后续位置判断
                        })
            
            # 使用互斥锁保护共享资源访问
            with detection_lock:
                # 保存此线程的检测结果
                results_dict[thread_id] = current_detections
                print(f"线程 {thread_id} 保存了 {len(current_detections)} 个检测结果到字典")
                
                # 检查是否所有线程都完成了检测 
                # 当所有三个线程的结果都保存后，设置事件
                if len([k for k in results_dict.keys() if k in [1, 2, 3]]) == 3:
                    print("所有线程检测完成，设置结果事件")
                    result_event.set()
                else:
                    print(f"等待其他线程完成检测... 当前已完成线程: {list(results_dict.keys())}")
                
            print(f"线程 {thread_id} 完成检测，发现 {len(current_detections)} 个对象")
            
        except queue.Empty:
            # 队列为空，短暂等待后继续
            time.sleep(0.001)
            continue
        except Exception as e:
            # 捕获并记录线程中的所有异常
            print(f"处理线程 {thread_id} 错误: {e}")
    
    print(f"YOLO线程 {thread_id} 结束")

def save_first_detection(all_detections, frame_width):
    """
    保存首次检测到的数字
    
    参数:
        all_detections: 所有检测到的对象列表
        frame_width: 图像宽度，用于记录参考值
    """
    global first_detected_number, first_detection_completed
    
    # 设置首次检测标志
    first_detection_completed = True
    
    # 如果没有检测到物体，不保存
    if not all_detections:
        print("首次检测未发现任何对象")
        return
    
    # 打印所有检测结果，不限于数字
    print("\n----- 首次检测的所有对象 -----")
    for i, det in enumerate(all_detections):
        class_name = det['class']
        confidence = det['confidence']
        box = det['box']
        print(f"  对象 {i+1}: 类别={class_name}, 置信度={confidence:.4f}, 位置={box}")
    
    # 找出置信度最高的数字
    max_conf = 0
    detected_number = None
    
    # 打印所有类别的名称，用于调试
    print("\n检查所有可能的类别:")
    all_classes = set()
    for det in all_detections:
        class_name = det['class']
        all_classes.add(class_name)
    print(f"检测到的所有类别: {all_classes}")
    
    # 遍历所有检测结果
    for det in all_detections:
        class_name = det['class']
        confidence = det['confidence']
        
        # 检查类别名是否为数字 - 采用尽可能宽松的判断
        try:
            # 尝试转换为数字，不限于0-9
            if class_name.isdigit() or (class_name.replace('.', '', 1).isdigit() and class_name.count('.') < 2):
                num_value = float(class_name)
                print(f"  有效数字类别: {class_name}, 置信度: {confidence:.4f}")
                if confidence > max_conf:
                    max_conf = confidence
                    detected_number = class_name
            else:
                print(f"  非数字类别: {class_name}")
        except ValueError:
            print(f"  无法转换为数字的类别: {class_name}")
    
    # 保存首次检测结果
    if detected_number:
        first_detected_number = detected_number
        print(f"首次检测选择了数字: {detected_number}，置信度: {max_conf:.4f} 作为参考")
    else:
        print("首次检测未发现有效数字，所有检测对象都不是数字类别")

def check_and_locate_number(all_detections, frame_width):
    """
    检查是否存在与首次检测相同的数字，并判断其位置
    
    参数:
        all_detections: 所有检测到的对象列表
        frame_width: 图像宽度，用于判断左右位置
        
    返回:
        0: 没有匹配的数字
        1: 匹配的数字在左侧
        2: 匹配的数字在右侧
    """
    global first_detected_number
    
    # 打印所有检测到的对象，不管是否匹配
    print("\n----- 后续检测的所有对象 -----")
    for i, det in enumerate(all_detections):
        class_name = det['class']
        confidence = det['confidence']
        box = det['box']
        center_x = det['center_x']
        position = "左侧" if center_x < frame_width//2 else "右侧"
        match = "匹配" if class_name == first_detected_number else "不匹配"
        print(f"  对象 {i+1}: 类别={class_name}, 置信度={confidence:.4f}, 位置={position}, {match}")
    
    if not first_detected_number or not all_detections:
        print(f"  没有参考数字或未检测到任何对象")
        return "0"
    
    # 图像中心位置
    center_threshold = frame_width // 2
    
    # 查找匹配数字并确定位置
    for det in all_detections:
        if det['class'] == first_detected_number:
            center_x = det['center_x']
            
            # 判断位置
            if center_x < center_threshold:
                print(f"  找到匹配的数字 {first_detected_number} 在左侧 (x={center_x})")
                return "1"  # 左侧
            else:
                print(f"  找到匹配的数字 {first_detected_number} 在右侧 (x={center_x})")
                return "2"  # 右侧
    
    print(f"  未发现与参考数字 {first_detected_number} 匹配的对象")
    return "0"  # 没有匹配的数字

def collect_all_detections(results_dict):
    """
    收集所有线程的检测结果到一个列表
    
    参数:
        results_dict: 包含所有线程检测结果的字典
        
    返回:
        所有线程检测到的对象列表
    """
    all_detections = []
    print(f"开始合并检测结果，字典包含 {len(results_dict)} 个线程的数据")
    for thread_id, detections in results_dict.items():
        print(f"合并线程 {thread_id} 的 {len(detections)} 个检测结果")
        all_detections.extend(detections)
    return all_detections

def main():
    """
    主函数 - 初始化设备，启动线程，等待串口信号，协调检测流程
    """
    global yolo_models, first_detection_completed, first_detected_number
    
    # 初始化串口
    try:
        print(f"尝试连接串口: {PORT}")
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,    # 8位数据位
            parity=serial.PARITY_NONE,    # 无校验
            stopbits=serial.STOPBITS_ONE, # 1位停止位
            timeout=1                     # 读超时
        )
        print("串口连接成功")
    except Exception as e:
        print(f"串口连接失败: {e}")
        return
    
    # 加载测试图像1.jpg
    print("加载测试图像1.jpg...")
    test_image = cv2.imread("1.jpg")
    if test_image is None:
        print("无法读取1.jpg，请确保文件存在")
        return
    
    # 获取图像宽度
    frame_width = test_image.shape[1]
    print(f"图像宽度: {frame_width} 像素")
    
    # 创建YOLO模型实例
    print("正在加载YOLO模型...")
    yolo_models = [
        YOLO("best.pt"),
        YOLO("best.pt"),
        YOLO("best.pt")
    ]
    
    # 打印模型的类别信息
    print("\n===== YOLO模型类别信息 =====")
    model_classes = yolo_models[0].names
    print(f"模型包含 {len(model_classes)} 个类别:")
    for idx, class_name in model_classes.items():
        print(f"  类别ID {idx}: {class_name}")
    print("=============================\n")
    
    # 预热YOLO模型
    dummy_img = np.zeros((320, 320, 3), dtype=np.uint8)
    
    print("预热YOLO模型...")
    for yolo in yolo_models:
        # 这个置信度最低0.7
        yolo.predict(dummy_img, conf=0.7, imgsz=320)
    
    # 创建线程通信队列 - 每个线程一个队列
    frame_queues = [queue.Queue(maxsize=5) for _ in range(3)]
    
    # 用于存储线程对象
    threads = []
    
    # 全局变量，用于存储当前处理的检测结果
    shared_results = {}
    
    try:
        print("等待串口信号...")
        frame_count = 0
        
        while True:
            # 清空共享结果字典
            shared_results.clear()
            # 重置事件
            result_event.clear()
            
            # 读取串口数据
            data = ser.read(4)
            
            # 检查是否接收到4个0xFF
            if data == b'\xFF\xFF\xFF\xFF':
                print("收到串口信号，开始处理图像...")
                
                # 使用1.jpg图像而不是摄像头捕获
                frame = test_image.copy()
                
                frame_count += 1
                print(f"处理1.jpg图像，第 {frame_count} 次")
                
                # 创建并启动新的线程来处理这一帧
                threads = []
                for i in range(3):
                    thread_id = i + 1
                    # 发送当前帧给每个处理线程
                    frame_queues[i].put((frame_count, frame.copy()))
                    
                    # 创建线程
                    processor = threading.Thread(target=process_thread, args=(thread_id, frame_queues[i], shared_results))
                    processor.daemon = True
                    processor.start()
                    threads.append(processor)
                
                # 等待所有线程完成检测 (最多等待15秒)
                print("等待所有线程完成检测...")
                if result_event.wait(timeout=15):
                    print("检测完成，开始处理结果")
                else:
                    print("警告：等待超时，部分线程可能未完成检测")
                
                # 打印原始共享结果
                print(f"\n===== 原始检测结果 =====")
                print(f"共享结果字典包含 {len(shared_results)} 个键: {list(shared_results.keys())}")
                for key, value in shared_results.items():
                    print(f"键 {key} 包含 {len(value)} 个检测结果")
                
                # 打印每个线程的检测结果
                print(f"\n===== 各线程检测结果 =====")
                for thread_id, detections in shared_results.items():
                    print(f"线程 {thread_id} 检测到 {len(detections)} 个对象:")
                    if len(detections) > 0:
                        for i, det in enumerate(detections):
                            class_name = det['class']
                            confidence = det['confidence']
                            box = det['box']
                            print(f"  对象 {i+1}:")
                            print(f"    - 类别: {class_name}")
                            print(f"    - 置信度: {confidence:.4f}")
                            print(f"    - 边界框: {box}")
                    else:
                        print("  未检测到任何对象")
                    print("----------------------------")
                
                # 收集所有线程的检测结果
                all_detections = []
                for thread_id, detections in shared_results.items():
                    all_detections.extend(detections)
                
                # 打印合并后的检测结果
                print(f"\n===== 合并检测结果 =====")
                detected_count = len(all_detections)
                print(f"总共检测到 {detected_count} 个对象")
                if detected_count > 0:
                    print("检测结果详细信息:")
                    for i, det in enumerate(all_detections):
                        class_name = det['class']
                        confidence = det['confidence']
                        box = det['box']
                        center_x = det['center_x']
                        print(f"对象 {i+1}:")
                        print(f"  - 类别: {class_name}")
                        print(f"  - 置信度: {confidence:.4f}")
                        print(f"  - 边界框: {box}")
                        print(f"  - 中心X坐标: {center_x}")
                        print(f"  - 位置: {'左侧' if center_x < frame_width//2 else '右侧'}")
                        print("----------------------------")
                print("=============================")
                
                # 处理首次检测或后续检测
                if not first_detection_completed:
                    # 首次检测 - 保存检测到的数字
                    save_first_detection(all_detections, frame_width)
                    
                    # 发送'0'表示首次检测完成
                    ser.write(b'0')
                    print("已发送首次检测完成信号")
                    print("=== 首次检测结果保存完成 ===")
                else:
                    # 后续检测 - 检查是否有匹配的数字并判断位置
                    result = check_and_locate_number(all_detections, frame_width)
                    
                    # 发送结果: 0(无匹配), 1(左侧), 2(右侧)
                    ser.write(result.encode('utf-8'))
                    
                    # 显示结果
                    print("\n=== 后续检测比对结果 ===")
                    if result == "0":
                        print("未检测到匹配的数字，已发送: 0")
                    elif result == "1":
                        print(f"检测到数字 {first_detected_number} 在左侧，已发送: 1")
                    else:
                        print(f"检测到数字 {first_detected_number} 在右侧，已发送: 2")
                    print(f"首次保存的参考数字: {first_detected_number}")
                    print("===========================\n")
            
            time.sleep(0.01)  # 防止CPU占用过高
            
    except KeyboardInterrupt:
        print("用户中断")
    except Exception as e:
        print(f"主线程错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 发送结束信号给所有线程
        for i in range(3):
            try:
                frame_queues[i].put((-1, None))  # 发送结束信号
            except:
                pass
        
        # 等待处理线程结束
        for t in threads:
            t.join(timeout=1)
            
        # 关闭资源
        try:
            if ser and ser.isOpen():
                ser.close()
        except:
            pass
        
        print("程序已安全退出")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序执行错误: {e}")
        import traceback
        traceback.print_exc() 