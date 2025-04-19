import cv2
import numpy as np
import time

def main():
    print("摄像头测试 - 解决黑屏显示问题")
    
    # 直接打开摄像头，端口0
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("错误: 无法打开摄像头")
        return
    
    print("摄像头已打开")
    print("按 'q' 退出，按 's' 保存图片")
    
    # 关键: 尝试不同的显示方法
    use_method = 1
    methods = ["直接显示", "BGR转RGB", "BGR转HSV", "BGR转GRAY", "直接显示+waitKey(100)"]
    print(f"当前显示方法: {methods[use_method-1]}")
    
    while True:
        # 读取一帧
        ret, frame = cap.read()
        
        if not ret:
            print("警告: 无法获取图像")
            time.sleep(0.5)
            continue
        
        # 显示帧数和分辨率
        h, w = frame.shape[:2]
        img_to_show = None
        
        # 尝试不同显示方法
        if use_method == 1:
            # 方法1: 直接显示
            img_to_show = frame
        elif use_method == 2:
            # 方法2: BGR转RGB
            img_to_show = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif use_method == 3:
            # 方法3: BGR转HSV
            img_to_show = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        elif use_method == 4:
            # 方法4: 灰度图
            img_to_show = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        elif use_method == 5:
            # 方法5: 使用不同的waitKey
            img_to_show = frame
        
        # 添加文本说明
        if img_to_show is not None:
            if len(img_to_show.shape) == 2:
                # 灰度图转为彩色以显示绿色文字
                img_to_show = cv2.cvtColor(img_to_show, cv2.COLOR_GRAY2BGR)
            
            text = f"分辨率: {w}x{h} | 方法: {methods[use_method-1]} | 1-5切换方法 | s保存 | q退出"
            cv2.putText(img_to_show, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 显示图像
        cv2.imshow('摄像头测试', img_to_show)
        
        # 按键处理
        if use_method == 5:
            key = cv2.waitKey(100) & 0xFF  # 使用较长的等待时间
        else:
            key = cv2.waitKey(1) & 0xFF
        
        # 切换显示方法
        if key >= ord('1') and key <= ord('5'):
            use_method = key - ord('0')
            print(f"切换显示方法: {methods[use_method-1]}")
        
        # 保存图像
        elif key == ord('s'):
            filename = f"camera_capture_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, frame)
            print(f"图像已保存为: {filename}")
        
        # 退出
        elif key == ord('q'):
            print("用户退出")
            break
    
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    print("程序已结束")

if __name__ == "__main__":
    main() 