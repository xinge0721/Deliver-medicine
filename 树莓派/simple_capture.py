import cv2
import os
import datetime

def main():
    # 创建保存图片的目录
    save_dir = "captured_images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"已创建图片保存目录: {save_dir}")
    
    # 打开摄像头
    print("正在打开摄像头...")
    cap = cv2.VideoCapture(0)
    
    # 设置摄像头参数
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    
    # 检查摄像头是否打开成功
    if not cap.isOpened():
        print("无法打开摄像头")
        return
    
    # 等待摄像头初始化
    print("等待摄像头初始化...")
    for _ in range(5):
        cap.read()
    
    # 图片计数器
    image_count = 0
    
    print("按下 'p' 键拍照，按下 'q' 键退出程序")
    
    while True:
        # 读取一帧
        ret, frame = cap.read()
        if not ret:
            continue
        
        # 显示当前帧，不添加任何文字
        cv2.imshow("Camera", frame)
        
        # 检测按键
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('p'):  # 按下 'p' 键拍照
            # 生成文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{image_count}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            # 保存图片
            cv2.imwrite(filepath, frame)
            print(f"已保存照片: {filepath}")
            
            # 更新计数器
            image_count += 1
        
        elif key == ord('q'):  # 按下 'q' 键退出
            print("退出程序")
            break
    
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    print(f"共拍摄了 {image_count} 张图片")

if __name__ == "__main__":
    main() 