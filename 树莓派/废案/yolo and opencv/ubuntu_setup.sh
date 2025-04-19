#!/bin/bash

# Ubuntu x64上安装YOLOv8、YOLOv5和OpenCV的配置脚本
# YOLOv8和YOLOv5将安装在虚拟环境中，OpenCV安装在系统环境
echo "开始安装配置..."

# 设置颜色变量
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 检测Ubuntu版本
OS_VERSION=$(lsb_release -cs)
echo -e "${GREEN}检测到系统版本: $OS_VERSION${NC}"

# 更新系统
echo "正在更新系统..."
sudo apt-get update || echo -e "${RED}更新源信息失败，继续执行...${NC}"
sudo apt-get upgrade -y || echo -e "${RED}系统升级失败，继续执行...${NC}"

# 安装基础依赖
echo "安装基础依赖..."
sudo apt-get install -y build-essential cmake unzip pkg-config git || echo -e "${RED}基础依赖安装失败，继续执行...${NC}"

# 安装图像和视频相关库
echo "安装图像和视频相关库..."
sudo apt-get install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev || echo -e "${RED}视频库安装失败，继续执行...${NC}"
sudo apt-get install -y libxvidcore-dev libx264-dev libgtk-3-dev || echo -e "${RED}图形界面库安装失败，继续执行...${NC}"

# 安装Python及开发工具
echo "安装Python及开发工具..."
sudo apt-get install -y python3 python3-dev python3-pip python3-venv || echo -e "${RED}Python安装失败，继续执行...${NC}"

# 系统级安装OpenCV
echo "在系统环境中安装OpenCV..."
sudo apt-get install -y python3-opencv || echo -e "${RED}系统OpenCV安装失败，尝试pip安装${NC}"
if ! python3 -c "import cv2" &>/dev/null; then
    echo "使用pip安装OpenCV到系统环境..."
    python3 -m pip install opencv-python || echo -e "${RED}OpenCV安装失败${NC}"
fi

# 安装系统级科学计算库
echo "安装系统级科学计算库..."
sudo apt-get install -y python3-numpy python3-matplotlib || echo -e "${RED}部分依赖安装失败，尝试pip安装${NC}"
python3 -m pip install numpy matplotlib || echo -e "${RED}NumPy/Matplotlib安装失败${NC}"

# 创建虚拟环境用于YOLO
echo -e "${GREEN}创建Python虚拟环境用于YOLO...${NC}"
VENV_DIR=~/yolo_venv
python3 -m venv $VENV_DIR || echo -e "${RED}创建虚拟环境失败${NC}"

# 激活虚拟环境并安装YOLO相关包
echo -e "${GREEN}激活虚拟环境并安装YOLO相关包...${NC}"
source $VENV_DIR/bin/activate || echo -e "${RED}激活虚拟环境失败${NC}"

# 升级虚拟环境中的pip
echo "在虚拟环境中升级pip..."
pip install --upgrade pip || echo -e "${RED}pip升级失败，继续执行...${NC}"

# 在虚拟环境中安装PyTorch (CPU版本，如需GPU版可修改)
echo "在虚拟环境中安装PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu || echo -e "${RED}PyTorch安装失败，继续执行...${NC}"

# 在虚拟环境中安装YOLOv8
echo "在虚拟环境中安装YOLOv8..."
pip install ultralytics || echo -e "${RED}YOLOv8安装失败，继续执行...${NC}"

# 在虚拟环境中安装YOLOv5 (使用git克隆方式)
echo "在虚拟环境中安装YOLOv5..."
cd ~
if [ ! -d "~/yolov5" ]; then
  git clone https://github.com/ultralytics/yolov5.git || echo -e "${RED}克隆YOLOv5失败${NC}"
fi
if [ -d "~/yolov5" ]; then
  cd yolov5
  pip install -e . || echo -e "${RED}YOLOv5安装失败${NC}"
  cd ~
fi

# 安装OpenCV到虚拟环境（因为YOLO可能需要它）
echo "在虚拟环境中安装OpenCV（YOLO依赖）..."
pip install opencv-python || echo -e "${RED}虚拟环境中的OpenCV安装失败${NC}"

# 验证虚拟环境中的安装
echo -e "${GREEN}验证虚拟环境中的安装:${NC}"
python -c "import cv2; print('虚拟环境中的OpenCV版本:', cv2.__version__)" || echo -e "${RED}OpenCV安装验证失败${NC}"
python -c "import torch; print('虚拟环境中的PyTorch版本:', torch.__version__)" || echo -e "${RED}PyTorch安装验证失败${NC}"
python -c "import ultralytics; print('虚拟环境中的YOLOv8安装成功')" || echo -e "${RED}YOLOv8安装验证失败${NC}"

# 退出虚拟环境
deactivate

# 验证系统环境中的OpenCV
echo -e "${GREEN}验证系统环境中的OpenCV:${NC}"
python3 -c "import cv2; print('系统环境中的OpenCV版本:', cv2.__version__)" || echo -e "${RED}系统OpenCV安装验证失败${NC}"

# 总结安装情况
echo ""
echo "==============================================="
echo -e "${GREEN}安装完成！${NC}"
echo "==============================================="

echo "OpenCV已安装到系统Python环境中"
echo "YOLOv8和YOLOv5已安装到虚拟环境中: $VENV_DIR"
echo ""
echo "使用YOLO相关库，请先激活虚拟环境:"
echo -e "${GREEN}source $VENV_DIR/bin/activate${NC}"
echo ""
echo "完成使用后退出虚拟环境:"
echo -e "${GREEN}deactivate${NC}"

echo ""
echo "如果遇到问题，可以尝试以下方法："
echo "1. 检查CUDA和cuDNN安装（如果需要GPU支持）"
echo "2. 如需GPU版本的PyTorch，请访问: https://pytorch.org/get-started/locally/"
echo "3. 手动安装YOLOv5: cd ~ && git clone https://github.com/ultralytics/yolov5.git"

# 添加执行权限提示
echo -e "${GREEN}请执行以下命令给脚本添加执行权限：${NC}"
echo "chmod +x ubuntu_setup.sh"
echo -e "${GREEN}然后通过以下命令运行：${NC}"
echo "./ubuntu_setup.sh"

exit 0 