#!/bin/bash
# ROS1 em模块修复专用脚本
# 功能：只修复ROS的em模块问题，不涉及YOLO

# 彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}              ROS1 em模块修复专用脚本                          ${NC}"
echo -e "${BLUE}================================================================${NC}"

# ROS的em模块路径
EM_FILES=(
  "/usr/lib/python3/dist-packages/em.py" 
  "/usr/lib/python3/dist-packages/em/__init__.py"
  "/opt/ros/noetic/lib/python3/dist-packages/em.py"
  "/opt/ros/noetic/lib/python3/dist-packages/em/__init__.py"
)

# 找到可用的em模块文件
EM_FILE=""
for file in "${EM_FILES[@]}"; do
  if [ -f "$file" ]; then
    EM_FILE="$file"
    echo -e "${GREEN}找到em模块文件: $EM_FILE${NC}"
    break
  fi
done

if [ -z "$EM_FILE" ]; then
  echo -e "${RED}错误: 找不到任何em模块文件${NC}"
  exit 1
fi

# 备份原始文件
BACKUP_FILE="${EM_FILE}.bak"
if [ ! -f "$BACKUP_FILE" ]; then
  sudo cp "$EM_FILE" "$BACKUP_FILE"
  echo -e "${GREEN}已备份原始文件到: $BACKUP_FILE${NC}"
else
  echo -e "${GREEN}发现已有备份文件: $BACKUP_FILE${NC}"
fi

# 检查文件是否已经包含RAW_OPT
if grep -q "RAW_OPT" "$EM_FILE"; then
  echo -e "${YELLOW}文件已包含RAW_OPT但似乎没有生效${NC}"
  
  # 确保文件权限正确
  sudo chmod 644 "$EM_FILE"
else
  # 直接修改文件，添加常量定义
  echo -e "${GREEN}正在修改em模块文件...${NC}"

  # 应用补丁 - 尝试在文件开头附近添加
  # 首先尝试在__version__行之后添加
  if grep -q "__version__" "$EM_FILE"; then
    sudo sed -i '/__version__/a \
# 添加由ROS-EM修复工具添加的必要常量\
RAW_OPT = "raw"\
BUFFERED_OPT = "buffered"' "$EM_FILE"
    echo -e "${GREEN}在__version__行后添加了常量${NC}"
  else
    # 如果没有__version__行，尝试在文件的第10行添加
    sudo sed -i '10i \
# 添加由ROS-EM修复工具添加的必要常量\
RAW_OPT = "raw"\
BUFFERED_OPT = "buffered"' "$EM_FILE"
    echo -e "${GREEN}在文件第10行添加了常量${NC}"
  fi
fi

# 确认修改
echo -e "${GREEN}修改已应用，检查结果:${NC}"
grep -A 3 "RAW_OPT" "$EM_FILE" || echo -e "${RED}未找到RAW_OPT，可能插入位置有误${NC}"

# 验证修复是否成功
echo -e "${GREEN}验证ROS的em模块修复...${NC}"
python3 -c "
import em
print('RAW_OPT 存在:', hasattr(em, 'RAW_OPT'))
print('BUFFERED_OPT 存在:', hasattr(em, 'BUFFERED_OPT'))
if hasattr(em, 'RAW_OPT') and hasattr(em, 'BUFFERED_OPT'):
    print('✓ ROS的em模块修复成功!')
else:
    print('✗ ROS的em模块修复失败')
"

# 创建ROS测试脚本
mkdir -p "$HOME/ros_examples"
cat > "$HOME/ros_examples/test_em_module.py" << 'EOF'
#!/usr/bin/env python3
# ROS em模块测试脚本

print("====== ROS em模块测试 ======")
try:
    import em
    print(f"使用的em模块: {em.__file__}")
    
    # 测试必要的属性
    has_raw = hasattr(em, 'RAW_OPT')
    has_buffered = hasattr(em, 'BUFFERED_OPT')
    
    print(f"em版本: {getattr(em, '__version__', '未知')}")
    print(f"RAW_OPT存在: {has_raw}")
    print(f"BUFFERED_OPT存在: {has_buffered}")
    
    if has_raw and has_buffered:
        print("\033[0;32m✓ em模块配置正确，ROS应该能正常编译\033[0m")
    else:
        print("\033[0;31m✗ em模块缺少必要属性，ROS可能无法正常编译\033[0m")
    
    # 测试创建Interpreter
    print("\n尝试创建em.Interpreter...")
    interpreter = em.Interpreter()
    print("\033[0;32m✓ 可以创建em.Interpreter对象\033[0m")
    
except ImportError:
    print("\033[0;31m✗ 未找到em模块\033[0m")
except Exception as e:
    print(f"\033[0;31m✗ 错误: {e}\033[0m")
    import traceback
    traceback.print_exc()
EOF

chmod +x "$HOME/ros_examples/test_em_module.py"
echo -e "${GREEN}✓ ROS em模块测试脚本已创建${NC}"

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}              ROS1 em模块修复完成!                             ${NC}"
echo -e "${BLUE}================================================================${NC}"

echo -e "\n${GREEN}验证ROS环境:${NC}"
echo -e "   cd ~/ros_examples && python3 test_em_module.py"
echo -e "   编译ROS: cd ~/catkin_ws && catkin_make"

echo -e "\n${GREEN}如需恢复原始文件:${NC}"
echo -e "   sudo cp ${BACKUP_FILE} ${EM_FILE}" 