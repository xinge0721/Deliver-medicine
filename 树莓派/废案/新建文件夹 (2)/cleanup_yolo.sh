#!/bin/bash
# YOLO环境清理脚本
# 功能：删除所有YOLO相关环境和文件，只保留ROS环境

# 彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}              YOLO环境清理脚本                                 ${NC}"
echo -e "${BLUE}================================================================${NC}"

# 清理YOLO虚拟环境
echo -e "\n${YELLOW}【第1步】清理YOLO虚拟环境...${NC}"

YOLO_ENV_DIRS=(
  "$HOME/.yolo_env"
  "$HOME/.yolo_venv"
)

for dir in "${YOLO_ENV_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    echo -e "${YELLOW}删除YOLO虚拟环境目录: $dir${NC}"
    rm -rf "$dir"
    echo -e "${GREEN}✓ 已删除${NC}"
  else
    echo -e "${GREEN}目录不存在: $dir${NC}"
  fi
done

# 清理YOLO配置目录
echo -e "\n${YELLOW}【第2步】清理YOLO配置文件...${NC}"

CONFIG_DIRS=(
  "$HOME/.config/yolo_ros"
  "$HOME/.config/yolo_ros_config"
)

for dir in "${CONFIG_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    echo -e "${YELLOW}删除YOLO配置目录: $dir${NC}"
    rm -rf "$dir"
    echo -e "${GREEN}✓ 已删除${NC}"
  else
    echo -e "${GREEN}目录不存在: $dir${NC}"
  fi
done

# 清理YOLO示例文件夹
echo -e "\n${YELLOW}【第3步】清理YOLO示例文件...${NC}"

EXAMPLE_DIRS=(
  "$HOME/yolo_examples"
  "$HOME/ros_yolo_examples"
)

for dir in "${EXAMPLE_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    echo -e "${YELLOW}删除YOLO示例目录: $dir${NC}"
    rm -rf "$dir"
    echo -e "${GREEN}✓ 已删除${NC}"
  else
    echo -e "${GREEN}目录不存在: $dir${NC}"
  fi
done

# 清理指南文件
echo -e "\n${YELLOW}【第4步】清理指南文件...${NC}"

GUIDE_FILES=(
  "$HOME/ROS_YOLO共存指南.md"
  "$HOME/YOLO_ROS_隔离指南.md"
)

for file in "${GUIDE_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo -e "${YELLOW}删除指南文件: $file${NC}"
    rm -f "$file"
    echo -e "${GREEN}✓ 已删除${NC}"
  else
    echo -e "${GREEN}文件不存在: $file${NC}"
  fi
done

# 检查是否有通过pip安装的YOLO
echo -e "\n${YELLOW}【第5步】检查系统Python中的YOLO包...${NC}"

if python3 -c "import ultralytics" 2>/dev/null; then
  echo -e "${YELLOW}系统Python中发现YOLO包，是否要卸载? [y/N]${NC}"
  read -r response
  if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    pip uninstall -y ultralytics
    echo -e "${GREEN}✓ 已卸载系统Python中的YOLO包${NC}"
  else
    echo -e "${YELLOW}保留系统Python中的YOLO包${NC}"
  fi
else
  echo -e "${GREEN}系统Python中未发现YOLO包${NC}"
fi

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}              YOLO环境清理完成!                               ${NC}"
echo -e "${BLUE}================================================================${NC}"

echo -e "\n${GREEN}所有YOLO相关环境和文件已清理完毕，ROS环境不受影响。${NC}"
echo -e "${GREEN}如果您需要修复ROS的em模块问题，请运行:${NC}"
echo -e "   cd em_fix && sudo ./fix_em_for_ros.sh" 