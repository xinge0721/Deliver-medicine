#!/bin/bash
# 文件整理脚本
# 功能：整理当前目录下的脚本文件，创建分类文件夹，并恢复YOLO配置脚本

# 彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}              文件整理脚本                                    ${NC}"
echo -e "${BLUE}================================================================${NC}"

# 创建目录
echo -e "\n${YELLOW}【第1步】创建分类目录...${NC}"

# 创建em修复专用目录
mkdir -p em_fix
echo -e "${GREEN}✓ 已创建em_fix目录${NC}"

# 创建ROS工具目录
mkdir -p ros_tools
echo -e "${GREEN}✓ 已创建ros_tools目录${NC}"

# 创建串口工具目录
mkdir -p serial_tools
echo -e "${GREEN}✓ 已创建serial_tools目录${NC}"

# 创建YOLO配置目录
mkdir -p yolo_config
echo -e "${GREEN}✓ 已创建yolo_config目录${NC}"

# 移动文件
echo -e "\n${YELLOW}【第2步】整理文件...${NC}"

# 移动em修复相关文件
if [ -f "em_fix/fix_em_for_ros.sh" ]; then
  echo -e "${GREEN}em修复脚本已存在于em_fix目录中${NC}"
else
  if [ -f "fix_em_conflict.sh" ]; then
    cp fix_em_conflict.sh em_fix/fix_em_for_ros.sh
    echo -e "${GREEN}✓ 已复制fix_em_conflict.sh到em_fix/fix_em_for_ros.sh${NC}"
  else
    echo -e "${RED}找不到fix_em_conflict.sh文件${NC}"
  fi
fi

# 移动YOLO清理脚本
if [ -f "cleanup_yolo.sh" ]; then
  mv cleanup_yolo.sh ros_tools/
  echo -e "${GREEN}✓ 已移动cleanup_yolo.sh到ros_tools目录${NC}"
else
  echo -e "${RED}找不到cleanup_yolo.sh文件${NC}"
fi

# 移动串口配置脚本
if [ -f "serial_config.sh" ]; then
  mv serial_config.sh serial_tools/
  echo -e "${GREEN}✓ 已移动serial_config.sh到serial_tools目录${NC}"
else
  echo -e "${RED}找不到serial_config.sh文件${NC}"
fi

# 检查YOLO配置脚本
echo -e "\n${YELLOW}【第3步】检查YOLO配置脚本...${NC}"
if [ -f "setup_yolo_opencv.sh" ]; then
  mv setup_yolo_opencv.sh yolo_config/
  echo -e "${GREEN}✓ 已移动setup_yolo_opencv.sh到yolo_config目录${NC}"
else
  # 如果在yolov8_ros_package目录中存在
  if [ -f "yolov8_ros_package/setup_yolo_opencv.sh" ]; then
    cp yolov8_ros_package/setup_yolo_opencv.sh yolo_config/
    echo -e "${GREEN}✓ 已从yolov8_ros_package复制setup_yolo_opencv.sh到yolo_config目录${NC}"
  else
    echo -e "${RED}警告: setup_yolo_opencv.sh文件未找到${NC}"
    echo -e "${YELLOW}创建YOLO与OpenCV安装脚本...${NC}"
    
    # 创建基本的YOLO和OpenCV安装脚本
    cat > yolo_config/setup_yolo_opencv.sh << 'EOF'
#!/bin/bash
# YOLOv8和OpenCV安装脚本 - 恢复版
# 功能: 安装YOLOv8和OpenCV，配置Python环境，使用中国镜像源

# 彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}     YOLOv8和OpenCV安装脚本 (中国镜像源加速)                  ${NC}"
echo -e "${BLUE}================================================================${NC}"

# 创建安装目录
INSTALL_DIR="$HOME/.yolov8_env"
mkdir -p "$INSTALL_DIR"
echo -e "${GREEN}✓ 已创建安装目录: $INSTALL_DIR${NC}"

# 配置pip使用中国镜像源
echo -e "\n${YELLOW}配置pip使用中国镜像源...${NC}"
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
echo -e "${GREEN}✓ 已配置pip使用清华源${NC}"

# 安装系统依赖
echo -e "\n${YELLOW}安装系统依赖...${NC}"
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev python3-venv

# 创建虚拟环境
echo -e "\n${YELLOW}创建Python虚拟环境...${NC}"
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"

# 升级pip
echo -e "\n${YELLOW}升级pip和安装基础依赖...${NC}"
pip install --upgrade pip setuptools wheel

# 安装NumPy
echo -e "\n${YELLOW}安装NumPy...${NC}"
pip install numpy==1.23.5

# 安装PyTorch (CPU版本)
echo -e "\n${YELLOW}安装PyTorch...${NC}"
pip install torch==1.13.1+cpu torchvision==0.14.1+cpu --index-url https://download.pytorch.org/whl/cpu

# 安装YOLOv8
echo -e "\n${YELLOW}安装YOLOv8...${NC}"
pip install ultralytics

# 安装OpenCV
echo -e "\n${YELLOW}安装OpenCV...${NC}"
pip install opencv-python

# 创建激活脚本
echo -e "\n${YELLOW}创建环境激活脚本...${NC}"
cat > "$HOME/activate_yolo.sh" << EOF
#!/bin/bash
# 激活YOLOv8环境
source "$INSTALL_DIR/venv/bin/activate"
echo "YOLOv8环境已激活"
EOF
chmod +x "$HOME/activate_yolo.sh"
echo -e "${GREEN}✓ 已创建环境激活脚本: ~/activate_yolo.sh${NC}"

