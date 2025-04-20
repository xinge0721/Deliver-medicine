import cv2
from ultralytics import YOLO
import time
import threading
import queue
import os
import serial
import numpy as np
from collections import defaultdict

# 设置环境变量禁用所有网络连接
os.environ['ULTRALYTICS_OFFLINE'] = '1'
os.environ['CURL_CA_BUNDLE'] = ''  # 禁用SSL验证
os.environ['no_proxy'] = '*'  # 禁用代理

# 在导入其他模块前禁用网络
import urllib.request
# 重写urlopen函数，防止任何网络请求
original_urlopen = urllib.request.urlopen
def offline_urlopen(url, *args, **kwargs):
    raise Exception("离线模式：禁止网络连接")
urllib.request.urlopen = offline_urlopen

# ================= 全局配置 =================
MODEL_PATH = "best.pt"  # 模型路径
NUM_THREADS = 3       # 线程数
FRAME_QUEUE_SIZE = 1  # 严格控制队列深度
PORT = '/dev/ttyUSB0'  # 串口端口
BAUDRATE = 115200       # 串口波特率
CONFIDENCE_THRESHOLD = 0.7  # 模型置信度阈值，越高越严格（范围0-1）
CENTER_OFFSET = 0  # 中心点校准值（像素），正值向右偏移，负值向左偏移
CENTER_MARGIN = 20  # 中心区域容错值（像素），越大中心区域容错越大
MAX_RETRY_COUNT = 2  # 未检测到有效数字时的最大重试次数

# 图片保存配置
SAVE_IMAGES = True  # 是否保存图片
SAVE_PATH = "captured_images"  # 图片保存路径
SAVE_DETECTION_RESULTS = True  # 是否保存标记了检测结果的图片

# 摄像头和图像处理参数
# 更高的分辨率可以提高识别准确性，但会增加处理时间
# 常用分辨率: 640x480(VGA), 1280x720(720p), 1920x1080(1080p)
CAMERA_WIDTH = 640  # 摄像头拍摄宽度（像素）
CAMERA_HEIGHT = 480  # 摄像头拍摄高度（像素）

# YOLO模型处理图像的大小
# 较小的尺寸处理更快，较大的尺寸准确度更高
# 常用值: 320, 416, 512, 640 (必须是32的倍数)
MODEL_IMAGE_SIZE = 320  # YOLO模型输入图像大小（像素）

# ================= 全局状态 =================
class GlobalState:
    """
    全局状态类 - 用于在多线程环境中共享和同步数据
    
    作用：
    在多个线程之间安全地共享数据，包括检测结果、帧计数和同步事件等。
    使用锁机制确保多线程访问共享数据时的安全性。
    """
    def __init__(self):
        """初始化全局状态对象"""
        # 首次检测到的数字，作为后续检测的参考
        self.first_detected_number = None
        
        # 线程同步事件，用于通知其他线程首次检测已完成
        # 当第一次成功检测到数字后，会设置此事件
        self.first_detection_completed = threading.Event()
        
        # 帧计数器，每次拍摄新照片时递增
        self.frame_counter = 0
        
        # 线程锁，用于保护共享资源的访问
        # 确保多线程环境下的数据安全
        self.lock = threading.Lock()
        
        # 当前活动帧ID，表示正在处理的帧
        # 只有活动帧的结果才会被保存
        self.active_frame_id = -1
        
        # 存储检测结果的嵌套字典
        # 结构: {帧ID: {线程ID: 检测结果列表}}
        # 使用defaultdict避免键不存在的问题
        self.results = defaultdict(dict)  # {frame_id: {thread_id: results}}

# ================= 图片保存函数 =================
def ensure_save_directory_exists():
    """
    确保图片保存目录存在，如果不存在则创建
    """
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
        print(f"创建图片保存目录: {SAVE_PATH}")

