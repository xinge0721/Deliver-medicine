#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派串口通信简易测试程序
适用于Ubuntu 20.04系统

这个程序用于测试串口通信，可以发送和接收数据。
用途：检测串口是否工作正常，测试与其他设备的通信。
"""

# 导入必要的库
import serial  # 用于串口通信的库，需要安装：pip install pyserial
import time    # 用于添加延时的库，是Python自带的

# 串口配置（全局变量）
PORT = "/dev/ttyUSB0"  # 默认串口设备路径。在Linux系统中，USB转串口通常是/dev/ttyUSB0
BAUDRATE = 115200      # 波特率，表示每秒传输的比特数，必须与接收设备一致

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

def send_hex_data(ser, hex_str):
    """
    发送十六进制数据到串口
    
    参数:
        ser: 串口对象，由setup_serial()函数返回
        hex_str: 十六进制字符串，例如 "FF 01 A2"，空格会被自动移除
    """
    # 移除所有空格，方便用户输入带空格的十六进制字符串
    hex_str = hex_str.replace(" ", "")
    
    try:
        # 将十六进制字符串转换为字节数据
        # 例如："FF01" 转换为 b'\xff\x01'
        data = bytes.fromhex(hex_str)
        
        # 发送数据到串口，write方法会返回发送的字节数
        bytes_sent = ser.write(data)
        
        # 打印发送信息，format(b, '02X')将每个字节转换为两位的十六进制字符串
        print(f"已发送 {bytes_sent} 字节: {' '.join(format(b, '02X') for b in data)}")
    except Exception as e:
        # 如果转换或发送出错，打印错误信息
        print(f"发送数据错误: {str(e)}")

def receive_data(ser):
    """
    从串口接收数据
    
    参数:
        ser: 串口对象，由setup_serial()函数返回
    
    返回:
        data: 接收到的数据（字节格式），如果没有数据或出错则返回None
    """
    try:
        # in_waiting 属性表示串口缓冲区中等待读取的字节数
        if ser.in_waiting > 0:  # 如果有数据可读
            # 读取所有可用数据
            data = ser.read(ser.in_waiting)
            if data:  # 如果读取到数据
                # 转换为十六进制显示，方便查看
                hex_data = ' '.join(format(b, '02X') for b in data)
                print(f"接收到 {len(data)} 字节: {hex_data}")
                return data  # 返回接收的数据
        # 如果没有数据可读，返回 None
        return None
    except Exception as e:
        # 如果读取出错，打印错误信息
        print(f"接收数据错误: {str(e)}")
        return None

def main():
    """
    主函数，程序的入口点
    显示菜单并处理用户的选择
    """
    # 设置串口
    ser = setup_serial()
    if not ser:  # 如果串口设置失败
        return   # 结束程序
    
    # 使用 try-finally 结构确保在程序结束时关闭串口
    try:
        # 无限循环，直到用户选择退出
        while True:
            # 显示菜单选项
            print("\n--- 串口测试工具 ---")
            print("1. 发送十六进制数据")
            print("2. 接收数据")
            print("3. 退出")
            
            # 获取用户输入
            choice = input("请选择功能 (1-3): ")
            
            # 根据用户选择执行不同操作
            if choice == "1":  # 发送数据
                hex_data = input("输入要发送的十六进制数据 (如 FF 01 A2): ")
                send_hex_data(ser, hex_data)  # 调用发送函数
                time.sleep(0.5)  # 等待发送完成，防止数据粘连
                
            elif choice == "2":  # 接收数据
                print("等待接收数据 (5秒)...")
                # 尝试接收10次，每次间隔0.5秒，总共约5秒
                for _ in range(10):  # _ 是一个惯用的临时变量名，表示我们不关心这个变量的实际值
                    data = receive_data(ser)
                    if data:  # 如果接收到数据
                        break  # 退出循环
                    time.sleep(0.5)  # 等待0.5秒再次尝试
                # 如果尝试结束后仍没有数据
                if not data:
                    print("未接收到数据")
                    
            elif choice == "3":  # 退出程序
                break  # 跳出while循环，程序将继续执行finally块
                
            else:  # 用户输入了无效选项
                print("无效选择，请重试")
                
    except KeyboardInterrupt:  # 捕获Ctrl+C按键中断
        print("\n程序已中断")
    finally:  # 无论如何，最后都要关闭串口
        ser.close()  # 关闭串口连接
        print("串口已关闭")

# 这是Python的标准写法，表示如果这个文件是直接运行的（而不是被导入的），则执行main()函数
if __name__ == "__main__":
    main()  # 调用主函数 