import requests
import pandas as pd
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


def save_hot_list(folder_path: str = "./listku/processed_listku") -> None:  # 新增文件夹路径参数
    # 确保文件夹存在
    os.makedirs(folder_path, exist_ok=True)

    # 请求头
    headers = {
        'User-Agent': 'osee2unifiedRelease/4318 osee2unifiedReleaseVersion/7.7.0 Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
        'Host': 'api.zhihu.com',
    }
    # 请求参数
    params = (
        ('limit', '50'),
        ('reverse_order', '0'),
    )
    # 发送请求
    response = requests.get(
        'https://zhihu.com/topstory/hot-list', headers=headers, params=params)

    items = response.json()['data']
    rows = []
    now = get_time()

    # 遍历全部热榜，取出几个属性
    for rank, item in enumerate(items, start=1):
        target = item.get('target')
        title = target.get('title')
        answer_count = target.get('answer_count')
        hot = int(item.get('detail_text').split(' ')[0])
        follower_count = target.get('follower_count')
        question_url = target.get('url').replace(
            'api', 'www').replace('questions', 'question')
        rows.append({
            '排名': rank,
            '标题': title,
            '回答数': answer_count,
            '关注数': follower_count,
            '热度(万)': hot,
            '问题链接': question_url
        })

    df = pd.DataFrame(rows)
    # 保存到指定文件夹
    csv_path = os.path.join(folder_path, f"{now}_当日知乎热搜热榜.txt")
    df.to_csv(csv_path, encoding='utf-8-sig', index=None)
    # print(f"{now} 的热榜数据已保存到文件 {csv_path}")


# 保存热榜数据到指定文件夹
# save_hot_list("D:/知乎热榜数据/")  # 使用示例

def get_zhihu_hot_list() -> str:
    """
    获取知乎热榜数据并返回纯文本格式

    返回:
        str: 格式化的热榜纯文本数据
    """
    headers = {
        'User-Agent': 'osee2unifiedRelease/4318 osee2unifiedReleaseVersion/7.7.0 Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
        'Host': 'api.zhihu.com',
    }
    params = (
        ('limit', '50'),
        ('reverse_order', '0'),
    )

    try:
        response = requests.get(
            'https://zhihu.com/topstory/hot-list',
            headers=headers,
            params=params
        )
        response.raise_for_status()
    except requests.RequestException as e:
        return f"请求失败: {str(e)}"

    items = response.json()['data']
    now = get_time()
    text = f"【今日{now}的知乎热搜热榜】\n"
    text += "=" * 40 + "\n"

    for rank, item in enumerate(items, start=1):
        target = item.get('target')
        title = target.get('title', '无标题')
        answer_count = target.get('answer_count', 0)
        hot = int(item.get('detail_text', '0').split(' ')[0])
        follower_count = target.get('follower_count', 0)
        question_url = target.get('url', '').replace('api', 'www').replace('questions', 'question')

        text += f"排名: {rank:2d} | 热度: {hot:5d}万 | 回答数: {answer_count:4d} | 关注数: {follower_count:4d}\n"
        text += f"标题: {title}\n"
        text += f"链接: {question_url}\n"
        text += "-" * 40 + "\n"

    return text

def main():
    save_hot_list()
    hot_list_text = get_zhihu_hot_list()
    print(hot_list_text)
    return hot_list_text

if __name__ == "__main__":
    main()