# 树莓派ROS开发环境工具集 - 文件说明

## 文件概览表

| 文件名 | 位置 | 用途 | 是否必需 |
|-------|------|------|---------|
| `fix_em_for_ros.sh` | em_fix/ | 修复ROS1的em模块问题 | ✅ 如果ROS报错时需要 |
| `cleanup_yolo.sh` | ros_tools/ | 清理YOLO环境，只保留ROS | ✅ 如果要删除YOLO |
| `serial_config.sh` | serial_tools/ | 配置树莓派串口 | ✅ 如果需要串口通信 |
| `file_organizer.sh` | 根目录 | 将所有脚本整理到对应目录 | ✅ 首次使用时运行 |

## 详细说明

### 1. EM模块修复工具 - `em_fix/fix_em_for_ros.sh`

**功能**：修复ROS1的em模块问题，添加缺失的常量（RAW_OPT和BUFFERED_OPT）

**什么时候需要**：
- 当使用`catkin_make`编译ROS包时出现与em模块相关的错误
- 当错误信息中提到缺少`RAW_OPT`或`BUFFERED_OPT`

**使用方法**：
```bash
sudo ./em_fix/fix_em_for_ros.sh
```

**运行后**：
- 会自动检测并修复em模块
- 会创建测试脚本验证修复是否成功
- 修复成功后可以正常使用`catkin_make`

### 2. YOLO环境清理工具 - `ros_tools/cleanup_yolo.sh`

**功能**：彻底清理所有YOLO相关环境和文件，只保留ROS环境

**什么时候需要**：
- 当不再需要YOLO时
- 当需要释放磁盘空间时
- 当想要完全专注于ROS开发时

**使用方法**：
```bash
sudo ./ros_tools/cleanup_yolo.sh
```

**运行后**：
- 会删除YOLO的虚拟环境
- 会删除YOLO的配置文件和示例代码
- 会询问是否卸载系统Python中的YOLO包

### 3. 串口配置工具 - `serial_tools/serial_config.sh`

**功能**：一键配置树莓派(Ubuntu 20.04, ARM64)串口通信环境

**什么时候需要**：
- 当需要通过串口与外部设备通信时
- 当开发需要使用串口的ROS节点时

**使用方法**：
```bash
sudo ./serial_tools/serial_config.sh
```

**运行后**：
- 会安装必要的串口通信库
- 会配置串口权限
- 会创建三个串口测试程序到`~/serial_test/`目录：
  1. `serial_test.py` - 测试检测串口
  2. `send_data.py` - 发送数据
  3. `receive_data.py` - 接收数据

### 4. 文件整理工具 - `file_organizer.sh`

**功能**：整理当前目录下的脚本文件，创建分类文件夹

**什么时候需要**：
- 在首次下载或创建这些脚本后
- 当文件结构混乱需要重新整理时

**使用方法**：
```bash
sudo ./file_organizer.sh
```

**运行后**：
- 会创建三个分类目录：`em_fix`、`ros_tools`、`serial_tools`
- 会将各脚本移动到对应目录
- 会赋予所有脚本执行权限
- 会创建README文件说明使用方法

## 推荐使用流程

1. **首次使用**：
   ```bash
   chmod +x file_organizer.sh
   sudo ./file_organizer.sh
   ```

2. **如果ROS编译出错**：
   ```bash
   sudo ./em_fix/fix_em_for_ros.sh
   ```

3. **如果需要配置串口**：
   ```bash
   sudo ./serial_tools/serial_config.sh
   ```

4. **如果不再需要YOLO**：
   ```bash
   sudo ./ros_tools/cleanup_yolo.sh
   ```

## 常见问题解答

1. **问**：如何知道我是否需要修复em模块？  
   **答**：如果在运行`catkin_make`时出现与`em`、`empy`或提到缺少`RAW_OPT`、`BUFFERED_OPT`的错误，就需要运行修复脚本。

2. **问**：串口脚本配置后需要重启吗？  
   **答**：是的，配置后需要重启系统或重新登录，以使权限设置生效。

3. **问**：清理YOLO会影响我的ROS吗？  
   **答**：不会，清理脚本专门设计为只删除YOLO相关内容，不会影响ROS环境。

4. **问**：如果我修复em模块后想恢复原始状态怎么办？  
   **答**：脚本会自动备份原始文件，运行脚本后会显示恢复命令，一般是：
   ```bash
   sudo cp /path/to/em.py.bak /path/to/em.py
   ``` 