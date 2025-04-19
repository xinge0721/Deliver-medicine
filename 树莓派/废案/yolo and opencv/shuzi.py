from PIL import Image, ImageDraw, ImageFont
import math
import random
import os

# 创建data文件夹（如果不存在）
if not os.path.exists("data"):
    os.makedirs("data")
    print("创建data文件夹")

# A4尺寸参数
A4_WIDTH = 2480
A4_HEIGHT = 3508

# 为YOLO训练优化数字布局参数
rows = 10
cols = 8
min_font_size = 60
max_font_size = 280

# 生成0~9的所有数字图像
for digit in range(10):
    # 创建A4大小的白底图片
    img = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体
    try:
        default_font = "arial.ttf"
    except IOError:
        print(f"Arial字体未找到，使用默认字体")
        default_font = None
    
    # 计算单元格大小
    cell_width = A4_WIDTH // cols
    cell_height = A4_HEIGHT // rows
    
    # 添加边距，避免数字太靠近边缘
    margin_x = cell_width // 6
    margin_y = cell_height // 6
    
    # 使用指数函数来增强变化幅度
    for row in range(rows):
        # 计算行的进度（0到1）
        row_progress = row / (rows - 1) if rows > 1 else 0
        
        for col in range(cols):
            # 计算列的进度（0到1）
            col_progress = col / (cols - 1) if cols > 1 else 0
            
            # 计算当前位置的字体大小，使用指数函数增强变化
            size_factor = math.pow(row_progress + col_progress/1.5, 1.5) / 1.5
            current_font_size = int(min_font_size + (max_font_size - min_font_size) * size_factor)
            
            # 确保字体大小在合理范围内
            current_font_size = max(min_font_size, min(current_font_size, max_font_size))
            
            # 创建字体对象
            try:
                if default_font:
                    font = ImageFont.truetype(default_font, current_font_size)
                else:
                    font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()
            
            # 为位置添加小的随机偏移，使数据更自然
            random_offset_x = random.randint(-margin_x//4, margin_x//4)
            random_offset_y = random.randint(-margin_y//4, margin_y//4)
            
            # 计算位置，确保数字在单元格内居中
            try:
                text_width, text_height = draw.textsize(str(digit), font=font)
            except AttributeError:
                text_width = current_font_size // 2
                text_height = current_font_size
                if row == 0 and col == 0:  # 仅显示一次警告
                    print("警告: 无法获取文本尺寸，使用估计值")
            
            x = col * cell_width + (cell_width - text_width) // 2 + random_offset_x
            y = row * cell_height + (cell_height - text_height) // 2 + random_offset_y
            
            # 绘制数字
            draw.text((x, y), str(digit), fill="black", font=font)
    
    # 保存图片到data文件夹
    save_path = os.path.join("data", f"number_{digit}_training.jpg")
    img.save(save_path, "JPEG", quality=95)
    print(f"已生成数字{digit}的训练图像: {save_path}")

print("所有0~9数字图像生成完成，已存放在data文件夹中，格式为JPG")