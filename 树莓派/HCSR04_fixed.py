# -*- coding: utf-8 -*-
# 这行代码声明使用UTF-8编码，支持中文等特殊字符

import RPi.GPIO as GPIO  # 导入树莓派GPIO控制库，用于控制引脚
import time  # 导入时间库，用于实现延时功能
import numpy as np  # 导入numpy库，用于数学计算和数组操作
import serial  # 导入串口通信库，用于通过串口发送数据


# GPIO引脚配置（BCM编号）及对应的物理引脚说明
# BCM是树莓派的GPIO编号方式之一，物理引脚是板子上实际的引脚位置
# BCM 4 = 物理引脚 7
# BCM 17 = 物理引脚 11
# BCM 18 = 物理引脚 12
# BCM 27 = 物理引脚 13
# BCM 22 = 物理引脚 15
# BCM 23 = 物理引脚 16
# BCM 24 = 物理引脚 18
# BCM 25 = 物理引脚 22
# BCM 26 = 物理引脚 37

# 可根据需要修改以下引脚配置
TRIG = 18  # 触发引脚，BCM 18，物理引脚 12，用于发送超声波信号
ECHO = 24  # 回声引脚，BCM 24，物理引脚 18，用于接收返回的超声波信号
INTERVAL = 0.2  # 超声波测量间隔时间（秒），控制测量频率，适用于避障

# 串口通信参数设置
# 树莓派自带串口配置说明
# 树莓派3及更高版本: GPIO 14 (TX, 物理引脚8) 和 GPIO 15 (RX, 物理引脚10)
PORT = '/dev/ttyS0'  # 树莓派自带串口设备路径
BAUDRATE = 115200    # 波特率，表示每秒传输的比特数

# 串口发送格式控制（True: 文本格式, False: 十六进制数据包格式）
SERIAL_TEXT_MODE = True  # 调试开关，修改此值切换发送模式

# 初始化串口通信
def init_serial():
    """
    初始化串口通信函数
    
    尝试打开串口并设置参数
    
    返回:
        成功返回串口对象，失败返回None
    """
    try:
        # 创建串口对象，设置端口、波特率和超时时间
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        print(f"串口通信初始化成功: {PORT}, {BAUDRATE}波特率")
        return ser
    except Exception as e:
        # 如果初始化失败，打印错误信息
        print(f"串口初始化失败: {e}")
        return None

# 发送串口数据函数
def send_serial_data(ser, data):
    """
    通过串口发送数据
    
    参数:
        ser: 串口对象
        data: 要发送的数据
    
    返回:
        成功返回True，失败返回False
    """
    # 如果串口对象为None，直接返回失败
    if ser is None:
        return False
    
    try:
        # 限制距离上限为99.99cm
        if isinstance(data, float) and data > 99.99:
            data = 99.99
        elif isinstance(data, str) and "cm" in data:
            try:
                # 尝试提取距离值
                distance_str = data.split("：")[1].split("cm")[0]
                distance_float = float(distance_str)
                if distance_float > 99.99:
                    # 替换为99.99
                    data = data.replace(distance_str, "99.99")
            except:
                pass
                
        if SERIAL_TEXT_MODE:
            # 文本模式：使用GBK编码发送中文（GBK支持中文字符）
            ser.write(data.encode('gbk'))
        else:
            # 数据包模式：发送十六进制数据（用于与其他设备通信的特定协议）
            # 假设data是一个浮点数，表示距离，或者是包含距离信息的字符串
            distance_float = float(data.split("：")[1].split("cm")[0]) if isinstance(data, str) else float(data)
            
            # 确保距离不超过99.99cm
            if distance_float > 99.99:
                distance_float = 99.99
                
            # 分离整数部分和小数部分
            integer_part = int(distance_float)  # 取整数部分
            decimal_part = int((distance_float - integer_part) * 100)  # 小数点后两位，乘100转为整数
            
            # 数据位1：小数点前两位（取最后两位数字）
            data1 = integer_part % 100  # 取模100，确保只保留最后两位数字
            # 数据位2：小数点后两位
            data2 = decimal_part
            
            # 计算校验位：帧头+数据位1+数据位2的和取模256
            # 校验位用于检测数据传输是否出错
            checksum = (0xAA + data1 + data2) % 256
            
            # 构建数据包：帧头(0xAA) + 数据位1 + 数据位2 + 校验位 + 帧尾(0x55)
            # 0xAA和0x55是特定的起始和结束标记
            data_packet = bytes([0xAA, data1, data2, checksum, 0x55])
            ser.write(data_packet)  # 发送数据包
            
        return True  # 发送成功返回True
    except Exception as e:
        # 如果发送失败，打印错误信息
        print(f"串口发送失败: {e}")
        return False  # 发送失败返回False

