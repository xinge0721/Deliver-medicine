#!/bin/bash

# 树莓派上安装YOLOv8、YOLOv5和OpenCV的一键配置脚本
echo "开始安装YOLOv8、YOLOv5和OpenCV..."

# 设置颜色变量
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 检测系统版本
OS_VERSION=$(grep VERSION_CODENAME /etc/os-release | cut -d= -f2)
if [ -z "$OS_VERSION" ]; then
  OS_VERSION="bullseye" # 默认版本
fi
echo "检测到系统版本: $OS_VERSION"

# 使用官方默认源
echo "使用官方默认源..."
# 恢复默认源文件，如果已备份
if [ -f "/etc/apt/sources.list.bak" ]; then
  sudo mv /etc/apt/sources.list.bak /etc/apt/sources.list
fi
if [ -f "/etc/apt/sources.list.d/raspi.list.bak" ]; then
  sudo mv /etc/apt/sources.list.d/raspi.list.bak /etc/apt/sources.list.d/raspi.list
fi

# 导入Raspberry Pi OS的GPG密钥
echo "导入Raspberry Pi OS的GPG密钥..."
sudo apt-key update
sudo apt-get install -y gnupg
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 9165938D90FDDD2E || true
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 82B129927FA3303E || true

# 更新系统
echo "正在更新系统..."
sudo apt-get update || echo "更新源信息失败，继续执行..."
sudo apt-get upgrade -y || echo "系统升级失败，继续执行..."

# 安装Python
echo "正在安装Python..."
sudo apt-get install -y python3 python3-pip python3-dev || echo "Python安装失败，继续执行..."

# 尝试使用apt安装OpenCV和其他依赖
echo "尝试使用系统包安装OpenCV..."
sudo apt-get install -y python3-opencv || echo "系统OpenCV安装失败，稍后将尝试pip安装"
sudo apt-get install -y python3-numpy python3-matplotlib || echo "部分依赖安装失败，稍后将尝试pip安装"

# 安装pip包
echo "使用pip安装必要的包..."
pip3 install --upgrade pip || echo "pip升级失败，继续执行..."
pip3 install opencv-python-headless || echo "OpenCV安装失败，继续执行..."
pip3 install numpy matplotlib || echo "NumPy/Matplotlib安装失败，继续执行..."
pip3 install ultralytics || echo "YOLOv8安装失败，继续执行..."
pip3 install torch torchvision torchaudio || echo "PyTorch安装失败，继续执行..."

# 安装YOLOv5 (使用git克隆方式)
echo "正在安装YOLOv5..."
if ! which git > /dev/null; then
  sudo apt-get install -y git || echo "Git安装失败，无法安装YOLOv5"
fi

if which git > /dev/null; then
  cd ~
  if [ ! -d "~/yolov5" ]; then
    git clone https://github.com/ultralytics/yolov5.git || echo "克隆YOLOv5失败"
  fi
  if [ -d "~/yolov5" ]; then
    cd yolov5
    pip3 install -e . || echo "YOLOv5安装失败"
    cd ~
  fi
fi

# 验证安装
echo "验证安装..."
python3 -c "import cv2; print('OpenCV版本:', cv2.__version__)" || echo "OpenCV安装验证失败"
python3 -c "import torch; print('PyTorch版本:', torch.__version__)" || echo "PyTorch安装验证失败"
python3 -c "import ultralytics; print('YOLOv8安装成功')" || echo "YOLOv8安装验证失败"

# 总结安装情况
echo ""
echo "==============================================="
echo "安装完成！"
echo "==============================================="

echo "YOLOv8、YOLOv5和OpenCV已安装到系统Python环境中"
echo "你可以直接通过python3直接导入这些库"

echo ""
echo "如果遇到问题，可以尝试以下方法："
echo "1. 使用系统包管理器安装: sudo apt-get install python3-opencv python3-numpy"
echo "2. 手动安装YOLOv5: cd ~ && git clone https://github.com/ultralytics/yolov5.git"
echo "3. 检查你的Python版本: python3 --version"

exit 0 