def save_image(frame, filename_prefix, detections=None):
    """
    保存图片，可选择是否标记检测结果
    
    参数:
        frame: 要保存的图像帧
        filename_prefix: 文件名前缀
        detections: 检测结果列表，如果不为None则在图像上标记检测框
    """
    if not SAVE_IMAGES:
        return
        
    ensure_save_directory_exists()
    
    # 生成时间戳用于文件命名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # 构建完整文件名
    filename = f"{SAVE_PATH}/{filename_prefix}_{timestamp}.jpg"
    
    # 如果需要标记检测结果
    if detections and SAVE_DETECTION_RESULTS:
        # 创建图像副本以便标记
        marked_frame = frame.copy()
        
        # 在图像上标记检测框和类别
        for det in detections:
            # 获取边界框
            x1, y1, x2, y2 = det['box']
            
            # 获取类别和置信度
            class_name = det['class']
            confidence = det['confidence']
            
            # 绘制矩形边界框
            color = (0, 255, 0)  # 绿色
            cv2.rectangle(marked_frame, (x1, y1), (x2, y2), color, 2)
            
            # 绘制类别标签
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(marked_frame, label, (x1, y1 - 10), 
                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 保存标记了检测结果的图像
        marked_filename = f"{SAVE_PATH}/{filename_prefix}_detected_{timestamp}.jpg"
        cv2.imwrite(marked_filename, marked_frame)
        print(f"已保存标记检测结果图片: {marked_filename}")
        
    # 保存原始图像
    cv2.imwrite(filename, frame)
    print(f"已保存原始图片: {filename}")
    
    return filename

# ================= 串口通信函数 =================
def send_serial_data(ser, data):
    """
    使用指定帧格式发送串口数据
    
    帧格式:
        帧头: 0xFF
        数据: 单字节数据
        帧尾: 0xEE
        
    参数:
        ser: 串口对象
        data: 要发送的数据(单字节字符或整数)
    """
    if isinstance(data, str):
        # 如果是字符串，转换为整数
        data_byte = ord(data[0]) if data else 0
    elif isinstance(data, bytes):
        # 如果是字节，直接获取值
        data_byte = data[0] if data else 0
    else:
        # 如果是整数，直接使用
        data_byte = data
    
    # 创建数据包: 帧头 + 数据 + 帧尾
    frame = bytes([0xFF, data_byte, 0xEE])
    
    # 发送数据包
    ser.write(frame)
    print(f"串口发送: 帧头[0xFF] 数据[{data_byte}] 帧尾[0xEE]")

# ================= 线程函数 =================
def processing_worker(thread_id, frame_queue, state, model=None):
    """
    YOLO处理线程函数 - 从队列获取图像并执行目标检测
    
    参数:
        thread_id: 线程ID，用于区分不同的处理线程
        frame_queue: 包含待处理图像的队列，线程从这里获取图片
        state: 全局状态对象，用于存储和共享检测结果
        model: YOLO模型实例（如果为None则创建新的）
    """
    # 打印线程启动信息
    print(f"YOLO处理器-{thread_id} 就绪")
    
    # 如果没有提供模型，则创建新模型
    # 模型用于执行图像识别
    if model is None:
        try:
            model = YOLO(MODEL_PATH)
            print(f"线程 {thread_id} 创建本地模型成功")
        except Exception as e:
            print(f"线程 {thread_id} 创建模型失败: {e}")
            return
    
    # 无限循环，持续处理队列中的图像
    while True:
        try:
            # 尝试从队列获取一帧图像和对应的帧ID
            # timeout=1表示如果1秒内没有获取到图像，则会抛出queue.Empty异常
            frame_id, frame = frame_queue.get(timeout=1)
            
            # 检查是否收到终止信号(-1表示需要结束线程)
            if frame_id == -1:  # 终止信号
                print(f"线程 {thread_id} 收到结束信号")
                break
            
            # 执行YOLO推理（目标检测）
            try:
                # conf: 置信度阈值，只有高于这个值的检测结果才会被保留
                # imgsz: 输入图像大小，使用全局设置的MODEL_IMAGE_SIZE
                # iou: 交并比阈值，用于非极大值抑制，避免重复检测
                # verbose: 是否打印详细信息
                results = model.predict(frame, conf=CONFIDENCE_THRESHOLD, imgsz=MODEL_IMAGE_SIZE, iou=0.45, verbose=False)
            except Exception as e:
                print(f"线程 {thread_id} 执行预测时出错: {e}")
                # 报告空结果
                with state.lock:
                    if frame_id == state.active_frame_id:
                        state.results[frame_id][thread_id] = []
                continue
            
            # 创建一个空列表，用于存储本次检测的所有结果
            detections = []
            
            # 解析YOLO返回的检测结果
            # results可能包含多个结果(多张图)，这里遍历每一个结果
            for r in results:
                # 获取所有检测到的边界框
                boxes = r.boxes
                
                # 遍历每一个检测到的边界框
                for box in boxes:
                    # 提取边界框坐标 (x1,y1是左上角坐标，x2,y2是右下角坐标)
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # 计算边界框中心点的X坐标 (用于后续判断物体在图像左侧还是右侧)
                    center_x = (x1 + x2) // 2
                    
                    # 提取置信度 (模型对该检测结果的确信程度，范围0-1)
                    conf = float(box.conf[0])
                    
                    # 提取类别ID (检测到的物体类别编号)
                    cls = int(box.cls[0])
                    
                    # 根据类别ID获取类别名称 (如"1", "2", "3"等，表示数字)
                    class_name = model.names[cls]
                    
                    # 将当前检测结果添加到检测列表中
                    # 包含类别、置信度、边界框和中心X坐标
                    detections.append({
                        'class': class_name,  # 类别名称，如"1", "2"等数字
                        'confidence': conf,   # 置信度，值越高表示越确信
                        'box': [x1, y1, x2, y2],  # 边界框坐标
                        'center_x': center_x  # 中心点X坐标，用于判断左右位置
                    })
            
            # 使用锁机制更新全局状态中的检测结果
            # 锁确保在多线程环境下安全地更新共享数据
            with state.lock:
                # 检查当前处理的帧是否仍然是活动帧
                # 这是为了避免处理已经过期的帧
                if frame_id == state.active_frame_id:
                    # 将当前线程的检测结果存入全局状态
                    state.results[frame_id][thread_id] = detections
                    print(f"帧[{frame_id}] 线程-{thread_id} 贡献 {len(detections)} 个检测")
            
            # 打印处理完成信息
            print(f"线程 {thread_id} 完成检测，发现 {len(detections)} 个对象")
            
        except queue.Empty:
            # 队列为空时的处理（超时未获取到图像）
            # 短暂等待后继续尝试获取
            time.sleep(0.001)
            continue
        except Exception as e:
            # 捕获并记录线程中的其他异常
            print(f"处理线程 {thread_id} 错误: {e}")
    
    # 线程结束时打印信息
    print(f"YOLO处理器-{thread_id} 结束")

# ================= 结果处理 =================
def apply_nms(detections, iou_threshold=0.5):
    """
    非极大值抑制实现，合并重叠的检测框
    
    作用：
    当同一个物体被多次检测到时，会产生多个重叠的检测框。
    这个函数通过保留置信度最高的检测框，删除与其重叠的其他框，来减少冗余。
    
    参数:
        detections: 检测结果列表，每个元素包含边界框信息
        iou_threshold: IOU阈值，高于此值的重叠框将被视为同一物体
        
    返回:
        过滤后的检测结果列表（去除了重叠的框）
    """
    # 如果没有检测结果，直接返回空列表
    if not detections:
        return []
    
    # 按置信度降序排序（保留置信度高的框）
    sorted_det = sorted(detections, key=lambda x: x['confidence'], reverse=True)
    
    # 用于存储保留的检测框
    keep = []
    
    # 当还有未处理的检测框时循环
    while sorted_det:
        # 取出置信度最高的框（列表的第一个元素）
        current = sorted_det.pop(0)
        # 将其添加到保留列表
        keep.append(current)
        
        # 计算剩余所有框与当前框的IOU，仅保留IOU小于阈值的框
        # （IOU小于阈值意味着两个框不重叠或重叠较少）
        sorted_det = [
            det for det in sorted_det
            if calculate_iou(current['center_x'], det['center_x']) < iou_threshold
        ]
    
    # 返回保留的检测框列表
    return keep

def calculate_iou(center1, center2, width=20):
    """
    简化版IOU计算（基于中心点区域）
    
    作用：
    判断两个检测框的中心点是否接近，接近意味着可能是同一物体。
    在这个应用中，我们只比较中心点X坐标，简化计算。
    
    参数:
        center1: 第一个检测框的中心X坐标
        center2: 第二个检测框的中心X坐标
        width: 中心点容许的最大距离
        
    返回:
        True如果两个中心点距离小于width，表示重叠；否则False
    """
    # 如果两个中心点的距离小于width，则认为它们可能是同一个物体
    return abs(center1 - center2) < width

def majority_vote(detections):
    """
    多数决投票机制，选择出现次数最多且置信度最高的类别
    
    作用：
    当多个线程或多次检测返回不同的结果时，
    使用投票机制选择出现频率最高或置信度最高的类别作为最终结果。
    
    参数:
        detections: 所有检测结果的列表
        
    返回:
        出现次数最多的类别，相同次数时选择置信度总和最高的；如果没有有效类别则返回None
    """
    # a. 如果没有检测结果，直接返回None
    if not detections:
        return None
        
    # b. 初始化类别统计字典，使用defaultdict避免键不存在的问题
    # 每个类别记录其出现次数和置信度总和
    class_stats = defaultdict(lambda: {'count': 0, 'total_conf': 0})
    
    # c. 遍历所有检测结果，统计每个类别的出现次数和总置信度
    for det in detections:
        cls = det['class']
        # 只处理数字类别（过滤掉非数字）
        if not cls.isdigit():
            continue
        
        # 累加当前类别的计数和置信度
        class_stats[cls]['count'] += 1
        class_stats[cls]['total_conf'] += det['confidence']
    
    # d. 如果没有有效的数字类别（全是非数字），返回None
    if not class_stats:
        return None
    
    # e. 找出出现次数最多的类别（可能有多个相同次数的类别）
    max_count = max(v['count'] for v in class_stats.values())
    # 获取所有出现次数等于max_count的类别
    candidates = [k for k, v in class_stats.items() if v['count'] == max_count]
    
    # f. 当有多个出现次数相同的类别时，选择置信度总和最高的类别
    return max(candidates, key=lambda x: class_stats[x]['total_conf'])

def check_digit_location(number, detections, frame_width, margin=None, offset=None):
    """
    检查特定数字在图像中的位置（左侧还是右侧）
    
    作用：
    确定检测到的特定数字在图像中的水平位置，以便判断机器人应该向左还是向右移动。
    
    参数:
        number: 要检查的数字（字符串）
        detections: 检测结果列表
        frame_width: 图像宽度（像素）
        margin: 中心区域容错值，如果为None则使用全局设置CENTER_MARGIN
        offset: 中心点校准值，如果为None则使用全局设置CENTER_OFFSET
        
    返回:
        0x00: 未找到匹配数字
        0x01: 数字在左侧
        0x02: 数字在右侧
    """
    # a. 检查参数有效性
    if not number or not detections:
        return 0x00  # 未找到匹配数字
    
    # b. 如果未指定margin或offset，使用全局设置
    if margin is None:
        margin = CENTER_MARGIN
    if offset is None:
        offset = CENTER_OFFSET
    
    # c. 计算校准后的图像中心和左右阈值
    # 使用偏移值调整中心点位置
    center_point = (frame_width // 2) + offset  # 校准后的中心点X坐标
    left_threshold = center_point - margin  # 左侧阈值
    right_threshold = center_point + margin  # 右侧阈值
    
    # d. 在所有检测结果中寻找匹配的数字
    for det in detections:
        if det['class'] == number:
            center_x = det['center_x']  # 获取该数字的中心X坐标
            
            # e. 判断数字位置，考虑中心误差
            if center_x < left_threshold:
                # 数字在左侧阈值以外
                print(f"  找到匹配的数字 {number} 在左侧 (x={center_x}, 中心点={center_point}, 偏移={offset})")
                return 0x01  # 左侧
            elif center_x > right_threshold:
                # 数字在右侧阈值以外
                print(f"  找到匹配的数字 {number} 在右侧 (x={center_x}, 中心点={center_point}, 偏移={offset})")
                return 0x02  # 右侧
            else:
                # 数字在中心区域（在左右阈值之间）
                print(f"  找到匹配的数字 {number} 在中心区域 (x={center_x}, 中心点={center_point}, 偏移={offset})")
                # 在中心区域时，根据是否靠近中心点左侧或右侧来判断
                return 0x01 if center_x <= center_point else 0x02
    
    # f. 未在检测结果中找到匹配的数字
    print(f"  未发现与参考数字 {number} 匹配的对象")
    return 0x00  # 没有匹配的数字

def print_detection_details(detections, stage, frame_width=None, reference_number=None):
    """
    打印检测结果的详细信息
    
    作用：
    将检测结果以格式化方式打印到控制台，方便调试和监控。
    可以显示每个检测对象的类别、置信度、位置和与参考数字的匹配情况。
    
    参数:
        detections: 检测结果列表
        stage: 检测阶段的描述，如"首次"或"后续"
        frame_width: 图像宽度，用于确定对象位置（左侧或右侧）
        reference_number: 参考数字，用于比较是否匹配
    """
    # 1. 打印标题，显示检测阶段和检测到的对象数量
    print(f"\n----- {stage}检测的所有对象 ({len(detections)}个) -----")
    
    # 2. 如果没有检测到对象，打印提示信息并返回
    if not detections:
        print("  未检测到任何对象")
        return
        
    # 3. 逐个打印每个检测结果的详细信息
    for i, det in enumerate(detections):
        # 获取检测对象的基本信息
        class_name = det['class']    # 类别名称
        confidence = det['confidence']  # 置信度
        center_x = det['center_x']   # 中心点X坐标
        
        # 初始化位置和匹配信息
        position = ""  # 将存储"左侧"或"右侧"
        match = ""     # 将存储"匹配"或"不匹配"
        
        # 4. 如果提供了图像宽度，确定对象在图像中的位置
        if frame_width:
            position = "左侧" if center_x < frame_width//2 else "右侧"
        
        # 5. 如果提供了参考数字，确定是否匹配
        if reference_number:
            match = "匹配" if class_name == reference_number else "不匹配"
            
        # 6. 打印当前检测对象的详细信息
        print(f"  对象 {i+1}: 类别={class_name}, 置信度={confidence:.4f}, 中心X={center_x}, {position} {match}")
    
    # 7. 打印所有检测到的类别集合（去重）
    all_classes = set(det['class'] for det in detections)
    print(f"检测到的所有类别: {all_classes}")

def capture_single_frame():
    """
    临时打开摄像头，拍摄一张照片后立即关闭
    （核心原因就是一直打开摄像头，会出现极大的延迟，延迟会打到十秒左右，难以消除）
    
    作用：
    快速拍摄一张照片并返回，而不是保持摄像头开启。
    这种方式可以减少资源占用，适合拍照-处理-拍照的工作流程。
    
    返回:
        frame: 拍摄的照片帧（numpy数组）
        frame_width: 照片的宽度（像素）
        
    如果拍摄失败，返回(None, 0)
    """
    try:
        # 1. 初始化摄像头（打开默认摄像头，设备号0）
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("无法打开摄像头！")
            return None, 0
        
        # 2. 设置摄像头参数
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)  # 设置宽度
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT) # 设置高度
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # 设置视频编码格式
        
        # 3. 获取摄像头实际宽度（可能与设置值不同）
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        
        # 4. 丢弃前几帧（让摄像头适应光线和对焦）
        for _ in range(5):
            cap.read()
            time.sleep(0.05)  # 每帧间短暂延时
        
        # 5. 拍摄照片
        ret, frame = cap.read()
        
        # 6. 立即释放摄像头资源
        cap.release()
        
        # 7. 检查是否成功读取了帧
        if not ret:
            print("无法读取摄像头帧")
            return None, 0
            
        # 8. 返回拍摄的照片和宽度
        print(f"成功拍摄照片，大小：{frame.shape}")
        return frame, frame_width
        
    except Exception as e:
        # 捕获并记录所有异常
        print(f"拍摄照片时发生错误: {e}")
        try:
            # 确保摄像头资源被释放
            if cap and cap.isOpened():
                cap.release()
        except:
            pass
        return None, 0