# 改进的卡尔曼滤波器类
class AdaptiveKalmanFilter:
    """
    自适应卡尔曼滤波器类
    
    用于平滑超声波测量数据，减少噪声和异常值的影响
    具有自适应能力，可以根据测量数据的变化调整过滤参数
    """
    def __init__(self, process_variance, measurement_variance, estimated_measurement, max_change_percent=50):
        """
        初始化卡尔曼滤波器
        
        参数:
            process_variance: 过程噪声方差（反映状态变化的不确定性，值越大对变化响应越快）
            measurement_variance: 测量噪声方差（反映测量的不确定性，值越大表示测量越不准确）
            estimated_measurement: 初始估计值（通常使用第一次的测量值）
            max_change_percent: 最大允许变化百分比（超过此值可能认为是异常值）
        """
        # 过程噪声方差（反映状态变化的不确定性）
        self.process_variance = process_variance
        # 测量噪声方差（反映测量的不确定性）
        self.measurement_variance = measurement_variance
        # 估计误差协方差（反映估计的不确定性）
        self.estimated_measurement_covariance = measurement_variance
        # 当前状态估计（滤波器当前的最佳估计值）
        self.estimated_measurement = estimated_measurement
        # 历史测量值数组，用于异常值检测
        self.history = [estimated_measurement]
        # 最大允许变化百分比，用于判断异常值
        self.max_change_percent = max_change_percent
        # 固定参数备份，用于自适应调整时参考
        self.default_process_variance = process_variance
        
    def is_outlier(self, measurement):
        """
        检测异常值函数
        
        降低限制以适应真实环境变化，判断当前测量是否为异常值
        
        参数:
            measurement: 当前测量值
            
        返回:
            True表示是异常值，False表示不是异常值
        """
        # 如果历史数据不足，无法判断异常值
        if len(self.history) < 3:
            return False
            
        # 计算最近几次测量的均值和标准差
        # 如果历史数据量大于等于5，取最近5个数据；否则使用所有历史数据
        recent_mean = np.mean(self.history[-5:]) if len(self.history) >= 5 else np.mean(self.history)
        recent_std = np.std(self.history[-5:]) if len(self.history) >= 5 else np.std(self.history)
        
        # 设置更宽松的动态阈值，允许更大的变化
        # 只过滤掉非常极端的异常值，允许真实的环境变化（如遇到障碍物）
        threshold = max(15, recent_mean * 0.45)  # 阈值设为45%的均值或至少15cm，取较大值
        if recent_std > 0:
            # 使用5个标准差而不是3个，更加宽松
            threshold = max(threshold, 5 * recent_std)
            
        # 检查当前测量是否偏离太多（与均值的差值超过阈值）
        return abs(measurement - recent_mean) > threshold
        
    def get_adaptive_process_variance(self, measurement):
        """
        获取自适应过程噪声方差
        
        根据测量值变化调整过程噪声方差，使滤波器能更好地适应环境变化
        
        参数:
            measurement: 当前测量值
            
        返回:
            调整后的过程噪声方差
        """
        # 如果历史数据不足，无法计算变化率，返回默认值
        if len(self.history) < 2:
            return self.process_variance
            
        # 计算相对变化率（百分比）
        last_measurement = self.history[-1]
        if last_measurement == 0:  # 避免除零错误
            last_measurement = 0.001  # 设置一个极小的值避免除零
        change_rate = abs(measurement - last_measurement) / last_measurement * 100
        
        # 更敏感地响应变化
        if change_rate > self.max_change_percent:
            # 变化越大，增益越大，最多增加15倍（比原来10倍更高）
            gain = min(15, 1.5 + change_rate / self.max_change_percent)
            return self.default_process_variance * gain  # 增大过程噪声方差
        else:
            # 如果变化小，使用略高于默认值的参数，提高整体响应性
            return self.default_process_variance * 1.2  # 轻微增大过程噪声方差
        
    def update(self, measurement):
        """
        更新滤波器状态
        
        使用新的测量值更新卡尔曼滤波器的状态估计
        
        参数:
            measurement: 新的测量值
            
        返回:
            (filtered_value, is_outlier): 滤波后的值和是否为异常值的标志
        """
        # 异常值检测
        is_outlier = self.is_outlier(measurement)
        
        if is_outlier:
            # 对于异常值，增加向异常值方向调整的幅度
            # 因为可能是真实障碍物引起的，需要更快响应
            # 确定调整方向（向上或向下）
            direction = 1 if measurement > self.estimated_measurement else -1
            # 计算调整大小，为差值的15%，但最多不超过5厘米
            adjustment = min(abs(measurement - self.estimated_measurement) * 0.15, 5)
            # 按计算的方向和大小调整估计值
            self.estimated_measurement += direction * adjustment
            
            # 添加调整后的估计值到历史记录
            self.history.append(self.estimated_measurement)
            
            # 限制历史记录长度，避免占用过多内存
            if len(self.history) > 15:  # 减少历史数据长度，更快遗忘旧值
                self.history = self.history[-15:]
            
            # 限制距离不超过99.99cm
            final_value = min(self.estimated_measurement, 99.99)
            return final_value, True
            
        # 动态调整过程噪声方差，使滤波器适应环境变化
        self.process_variance = self.get_adaptive_process_variance(measurement)
            
        # 预测步骤 - 卡尔曼滤波的第一阶段
        # 预测误差协方差 = 上一时刻误差协方差 + 过程噪声方差
        prediction_covariance = self.estimated_measurement_covariance + self.process_variance
        
        # 更新步骤 - 卡尔曼滤波的第二阶段
        # 卡尔曼增益 = 预测误差协方差 / (预测误差协方差 + 测量噪声方差)
        # 卡尔曼增益决定了对新测量值的信任程度
        kalman_gain = prediction_covariance / (prediction_covariance + self.measurement_variance)
        # 更新状态估计 = 预测状态 + 卡尔曼增益 * (测量值 - 预测状态)
        # 这是卡尔曼滤波的核心公式，融合预测值和测量值
        self.estimated_measurement = self.estimated_measurement + kalman_gain * (measurement - self.estimated_measurement)
        # 更新误差协方差 = (1 - 卡尔曼增益) * 预测误差协方差
        # 更新对当前估计的不确定性
        self.estimated_measurement_covariance = (1 - kalman_gain) * prediction_covariance
        
        # 添加当前测量值到历史记录
        self.history.append(measurement)
        
        # 限制历史记录长度，避免占用过多内存
        if len(self.history) > 15:  # 减少历史数据长度，提高适应性
            self.history = self.history[-15:]
        
        # 限制距离不超过99.99cm
        final_value = min(self.estimated_measurement, 99.99)
        return final_value, False

