#!/bin/bash

# 设置工作目录为脚本所在的目录
cd "$(dirname "$0")"

# 获取当前日期时间用于日志文件名
current_date=$(date '+%Y-%m-%d_%H-%M-%S')
log_dir="logs"
mkdir -p "$log_dir"

# 创建日志文件
hcsr_log="$log_dir/hcsr04_$current_date.log"
yolo_log="$log_dir/yolo_$current_date.log"

echo "启动程序中..."
echo "日志将保存在: $log_dir 目录"

# 启动超声波测距程序
echo "启动超声波测距程序 (HCSR04_fixed.py)..."
python3 HCSR04_fixed.py > "$hcsr_log" 2>&1 &
hcsr_pid=$!
echo "超声波测距程序已启动，PID: $hcsr_pid"

# 等待短暂时间确保串口初始化完成
sleep 2

# 启动YOLO检测程序
echo "启动YOLO检测程序 (YOLO_detection.py)..."
python3 YOLO_detection.py > "$yolo_log" 2>&1 &
yolo_pid=$!
echo "YOLO检测程序已启动，PID: $yolo_pid"

# 显示运行的程序信息
echo "所有程序已成功启动!"
echo "超声波程序 (PID: $hcsr_pid) - 日志: $hcsr_log"
echo "YOLO程序 (PID: $yolo_pid) - 日志: $yolo_log" 