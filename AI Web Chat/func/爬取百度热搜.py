from bs4 import BeautifulSoup
import re
import urllib.request, urllib.error
import os
import time

def get_time(fmt: str = '%Y年%m月%d日') -> str:
    '''
    获取当前时间（文件名安全格式）
    '''
    ts = time.time()
    ta = time.localtime(ts)
    t = time.strftime(fmt, ta)
    return t

class TestHotsearch():
    def __init__(self):
        self.url = 'https://top.baidu.com/board?tab=realtime'
        self.all_content = "category-wrap_iQLoo horizontal_1eKyQ"

    def test_html_content(self):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        request = urllib.request.Request(self.url, headers=header)
        try:
            response = urllib.request.urlopen(request)
            html_content = response.read().decode("utf-8")
            return html_content.encode('gbk', 'ignore').decode('gbk')
        except urllib.error.URLError as e:
            print(f"请求失败: {e.reason}")
            return ""

    def test_get_content(self):
        html = self.test_html_content()
        data_info = []
        content = BeautifulSoup(html, "html.parser")

        for name in content.find_all('div', class_=self.all_content):
            # 提取标题
            title_element = name.find('div', class_='c-single-text-ellipsis')
            title = title_element.text.strip() if title_element else "N/A"

            # 提取简介
            intro_element = name.find('div', class_='hot-desc_1m_jR small_Uvkd3 ellipsis_DupbZ')
            introduction = intro_element.text.strip() if intro_element else "暂无简介"

            # 提取热度指数
            index_element = name.find('div', class_='hot-index_1Bl1a')
            index = index_element.text.strip() if index_element else "0"

            # 确保每个字段至少有一个元素
            cleaned_data = [
                [title],
                [introduction],
                [index]
            ]
            data_info.append(cleaned_data)
        return data_info

    def pretty_print(self, data, save_path=None):
        if not data:
            print("未获取到热搜数据")
            return

        # 计算最大宽度（增加空值检查）
        max_widths = [
            max(len(str(item[0][0])) for item in data if item[0]),
            max(len(str(item[1][0])) for item in data if item[1]),
            max(len(str(item[2][0])) for item in data if item[2])
        ]

        # 构建输出内容
        output = []
        # 标题行（无横线）
        output.append("{:^{width1}} | {:^{width2}} | {:^{width3}}".format(
            "热搜标题", "简介", "热度指数",
            width1=max_widths[0] + 4,
            width2=max_widths[1] + 4,
            width3=max_widths[2] + 4
        ))

        # 数据行（无横线）
        for item in data:
            title = item[0][0] if item[0] else "N/A"
            intro = item[1][0] if item[1] else "暂无简介"
            index = item[2][0] if item[2] else "0"

            output.append("{title:{width1}} | {intro:{width2}} | {index:{width3}}".format(
                title=title,
                intro=intro,
                index=index,
                width1=max_widths[0],
                width2=max_widths[1],
                width3=max_widths[2]
            ))

        # 打印到控制台
        print('\n'.join(output))

        # 保存到文件
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output))
            print(f"结果已保存到 {save_path}")

def main():
    now = get_time()
    print("以下为今日" + now + "的百度热搜热榜词条：")
    hot_search = TestHotsearch()
    get_content = hot_search.test_get_content()

    # 指定保存路径（例如：保存到当前目录下的output文件夹中的hot_search.txt）
    save_directory = "./listku/processed_listku"
    save_filename = "{}".format(get_time()) + "_当日百度热搜热榜.txt"
    save_path = os.path.join(save_directory, save_filename)

    hot_search.pretty_print(get_content, save_path=save_path)

if __name__ == "__main__":
    main()