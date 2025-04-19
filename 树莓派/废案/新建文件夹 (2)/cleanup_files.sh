#!/bin/bash
# 文件清理脚本
# 功能：删除不必要的文件，只保留关键脚本

# 彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}              文件清理脚本                                    ${NC}"
echo -e "${BLUE}================================================================${NC}"

# 执行file_organizer.sh进行整理
echo -e "\n${YELLOW}【第1步】先执行文件整理脚本...${NC}"

if [ -f "file_organizer.sh" ]; then
  chmod +x file_organizer.sh
  ./file_organizer.sh
  echo -e "${GREEN}✓ 文件整理完成${NC}"
else
  echo -e "${RED}找不到file_organizer.sh脚本${NC}"
  exit 1
fi

# 删除冗余文件
echo -e "\n${YELLOW}【第2步】删除冗余文件...${NC}"

REDUNDANT_FILES=(
  "fix_ros_em.sh"
  "complete_solution.sh"
  "em_fix.py"
  "README.md"  # 已有SUMMARY.md，这个可能是旧的
)

for file in "${REDUNDANT_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo -e "${YELLOW}删除文件: $file${NC}"
    rm -f "$file"
    echo -e "${GREEN}✓ 已删除${NC}"
  else
    echo -e "${GREEN}文件不存在: $file${NC}"
  fi
done

# 处理yolov8_ros_package目录
echo -e "\n${YELLOW}【第3步】处理yolov8_ros_package目录...${NC}"

if [ -d "yolov8_ros_package" ]; then
  echo -e "${YELLOW}yolov8_ros_package目录包含以下文件:${NC}"
  ls -la yolov8_ros_package
  
  echo -e "${YELLOW}是否删除整个yolov8_ros_package目录? [y/N]${NC}"
  read -r response
  if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    rm -rf yolov8_ros_package
    echo -e "${GREEN}✓ 已删除yolov8_ros_package目录${NC}"
  else
    echo -e "${GREEN}保留yolov8_ros_package目录${NC}"
  fi
else
  echo -e "${GREEN}目录不存在: yolov8_ros_package${NC}"
fi

# 处理yolo_examples目录
echo -e "\n${YELLOW}【第4步】处理yolo_examples目录...${NC}"

if [ -d "yolo_examples" ]; then
  echo -e "${YELLOW}yolo_examples目录包含以下文件:${NC}"
  ls -la yolo_examples
  
  echo -e "${YELLOW}是否删除整个yolo_examples目录? [y/N]${NC}"
  read -r response
  if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    rm -rf yolo_examples
    echo -e "${GREEN}✓ 已删除yolo_examples目录${NC}"
  else
    echo -e "${GREEN}保留yolo_examples目录${NC}"
  fi
else
  echo -e "${GREEN}目录不存在: yolo_examples${NC}"
fi

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}              文件清理完成!                                   ${NC}"
echo -e "${BLUE}================================================================${NC}"

echo -e "\n${GREEN}当前目录下的文件:${NC}"
ls -la

echo -e "\n${GREEN}现在目录结构已经整理好，只保留了必要的文件:${NC}"
echo -e "1. ${YELLOW}em_fix/fix_em_for_ros.sh${NC} - 修复ROS的em模块问题"
echo -e "2. ${YELLOW}ros_tools/cleanup_yolo.sh${NC} - 清理YOLO环境"
echo -e "3. ${YELLOW}serial_tools/serial_config.sh${NC} - 配置串口通信"
echo -e "4. ${YELLOW}file_organizer.sh${NC} - 文件整理工具"
echo -e "5. ${YELLOW}SUMMARY.md${NC} - 详细说明文档"
echo -e "6. ${YELLOW}cleanup_files.sh${NC} - 本脚本，用于清理冗余文件" 