# 初始化超声波传感器函数
def distanceInit():
    """
    初始化超声波距离测量
    
    设置GPIO模式和引脚方向，为超声波测量做准备
    """
    print('开始超声波距离测量')
    print('初始化GPIO引脚配置: TRIG={} (物理引脚 12), ECHO={} (物理引脚 18)'.format(TRIG, ECHO))
    # 设置GPIO模式为BCM编号方式
    GPIO.setmode(GPIO.BCM)
    # 设置TRIG引脚为输出模式，用于发送超声波
    GPIO.setup(TRIG,GPIO.OUT)
    # 设置ECHO引脚为输入模式，用于接收超声波回波
    GPIO.setup(ECHO,GPIO.IN)
    print('GPIO引脚初始化完成')


# 开始超声波测量函数
def distanceStart():
    """
    执行一次超声波距离测量
    
    发送超声波脉冲，测量回波时间，并计算距离
    
    返回:
        距离（厘米），如果测量无效则返回-1，最大值限制为99.99cm
    """
    # 发送trig信号，持续10us的方波脉冲
    GPIO.output(TRIG,True)  # 设置TRIG引脚为高电平
    time.sleep(0.00001)     # 持续10微秒
    GPIO.output(TRIG,False) # 将TRIG引脚设回低电平

    # 等待ECHO引脚变为低电平结束，然后记录时间
    start_time = time.time()  # 记录当前时间
    while GPIO.input(ECHO) == 0:  # 等待ECHO引脚变为高电平
        if time.time() - start_time > 0.1:  # 超时保护，避免无限等待
            return -1  # 如果超过0.1秒仍未响应，返回错误值
        pass
    pulse_start = time.time()  # 记录ECHO引脚变为高电平的时间

    # 等待ECHO引脚的高电平结束，然后记录时间
    start_time = time.time()  # 记录当前时间
    while GPIO.input(ECHO) == 1:  # 等待ECHO引脚变为低电平
        if time.time() - start_time > 0.1:  # 超时保护，避免无限等待
            return -1  # 如果超过0.1秒仍未结束，返回错误值
        pass
    pulse_end = time.time()  # 记录ECHO引脚变回低电平的时间

    # 距离(单位:m) = (pulse_end - pulse_start) * 声波速度 / 2
    # 声波速度取 343m/s
    #
    # 距离(单位:cm) = (pulse_end - pulse_start) * 声波速度 / 2 * 100
    # 即 (pulse_end - pulse_start) * 17150
    # 17150 = 343 * 100 / 2
    pulse_duration = pulse_end - pulse_start  # 计算脉冲持续时间
    distance = pulse_duration * 17150  # 计算距离（厘米）
    distance = round(distance,2)  # 四舍五入到小数点后两位
    
    # 基本有效性检查：HC-SR04测量范围一般为2-400cm
    if distance < 2 or distance > 400:
        # 返回-1表示无效测量（超出传感器正常测量范围）
        return -1
    
    # 限制最大距离为99.99cm
    distance = min(distance, 99.99)
    
    return distance  # 返回有效的距离值


