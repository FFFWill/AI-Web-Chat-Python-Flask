import requests
from bs4 import BeautifulSoup
import time
import os

def get_history_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.baidu.com/'
    }

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取简介
        brief_div = soup.find('div', class_='block-content-right')
        brief_content = brief_div.get_text(strip=True) if brief_div else "暂无简介"

        # 提取历史事件列表
        event_list = []
        events_container = soup.find('div', class_='bd-box')
        if events_container:
            title_tag = events_container.find('h2')
            public_title = title_tag.get_text(strip=True) if title_tag else "历史上的今天"

            all_p_tags = events_container.find_all('p')
            for p in all_p_tags:
                content = p.get_text(strip=True)
                event_list.append({
                    'title': public_title,
                    'content': content
                })

        # 移除事件1、事件2和最后一个事件
        if len(event_list) > 2:
            event_list = event_list[2:-1]

        return {
            'brief': brief_content,
            'events': event_list
        }

    except Exception as e:
        print(f"爬取失败: {str(e)}")
        return None

def save_to_txt(data, path="./", filename_prefix="历史上的"):
    """
    将数据保存到txt文件
    :param path: 保存路径（默认当前目录）
    :param filename_prefix: 文件名前缀（默认"历史上的"）
    """
    try:
        # 生成时间字符串
        time_str = get_time()

        # 构造完整文件名
        filename = f"{filename_prefix}{time_str}.txt"

        # 组合完整路径
        full_path = os.path.join(path, filename)

        # 确保目录存在
        os.makedirs(path, exist_ok=True)

        # 写入文件（修复路径问题）
        with open(full_path, 'w', encoding='utf-8') as file:  # 使用full_path代替filename
            # 写入简介
            file.write("=== 今日简介 ===\n")
            file.write(data['brief'] + "\n\n")

            # 写入历史事件
            file.write("=== 历史事件 ===\n")
            for idx, event in enumerate(data['events'], 1):
                file.write(f"\n事件 {idx}:\n")
                file.write(f"标题: {event['title']}\n")
                file.write(f"内容: {event['content']}\n")
        print(f"数据已保存到 {full_path}")
    except Exception as e:
        print(f"保存文件失败: {str(e)}")

def get_time(fmt: str = '%m月%d日') -> str:
    """生成指定格式的时间字符串"""
    ts = time.time()
    ta = time.localtime(ts)
    return time.strftime(fmt, ta)

if __name__ == "__main__":
    target_url = "https://jintian.txcx.com/"
    save_path = "./listku/listku"  # 可以改为任意有效路径，如"D:/history_data"

    print("正在爬取数据，请稍候...")
    time.sleep(0.09)
    result = get_history_data(target_url)

    if result:
        save_to_txt(result,
                    path=save_path,
                    filename_prefix="历史上的")
    else:
        print("未能获取到数据")

    if result:
        # 打印到控制台
        print("\n=== 今日简介 ===")
        print(result['brief'])

        print("\n=== 历史事件 ===")
        for idx, event in enumerate(result['events'], 1):
            #print(f"\n事件 {idx}:")
            #print(f"标题: {event['title']}")
            print(f"{event['content']}")