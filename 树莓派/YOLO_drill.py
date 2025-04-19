from ultralytics import YOLO
import os


# 基础配置（不要随意修改底层设置）
def safe_train():
    # 加载模型（自动处理预训练权重）
    model = YOLO('last.pt')  # 自动包含预训练参数

    # 训练配置
    model.train(
        data='data.yaml',
        epochs=500,
        imgsz=640,  # 保持与预训练模型一致
        batch=16,  # 根据显存调整（推荐16-64）
        device='0',  # 使用GPU（确保CUDA可用）
        workers=4,  # 推荐设置为CPU核心数的1/2
        patience=50,  # 早停机制（默认值）
        save=True,
        exist_ok=True,
        resume=False  # 不要手动实现恢复逻辑
    )


if __name__ == '__main__':
    # 仅需设置必须的环境变量
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    safe_train()

