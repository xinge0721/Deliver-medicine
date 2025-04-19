import cv2
import time
import os
from datetime import datetime

# 初始化摄像头
# 获取摄像头函数
# 参数就是摄像头端口
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("无法打开摄像头！")
    exit()

# 设置分辨率（降低分辨率以提高帧率）
width = 320
height = 240
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)  # 降低分辨率到320x240
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
# 设置摄像头帧率（部分摄像头支持）
fps_target = 30
cap.set(cv2.CAP_PROP_FPS, fps_target)  # 设置帧率
# 降低编码质量
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # 使用MJPG编码，比常用的YUY2更快

# 定义按键码
KEY_Q = ord('q')  # 退出
KEY_A = ord('a')  # 测试按键
KEY_R = ord('r')  # 开始/停止录制

# 帧率计算变量（仅控制台输出，不显示在画面上）
frame_count = 0
fps = 0
start_time = time.time()

# 视频录制变量
recording = False
video_writer = None
output_dir = "recordings"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def start_recording():
    global video_writer, recording
    # 创建当前时间的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"video_{timestamp}.avi")
    # 创建VideoWriter对象
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 使用XVID编码
    video_writer = cv2.VideoWriter(output_path, fourcc, fps_target, (width, height))
    recording = True
    print(f"开始录制视频: {output_path}")

def stop_recording():
    global video_writer, recording
    if video_writer is not None:
        video_writer.release()
        video_writer = None
    recording = False
    print("停止录制视频")

def send():
    global frame_count, fps, start_time, recording, video_writer
    
    # 在此处能获得俩个参数，一个是是否获得了图像，另一个ie就是获取的图像
    # 若前者为空，则没有获取到图像，或者首后者就是野指针，一用程序就会崩溃
    ret, frame = cap.read()
    if not ret:
        print("无法获取帧！")
        return 0
    
    # 更新帧数计数（只用于控制台输出，不显示在画面上）
    frame_count += 1
    
    # 每秒更新一次FPS
    elapsed_time = time.time() - start_time
    if elapsed_time >= 1.0:
        fps = frame_count / elapsed_time
        print(f"当前帧率: {fps:.2f} FPS")
        frame_count = 0
        start_time = time.time()
    
    # 如果正在录制，写入帧
    if recording and video_writer is not None:
        video_writer.write(frame)
        # 在画面右上角显示红色录制指示点
        cv2.circle(frame, (width - 20, 20), 10, (0, 0, 255), -1)
    
    # 显示画面
    # 画面显示函数（其实因该叫放入显示队列函数）
    # 前者是窗口的名称，叫什么的行
    # 后者是需要显示的图像
    cv2.imshow('Camera', frame)
    
    # 退出条件
    # cv2.imshow()并不是立即绘制窗口，而是将绘制请求放入事件队列
    # cv2.waitKey()是触发事件处理的关键函数
    # 所以他不仅是获取按键的函数，更是刷新屏幕的函数
    # imshow虽然是显示画面函数，但还是需要配合该函数
    key = cv2.waitKey(1) & 0xFF  # 添加位掩码以确保跨平台兼容性
    
    # 检测按键
    if key == KEY_Q or cv2.getWindowProperty('Camera', cv2.WND_PROP_VISIBLE) < 1:
        print("程序退出")
        if recording:
            stop_recording()
        cap.release()
        cv2.destroyAllWindows()
        return 0
    elif key == KEY_R:  # R键控制录制
        if not recording:
            start_recording()
        else:
            stop_recording()
    elif key == KEY_A:  # A键仍保留用于测试
        print("按下了A键")
    elif key != 255:  # 当有任何按键按下时打印ASCII码（调试用）
        print(f"按下了键: {key} (ASCII码)")

    return 1

def main():
    print("按 'r' 开始/停止录制")
    print("按 'q' 退出程序")
    while send():
        pass

if __name__ == "__main__":
    main()
