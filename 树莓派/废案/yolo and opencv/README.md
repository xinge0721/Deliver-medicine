# 树莓派YOLOv5/YOLOv8和OpenCV一键配置

这个仓库包含用于在树莓派上一键配置YOLOv5、YOLOv8和OpenCV的脚本，适用于Raspberry Pi OS (64-bit)系统。

## 文件说明

- `setup.sh`: 一键安装脚本，用于安装所有必要的依赖和库
- `test_yolo.py`: 测试YOLOv5和YOLOv8是否正确安装
- `test_opencv.py`: 测试OpenCV是否正确安装及其基本功能

## 使用方法

### 1. 将文件传输到树莓派

可以通过多种方式将这些文件传输到树莓派:

- 使用SCP命令从Windows传输:
  ```
  scp setup.sh test_yolo.py test_opencv.py pi@树莓派IP地址:/home/pi/
  ```
  
- 或者使用WinSCP等工具直接传输

- 也可以在树莓派上使用git克隆此仓库

### 2. 给脚本添加执行权限

```bash
chmod +x setup.sh
```

### 3. 运行安装脚本

```bash
./setup.sh
```

安装过程可能需要较长时间，请耐心等待。脚本会自动安装所有必要的依赖、库和软件包。

### 4. 激活虚拟环境

```bash
source ~/yolo_env/bin/activate
```

### 5. 运行测试脚本

测试YOLOv5和YOLOv8:
```bash
python test_yolo.py
```

测试OpenCV:
```bash
python test_opencv.py
```

## 网络问题解决方案

在树莓派上安装大型Python包时可能会遇到网络超时问题，这个脚本已经针对这些问题做了优化：

1. **配置系统apt源为清华源**：加速系统包的下载和安装
2. **使用清华PyPI镜像源**：加快Python包的下载速度
3. **增加超时时间**：为pip下载设置了更长的超时时间（300秒）
4. **使用--no-cache-dir参数**：避免缓存问题
5. **分步安装**：将大型依赖分开安装，降低单次失败风险

如果仍然遇到超时错误，可以尝试：

1. 确保网络连接稳定，或使用网线连接代替WiFi
2. 手动逐个安装包：
   ```bash
   pip install --timeout=300 包名
   ```
3. 尝试其他镜像源：
   ```bash
   pip install -i https://mirrors.aliyun.com/pypi/simple/ 包名
   ```
4. 对于GitHub的内容（如YOLOv5），可以先克隆再安装：
   ```bash
   git clone https://github.com/ultralytics/yolov5.git
   cd yolov5
   pip install -e .
   ```
5. 对于特别大的包（如OpenCV），可以考虑先下载wheel文件再安装：
   ```bash
   wget 包的wheel文件URL
   pip install 下载的wheel文件
   ```

## 注意事项

- 安装过程需要较长时间，特别是在树莓派等性能较低的设备上（可能需要1-2小时）
- 首次运行YOLOv5或YOLOv8时，会自动下载预训练模型，需要网络连接
- 在无显示器的环境中，摄像头测试部分可能会失败，这是正常的
- 树莓派上运行YOLO模型可能会比较慢，这是由于硬件限制
- 推荐使用Raspberry Pi 4或更高版本，至少4GB RAM以获得更好性能

## 故障排除

如果遇到问题，请检查:

1. 是否激活了虚拟环境：`source ~/yolo_env/bin/activate`
2. 树莓派是否有足够的存储空间：`df -h`
3. 网络连接是否正常，能够下载模型：`ping www.baidu.com`
4. 是否有足够的RAM：`free -h`
5. Python版本是否兼容：`python --version`（推荐Python 3.7+）
6. 安装日志是否有具体错误：检查终端输出
7. 如果apt源配置失败，请手动设置为清华源：https://mirrors.tuna.tsinghua.edu.cn/help/raspbian/

## 自定义

可以根据需要修改脚本来满足特定要求:

- 在`setup.sh`中添加或移除包
- 修改`test_yolo.py`来使用不同的模型或图像
- 修改`test_opencv.py`来测试其他OpenCV功能
- 如需针对特定模型优化，可以调整脚本中的安装选项 