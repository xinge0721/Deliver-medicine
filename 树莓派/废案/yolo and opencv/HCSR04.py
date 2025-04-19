# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import time


TRIG = 4
ECHO = 17
RED_LED = 26
pwm = None
INTERVAL = 5

def distanceInit():
	print('Distance Measurement In Progress')
	print('初始化GPIO引脚配置: TRIG={}, ECHO={}'.format(TRIG, ECHO))
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(TRIG,GPIO.OUT)
	GPIO.setup(ECHO,GPIO.IN)
	print('GPIO引脚初始化完成')


def distanceStart():
	# 发送trig信号，持续10us的方波脉冲
	print('开始发送超声波...')
	GPIO.output(TRIG,True)
	time.sleep(0.00001)
	GPIO.output(TRIG,False)

	# 等待低电平结束，然后记录时间
	print('等待ECHO引脚低电平结束...')
	while GPIO.input(ECHO) == 0:
		pass
	pulse_start = time.time()
	print('ECHO引脚变为高电平，时间: {}'.format(pulse_start))

	# 等待高电平结束，然后记录时间
	print('等待ECHO引脚高电平结束...')
	while GPIO.input(ECHO) == 1:
		pass
	pulse_end = time.time()
	print('ECHO引脚变为低电平，时间: {}'.format(pulse_end))

	# 距离(单位:m) = (pulse_end - pulse_start) * 声波速度 / 2
	# 声波速度取 343m/s
	#
	# 距离(单位:cm) = (pulse_end - pulse_start) * 声波速度 / 2 * 100
	# 即 (pulse_end - pulse_start) * 17150
	pulse_duration = pulse_end - pulse_start
	print('脉冲持续时间: {} 秒'.format(pulse_duration))
	distance = pulse_duration * 17150
	distance = round(distance,2)
	print('计算得出距离: {} 厘米'.format(distance))
	return distance


def ledStart():
	global pwm
	print('开始LED闪烁序列')
	GPIO.setup(RED_LED, GPIO.OUT)
	# 创建一个 PWM 实例，需要两个参数，第一个是GPIO端口号，这里我们用26号
	# 第二个是频率（Hz），频率越高LED看上去越不会闪烁，相应对CPU要求就越高，设置合适的值就可以
	pwm = GPIO.PWM(RED_LED,60)
	print('PWM初始化完成，频率: 60Hz')
	
	# 启用PWM，参数是占空比，范围：0.0<=占空比<=100.0
	pwm.start(0)
	print('PWM启动，初始占空比: 0')
	for i in range(3):
		print('开始第 {} 次亮度循环'.format(i+1))
		# 电流从小到大，LED由暗到亮
		for i in range(101):
			# 更改占空比
			pwm.ChangeDutyCycle(i)
			time.sleep(0.02)

		# 电流从大到小，LED由亮变暗
		for i in range(100,-1,-1):
			pwm.ChangeDutyCycle(i)
			time.sleep(0.02)
	print('LED闪烁序列完成')
	pwm.stop()


try:
	print("程序开始运行")
	print("ok")
	distanceInit()
	print('进入主循环')
	while True:
		print('\n--- 新的测量周期开始 ---')
		distance = distanceStart()
		print("Distance:{}cm".format(distance))
		if distance < 100:
			print('检测到距离小于100厘米，启动LED警示')
			ledStart()
		else:
			print('距离大于100厘米，无需触发LED')
		print('等待 {} 秒进行下一次测量...'.format(INTERVAL))
		time.sleep(INTERVAL)
except KeyboardInterrupt:
	print('\n程序被用户中断')
	if pwm != None:
		pwm.stop()
	GPIO.cleanup()
	print('GPIO资源已清理')

