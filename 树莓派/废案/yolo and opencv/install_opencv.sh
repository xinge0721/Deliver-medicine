#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}开始安装OpenCV...${NC}"

# 检查Python版本
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}检测到Python版本: ${PYTHON_VERSION}${NC}"

# 安装系统依赖
echo -e "${GREEN}安装系统依赖...${NC}"
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    libatlas-base-dev \
    libhdf5-dev \
    libharfbuzz0b \
    libwebp7 \
    libtiff6 \
    libopenjp2-7 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgtk-3-dev \
    libtbb-dev \
    libdc1394-dev \
    v4l-utils \
    libopenblas-dev \
    liblapack-dev \
    libblas-dev \
    pkg-config \
    qt5-default \
    libqt5gui5 \
    libqt5core5a \
    libqt5widgets5

# 创建虚拟环境
echo -e "${GREEN}创建Python虚拟环境...${NC}"
python3 -m venv ~/opencv_env
source ~/opencv_env/bin/activate

# 升级pip
echo -e "${GREEN}升级pip...${NC}"
pip install --upgrade pip

# 安装OpenCV
echo -e "${GREEN}安装OpenCV...${NC}"
pip install opencv-python-headless

# 验证安装
echo -e "${GREEN}验证OpenCV安装...${NC}"
python3 -c "import cv2; print('OpenCV版本:', cv2.__version__)"

echo -e "${GREEN}安装完成！${NC}"
echo -e "${GREEN}使用方法：${NC}"
echo -e "1. 激活虚拟环境：source ~/opencv_env/bin/activate"
echo -e "2. 运行Python：python3"
echo -e "3. 导入OpenCV：import cv2"

# 退出虚拟环境
deactivate 