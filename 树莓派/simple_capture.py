import cv2
import os
import time
import datetime

# 创建保存图片的目录
save_dir = "captured_images"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
    print(f"已创建图片保存目录: {save_dir}")

# 尝试打开摄像头
print("正在打开摄像头...")
cap = cv2.VideoCapture(0)  # 首先尝试默认摄像头

# 如果默认摄像头打开失败，尝试其他摄像头
if not cap.isOpened():
    print("默认摄像头打开失败，尝试其他摄像头...")
    for i in [1, 2]:
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"成功打开摄像头 {i}")
            break

# 检查摄像头是否成功打开
if not cap.isOpened():
    print("无法打开任何摄像头，程序退出")
    exit()

# 设置分辨率
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# 创建全英文名称的窗口
window_name = "Camera Capture"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

# 计数器
image_count = 0

print("摄像头准备就绪")
print("按空格键拍照，按Q键退出")

while True:
    # 读取一帧
    ret, frame = cap.read()
    
    # 检查是否成功读取
    if not ret:
        print("无法读取摄像头画面，退出程序")
        break
    
    # 在画面上显示计数器
    info_text = f"Images: {image_count} | Press SPACE to capture, Q to quit"
    cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # 显示图像
    cv2.imshow(window_name, frame)
    
    # 按键检测
    key = cv2.waitKey(1) & 0xFF
    
    # 按空格键拍照
    if key == 32:  # 空格键的ASCII码是32
        # 生成文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}_{image_count:04d}.jpg"
        filepath = os.path.join(save_dir, filename)
        
        # 保存图片
        cv2.imwrite(filepath, frame)
        print(f"已保存图片: {filepath}")
        
        # 更新计数器
        image_count += 1
    
    # 按Q键退出
    elif key == ord('q') or key == ord('Q'):
        print("程序结束")
        break

# 释放资源
cap.release()
cv2.destroyAllWindows()
print(f"共拍摄了 {image_count} 张图片")
print(f"图片保存在: {os.path.abspath(save_dir)}") 