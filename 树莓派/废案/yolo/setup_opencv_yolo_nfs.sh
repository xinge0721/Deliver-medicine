#!/bin/bash

# 树莓派 OpenCV 和 YOLOv8 一键配置脚本
# 适用于 Ubuntu Server 20.04.5 LTS (64-bit)

echo "=========================================="
echo "树莓派 OpenCV 和 YOLOv8 一键配置脚本"
echo "适用于 Ubuntu Server 20.04.5 LTS (64-bit)"
echo "=========================================="

# 1. 系统更新
echo "[1/7] 正在更新系统..."
sudo apt update && sudo apt upgrade -y

# 2. 安装依赖项
echo "[2/7] 正在安装依赖项..."
sudo apt install -y build-essential cmake pkg-config libgtk-3-dev \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    libxvidcore-dev libx264-dev libjpeg-dev libpng-dev libtiff-dev \
    gfortran openexr libatlas-base-dev python3-dev python3-pip \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    libfaac-dev libmp3lame-dev libtheora-dev libvorbis-dev \
    libopencore-amrnb-dev libopencore-amrwb-dev \
    libgphoto2-dev libeigen3-dev libhdf5-dev \
    python3-numpy python3-matplotlib python3-scipy python3-pillow \
    libgtk2.0-dev libqt5x11extras5-dev libatlas-base-dev

# 3. 设置清华pip源
echo "[3/7] 正在设置清华pip源..."
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF

# 4. 安装OpenCV
echo "[4/7] 正在安装OpenCV..."
python3 -m pip install -U pip
python3 -m pip install opencv-python opencv-contrib-python

# 5. 解决GUI缺失问题
echo "[5/7] 正在解决GUI缺失问题..."
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6

# 6. 安装YOLOv8
echo "[6/7] 正在安装YOLOv8..."
python3 -m pip install ultralytics

# 7. 安装和配置NFS服务
echo "[7/7] 正在安装和配置NFS服务..."
# 确保系统已更新，并安装NFS服务器软件包
sudo apt update
sudo apt install -y nfs-kernel-server

# 创建共享目录
sudo mkdir -p /home/xinge/chengxu
sudo chmod -R 777 /home/xinge/chengxu

# 编辑/etc/exports文件来添加共享目录
cat > /tmp/exports_config << EOF
/home/xinge/chengxu *(rw,sync,no_subtree_check)
EOF
sudo mv /tmp/exports_config /etc/exports

# 更新导出表并重启NFS服务
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server

# 验证安装
echo "=========================================="
echo "正在验证安装..."

# 验证OpenCV
python3 -c "import cv2; print('OpenCV 版本:', cv2.__version__)"

# 验证YOLOv8
python3 -c "from ultralytics import YOLO; print('YOLOv8 安装成功')"

# 验证NFS
echo "NFS服务状态:"
sudo systemctl status nfs-kernel-server --no-pager

echo "=========================================="
echo "配置完成！OpenCV和YOLOv8已成功安装，NFS服务已配置。"
echo "NFS共享目录: /home/xinge/chengxu"
echo "要在其他电脑上挂载这个NFS共享，请使用以下命令："
echo "sudo mount -t nfs 树莓派IP地址:/home/xinge/chengxu /挂载点"
echo "==========================================" 