# 创建测试脚本
echo -e "\n${YELLOW}创建YOLO测试脚本...${NC}"
mkdir -p "$HOME/yolo_test"
cat > "$HOME/yolo_test/test_yolo.py" << EOF
#!/usr/bin/env python3
# YOLO测试脚本
import os
import sys
from ultralytics import YOLO

print("加载YOLOv8模型...")
model = YOLO('yolov8n.pt')

image_path = "test.jpg"
if not os.path.exists(image_path):
    print(f"找不到测试图片: {image_path}")
    print("请先下载测试图片")
    sys.exit(1)

print(f"对图片 {image_path} 进行检测...")
results = model(image_path)

output_path = "result.jpg"
for r in results:
    im_array = r.plot()
    import cv2
    cv2.imwrite(output_path, im_array)
    print(f"结果已保存到: {output_path}")
EOF
chmod +x "$HOME/yolo_test/test_yolo.py"
echo -e "${GREEN}✓ 已创建测试脚本: ~/yolo_test/test_yolo.py${NC}"

# 完成
echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}     YOLOv8和OpenCV安装完成!                                  ${NC}"
echo -e "${BLUE}================================================================${NC}"

echo -e "\n${GREEN}使用方法:${NC}"
echo -e "1. 激活环境: source ~/activate_yolo.sh"
echo -e "2. 测试YOLO: cd ~/yolo_test && python test_yolo.py"

echo -e "\n${GREEN}注意:${NC}"
echo -e "在测试前请先下载一张测试图片:"
echo -e "cd ~/yolo_test && wget https://ultralytics.com/images/zidane.jpg -O test.jpg"

# 退出虚拟环境
deactivate
EOF
    chmod +x yolo_config/setup_yolo_opencv.sh
    echo -e "${GREEN}✓ 已创建新的setup_yolo_opencv.sh脚本${NC}"
  fi
fi

# 赋予脚本执行权限
echo -e "\n${YELLOW}【第4步】赋予脚本执行权限...${NC}"

find em_fix ros_tools serial_tools yolo_config -type f -name "*.sh" -exec chmod +x {} \;
echo -e "${GREEN}✓ 已赋予所有脚本执行权限${NC}"

# 创建运行说明
echo -e "\n${YELLOW}【第5步】创建README文件...${NC}"

# 创建总README
cat > README.md << 'EOF'
# 树莓派ROS工具集

此目录包含多个用于树莓派ROS环境配置和管理的工具脚本。

## 目录结构

- `em_fix/`: 用于修复ROS的em模块问题
- `ros_tools/`: ROS环境管理工具
- `serial_tools/`: 串口通信配置和测试工具
- `yolo_config/`: YOLO与OpenCV安装配置

## 使用方法

1. 如需修复ROS的em模块问题:
   ```
   cd em_fix
   sudo ./fix_em_for_ros.sh
   ```

2. 如需清理YOLO环境:
   ```
   cd ros_tools
   sudo ./cleanup_yolo.sh
   ```

3. 如需配置串口通信:
   ```
   cd serial_tools
   sudo ./serial_config.sh
   ```

4. 如需安装YOLO和OpenCV:
   ```
   cd yolo_config
   sudo ./setup_yolo_opencv.sh
   ```

## 注意事项

- 所有脚本都需要使用sudo权限运行
- 运行脚本后，请按照脚本提示进行后续操作
EOF

# 创建YOLO配置README
cat > yolo_config/README.md << 'EOF'
# YOLO配置工具

此目录包含用于安装和配置YOLOv8和OpenCV的工具。

## 文件说明

- `setup_yolo_opencv.sh`: 一键安装YOLOv8和OpenCV的脚本

## 使用方法

```bash
sudo ./setup_yolo_opencv.sh
```

## 功能说明

该脚本会：
- 配置pip使用中国镜像源加速下载
- 创建Python虚拟环境
- 安装NumPy、PyTorch、YOLOv8和OpenCV
- 创建激活脚本和测试脚本

## 注意事项

- 安装过程可能需要较长时间，请耐心等待
- 安装完成后需要使用激活脚本激活环境
- 为提高性能，脚本默认安装CPU版本的PyTorch
EOF

echo -e "${GREEN}✓ 已创建README文件${NC}"

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}              文件整理完成!                                   ${NC}"
echo -e "${BLUE}================================================================${NC}"

echo -e "\n${GREEN}目录结构:${NC}"
echo -e "1. ${YELLOW}em_fix/${NC} - 修复ROS的em模块问题"
echo -e "   - fix_em_for_ros.sh: 修复脚本"
echo -e "   - README.md: 使用说明"
echo -e ""
echo -e "2. ${YELLOW}ros_tools/${NC} - ROS环境管理工具"
echo -e "   - cleanup_yolo.sh: YOLO环境清理脚本"
echo -e "   - README.md: 使用说明"
echo -e ""
echo -e "3. ${YELLOW}serial_tools/${NC} - 串口通信工具"
echo -e "   - serial_config.sh: 串口配置脚本"
echo -e "   - README.md: 使用说明"
echo -e ""
echo -e "4. ${YELLOW}yolo_config/${NC} - YOLO配置工具"
echo -e "   - setup_yolo_opencv.sh: YOLO和OpenCV安装脚本"
echo -e "   - README.md: 使用说明"
echo -e ""
echo -e "${GREEN}请参考各目录中的README.md文件了解详细使用方法${NC}" 