# ================= 主逻辑 =================
def main():
    """
    主函数 - 初始化设备，启动线程，等待串口信号，协调检测流程
    
    作用：
    作为程序的入口点，协调整个系统的运行。
    初始化所有组件，创建线程，处理串口通信，协调检测过程。
    """
    
    # 创建图片保存目录
    if SAVE_IMAGES:
        ensure_save_directory_exists()
    
    # 初始化全局状态对象，用于线程间共享数据
    state = GlobalState()
    
    # 尝试连接串口设备
    try:
        print(f"尝试连接串口: {PORT}")
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,    # 8位数据位
            parity=serial.PARITY_NONE,    # 无校验
            stopbits=serial.STOPBITS_ONE, # 1位停止位
            timeout=1                     # 读超时（秒）
        )
        print("串口连接成功")
    except Exception as e:
        print(f"串口连接失败: {e}")
        return
    
    # 加载YOLO模型（为每个线程创建一个独立的模型实例）
    try:
        print("正在加载YOLO模型...")
        # 确认模型文件存在
        if not os.path.exists(MODEL_PATH):
            print(f"错误：模型文件 {MODEL_PATH} 不存在！")
            return
            
        models = []
        for i in range(NUM_THREADS):
            try:
                # 离线加载模型
                model = YOLO(MODEL_PATH)
                models.append(model)
                print(f"线程 {i+1} 模型加载成功")
            except Exception as e:
                print(f"线程 {i+1} 模型加载失败: {e}")
                return
        
        if not models:
            print("所有模型加载失败，程序退出")
            return
    except Exception as e:
        print(f"加载模型时出错: {e}")
        return
    
    # 打印模型的类别信息（帮助调试）
    print("\n===== YOLO模型类别信息 =====")
    model_classes = models[0].names
    print(f"模型包含 {len(model_classes)} 个类别:")
    for idx, class_name in model_classes.items():
        print(f"  类别ID {idx}: {class_name}")
    print("=============================\n")
    
    # 预热YOLO模型（第一次推理通常较慢，预热可以减少实际使用时的延迟）
    dummy_img = np.zeros((MODEL_IMAGE_SIZE, MODEL_IMAGE_SIZE, 3), dtype=np.uint8)  # 创建空白图像
    print("预热YOLO模型...")
    for model in models:
        model.predict(dummy_img, conf=CONFIDENCE_THRESHOLD, imgsz=MODEL_IMAGE_SIZE)
    
    # 创建线程通信队列 - 每个处理线程一个队列
    # 队列用于将图像数据从主线程传递给处理线程
    frame_queues = [queue.Queue(maxsize=FRAME_QUEUE_SIZE) for _ in range(NUM_THREADS)]
    
    # 创建并启动YOLO处理线程
    threads = []
    for i in range(NUM_THREADS):
        thread_id = i + 1  # 线程ID从1开始计数
        # 创建线程，指定目标函数和参数
        processor = threading.Thread(
            target=processing_worker, 
            args=(thread_id, frame_queues[i], state, models[i])
        )
        processor.daemon = True  # 设置为守护线程，主线程结束时自动终止
        processor.start()  # 启动线程
        threads.append(processor)  # 添加到线程列表，便于后续管理
    
    try:
        print("等待串口信号...")
        
        # 主循环：持续等待串口信号并处理
        while True:
            # 读取串口数据（最多4字节）
            data = ser.read(4)
            
            # 检查是否接收到指定信号
            if data == b'\xAA\xAA\xAA\xAA':
                # 接收到四个0xAA字节，获取或更新参考数字
                print("收到串口信号[0xAA]，开始获取/更新参考数字...")
                
                # 无论先前是否已完成检测，都进行新的参考数字获取
                # 重置首次检测完成事件
                state.first_detection_completed.clear()
                
                retry_count = 0  # 初始化重试计数器
                final_number = None  # 初始化最终识别的数字
                
                # 重试循环，直到找到有效数字或达到最大重试次数
                while retry_count < MAX_RETRY_COUNT and final_number is None:
                    # 拍摄单帧照片
                    frame, frame_width = capture_single_frame()
                    if frame is None:
                        # 拍摄失败，增加重试计数
                        retry_count += 1
                        print(f"拍照失败，第 {retry_count}/{MAX_RETRY_COUNT} 次重试")
                        continue
                    
                    # 保存原始拍摄图片
                    save_image(frame, f"reference_attempt{retry_count}")
                    
                    # 更新帧状态（使用锁保护共享数据）
                    with state.lock:
                        # 递增帧计数器
                        state.frame_counter += 1
                        # 记录当前帧ID
                        current_frame_id = state.frame_counter
                        # 更新当前活动帧ID
                        state.active_frame_id = current_frame_id
                        # 为当前帧初始化结果存储空间
                        state.results[current_frame_id] = {}
                    
                    print(f"拍摄第 {current_frame_id} 张照片 (重试 {retry_count}/{MAX_RETRY_COUNT})")
                    
                    # 分发任务到各处理线程（每个线程处理同一张图像的副本）
                    for q in frame_queues:
                        q.put((current_frame_id, frame.copy()))
                    
                    # 等待所有线程完成检测 (最多等待5秒)
                    start_time = time.time()
                    all_completed = False
                    
                    # 等待循环，检查是否所有线程都完成了处理
                    while time.time() - start_time < 5:  # 最多等待5秒
                        with state.lock:  # 使用锁访问共享数据
                            # 检查是否所有线程都已经贡献了结果
                            if len(state.results[current_frame_id]) == NUM_THREADS:
                                all_completed = True
                                break
                        # 短暂休眠，避免过度消耗CPU
                        time.sleep(0.01)
                    
                    # 检查是否有未完成的线程
                    if not all_completed:
                        print(f"警告：等待超时，部分线程可能未完成检测")
                    
                    # 收集所有线程的检测结果
                    all_detections = []
                    with state.lock:  # 使用锁访问共享数据
                        # 遍历当前帧的所有线程结果
                        for thread_id, detections in state.results[current_frame_id].items():
                            print(f"合并线程 {thread_id} 的 {len(detections)} 个检测结果")
                            # 将线程检测结果添加到总列表
                            all_detections.extend(detections)
                    
                    # 应用非极大值抑制，合并重复检测
                    filtered_detections = apply_nms(all_detections)
                    
                    # 保存标记了检测结果的图片
                    save_image(frame, f"reference_detected{retry_count}", filtered_detections)
                    
                    # 打印检测结果摘要
                    print(f"\n===== 检测结果 (重试 {retry_count}/{MAX_RETRY_COUNT}) =====")
                    print(f"总共检测到 {len(all_detections)} 个原始对象，应用NMS后保留 {len(filtered_detections)} 个")
                    
                    # 打印首次检测结果的详细信息
                    print_detection_details(filtered_detections, f"参考数字获取(重试 {retry_count}/{MAX_RETRY_COUNT})")
                    
                    # 通过多数投票确定最佳数字
                    final_number = majority_vote(filtered_detections)
                    
                    if final_number:
                        # 找到有效数字，跳出重试循环
                        print(f"检测到有效数字: {final_number}，停止重试")
                        break
                    else:
                        # 未找到有效数字，增加重试计数
                        retry_count += 1
                        print(f"未检测到有效数字，第 {retry_count}/{MAX_RETRY_COUNT} 次重试")
                        # 如果还没达到最大重试次数，等待短暂时间后再次尝试
                        if retry_count < MAX_RETRY_COUNT:
                            time.sleep(0.5)  # 等待0.5秒再次尝试
                
                # 重试循环结束后的处理
                if final_number:
                    # 设置/更新参考数字（用于后续检测比对）
                    state.first_detected_number = final_number
                    # 设置首次检测完成事件
                    state.first_detection_completed.set()
                    print(f"参考数字更新为: {final_number}")
                    
                    # 发送完成信号到串口 - 成功时发送0xFE
                    send_serial_data(ser, 0xFE)
                    print(f"已发送参考数字更新成功信号(0xFE)，参考数字: {final_number}")
                else:
                    # 达到最大重试次数仍未找到有效数字
                    print(f"经过 {MAX_RETRY_COUNT} 次重试后仍未发现有效数字")
                    # 如果之前已经有参考数字，保留原参考数字
                    if state.first_detected_number:
                        print(f"保留原参考数字: {state.first_detected_number}")
                        state.first_detection_completed.set()
                    
                    # 发送失败信号 - 0x00
                    send_serial_data(ser, 0x00)
                    print("已发送参考数字更新失败信号(0x00)")
                
                print("=== 参考数字处理完成 ===")
                
            elif data == b'\xFF\xFF\xFF\xFF':
                # 接收到四个0xFF字节，进行普通识别但不更新参考数字
                print("收到串口信号[0xFF]，开始普通识别...")
                
                # 如果参考数字尚未设置，则提示错误
                if not state.first_detection_completed.is_set():
                    print("错误：尚未设置参考数字，无法进行识别！")
                    send_serial_data(ser, b'0')  # 发送错误信号
                    continue
                
                # 拍摄单帧照片
                frame, frame_width = capture_single_frame()
                if frame is None:
                    # 拍摄失败，发送错误信号
                    send_serial_data(ser, b'0')
                    continue
                
                # 保存原始拍摄图片
                save_image(frame, "recognition_original")
                
                # 更新帧状态（使用锁保护共享数据）
                with state.lock:
                    # 递增帧计数器
                    state.frame_counter += 1
                    # 记录当前帧ID
                    current_frame_id = state.frame_counter
                    # 更新当前活动帧ID
                    state.active_frame_id = current_frame_id
                    # 为当前帧初始化结果存储空间
                    state.results[current_frame_id] = {}
                
                print(f"拍摄第 {current_frame_id} 张照片进行普通识别")
                
                # 分发任务到各处理线程（每个线程处理同一张图像的副本）
                for q in frame_queues:
                    q.put((current_frame_id, frame.copy()))
                
                # 等待所有线程完成检测 (最多等待5秒)
                start_time = time.time()
                all_completed = False
                
                # 等待循环，检查是否所有线程都完成了处理
                while time.time() - start_time < 5:  # 最多等待5秒
                    with state.lock:  # 使用锁访问共享数据
                        # 检查是否所有线程都已经贡献了结果
                        if len(state.results[current_frame_id]) == NUM_THREADS:
                            all_completed = True
                            break
                    # 短暂休眠，避免过度消耗CPU
                    time.sleep(0.01)
                
                # 检查是否有未完成的线程
                if not all_completed:
                    print(f"警告：等待超时，部分线程可能未完成检测")
                
                # 收集所有线程的检测结果
                all_detections = []
                with state.lock:  # 使用锁访问共享数据
                    # 遍历当前帧的所有线程结果
                    for thread_id, detections in state.results[current_frame_id].items():
                        print(f"合并线程 {thread_id} 的 {len(detections)} 个检测结果")
                        # 将线程检测结果添加到总列表
                        all_detections.extend(detections)
                
                # 应用非极大值抑制，合并重复检测
                filtered_detections = apply_nms(all_detections)
                
                # 保存标记了检测结果的图片
                save_image(frame, "recognition_detected", filtered_detections)
                
                # 打印检测结果摘要
                print(f"\n===== 检测结果 =====")
                print(f"总共检测到 {len(all_detections)} 个原始对象，应用NMS后保留 {len(filtered_detections)} 个")
                
                # 打印后续检测的详细信息，包括位置和匹配状态
                print_detection_details(
                    filtered_detections, 
                    "识别", 
                    frame_width, 
                    state.first_detected_number
                )
                
                # 确定检测到的数字相对于图像中心的位置
                result = check_digit_location(
                    state.first_detected_number,  # 参考数字
                    filtered_detections,          # 当前检测结果
                    frame_width,                  # 图像宽度
                    CENTER_MARGIN,                 # 中心区域容错值
                    CENTER_OFFSET                 # 中心点校准值
                )
                
                # 发送结果到串口: 0(无匹配), 1(左侧), 2(右侧)
                send_serial_data(ser, result)
                
                # 显示检测比对结果
                print("\n=== 识别比对结果 ===")
                if result == 0x00:
                    # 处理未找到匹配数字的情况
                    if not state.first_detected_number:
                        print("参考数字为空，未能进行有效比对")
                    elif not filtered_detections:
                        print("当前帧未检测到任何对象，无法比对")
                    else:
                        print("检测到对象但没有匹配的数字，已发送: 0x00")
                elif result == 0x01:
                    # 数字在左侧
                    print(f"检测到数字 {state.first_detected_number} 在左侧，已发送: 0x01")
                else:
                    # 数字在右侧
                    print(f"检测到数字 {state.first_detected_number} 在右侧，已发送: 0x02")
                
                # 打印参考信息
                print(f"当前参考数字: {state.first_detected_number if state.first_detected_number else '无'}")
                print("===========================\n")
                
            # 短暂休眠，避免CPU过度使用
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        # 处理用户中断（Ctrl+C）
        print("用户中断")
    except Exception as e:
        # 处理其他异常
        print(f"主线程错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源和终止线程的收尾工作
        
        # 发送结束信号给所有线程
        for q in frame_queues:
            try:
                q.put((-1, None))  # 发送结束信号
            except:
                pass
        
        # 等待处理线程结束（最多等待1秒）
        for t in threads:
            t.join(timeout=1)
            
        # 关闭串口资源
        try:
            ser.close()
        except:
            pass
        
        print("程序已安全退出")

if __name__ == "__main__":
    try:
        print("\n===== YOLO离线检测系统启动 =====")
        print("模式: 完全离线")
        print(f"模型路径: {MODEL_PATH}")
        print(f"处理线程数: {NUM_THREADS}")
        print(f"串口设置: {PORT}, {BAUDRATE} 波特率")
        print(f"置信度阈值: {CONFIDENCE_THRESHOLD}")
        print(f"中心点校准: {CENTER_OFFSET}像素 (正值向右偏移，负值向左偏移)")
        print(f"中心区域容错: {CENTER_MARGIN}像素")
        
        print("\n串口通信协议:")
        print("接收命令: 0xAA,0xAA,0xAA,0xAA - 获取参考数字")
        print("         0xFF,0xFF,0xFF,0xFF - 执行位置识别")
        print("发送数据: [0xFF][数据][0xEE] 格式")
        print("发送值:   0xFE - 参考数字锁定成功")
        print("         0x00 - 参考数字锁定失败/未找到匹配数字")
        print("         0x01 - 数字在左侧")
        print("         0x02 - 数字在右侧")
        print("==================================\n")
        main()
    except Exception as e:
        print(f"程序执行错误: {e}")
        import traceback
        traceback.print_exc()
