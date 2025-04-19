# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import time
import numpy as np
import serial  # 导入串口通信库


# GPIO引脚配置（BCM编号）及对应的物理引脚
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
TRIG = 18  # 触发引脚，BCM 18，物理引脚 12
ECHO = 24  # 回声引脚，BCM 24，物理引脚 18
INTERVAL = 0.2  # 超声波测量间隔时间（秒），适用于避障

# 串口通信参数
PORT = '/dev/ttyUSB0'  # 串口设备
BAUDRATE = 115200      # 波特率

# 初始化串口
def init_serial():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        print(f"串口通信初始化成功: {PORT}, {BAUDRATE}波特率")
        return ser
    except Exception as e:
        print(f"串口初始化失败: {e}")
        return None

# 发送串口数据
def send_serial_data(ser, data):
    if ser is None:
        return False
    
    try:
        # 使用GBK编码发送中文
        ser.write(data.encode('gbk'))
        return True
    except Exception as e:
        print(f"串口发送失败: {e}")
        return False

# 改进的卡尔曼滤波器
class AdaptiveKalmanFilter:
    def __init__(self, process_variance, measurement_variance, estimated_measurement, max_change_percent=50):
        # 过程噪声方差（反映状态变化的不确定性）
        self.process_variance = process_variance
        # 测量噪声方差（反映测量的不确定性）
        self.measurement_variance = measurement_variance
        # 估计误差协方差（反映估计的不确定性）
        self.estimated_measurement_covariance = measurement_variance
        # 当前状态估计
        self.estimated_measurement = estimated_measurement
        # 历史测量值
        self.history = [estimated_measurement]
        # 最大允许变化百分比
        self.max_change_percent = max_change_percent
        # 固定参数备份
        self.default_process_variance = process_variance
        
    def is_outlier(self, measurement):
        """检测异常值 - 降低限制以适应真实环境变化"""
        if len(self.history) < 3:
            return False
            
        # 最近几次测量的均值和标准差
        recent_mean = np.mean(self.history[-5:]) if len(self.history) >= 5 else np.mean(self.history)
        recent_std = np.std(self.history[-5:]) if len(self.history) >= 5 else np.std(self.history)
        
        # 设置更宽松的动态阈值，允许更大的变化
        # 只过滤掉非常极端的异常值，允许真实的环境变化（如遇到障碍物）
        threshold = max(15, recent_mean * 0.45)  # 增加阈值到45%或至少15cm
        if recent_std > 0:
            # 使用5个标准差而不是3个，更加宽松
            threshold = max(threshold, 5 * recent_std)
            
        # 检查当前测量是否偏离太多
        return abs(measurement - recent_mean) > threshold
        
    def get_adaptive_process_variance(self, measurement):
        """根据测量值变化调整过程噪声方差"""
        if len(self.history) < 2:
            return self.process_variance
            
        # 计算相对变化率
        last_measurement = self.history[-1]
        if last_measurement == 0:  # 避免除零错误
            last_measurement = 0.001
        change_rate = abs(measurement - last_measurement) / last_measurement * 100
        
        # 更敏感地响应变化
        if change_rate > self.max_change_percent:
            # 变化越大，增益越大，最多增加15倍（比原来10倍更高）
            gain = min(15, 1.5 + change_rate / self.max_change_percent)
            return self.default_process_variance * gain
        else:
            # 如果变化小，使用略高于默认值的参数，提高整体响应性
            return self.default_process_variance * 1.2
        
    def update(self, measurement):
        # 异常值检测
        is_outlier = self.is_outlier(measurement)
        
        if is_outlier:
            # 对于异常值，增加向异常值方向调整的幅度
            # 因为可能是真实障碍物引起的，需要更快响应
            direction = 1 if measurement > self.estimated_measurement else -1
            adjustment = min(abs(measurement - self.estimated_measurement) * 0.15, 5)  # 增加到15%，最多5厘米
            self.estimated_measurement += direction * adjustment
            
            # 添加调整后的估计值到历史记录
            self.history.append(self.estimated_measurement)
            
            # 限制历史记录长度
            if len(self.history) > 15:  # 减少历史数据长度，更快遗忘旧值
                self.history = self.history[-15:]
                
            return self.estimated_measurement, True
            
        # 动态调整过程噪声方差
        self.process_variance = self.get_adaptive_process_variance(measurement)
            
        # 预测步骤
        # 预测误差协方差 = 上一时刻误差协方差 + 过程噪声方差
        prediction_covariance = self.estimated_measurement_covariance + self.process_variance
        
        # 更新步骤
        # 卡尔曼增益 = 预测误差协方差 / (预测误差协方差 + 测量噪声方差)
        kalman_gain = prediction_covariance / (prediction_covariance + self.measurement_variance)
        # 更新状态估计 = 预测状态 + 卡尔曼增益 * (测量值 - 预测状态)
        self.estimated_measurement = self.estimated_measurement + kalman_gain * (measurement - self.estimated_measurement)
        # 更新误差协方差 = (1 - 卡尔曼增益) * 预测误差协方差
        self.estimated_measurement_covariance = (1 - kalman_gain) * prediction_covariance
        
        # 添加到历史记录
        self.history.append(measurement)
        
        # 限制历史记录长度
        if len(self.history) > 15:  # 减少历史数据长度，提高适应性
            self.history = self.history[-15:]
            
        return self.estimated_measurement, False

def distanceInit():
	print('开始超声波距离测量')
	print('初始化GPIO引脚配置: TRIG={} (物理引脚 12), ECHO={} (物理引脚 18)'.format(TRIG, ECHO))
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(TRIG,GPIO.OUT)
	GPIO.setup(ECHO,GPIO.IN)
	print('GPIO引脚初始化完成')


