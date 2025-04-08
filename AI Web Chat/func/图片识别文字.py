from PIL import Image
import pytesseract
import re
import cv2
import numpy as np
import os
from datetime import datetime


def get_time(fmt: str = '%Y年%m月%d日_%H时%M分%S秒') -> str:
    '''获取当前时间（文件名安全格式）'''
    return datetime.now().strftime(fmt)


pytesseract.pytesseract.tesseract_cmd = r"F:\Tesseract\tesseract.exe"#你的tesseract.exe的目录#可以在win环境变量设定方便一些


def get_latest_image():
    """获取image文件夹中最新的图片文件（基于创建时间）"""
    folder = './image'
    files = []

    #print("\n===== 正在扫描图片文件夹 =====")
    for f in os.listdir(folder):
        file_path = os.path.join(folder, f)

        # 跳过非图片文件
        if not f.lower().endswith(('.png', '.jpg', '.jpeg')):
            #print(f"跳过非图片文件: {f}")
            continue

        # 获取文件创建时间
        creation_time = os.path.getctime(file_path)
        files.append((creation_time, file_path))
        #print(f"有效文件: {f} -> 创建时间: {datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')}")

    if not files:
        raise FileNotFoundError("image文件夹中未找到有效图片文件")

    # 按创建时间排序并返回最新文件
    latest = max(files, key=lambda x: x[0])
    #print("\n===== 文件检测完成 =====")
    #print(f"找到 {len(files)} 个有效文件")
    #print(f"最新文件: {latest[1]} (创建时间: {datetime.fromtimestamp(latest[0]).strftime('%Y-%m-%d %H:%M:%S')})")
    return latest[1]


def get_list(image_path):
    # 使用Pillow打开图片
    image = Image.open(image_path)
    screenshot = np.array(image)

    # 1. 灰度化处理（减少颜色干扰，提升处理速度）
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    scale_factor = 1 # 放大一倍

    screenshot = cv2.resize(screenshot, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)

    # 使用pytesseract提取文字
    text = pytesseract.image_to_string(screenshot, lang='chi_sim+eng', config='--psm 11')

    # 清理文字
    cleaned_text = re.sub(r'[\r\n\t]+', ' ', text).strip()
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = re.sub(r'\s+', '', cleaned_text).strip()

    print("\n文字识别结果:")
    print(cleaned_text)
    return cleaned_text


def main():
    try:
        latest_image = get_latest_image()
        #print(f"\n正在处理最新图片: {latest_image}")
        get_list(latest_image)
    except FileNotFoundError as e:
        print(f"\n错误: {e}")
        print("请确保image文件夹中存在有效的图片文件")
    except Exception as e:
        print(f"\n发生未知错误: {str(e)}")


if __name__ == '__main__':
    main()