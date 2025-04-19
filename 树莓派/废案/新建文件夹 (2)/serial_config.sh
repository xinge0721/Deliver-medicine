#!/bin/bash
# 树莓派串口配置一键脚本 (Ubuntu 20.04, ARM64)
# 功能：配置树莓派串口，安装所需的串口通信库

# 彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}         树莓派串口配置一键脚本 (Ubuntu 20.04, ARM64)         ${NC}"
echo -e "${BLUE}================================================================${NC}"

# 确保脚本以root权限运行
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}请以root权限运行此脚本:${NC}"
  echo -e "${YELLOW}sudo $0${NC}"
  exit 1
fi

# 检查系统
echo -e "\n${YELLOW}【第1步】检查系统...${NC}"

# 检查是否为ARM64架构
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" ]]; then
  echo -e "${RED}警告: 当前架构不是ARM64 (aarch64), 而是 $ARCH${NC}"
  echo -e "${YELLOW}此脚本专为树莓派 ARM64 设计，可能不适用于当前系统${NC}"
  read -p "是否继续? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}已取消操作${NC}"
    exit 1
  fi
fi

# 检查Ubuntu版本
if [ -f /etc/os-release ]; then
  . /etc/os-release
  if [[ "$VERSION_ID" != "20.04" ]]; then
    echo -e "${RED}警告: 当前系统不是Ubuntu 20.04, 而是 $PRETTY_NAME${NC}"
    echo -e "${YELLOW}此脚本专为Ubuntu 20.04设计，可能不适用于当前系统${NC}"
    read -p "是否继续? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${RED}已取消操作${NC}"
      exit 1
    fi
  else
    echo -e "${GREEN}✓ 系统为Ubuntu 20.04 ($PRETTY_NAME)${NC}"
  fi
else
  echo -e "${RED}无法确定操作系统版本${NC}"
  read -p "是否继续? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}已取消操作${NC}"
    exit 1
  fi
fi

# 安装依赖包
echo -e "\n${YELLOW}【第2步】安装必要依赖...${NC}"
apt-get update
apt-get install -y python3-serial python3-pip build-essential
echo -e "${GREEN}✓ 已安装基本依赖${NC}"

# 安装pyserial库
echo -e "\n${YELLOW}【第3步】安装Python串口库...${NC}"
pip3 install pyserial
echo -e "${GREEN}✓ 已安装pyserial库${NC}"

# 检测可用串口
echo -e "\n${YELLOW}【第4步】检测可用串口...${NC}"
if [ -d /dev/serial/by-id ]; then
  echo -e "${GREEN}可用串口设备:${NC}"
  ls -l /dev/serial/by-id
else
  echo -e "${YELLOW}没有找到串口设备 (/dev/serial/by-id)${NC}"
fi

echo -e "${GREEN}系统串口:${NC}"
ls -l /dev/ttyS* /dev/ttyAMA* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo -e "${YELLOW}未找到任何串口设备${NC}"

# 配置串口权限
echo -e "\n${YELLOW}【第5步】配置串口权限...${NC}"
# 添加当前用户到dialout组
username=$(logname)
if [ -z "$username" ]; then
  echo -e "${YELLOW}无法确定当前登录用户，请手动输入用户名:${NC}"
  read -p "用户名: " username
fi

if [ -n "$username" ]; then
  usermod -a -G dialout $username
  echo -e "${GREEN}✓ 已将用户 $username 添加到dialout组${NC}"
else
  echo -e "${RED}未指定用户名，无法设置权限${NC}"
fi

# 创建udev规则
echo -e "\n${YELLOW}【第6步】创建udev规则...${NC}"
cat > /etc/udev/rules.d/99-serial.rules << EOF
# 串口设备权限设置
KERNEL=="ttyS*", GROUP="dialout", MODE="0666"
KERNEL=="ttyACM*", GROUP="dialout", MODE="0666"
KERNEL=="ttyUSB*", GROUP="dialout", MODE="0666"
KERNEL=="ttyAMA*", GROUP="dialout", MODE="0666"
EOF
echo -e "${GREEN}✓ 已创建串口udev规则${NC}"