def distanceStart():
	# 发送trig信号，持续10us的方波脉冲
	GPIO.output(TRIG,True)
	time.sleep(0.00001)
	GPIO.output(TRIG,False)

	# 等待低电平结束，然后记录时间
	start_time = time.time()
	while GPIO.input(ECHO) == 0:
		if time.time() - start_time > 0.1:  # 超时保护
			return -1
		pass
	pulse_start = time.time()

	# 等待高电平结束，然后记录时间
	start_time = time.time()
	while GPIO.input(ECHO) == 1:
		if time.time() - start_time > 0.1:  # 超时保护
			return -1
		pass
	pulse_end = time.time()

	# 距离(单位:m) = (pulse_end - pulse_start) * 声波速度 / 2
	# 声波速度取 343m/s
	#
	# 距离(单位:cm) = (pulse_end - pulse_start) * 声波速度 / 2 * 100
	# 即 (pulse_end - pulse_start) * 17150
	pulse_duration = pulse_end - pulse_start
	distance = pulse_duration * 17150
	distance = round(distance,2)
	
	# 基本有效性检查：HC-SR04测量范围一般为2-400cm
	if distance < 2 or distance > 400:
		# 返回-1表示无效测量
		return -1
	
	return distance


try:
	print("程序开始运行")
	distanceInit()
	
	# 初始化串口
	serial_port = init_serial()
	
	print('进入持续测量循环，按Ctrl+C退出')
	print('启用改进型自适应卡尔曼滤波处理测量数据（避障优化版）')
	
	# 创建卡尔曼滤波器实例
	# 参数1：过程噪声方差 - 越大表示状态变化越剧烈
	# 参数2：测量噪声方差 - 越大表示测量越不准确
	# 参数3：初始估计值 - 可以是第一次测量的值
	# 参数4：单次最大变化百分比 - 超过此值认为可能是突变
	
	# 获取有效的第一次测量值
	first_measurement = -1
	for _ in range(5):  # 尝试最多5次
		measurement = distanceStart()
		if measurement != -1:
			first_measurement = measurement
			break
		time.sleep(0.1)
		
	if first_measurement == -1:
		first_measurement = 100  # 如果无法获得有效值，使用默认值
	
	kalman_filter = AdaptiveKalmanFilter(
		process_variance=0.05,  # 进一步增大过程噪声方差，提高对变化的响应速度
		measurement_variance=0.8,  # 降低测量噪声方差，更信任测量值
		estimated_measurement=first_measurement,
		max_change_percent=40  # 增加允许的单次变化百分比，适应避障场景
	)
	
	# 记录原始数据和滤波后数据
	raw_data = []
	filtered_data = []
	
	count = 0
	outlier_count = 0
	while True:
		count += 1
		distance = distanceStart()
		
		if distance == -1:
			print("[{}] 测量超时或无效，传感器可能未正确连接".format(count))
			continue
			
		# 应用卡尔曼滤波
		filtered_distance, is_outlier = kalman_filter.update(distance)
		
		# 标记异常值
		outlier_mark = "⚠️异常值" if is_outlier else ""
		if is_outlier:
			outlier_count += 1
		
		# 保存数据
		raw_data.append(distance)
		filtered_data.append(filtered_distance)
		
		# 准备串口发送的数据（使用GBK编码中文）
		serial_message = "当前距离为：{:.2f}cm\r\n".format(filtered_distance)
		send_serial_data(serial_port, serial_message)
		
		# 计算波动幅度（标准差）
		if len(raw_data) > 10:
			raw_std = np.std(raw_data[-10:])
			filtered_std = np.std(filtered_data[-10:])
			
			# 确保分母不为零，并限制改进百分比范围
			if raw_std > 0:
				improvement = (raw_std - filtered_std) / raw_std * 100
				improvement = max(-100, min(99.9, improvement))  # 限制在-100%到99.9%之间
				print("[{}] 原始: {:.2f}cm, 滤波后: {:.2f}cm, 波动减少: {:.1f}% {}".format(
					count, distance, filtered_distance, improvement, outlier_mark))
			else:
				print("[{}] 原始: {:.2f}cm, 滤波后: {:.2f}cm, 原始数据无波动 {}".format(
					count, distance, filtered_distance, outlier_mark))
		else:
			print("[{}] 原始: {:.2f}cm, 滤波后: {:.2f}cm {}".format(
				count, distance, filtered_distance, outlier_mark))
		
		time.sleep(INTERVAL)
except KeyboardInterrupt:
	print('\n程序被用户中断')
	GPIO.cleanup()
	
	# 关闭串口
	if 'serial_port' in locals() and serial_port is not None:
		serial_port.close()
		print('串口通信已关闭')
		
	print('GPIO资源已清理')
	
	# 如果有足够的数据，显示统计信息
	if len(raw_data) > 2:
		print("\n数据统计:")
		print("原始数据平均值: {:.2f}cm, 标准差: {:.2f}".format(
			np.mean(raw_data), np.std(raw_data)))
		print("滤波后数据平均值: {:.2f}cm, 标准差: {:.2f}".format(
			np.mean(filtered_data), np.std(filtered_data)))
		
		if np.std(raw_data) > 0:
			improvement = (np.std(raw_data) - np.std(filtered_data)) / np.std(raw_data) * 100
			improvement = max(-100, min(99.9, improvement))
			print("整体波动减少: {:.1f}%".format(improvement))
		else:
			print("原始数据无波动")
			
		print("检测到的异常值数量: {} (占比 {:.1f}%)".format(
			outlier_count, outlier_count/len(raw_data)*100 if len(raw_data) > 0 else 0))