try:
    # 主程序开始
    print("程序开始运行")
    # 初始化超声波传感器的GPIO引脚
    distanceInit()
    
    # 初始化串口通信
    serial_port = init_serial()
    
    print('进入持续测量循环，按Ctrl+C退出')
    print('启用改进型自适应卡尔曼滤波处理测量数据（避障优化版）')
    print(f'串口发送模式: {"文本格式" if SERIAL_TEXT_MODE else "十六进制数据包格式"}')
    print('距离测量上限: 99.99cm（超过此值将统一报告为99.99cm）')
    
    # 创建卡尔曼滤波器实例
    # 参数1：过程噪声方差 - 越大表示状态变化越剧烈，滤波器对变化响应越快
    # 参数2：测量噪声方差 - 越大表示测量越不准确，滤波器越不信任新测量值
    # 参数3：初始估计值 - 可以是第一次测量的值，作为滤波起点
    # 参数4：单次最大变化百分比 - 超过此值认为可能是突变
    
    # 获取有效的第一次测量值，作为滤波器的初始估计值
    first_measurement = -1  # 初始值设为-1（无效值）
    for _ in range(5):  # 尝试最多5次测量
        measurement = distanceStart()  # 执行一次测量
        if measurement != -1:  # 如果测量有效
            first_measurement = measurement  # 记录有效值
            break  # 退出循环
        time.sleep(0.1)  # 短暂等待后重试
        
    # 如果无法获得有效测量值，使用默认值
    if first_measurement == -1:
        first_measurement = 100  # 默认距离设为100厘米
    
    # 创建自适应卡尔曼滤波器对象
    kalman_filter = AdaptiveKalmanFilter(
        process_variance=0.05,  # 进一步增大过程噪声方差，提高对变化的响应速度
        measurement_variance=0.8,  # 降低测量噪声方差，更信任测量值
        estimated_measurement=first_measurement,  # 初始估计值
        max_change_percent=40  # 增加允许的单次变化百分比，适应避障场景
    )
    
    # 记录原始数据和滤波后数据，用于统计分析
    raw_data = []  # 存储原始测量值
    filtered_data = []  # 存储滤波后的值
    
    # 统计计数器
    count = 0  # 总测量次数
    outlier_count = 0  # 异常值计数
    
    # 主循环：持续测量距离
    while True:
        count += 1  # 测量次数加1
        distance = distanceStart()  # 执行一次超声波测量
        
        # 检查测量是否有效
        if distance == -1:
            print("[{}] 测量超时或无效，传感器可能未正确连接".format(count))
            continue  # 跳过本次循环，重新测量
            
        # 应用卡尔曼滤波，获取滤波后的距离值和是否为异常值的标志
        filtered_distance, is_outlier = kalman_filter.update(distance)
        
        # 标记异常值
        outlier_mark = "⚠️异常值" if is_outlier else ""  # 如果是异常值，添加警告标记
        if is_outlier:
            outlier_count += 1  # 异常值计数加1
        
        # 保存数据到数组，用于后续统计
        raw_data.append(distance)  # 保存原始测量值
        filtered_data.append(filtered_distance)  # 保存滤波后的值
        
        # 准备串口发送的数据
        if SERIAL_TEXT_MODE:
            # 文本模式：发送文本格式的距离信息
            serial_message = "当前距离为：{:.2f}cm\r\n".format(filtered_distance)
        else:
            # 数据包模式：发送浮点数距离值，函数内部会处理为数据包格式
            serial_message = filtered_distance
            
        # 通过串口发送数据
        send_serial_data(serial_port, serial_message)
        
        # 计算波动幅度（标准差）并显示测量结果
        # 当数据量足够（>10）时，计算最近10次测量的标准差
        if len(raw_data) > 10:
            # 计算原始数据和滤波后数据的标准差
            raw_std = np.std(raw_data[-10:])  # 原始数据的标准差
            filtered_std = np.std(filtered_data[-10:])  # 滤波后数据的标准差
            
            # 确保分母不为零，并限制改进百分比范围
            if raw_std > 0:
                # 计算滤波改进百分比 = (原始标准差 - 滤波后标准差) / 原始标准差 * 100%
                improvement = (raw_std - filtered_std) / raw_std * 100
                # 限制在-100%到99.9%之间，避免异常值
                improvement = max(-100, min(99.9, improvement))
                # 打印测量结果和改进百分比
                print("[{}] 原始: {:.2f}cm, 滤波后: {:.2f}cm, 波动减少: {:.1f}% {}".format(
                    count, distance, filtered_distance, improvement, outlier_mark))
            else:
                # 如果原始数据无波动（标准差为0），直接显示测量结果
                print("[{}] 原始: {:.2f}cm, 滤波后: {:.2f}cm, 原始数据无波动 {}".format(
                    count, distance, filtered_distance, outlier_mark))
        else:
            # 数据量不足时，只显示测量结果
            print("[{}] 原始: {:.2f}cm, 滤波后: {:.2f}cm {}".format(
                count, distance, filtered_distance, outlier_mark))
        
        # 等待指定的间隔时间后进行下一次测量
        time.sleep(INTERVAL)
        