# 重新加载udev规则
echo -e "\n${YELLOW}【第7步】应用udev规则...${NC}"
udevadm control --reload-rules
udevadm trigger
echo -e "${GREEN}✓ 已应用udev规则${NC}"

# 创建测试脚本
echo -e "\n${YELLOW}【第8步】创建串口测试脚本...${NC}"
mkdir -p /home/$username/serial_test
cat > /home/$username/serial_test/serial_test.py << 'EOF'
#!/usr/bin/env python3
# 串口测试程序

import serial
import time
import sys
import glob
import os

def list_serial_ports():
    """列出所有可用的串口"""
    if sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # 这将匹配任何类型的串口
        ports = glob.glob('/dev/tty[A-Za-z]*')
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result
    else:
        raise EnvironmentError('不支持的操作系统')

def test_serial_port(port, baudrate=9600, timeout=1):
    """测试串口是否可用"""
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        ser.close()
        return True
    except:
        return False

# 主程序
if __name__ == "__main__":
    print("======= 串口测试程序 =======")
    
    # 列出可用串口
    print("\n发现的串口设备:")
    ports = list_serial_ports()
    
    if not ports:
        print("未找到可用串口设备")
        sys.exit(1)
    
    for i, port in enumerate(ports):
        status = "可用" if test_serial_port(port) else "不可用"
        print(f"{i+1}. {port} - {status}")
    
    # 选择一个串口进行测试
    try:
        choice = int(input("\n选择一个串口进行测试 (输入编号): ")) - 1
        if choice < 0 or choice >= len(ports):
            raise ValueError()
        test_port = ports[choice]
    except:
        print("无效选择，退出")
        sys.exit(1)
    
    # 选择波特率
    try:
        baudrate = int(input("\n输入波特率 (默认9600): ") or "9600")
    except:
        print("使用默认波特率9600")
        baudrate = 9600
    
    print(f"\n测试串口 {test_port} 波特率 {baudrate}...")
    
    try:
        ser = serial.Serial(test_port, baudrate, timeout=1)
        print(f"成功打开串口 {test_port}")
        
        # 发送测试数据
        test_data = b'Hello from Raspberry Pi\r\n'
        print(f"发送测试数据: {test_data}")
        ser.write(test_data)
        
        # 读取响应
        print("等待响应...")
        for i in range(5):  # 尝试5次
            response = ser.readline()
            if response:
                print(f"收到响应: {response}")
                break
            print(f"等待中... ({i+1}/5)")
            time.sleep(1)
        else:
            print("未收到响应")
        
        # 关闭串口
        ser.close()
        print("串口已关闭")
        
    except Exception as e:
        print(f"错误: {e}")
        
    print("\n======= 测试完成 =======")
EOF

cat > /home/$username/serial_test/send_data.py << 'EOF'
#!/usr/bin/env python3
# 串口发送数据程序

import serial
import time
import sys

def send_data(port, baudrate=9600, data=None):
    """通过串口发送数据"""
    try:
        # 打开串口
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"成功打开串口 {port}")
        
        if data is None:
            # 循环发送数据
            print("开始发送数据 (按Ctrl+C结束)...")
            count = 0
            try:
                while True:
                    message = f"测试数据 #{count}\r\n"
                    ser.write(message.encode('utf-8'))
                    print(f"发送: {message.strip()}")
                    count += 1
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n停止发送")
        else:
            # 发送指定数据
            print(f"发送数据: {data}")
            ser.write(data.encode('utf-8') if isinstance(data, str) else data)
            time.sleep(0.1)  # 等待数据发送完成
        
        # 关闭串口
        ser.close()
        print("串口已关闭")
        return True
    
    except Exception as e:
        print(f"错误: {e}")
        return False

