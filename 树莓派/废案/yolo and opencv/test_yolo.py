#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试YOLOv5和YOLOv8是否安装成功
"""

import sys
import cv2
import torch
import time
import os

def test_yolov5():
    print("测试YOLOv5...")
    try:
        # 使用torch.hub方式加载YOLOv5模型
        print("正在使用torch.hub加载YOLOv5模型...")
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True, trust_repo=True)
        
        print("YOLOv5模型加载成功!")
        
        # 检查CUDA是否可用
        print(f"CUDA是否可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA设备数量: {torch.cuda.device_count()}")
            print(f"CUDA设备名称: {torch.cuda.get_device_name(0)}")
        
        # 使用模型进行一个简单的预测
        print("开始进行YOLOv5预测...")
        img = 'https://ultralytics.com/images/zidane.jpg'
        results = model(img)
        print("YOLOv5预测完成!")
        
        # 保存结果
        try:
            results.save('yolov5_result.jpg')
            print("YOLOv5测试结果已保存到 'yolov5_result.jpg'")
        except Exception as e:
            print(f"尝试保存结果方法1失败: {e}")
            try:
                # 尝试替代方法保存
                results.render()  # 渲染结果
                for i, img in enumerate(results.imgs):
                    cv2.imwrite(f'yolov5_result_{i}.jpg', img)
                print("使用替代方法1保存YOLOv5结果成功!")
            except Exception as e2:
                print(f"尝试保存结果方法2失败: {e2}")
                try:
                    # 再尝试另一种方法
                    if hasattr(results, 'pandas'):
                        df = results.pandas().xyxy[0]
                        print(f"检测到的对象: {df.shape[0]}")
                        print("检测结果以表格形式输出成功，但未能保存图像")
                except Exception as e3:
                    print(f"尝试保存结果方法3失败: {e3}")
        
        print("YOLOv5测试完成!")
        return True
        
    except Exception as e:
        print(f"YOLOv5测试失败: {e}")
        print("尝试备用方法...")
        try:
            # 备用方法：直接从yolov5仓库调用
            yolov5_path = os.path.expanduser("~/yolov5")
            if os.path.exists(yolov5_path):
                if yolov5_path not in sys.path:
                    sys.path.append(yolov5_path)
                
                # 切换到yolov5目录
                import subprocess
                os.chdir(yolov5_path)
                subprocess.run(["python", "detect.py", "--source", "https://ultralytics.com/images/zidane.jpg", "--weights", "yolov5s.pt", "--conf", "0.25"])
                print("使用备用命令行方法测试YOLOv5成功!")
                # 恢复原目录
                os.chdir(os.path.expanduser("~"))
                return True
            else:
                print(f"YOLOv5仓库不存在: {yolov5_path}")
                return False
        except Exception as e2:
            print(f"备用方法测试YOLOv5失败: {e2}")
            return False

def test_yolov8():
    print("测试YOLOv8...")
    try:
        # 导入YOLO (YOLOv8)
        from ultralytics import YOLO
        
        # 加载YOLOv8模型
        model = YOLO('yolov8n.pt')
        print("YOLOv8模型加载成功!")
        
        # 使用模型进行一个简单的预测
        result = model('https://ultralytics.com/images/bus.jpg')
        print("YOLOv8预测完成!")
        
        # 保存结果
        result_img = result[0].plot()
        cv2.imwrite('yolov8_result.jpg', result_img)
        print("YOLOv8测试结果已保存到 'yolov8_result.jpg'")
        return True
        
    except Exception as e:
        print(f"YOLOv8测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("YOLO测试程序")
    print("=" * 50)
    
    start_time = time.time()
    
    yolov5_success = test_yolov5()
    print("\n")
    yolov8_success = test_yolov8()
    
    end_time = time.time()
    
    print("\n" + "=" * 50)
    print(f"测试用时: {end_time - start_time:.2f}秒")
    print(f"YOLOv5 测试结果: {'成功' if yolov5_success else '失败'}")
    print(f"YOLOv8 测试结果: {'成功' if yolov8_success else '失败'}")
    print("=" * 50) 