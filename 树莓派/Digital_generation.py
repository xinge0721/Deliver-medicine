from PIL import Image, ImageDraw, ImageFont
import os
import random

# 创建data文件夹（如果不存在）
if not os.path.exists("data"):
    os.makedirs("data")
    print("创建data文件夹")

# A4尺寸参数
A4_WIDTH = 2480
A4_HEIGHT = 3508

# 创建九宫格布局（3x3）
rows = 3
cols = 3
cell_width = A4_WIDTH // cols
cell_height = A4_HEIGHT // rows

# 字体大小
font_size = 1000  # 较大的字体，但不至于超出单元格

for i in range(5):
    # 创建A4大小的白底图片
    img = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    # 尝试加载字体
    try:
        default_font = "arial.ttf"
        font = ImageFont.truetype(default_font, font_size)
    except Exception:
        print(f"Arial字体未找到，使用默认字体")
        # 在默认字体不可用时尝试其他常见字体
        try:
            default_font = "DejaVuSans.ttf"
            font = ImageFont.truetype(default_font, font_size)
        except Exception:
            print("使用默认字体")
            font = ImageFont.load_default()

    # 绘制九宫格中的随机数字（0-9）
    for row in range(rows):
        for col in range(cols):
            # 生成0~9的随机整数
            random_digit = random.randint(0, 9)
            
            # 计算文本尺寸
            try:
                # PIL 9.0.0及以上版本
                bbox = draw.textbbox((0, 0), str(random_digit), font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                try:
                    # 旧版PIL
                    text_width, text_height = draw.textsize(str(random_digit), font=font)
                except Exception:
                    # 如果无法获取尺寸，则估算
                    text_width = font_size // 2
                    text_height = font_size
                    print("警告: 无法获取文本尺寸，使用估计值")

            # 计算每个格子中数字的居中位置
            x = col * cell_width + (cell_width - text_width) // 2
            y = row * cell_height + (cell_height - text_height) // 2

            # 绘制数字
            draw.text((x, y), str(random_digit), fill="black", font=font)

    # 可选：绘制九宫格线条
    line_color = (200, 200, 200)  # 浅灰色
    line_width = 5

    # 画竖线
    for i in range(1, cols):
        x = i * cell_width
        draw.line([(x, 0), (x, A4_HEIGHT)], fill=line_color, width=line_width)

    # 画横线
    for i in range(1, rows):
        y = i * cell_height
        draw.line([(0, y), (A4_WIDTH, y)], fill=line_color, width=line_width)

    # 保存图片到data文件夹
    save_path = os.path.join("data", "numbers_random_3x3_grid{i}.jpg")
    img.save(save_path, "JPEG", quality=95)
    print(f"已生成随机数字九宫格图像: {save_path}")