# 主程序
if __name__ == "__main__":
    print("======= 串口发送数据程序 =======")
    
    if len(sys.argv) < 2:
        print("用法: python3 send_data.py <串口> [波特率] [数据]")
        print("例如: python3 send_data.py /dev/ttyUSB0 9600 'Hello'")
        sys.exit(1)
    
    port = sys.argv[1]
    
    baudrate = 9600
    if len(sys.argv) > 2:
        try:
            baudrate = int(sys.argv[2])
        except:
            print(f"波特率格式错误，使用默认值: {baudrate}")
    
    data = None
    if len(sys.argv) > 3:
        data = sys.argv[3]
    
    send_data(port, baudrate, data)
EOF

cat > /home/$username/serial_test/receive_data.py << 'EOF'
#!/usr/bin/env python3
# 串口接收数据程序

import serial
import time
import sys

def receive_data(port, baudrate=9600, timeout=10):
    """从串口接收数据"""
    try:
        # 打开串口
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"成功打开串口 {port}")
        
        # 循环接收数据
        print("开始接收数据 (按Ctrl+C结束)...")
        start_time = time.time()
        try:
            while True:
                # 读取一行数据
                line = ser.readline()
                if line:
                    try:
                        # 尝试解码为字符串
                        decoded = line.decode('utf-8').strip()
                        print(f"接收: {decoded}")
                    except UnicodeDecodeError:
                        # 如果解码失败，显示十六进制
                        print(f"接收: {line.hex()}")
                
                # 如果设置了超时，检查是否已超时
                if timeout > 0 and (time.time() - start_time) > timeout:
                    print(f"\n已超过设定的 {timeout} 秒超时时间")
                    break
                
                time.sleep(0.1)  # 短暂休眠避免CPU占用过高
                
        except KeyboardInterrupt:
            print("\n停止接收")
        
        # 关闭串口
        ser.close()
        print("串口已关闭")
        return True
    
    except Exception as e:
        print(f"错误: {e}")
        return False

# 主程序
if __name__ == "__main__":
    print("======= 串口接收数据程序 =======")
    
    if len(sys.argv) < 2:
        print("用法: python3 receive_data.py <串口> [波特率] [超时秒数]")
        print("例如: python3 receive_data.py /dev/ttyUSB0 9600 30")
        print("超时设为0表示无限等待")
        sys.exit(1)
    
    port = sys.argv[1]
    
    baudrate = 9600
    if len(sys.argv) > 2:
        try:
            baudrate = int(sys.argv[2])
        except:
            print(f"波特率格式错误，使用默认值: {baudrate}")
    
    timeout = 0  # 默认无超时
    if len(sys.argv) > 3:
        try:
            timeout = int(sys.argv[3])
        except:
            print(f"超时格式错误，使用默认值: {timeout}")
    
    receive_data(port, baudrate, timeout)
EOF

chmod +x /home/$username/serial_test/serial_test.py
chmod +x /home/$username/serial_test/send_data.py
chmod +x /home/$username/serial_test/receive_data.py
chown -R $username:$username /home/$username/serial_test

echo -e "${GREEN}✓ 已创建串口测试脚本:${NC}"
echo -e "   1. /home/$username/serial_test/serial_test.py - 串口测试程序"
echo -e "   2. /home/$username/serial_test/send_data.py - 发送数据程序"
echo -e "   3. /home/$username/serial_test/receive_data.py - 接收数据程序"

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}         树莓派串口配置完成!                                  ${NC}"
echo -e "${BLUE}================================================================${NC}"

echo -e "\n${GREEN}重要提示:${NC}"
echo -e "1. 请${RED}重新启动系统${NC}或${RED}注销并重新登录${NC}以使权限设置生效"
echo -e "2. 串口测试程序位置: ${YELLOW}/home/$username/serial_test/${NC}"
echo -e "3. 使用方法:"
echo -e "   ${YELLOW}cd ~/serial_test${NC}"
echo -e "   ${YELLOW}./serial_test.py${NC} - 测试检测到的串口"
echo -e "   ${YELLOW}./send_data.py /dev/ttyXXX 9600${NC} - 发送数据"
echo -e "   ${YELLOW}./receive_data.py /dev/ttyXXX 9600${NC} - 接收数据"
echo -e "4. 请根据实际设备替换 /dev/ttyXXX 为正确的串口名称" 