# 捕获键盘中断异常（Ctrl+C）
except KeyboardInterrupt:
    # 用户中断程序时执行清理操作
    print('\n程序被用户中断')
    # 清理GPIO资源，释放引脚
    GPIO.cleanup()
    
    # 关闭串口连接
    if 'serial_port' in locals() and serial_port is not None:
        serial_port.close()
        print('串口通信已关闭')
        
    print('GPIO资源已清理')
    
    # 如果有足够的数据，显示统计信息
    if len(raw_data) > 2:
        print("\n数据统计:")
        # 计算并显示原始数据的平均值和标准差
        print("原始数据平均值: {:.2f}cm, 标准差: {:.2f}".format(
            np.mean(raw_data), np.std(raw_data)))
        # 计算并显示滤波后数据的平均值和标准差
        print("滤波后数据平均值: {:.2f}cm, 标准差: {:.2f}".format(
            np.mean(filtered_data), np.std(filtered_data)))
        
        # 计算整体波动减少百分比
        if np.std(raw_data) > 0:
            # 计算改进百分比 = (原始标准差 - 滤波后标准差) / 原始标准差 * 100%
            improvement = (np.std(raw_data) - np.std(filtered_data)) / np.std(raw_data) * 100
            # 限制在-100%到99.9%之间，避免异常值
            improvement = max(-100, min(99.9, improvement))
            print("整体波动减少: {:.1f}%".format(improvement))
        else:
            print("原始数据无波动")
            
        # 显示异常值统计
        print("检测到的异常值数量: {} (占比 {:.1f}%)".format(
            outlier_count, outlier_count/len(raw_data)*100 if len(raw_data) > 0 else 0))

