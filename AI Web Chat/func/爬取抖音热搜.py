import requests
import datetime
from typing import List, Dict
import time
import os


def get_time(fmt: str = '%Y年%m月%d日') -> str:#'%Y-%m-%d_%H-%M-%S'
    '''
    获取当前时间（文件名安全格式）
    '''
    ts = time.time()
    ta = time.localtime(ts)
    t = time.strftime(fmt, ta)
    return t


def save_douyin_hot_search(directory: str = None, filename: str = None) -> str:
    """
    获取抖音热搜榜数据并保存到指定文件

    参数:
        directory (str): 可选，指定保存目录（默认当前目录）
        filename (str): 可选，自定义文件名（默认格式：YYYY_MM_DD_当日抖音热搜.txt）

    返回:
        str: 保存文件的完整路径，或错误信息
    """
    hot_search_url = 'https://aweme-hl.snssdk.com/aweme/v1/hot/search/list/?detail_list=1'
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Mobile Safari/537.36"
    }

    # 处理默认文件名
    if not filename:
        today = datetime.date.today()
        formatted_date = today.strftime("%Y年%m月%d日")
        filename = f"{formatted_date}_当日抖音热搜热榜.txt"

    # 构建完整文件路径
    if directory:
        os.makedirs(directory, exist_ok=True)  # 自动创建目录（如果不存在）
        full_path = os.path.join(directory, filename)
    else:
        full_path = filename

    try:
        # 获取数据
        response = requests.get(hot_search_url, headers=headers)
        response.raise_for_status()
        hot_json = response.json()

        # 提取并保存数据
        with open(full_path, 'w', encoding='utf-8') as f:
            for data in hot_json['data']['word_list']:
                f.write(f"关键词: {data['word']}, 热度值: {data['hot_value']}\n")

        return full_path

    except requests.exceptions.RequestException as e:
        return f"请求失败: {str(e)}"
    except KeyError as e:
        return f"数据解析失败: 缺少字段 {str(e)}"
    except Exception as e:
        return f"发生未知错误: {str(e)}"



def get_douyin_hot_search_text() -> str:
    """
    获取当日抖音热搜数据并返回完整文本内容

    返回格式示例：
    "1. 关键词: 热点事件1, 热度值: 1234567
    2. 关键词: 热点事件2, 热度值: 987654
    ..."
    """
    hot_search_url = 'https://aweme-hl.snssdk.com/aweme/v1/hot/search/list/?detail_list=1'
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Mobile Safari/537.36"
    }

    try:
        response = requests.get(hot_search_url, headers=headers)
        response.raise_for_status()

        hot_json = response.json()
        hot_text = []

        for index, data in enumerate(hot_json['data']['word_list'], 1):
            hot_text.append(
                f"{index}. 关键词: {data['word']}, 热度值: {data['hot_value']}"
            )

        return "\n".join(hot_text)

    except requests.exceptions.RequestException as e:
        return f"请求失败: {str(e)}"
    except KeyError as e:
        return f"数据解析失败: 缺少关键字段 {str(e)}"
    except Exception as e:
        return f"发生未知错误: {str(e)}"

def main():
    save_directory = r"./listku/processed_listku"
    result = save_douyin_hot_search(directory=save_directory)#保存

    now = get_time()  # 获取现在时间
    text = f"【今日{now}的抖音热搜热榜】\n"
    hot_text = get_douyin_hot_search_text()#获取纯文本
    print(text,"\n",hot_text)#打印纯文本
    return hot_text#顺便返回



if __name__ == "__main__":
    main()


