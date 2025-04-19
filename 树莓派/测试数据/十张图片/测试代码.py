from ultralytics import YOLO
import numpy as np
from collections import Counter
import sys
import datetime
import os

class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')
        
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        
    def flush(self):
        self.terminal.flush()
        self.log.flush()

def main():
    # 设置日志文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "analysis_logs"
    
    # 创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_filename = os.path.join(log_dir, f"detection_analysis_{timestamp}.txt")
    
    # 设置输出同时写入到终端和文件
    sys.stdout = Logger(log_filename)
    
    print(f"数字识别分析报告 - 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"日志文件保存位置: {os.path.abspath(log_filename)}")
    print("=" * 80)
    
    # 加载YOLO模型，使用较小的模型版本以提高速度
    yolo = YOLO("best.pt") 
    cont = 9  # 9张不同的图片，每张对应一个数字(0-8)
    test_times = 10  # 每张图片测试10次
    
    expected_objects = 80  # 每张图片中预期的目标数量
    
    # 设置置信度阈值，减少误识别
    confidence_threshold = 0.25  # 可以调整这个值
    
    # 用于存储结果的数据结构
    all_results = {}
    digit_mapping = {
        "photo_1.jpg": "数字0",
        "photo_11.jpg": "数字1", 
        "photo_21.jpg": "数字2",
        "photo_31.jpg": "数字3",
        "photo_41.jpg": "数字4",
        "photo_51.jpg": "数字5",
        "photo_61.jpg": "数字6",
        "photo_71.jpg": "数字7", 
        "photo_81.jpg": "数字8"
    }
    
    # 类别ID到数字名称的映射
    class_mapping = {
        0: "数字0",
        1: "数字1",
        2: "数字未知", # 标签错位，模型中不应该有2对应数字2
        3: "数字2",    # 修正后的映射
        4: "数字3",    # 修正后的映射
        5: "数字4",    # 修正后的映射
        6: "数字5",    # 修正后的映射
        7: "数字6",    # 修正后的映射
        8: "数字7",    # 修正后的映射
        9: "数字8"     # 修正后的映射
    }
    
    # 从图片序号到预期类别ID的映射（处理标签错位）
    # 数字0和1正常，2及以后需要+1
    def get_expected_class(digit_index):
        # digit_index是0-8，对应数字0-8
        if digit_index <= 1:  # 数字0和1
            return digit_index
        else:  # 数字2及以后，标签+1
            return digit_index + 1
    
    print("=== 标签映射信息（由于训练时标签错位）===")
    print("图片中的数字 -> 模型预期的类别ID:")
    for i in range(cont):
        digit = i  # 0-8对应数字0-8
        expected_class = get_expected_class(i)
        print(f"  数字{digit} -> 类别ID {expected_class} ({class_mapping.get(expected_class, '未知')})")
    print("")
    
    # 对每张图片进行多次测试
    for i in range(cont):
        index = i * 10 + 1  # 生成序列1, 11, 21, 31, 41...
        img_path = "photo_"+str(index)+".jpg"
        digit_name = digit_mapping.get(img_path, f"未知数字({index})")
        expected_digit_class = get_expected_class(i)  # 考虑标签错位
        
        print(f"\n处理图片 {img_path} - {digit_name}:")
        print(f"  预期类别ID: {expected_digit_class} ({class_mapping.get(expected_digit_class, '未知类别')})")
        detection_counts = []
        confidence_scores = []
        class_counts_all_tests = []
        
        # 每张图片测试10次
        for test in range(test_times):
            # 获取检测结果
            results = yolo(img_path, save=(test == 0), conf=confidence_threshold)  # 应用置信度阈值
            
            # 获取所有检测框
            boxes = results[0].boxes
            detected_objects = len(boxes)
            
            # 统计检测到的各类别数量
            if detected_objects > 0:
                # 获取类别ID并转为列表
                class_ids = boxes.cls.cpu().numpy().astype(int)
                # 计算每个类别的检测数量
                class_counts = Counter(class_ids)
                
                # 收集置信度分数
                confidences = boxes.conf.cpu().numpy()
                avg_confidence = np.mean(confidences)
                confidence_scores.append(avg_confidence)
            else:
                class_counts = Counter()
                confidence_scores.append(0)
                
            class_counts_all_tests.append(class_counts)
            detection_counts.append(detected_objects)
            
            # 显示各类别检测数量
            class_report = ", ".join([f"{class_mapping.get(cls, f'类别{cls}')}: {count}" for cls, count in class_counts.items()])
            
            # 计算识别率和准确度
            detection_rate = detected_objects / expected_objects * 100
            
            print(f"  测试 {test+1}: 检测到 {detected_objects} 个目标, 识别率: {detection_rate:.2f}%")
            print(f"    类别分布: {class_report}")
            
            # 检查是否有明显的误识别
            if expected_digit_class in class_counts:
                correct_detections = class_counts[expected_digit_class]
                misclassified = detected_objects - correct_detections
                if misclassified > 0:
                    print(f"    警告: {misclassified} 个目标被错误分类 (应为 {class_mapping.get(expected_digit_class, '未知类别')})")
            else:
                print(f"    警告: 没有正确识别为 {class_mapping.get(expected_digit_class, '未知类别')} 的目标!")
                
            if detected_objects > expected_objects:
                print(f"    警告: 检测到 {detected_objects - expected_objects} 个额外目标 (假阳性)")
            elif detected_objects < expected_objects:
                print(f"    警告: 漏检了 {expected_objects - detected_objects} 个目标 (假阴性)")
        
        # 合并所有测试的类别统计
        merged_class_counts = Counter()
        for counts in class_counts_all_tests:
            merged_class_counts.update(counts)
        
        # 计算各类别的平均检测数量
        avg_class_counts = {cls: count/test_times for cls, count in merged_class_counts.items()}
        
        # 这张图片的预期类别
        expected_class = expected_digit_class
        
        # 计算正确识别和误识别比例
        total_detections = sum(detection_counts)
        correct_detections = merged_class_counts.get(expected_class, 0)
        correct_rate = correct_detections / total_detections * 100 if total_detections > 0 else 0
        
        # 找出主要的误识别类别
        misclassified_classes = {cls: count for cls, count in merged_class_counts.items() if cls != expected_class}
        major_misclassified = sorted(misclassified_classes.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # 计算这张图片的平均检测数和统计
        avg_detections = np.mean(detection_counts)
        std_dev = np.std(detection_counts)
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
        
        # 计算识别率和过度/欠检测
        avg_rate = avg_detections / expected_objects * 100
        overdetection = max(0, avg_detections - expected_objects)
        underdetection = max(0, expected_objects - avg_detections)
        
        all_results[img_path] = {
            "digit": digit_name,
            "avg_detections": avg_detections,
            "avg_rate": avg_rate,
            "std_dev": std_dev,
            "avg_confidence": avg_confidence,
            "overdetection": overdetection,
            "underdetection": underdetection,
            "correct_rate": correct_rate,
            "class_counts": avg_class_counts,
            "expected_class": expected_class
        }
        
        print(f"  图片 {img_path} ({digit_name}) 统计:")
        print(f"    预期类别ID: {expected_class} ({class_mapping.get(expected_class, '未知类别')})")
        print(f"    平均检测目标数: {avg_detections:.2f} (预期: {expected_objects})")
        print(f"    平均识别率: {avg_rate:.2f}%")
        print(f"    正确分类比例: {correct_rate:.2f}%")
        print(f"    平均置信度: {avg_confidence:.2f}")
        print(f"    过度检测: {overdetection:.2f} 个目标")
        print(f"    欠检测: {underdetection:.2f} 个目标")
        
        # 显示主要误识别情况
        if major_misclassified:
            print(f"    主要误识别:")
            for cls, count in major_misclassified:
                cls_name = class_mapping.get(cls, f"类别{cls}")
                error_rate = count / total_detections * 100
                print(f"      - 误识别为 {cls_name}: {count} 次 ({error_rate:.2f}%)")
    
    # 计算所有图片的总平均识别率和准确率
    all_avg_rates = [data["avg_rate"] for data in all_results.values()]
    overall_avg_rate = np.mean(all_avg_rates)
    
    total_overdetection = sum(data["overdetection"] for data in all_results.values()) / len(all_results)
    total_underdetection = sum(data["underdetection"] for data in all_results.values()) / len(all_results)
    overall_correct_rate = np.mean([data["correct_rate"] for data in all_results.values()])
    
    print("\n===== 总结报告 =====")
    print(f"所有图片的平均识别率: {overall_avg_rate:.2f}%")
    print(f"所有图片的平均正确分类率: {overall_correct_rate:.2f}%")
    print(f"平均过度检测: {total_overdetection:.2f} 个目标/图")
    print(f"平均欠检测: {total_underdetection:.2f} 个目标/图")
    print("\n各数字的识别情况:")
    
    for img_path, data in all_results.items():
        status = "正常" if 95 <= data["avg_rate"] <= 105 else "过度检测" if data["avg_rate"] > 105 else "欠检测"
        print(f"  {img_path} ({data['digit']}): 识别率 {data['avg_rate']:.2f}%, 正确分类 {data['correct_rate']:.2f}% - {status}")
        
        # 显示详细的误识别情况
        expected_cls = data["expected_class"]
        expected_count = data["class_counts"].get(expected_cls, 0)
        total_count = sum(data["class_counts"].values())
        
        # 只显示误识别率较高的类别
        misclassified = {cls: count for cls, count in data["class_counts"].items() if cls != expected_cls and count > 0}
        if misclassified:
            for cls, count in sorted(misclassified.items(), key=lambda x: x[1], reverse=True):
                cls_name = class_mapping.get(cls, f"类别{cls}")
                if count > expected_count * 0.1 or expected_count == 0:  # 只显示占比超过10%的误识别类别或者正确识别为0时
                    error_rate = count / total_count * 100 if total_count > 0 else 0
                    print(f"    - 误识别为 {cls_name}: {count:.1f} 个 ({error_rate:.2f}%)")
    
    print("\n" + "=" * 80)
    print(f"分析完成，结果已保存到文件: {os.path.abspath(log_filename)}")
    
    # 恢复标准输出
    sys.stdout = sys.__stdout__
    print(f"分析报告已保存到: {os.path.abspath(log_filename)}")

if __name__ == "__main__":
    main()
